"""Independent, read-only verification of saved P6 predictions and uncertainty.

No model or production P6 metric/bootstrap function is called. Bootstrap samples
are represented as timestamp frequency weights, independently of the production
error-prefix implementation. Original outputs are never changed.
"""
from __future__ import annotations

from hashlib import sha256
import io
import json
from pathlib import Path
import re
from typing import Callable

import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

from airsense_r.artifacts import RunStore, json_bytes

ATOL = 1e-8
RTOL = 1e-10


class Snapshot:
    """Verify a frozen Git snapshot once and read its checksum-verified bytes."""

    def __init__(self, directory: Path):
        self.raw_manifest = (directory / "manifest.json").read_bytes()
        self.manifest = json.loads(self.raw_manifest)
        self.blobs = {}
        for name, record in self.manifest["artifacts"].items():
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*\.(json|csv|png|svg|ipynb)", name):
                raise ValueError("Unsafe artifact name")
            path = directory / name
            raw = path.read_bytes()
            if path.is_symlink() or sha256(raw).hexdigest() != record["sha256"]:
                raise ValueError(f"Corrupt Git artifact: {name}")
            self.blobs[name] = raw

    def json(self, name: str) -> dict:
        """Read a registered JSON artifact."""
        return json.loads(self.blobs[name])


def read_bundle(directory: Path, name: str, snapshot: Snapshot) -> dict[str, np.ndarray]:
    """Check exact Drive bytes, shape and dtype before deserialization."""
    if not re.fullmatch(r"[A-Za-z0-9_-]+", name):
        raise ValueError("Unsafe bundle name")
    record = snapshot.json(f"bundle-{name}.json")
    if record["file"] != name + ".npz":
        raise ValueError("Bundle reference filename mismatch")
    path = directory / record["file"]
    if path.is_symlink():
        raise ValueError("Symlink bundle forbidden")
    raw = path.read_bytes()
    if len(raw) != record["bytes"] or sha256(raw).hexdigest() != record["sha256"]:
        raise ValueError(f"Drive file differs from final Git reference: {name}")
    with np.load(io.BytesIO(raw), allow_pickle=False) as data:
        result = {key: data[key] for key in data.files}
    if set(result) != set(record["arrays"]):
        raise ValueError("Bundle arrays differ")
    for key, array in result.items():
        if list(array.shape) != record["arrays"][key]["shape"] or str(array.dtype) != record["arrays"][key]["dtype"]:
            raise ValueError("Bundle shape/dtype differs")
    return result


def sampling_weights(hours: int, config: dict) -> np.ndarray:
    """Explicitly count calendar-hour occurrences in each frozen block sample."""
    block = config["uncertainty"]["block_length_hours"]
    if not 1 <= block <= hours:
        raise ValueError("Invalid block length")
    lengths = [min(block, hours - offset) for offset in range(0, hours, block)]
    rng = np.random.default_rng(config["seeds"]["bootstrap"])
    weights = np.empty((config["uncertainty"]["n_bootstrap"], hours), dtype=np.float64)
    for b in range(len(weights)):
        starts = rng.integers(0, hours-block+1, size=len(lengths))
        indices = np.concatenate([np.arange(start, start+length) for start, length in zip(starts, lengths)])
        weights[b] = np.bincount(indices, minlength=hours)
    return weights


def independently_bootstrap(clean: np.ndarray, stress: np.ndarray, weights: np.ndarray,
                            models: list[str], stations: list[str], selected: str,
                            confidence: float) -> dict:
    """Recompute uncertainty using weighted timestamp counts and matrix products."""
    valid = np.isfinite(clean)
    if (clean.shape != stress.shape or clean.ndim != 4
            or not np.array_equal(valid, np.isfinite(stress))
            or not np.array_equal(valid, np.broadcast_to(valid[:, :1], valid.shape))
            or not valid.any(axis=-1).all()):
        raise ValueError("Unaligned or empty paired targets")
    shape = clean.shape[:-1]
    with threadpool_limits(limits=2):
        counts = weights @ valid.reshape(-1, clean.shape[-1]).astype(float).T
        if np.any(counts == 0):
            return {"available": False}
        sampled = []
        points = []
        for errors in (clean, stress):
            totals = weights @ np.nan_to_num(errors).reshape(-1, errors.shape[-1]).T
            sampled.append((totals / counts).reshape(len(weights), *shape).mean(axis=1))
            points.append(np.nanmean(errors, axis=-1).mean(axis=0))
    # Each element is [replicate, model, station]; realizations were averaged first.
    aggregate = [x.mean(axis=-1) for x in sampled]
    point = [x.mean(axis=-1) for x in points]
    chosen = models.index(selected)
    alpha = (1-confidence)/2
    def interval(values: np.ndarray, estimate: float) -> dict:
        lower, upper = np.quantile(values, [alpha, 1-alpha])
        return {"estimate": float(estimate), "ci_low": float(lower), "ci_high": float(upper)}
    return {"available": True,
        "differences": {m: interval(aggregate[1][:, chosen]-aggregate[1][:, i], point[1][chosen]-point[1][i])
                        for i, m in enumerate(models)},
        "selection_regret": interval(aggregate[1][:, chosen]-aggregate[1].min(axis=1), point[1][chosen]-point[1].min()),
        "station_changes": {m: {s: interval(sampled[1][:, i, j]-sampled[0][:, i, j], points[1][i, j]-points[0][i, j])
                                for j, s in enumerate(stations)} for i, m in enumerate(models)}}


def compare_numbers(actual: dict, expected: dict) -> None:
    """Compare independently calculated values without changing scientific tolerances."""
    for key, value in actual.items():
        if isinstance(value, dict):
            compare_numbers(value, expected[key])
        elif isinstance(value, bool):
            if value != expected[key]:
                raise ValueError(f"Verification differs: {key}")
        else:
            np.testing.assert_allclose(value, expected[key], atol=ATOL, rtol=RTOL, err_msg=key)


def affected_targets(station: np.ndarray, time: np.ndarray, events: list[dict], lookback: int) -> np.ndarray:
    """Select targets whose strictly past input interval intersects an outage."""
    affected = np.zeros(len(time), dtype=bool)
    for event in events:
        first = pd.Timestamp(event["start"]).value + 3600*10**9
        last = pd.Timestamp(event["end"]).value + lookback*3600*10**9
        affected |= (station == event["station"]) & (time >= first) & (time <= last)
    return affected


def verify_saved_run(snapshot: Snapshot, directory: Path, output: RunStore,
                     progress: Callable[[str], None] = print) -> dict:
    """Verify all saved files on every invocation; checkpoint each condition review."""
    config = snapshot.manifest["provenance"]["config"]
    identity = json.loads((directory / "identity.json").read_bytes())
    if identity != {"provenance_hash": sha256(json_bytes(snapshot.manifest["provenance"])).hexdigest()}:
        raise ValueError("Wrong Drive run identity")
    if not snapshot.json("complete.json")["sensor_degradation_complete"]:
        raise ValueError("Original evaluation is incomplete")
    names = sorted(k[7:-5] for k in snapshot.blobs if k.startswith("bundle-"))
    for i, name in enumerate(names, 1):
        read_bundle(directory, name, snapshot)
        if i % 25 == 0 or i == len(names):
            progress(f"Checking saved files: {i}/{len(names)}")
    output.save("files-verified.json", json_bytes({"verified": len(names), "passed": True}))
    target = read_bundle(directory, "targets", snapshot)
    station, time, y = target["station"], target["time"], target["y"]
    if not (station.ndim == time.ndim == y.ndim == 1 and len(station) == len(time) == len(y)):
        raise ValueError("Target arrays are not aligned")
    if not np.isfinite(y).all() or pd.MultiIndex.from_arrays([station, time]).has_duplicates:
        raise ValueError("Invalid/duplicate targets")
    calendar = pd.date_range(config["data"]["test_target_start"], config["data"]["test_target_end"], freq="h")
    offsets = calendar.get_indexer(pd.to_datetime(time))
    if np.any(offsets < 0):
        raise ValueError("Targets outside frozen calendar")
    stations = sorted(set(station)); models = config["models"]["candidates"]
    selected = snapshot.json("lineage.json")["selection"]["selected_family"]
    keys = [(m, seed) for m in models for seed in ([-1] if m == "persistence" else config["seeds"]["training"])]
    weights = None
    reports = snapshot.json("dashboard-p6.json")["reports"]
    if len(reports) != 2 * snapshot.json("complete.json")["conditions_per_policy"]:
        raise ValueError("Incomplete report matrix")
    def predictions(policy: str, unit: str) -> dict:
        result = {}
        for model, seed in keys:
            pred = read_bundle(directory, f"pred-{policy}-{unit}-{model}-{seed}", snapshot)["prediction"]
            if pred.shape != y.shape or not np.isfinite(pred).all():
                raise ValueError("Invalid prediction array")
            result[(model, seed)] = pred
        return result
    def errors(preds: dict, mask: np.ndarray) -> np.ndarray:
        result = np.full((len(models), len(stations), len(calendar)), np.nan)
        for i, model in enumerate(models):
            mean = np.mean([np.abs(v-y) for (m, _), v in preds.items() if m == model], axis=0)
            for j, s in enumerate(stations):
                take = (station == s) & mask
                result[i, j, offsets[take]] = mean[take]
        return result
    clean_cache = {}
    for number, report in enumerate(reports, 1):
        policy, spec = report["policy"], report["condition"]
        checkpoint = f"review-{policy}-{spec['id']}.json"
        if output.has(checkpoint):
            progress(f"Verified review checkpoint {number}/{len(reports)}: {policy} {spec['id']}")
            continue
        progress(f"Reviewing condition {number}/{len(reports)}: {policy} {spec['id']}")
        if weights is None:
            weights = sampling_weights(len(calendar), config)
        if policy not in clean_cache:
            clean_cache[policy] = predictions(policy, "clean")
        clean = clean_cache[policy]
        pairs = {scope: ([], []) for scope in report["scopes"]}
        metric_rows = []
        for corruption_seed in spec["seeds"]:
            unit = f"{spec['id']}-c{corruption_seed}"
            preds = predictions(policy, unit)
            np.testing.assert_array_equal(preds[("persistence", -1)], clean[("persistence", -1)])
            masks = {"full": np.ones(len(y), dtype=bool)}
            if "affected" in pairs:
                masks["affected"] = affected_targets(station, time,
                    snapshot.json(f"realization-{unit}.json")["outage_events"], config["data"]["lookback_hours"])
            saved = pd.read_csv(io.BytesIO(snapshot.blobs[f"metrics-{policy}-{unit}.csv"]), float_precision="round_trip")
            if len(saved) != len(masks)*len(stations)*len(keys) or saved.duplicated(["scope", "station", "model", "seed"]).any():
                raise ValueError("Missing/duplicate seed metrics")
            for scope, mask in masks.items():
                pairs[scope][0].append(errors(clean, mask)); pairs[scope][1].append(errors(preds, mask))
                for s in stations:
                    take = mask & (station == s); truth = y[take]
                    if not len(truth):
                        raise ValueError("Empty station subset")
                    for model, seed in keys:
                        calculated = {}
                        for prefix, source in (("", preds), ("clean_", clean)):
                            residual = source[(model, seed)][take]-truth
                            sse = float(residual @ residual); sst = float(np.sum((truth-truth.mean())**2))
                            calculated.update({prefix+"mae": float(np.abs(residual).mean()),
                                prefix+"rmse": float(np.sqrt(sse/len(truth))),
                                prefix+"r2": 1-sse/sst if sst else (1.0 if sse == 0 else 0.0)})
                        row = saved.loc[(saved.scope == scope) & (saved.station == s) & (saved.model == model) & (saved.seed == seed)]
                        if len(row) != 1 or int(row.iloc[0]["n"]) != len(truth) or int(row.iloc[0].corruption_seed) != corruption_seed:
                            raise ValueError("Metric key/count differs")
                        compare_numbers(calculated, row.iloc[0].to_dict())
                        metric_rows.append({"scope": scope, "station": s, "model": model,
                                            "corruption_seed": corruption_seed, **calculated})
        checked = {}
        for scope, (a, b) in pairs.items():
            rows = pd.DataFrame(metric_rows).query("scope == @scope")
            cols = ["mae", "rmse", "r2", "clean_mae", "clean_rmse", "clean_r2"]
            grouped = rows.groupby(["model", "station", "corruption_seed"])[cols].mean()
            scores = grouped.groupby(["model", "station"]).mean().groupby("model").mean()
            summary = report["scopes"][scope]
            for metric in summary["metrics"]:
                actual = scores.loc[metric["model"]].to_dict()
                actual["rpd_percent"] = 100*(actual["mae"]/actual["clean_mae"]-1)
                actual["clean_rank"] = float(scores.clean_mae.rank(method="average").loc[metric["model"]])
                actual["stress_rank"] = float(scores.mae.rank(method="average").loc[metric["model"]])
                actual["rank_change"] = actual["stress_rank"]-actual["clean_rank"]
                compare_numbers(actual, metric)
            regret = float(scores.loc[selected, "mae"]-scores.mae.min())
            compare_numbers({"selection_regret": regret}, summary)
            oracle = set(scores.index[scores.mae == scores.mae.min()])
            near = set(scores.index[scores.mae <= scores.mae.min()+summary["threshold"]])
            if (set(summary["test_oracle_families"]) != oracle or set(summary["near_ties"]) != near
                    or summary["selected_is_numerical_best"] != (selected in oracle)
                    or summary["selected_within_practical_near_tie"] != (selected in near)):
                raise ValueError("Winner/near-tie summary differs")
            if "near_tie" in config and summary["threshold"] != config["near_tie"]["absolute_threshold_ug_m3"]:
                raise ValueError("Practical threshold differs")
            u = summary["uncertainty"]
            if (u["replicates"] != config["uncertainty"]["n_bootstrap"]
                    or u["block_hours"] != config["uncertainty"]["block_length_hours"]):
                raise ValueError("Uncertainty settings differ")
            intervals = independently_bootstrap(np.asarray(a), np.asarray(b), weights, models, stations, selected,
                                                config["uncertainty"]["confidence"])
            compare_numbers(intervals, summary["uncertainty"])
            checked[scope] = {"metrics_match": True, "intervals": intervals}
        output.save(checkpoint, json_bytes({"passed": True, "policy": policy, "condition": spec["id"], "scopes": checked}))
        progress(f"Saved and synchronized review {number}/{len(reports)}")
    complete = {"passed": True, "prediction_files": len(names), "condition_reports": len(reports),
                "independent_metrics": True, "independent_bootstrap": True,
                "comparison_atol": ATOL, "comparison_rtol": RTOL, "no_models_fitted_or_predicted": True}
    output.save("complete.json", json_bytes(complete))
    progress("COMPLETE: saved predictions, metrics and uncertainty verified and synchronized.")
    return complete
