"""Frozen-model sensor degradation with development/clean replay and persistent predictions."""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
import logging
from pathlib import Path
import re
import subprocess

import numpy as np
import pandas as pd

from airsense_r.artifacts import RunStore, json_bytes, atomic_write
from airsense_r.checkpoints import open_run
from airsense_r.corruption.noise import fit_noise_scales
from airsense_r.data.pipeline import CausalPreprocessor, build_windows, read_stations, target_partition
from airsense_r.data.remote import temporary_uci_dataset, assert_same_acquisition, load_receipt
from airsense_r.data.stress import stress_stream
from airsense_r.evaluation.metrics import regression_metrics
from airsense_r.evaluation.stress_summary import reliability_summary, stress_intervals
from airsense_r.models.learned import predict_model
from airsense_r.p5 import require_selection, read_predictions
from airsense_r.p5_recovery import frozen_model, verify_validation, local_writer_lock, PARENT_RUN
from airsense_r.p6_storage import PredictionBundles
from airsense_r.training.settings import training_provenance

LOG = logging.getLogger(__name__)
CLEAN_RUN = "p5-clean-01-corrected-02"
CLEAN_COMMIT = "118ae94a23517319d1c31b1159f25a9b77f6b230"
POLICIES = ("primary", "no_ffill")


def conditions(config: dict) -> list[dict]:
    """Enumerate all frozen conditions; no outcome-dependent subset selection."""
    c, seeds = config["corruptions"], config["seeds"]["corruption"]
    cases = []
    for kind, levels in (("random_dropout", c["random_dropout_levels"]), ("noise", c["noise_levels"])):
        cases.extend({"id": f"{kind}-{round(level*100):02d}", "kind": kind, "severity": level,
                      "channel": None, "seeds": seeds} for level in levels)
    cases.extend({"id": f"whole-{channel}", "kind": "whole_variable", "severity": 1,
                  "channel": channel, "seeds": [-1]} for channel in c["whole_variable_dropout"])
    cases.extend({"id": f"outage-{channel}-{hours}", "kind": "outage", "severity": hours,
                  "channel": channel, "seeds": seeds} for channel in c["contiguous_outage_channels"]
                 for hours in c["contiguous_outage_hours"])
    return cases


def accepted_clean(root: Path, remote: str) -> RunStore:
    """Read exact accepted P5 results without modifying or publishing their branch."""
    directory = root / ".tmp" / "p6-clean-parent" / CLEAN_COMMIT
    def git(*args):
        result = subprocess.run(["git", *args], capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError("Unable to read accepted clean-result checkout")
        return result.stdout.strip()
    if not directory.exists():
        directory.parent.mkdir(parents=True, exist_ok=True)
        git("clone", "--no-checkout", "--single-branch", "--branch", f"results/{CLEAN_RUN}",
            "--config", "core.autocrlf=false", remote, str(directory))
        git("-C", str(directory), "checkout", "--detach", CLEAN_COMMIT)
    if (git("-C", str(directory), "rev-parse", "HEAD") != CLEAN_COMMIT
            or git("-C", str(directory), "remote", "get-url", "origin") != remote
            or git("-C", str(directory), "status", "--porcelain")):
        raise ValueError("Accepted clean checkout changed; inspect without resetting it")
    output = directory / "results" / CLEAN_RUN
    manifest = json.loads((output / "manifest.json").read_text())
    store = RunStore(output, manifest["provenance"])
    if (not store.load_json("complete.json")["clean_benchmark_complete"]
            or not store.load_json("validation-replay-complete.json")["passed"]):
        raise ValueError("Accepted clean evaluation is incomplete")
    require_selection(store)
    return store


class ReplayEvidence:
    """Read frozen evidence; publish only replay reports to the new P6 run."""
    def __init__(self, parent: RunStore, output: RunStore):
        self.parent, self.output = parent, output
        self.directory, self.manifest = parent.directory, parent.manifest

    def verify(self) -> None:
        self.parent.verify()

    def load_json(self, name: str) -> object:
        return self.parent.load_json(name)

    def save(self, name: str, data: bytes) -> None:
        if not name.startswith("replay-") and name != "validation-replay-complete.json":
            raise ValueError("Only replay reports may be published")
        self.output.save("development-" + name, data)


def policy_processor(state: dict, policy: str) -> CausalPreprocessor:
    """Use original numeric statistics under primary or inference-only no-fill sensitivity."""
    if policy not in POLICIES:
        raise ValueError("Unknown imputation policy")
    state = deepcopy(state)
    if policy == "no_ffill":
        state["forward_fill_hours"] = 0
    return CausalPreprocessor.from_state(state)


def targets(frame: pd.DataFrame, processor: CausalPreprocessor, config: dict) -> dict[str, np.ndarray]:
    """Return canonical original targets and keys in the frozen test period."""
    windows = build_windows(frame, processor)
    indices = np.flatnonzero(target_partition(windows.keys, config, "test"))
    keys = windows.keys.iloc[indices].reset_index(drop=True)
    return {"station": keys.station.to_numpy(dtype=str),
            "time": keys.target_timestamp.to_numpy(dtype="datetime64[ns]").astype("int64"),
            "y": windows.y[indices]}


def aligned_indices(windows, expected: dict[str, np.ndarray], config: dict) -> np.ndarray:
    """Reject different ordering, target values, or eligible observations."""
    indices = np.flatnonzero(target_partition(windows.keys, config, "test"))
    keys = windows.keys.iloc[indices]
    for actual, wanted in ((keys.station.to_numpy(dtype=str), expected["station"]),
            (keys.target_timestamp.to_numpy(dtype="datetime64[ns]").astype("int64"), expected["time"]),
            (windows.y[indices], expected["y"])):
        np.testing.assert_array_equal(actual, wanted)
    return indices


def outage_affected(targets: dict, events: list[dict], lookback: int = 24) -> np.ndarray:
    """Mark exactly the target histories intersecting at least one outage event."""
    time = pd.to_datetime(targets["time"])
    affected = np.zeros(len(time), dtype=bool)
    for event in events:
        start, end = pd.Timestamp(event["start"]), pd.Timestamp(event["end"])
        affected |= ((targets["station"] == event["station"]) & (time >= start+pd.Timedelta(hours=1))
                     & (time <= end+pd.Timedelta(hours=lookback)))
    return affected


def model_keys(config: dict) -> list[tuple[str, int]]:
    """Include all training seeds; persistence is never artificially replicated."""
    return [(family, seed) for family in config["models"]["candidates"]
            for seed in ([-1] if family == "persistence" else config["seeds"]["training"])]


def predict_case(frame: pd.DataFrame, original: pd.DataFrame, state: dict, policy: str,
                 case_id: str, models: dict, bundles: PredictionBundles, config: dict,
                 expected: dict[str, np.ndarray], plan: dict) -> dict[tuple[str, int], np.ndarray]:
    """Checkpoint each model/seed's predictions; reuse only checksum-verified arrays."""
    output = {}
    for scaled in (False, True):
        processor = policy_processor(state, policy)
        windows = None
        for family, seed in model_keys(config):
            if (family in {"mlp", "gru"}) != scaled:
                continue
            name = f"pred-{policy}-{case_id}-{family}-{seed}"
            if bundles.has(name):
                pred = bundles.load(name)["prediction"]
            else:
                if windows is None:
                    windows = build_windows(frame, processor, scaled=scaled, targets=original)
                    indices = aligned_indices(windows, expected, config)
                LOG.info("P6 prediction: %s %s %s seed=%s", policy, case_id, family, seed)
                pred = predict_model(family, models.get((family, seed)), windows, indices, plan["prediction_batch_size"])
                bundles.save(name, {"prediction": pred})
            if pred.shape != expected["y"].shape or not np.isfinite(pred).all():
                raise ValueError("Invalid saved prediction shape or values")
            output[(family, seed)] = pred
        del windows
    return output


def score_rows(predictions: dict, clean: dict, expected: dict, masks: dict,
               corruption_seed: int) -> pd.DataFrame:
    """Retain station/training/corruption-seed metrics and matched clean comparators."""
    rows = []
    for scope, mask in masks.items():
        for station in sorted(set(expected["station"])):
            subset = mask & (expected["station"] == station)
            if not subset.any():
                raise ValueError("No targets in an affected station; cannot silently drop it")
            y = expected["y"][subset]
            for (family, seed), pred in predictions.items():
                row = {"scope": scope, "station": station, "model": family, "seed": seed,
                    "corruption_seed": corruption_seed, "n": int(subset.sum()),
                    **regression_metrics(y, pred[subset]),
                    **{"clean_"+k: v for k, v in regression_metrics(y, clean[(family, seed)][subset]).items()}}
                rows.append(row)
    return pd.DataFrame(rows)


def error_calendar(predictions: dict, expected: dict, mask: np.ndarray, config: dict) -> np.ndarray:
    """Average absolute errors over fitted seeds, preserving original hourly gaps."""
    stations = sorted(set(expected["station"]))
    models = config["models"]["candidates"]
    calendar = pd.date_range(config["data"]["test_target_start"], config["data"]["test_target_end"], freq="h")
    output = np.full((len(models), len(stations), len(calendar)), np.nan)
    offsets = calendar.get_indexer(pd.to_datetime(expected["time"]))
    if (offsets < 0).any():
        raise ValueError("Targets outside test calendar")
    for i, family in enumerate(models):
        mean = np.mean([np.abs(pred-expected["y"]) for (f, _), pred in predictions.items() if f == family], axis=0)
        for j, station in enumerate(stations):
            subset = mask & (expected["station"] == station)
            output[i, j, offsets[subset]] = mean[subset]
    return output


def realization_audit(frame: pd.DataFrame, stressed: pd.DataFrame, events: list[dict],
                      spec: dict, seed: int, config: dict) -> dict:
    """Record deterministic realization identity and counts without retaining raw data."""
    cols = config["corruptions"]["random_dropout_channels"]
    start = pd.Timestamp(config["data"]["test_target_start"])-pd.Timedelta(hours=24)
    end = pd.Timestamp(config["data"]["test_target_end"])-pd.Timedelta(hours=1)
    eligible = frame.timestamp.between(start, end)
    raw = stressed.loc[eligible, ["station", "timestamp", *cols]].to_csv(index=False, float_format="%.17g").encode()
    before, after = frame.loc[eligible, cols], stressed.loc[eligible, cols]
    changed = ~(before.eq(after) | (before.isna() & after.isna()))
    return {"condition": spec, "seed": seed, "stream_sha256": sha256(raw).hexdigest(),
            "changed_cells": {c: int(changed[c].sum()) for c in cols}, "outage_events": events,
            "target_unchanged": bool(frame["PM2.5"].equals(stressed["PM2.5"]))}


def evaluate_conditions(frame: pd.DataFrame, parent: RunStore, store: RunStore,
                        bundles: PredictionBundles, models: dict, config: dict,
                        plan: dict, scales: dict) -> None:
    """Evaluate the entire frozen matrix, checkpointing model predictions and summaries."""
    state = parent.load_json("preprocessing.json")
    expected = bundles.load("targets")
    selected = require_selection(parent)["selected_family"]
    specs = conditions(config)
    for policy in POLICIES:
        clean = predict_case(frame, frame, state, policy, "clean", models, bundles, config, expected, plan)
        all_mask = np.ones(len(expected["y"]), dtype=bool)
        store.save(f"clean-{policy}-metrics.csv", score_rows(clean, clean, expected, {"full": all_mask}, -1).to_csv(index=False).encode())
        for spec in specs:
            summary_name = f"summary-{policy}-{spec['id']}.json"
            # Predictions remain required: verify every registered file even on resume.
            if store.has(summary_name):
                for corruption_seed in spec["seeds"]:
                    unit = f"{spec['id']}-c{corruption_seed}"
                    store.load_json(f"realization-{unit}.json")
                    if not store.has(f"metrics-{policy}-{unit}.csv"):
                        raise ValueError("Completed condition is missing seed metrics")
                    for family, seed in model_keys(config):
                        pred = bundles.load(f"pred-{policy}-{unit}-{family}-{seed}")["prediction"]
                        if pred.shape != expected["y"].shape or not np.isfinite(pred).all():
                            raise ValueError("Invalid completed condition prediction")
                LOG.info("Verified completed condition: %s %s", policy, spec["id"])
                continue
            clean_errors, stress_errors, metric_parts = {}, {}, []
            for corruption_seed in spec["seeds"]:
                unit = f"{spec['id']}-c{corruption_seed}"
                stressed, events = stress_stream(frame, config, spec["kind"], spec["severity"],
                                                corruption_seed, scales, spec["channel"])
                pd.testing.assert_series_equal(frame["PM2.5"], stressed["PM2.5"])
                audit = realization_audit(frame, stressed, events, spec, corruption_seed, config)
                store.save(f"realization-{unit}.json", json_bytes(audit))
                predictions = predict_case(stressed, frame, state, policy, unit, models, bundles, config, expected, plan)
                np.testing.assert_array_equal(predictions[("persistence", -1)], clean[("persistence", -1)])
                masks = {"full": all_mask}
                if spec["kind"] == "outage":
                    masks["affected"] = outage_affected(expected, events)
                metrics = score_rows(predictions, clean, expected, masks, corruption_seed)
                store.save(f"metrics-{policy}-{unit}.csv", metrics.to_csv(index=False).encode())
                metric_parts.append(metrics)
                for scope, mask in masks.items():
                    clean_errors.setdefault(scope, []).append(error_calendar(clean, expected, mask, config))
                    stress_errors.setdefault(scope, []).append(error_calendar(predictions, expected, mask, config))
                del stressed, predictions
            combined = pd.concat(metric_parts, ignore_index=True)
            reports = {}
            for scope in clean_errors:
                rows = combined.loc[combined.scope == scope]
                report = reliability_summary(rows, selected, config["near_tie"]["absolute_threshold_ug_m3"])
                intervals = stress_intervals(np.stack(clean_errors[scope]), np.stack(stress_errors[scope]),
                    config["models"]["candidates"], selected, sorted(set(expected["station"])), config)
                if scope == "full" and not intervals["available"]:
                    raise ValueError("Headline uncertainty unavailable; do not mark condition complete")
                if intervals["available"]:
                    np.testing.assert_allclose(report["selection_regret"], intervals["selection_regret"]["estimate"], rtol=1e-10, atol=1e-10)
                report["uncertainty"] = intervals
                reports[scope] = report
            store.save(summary_name, json_bytes({"policy": policy, "condition": spec, "scopes": reports}))
            LOG.info("P6 condition complete: %s %s", policy, spec["id"])
    export_summaries(store, specs)
    store.save("complete.json", json_bytes({"phase": "P6", "sensor_degradation_complete": True,
        "policies": list(POLICIES), "conditions_per_policy": len(specs), "selected_family": selected}))


def export_summaries(store: RunStore, specs: list[dict]) -> None:
    """Produce compact dashboard data and condition-level MAE/regret figures."""
    reports = [store.load_json(f"summary-{p}-{s['id']}.json") for p in POLICIES for s in specs]
    store.save("dashboard-p6.json", json_bytes({"phase": "P6", "reports": reports}))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import io
    for policy in POLICIES:
        current = [r for r in reports if r["policy"] == policy]
        fig, ax = plt.subplots(figsize=(12, 5))
        for model in ("persistence", "xgboost", "mlp", "gru"):
            ax.plot([r["condition"]["id"] for r in current],
                [next(m["mae"] for m in r["scopes"]["full"]["metrics"] if m["model"] == model) for r in current], marker="o", label=model)
        ax.set_ylabel("Equal-station MAE (PM2.5 micrograms/m³)")
        ax.tick_params(axis="x", rotation=70)
        ax.set_title(f"Frozen models under sensor degradation: {policy}")
        ax.legend(); fig.tight_layout()
        buffer = io.BytesIO(); fig.savefig(buffer, format="png", dpi=140); plt.close(fig)
        store.save(f"figure-p6-{policy}.png", buffer.getvalue())


def run_p6(root: Path, run_id: str, model_directory: Path, remote: str, stage: str) -> Path:
    """Preflight accepted models, then explicitly opt into the complete stress matrix."""
    if stage not in {"preflight", "evaluate"} or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", run_id):
        raise ValueError("Invalid P6 stage/run ID")
    with local_writer_lock(root / ".tmp" / "p6-writer.lock"):
        parent = accepted_clean(root, remote)
        marker = model_directory / "storage.json"
        if not marker.is_file():
            raise ValueError("Original persistent model storage is required")
        storage_id = json.loads(marker.read_text())["storage_id"]
        if storage_id != parent.manifest["provenance"]["parameters"]["model_storage_id"]:
            raise ValueError("Wrong model storage identity")
        prov = training_provenance(root, {"phase": "P6", "mode": "frozen_sensor_evaluation",
            "model_storage_id": storage_id, "clean_run": CLEAN_RUN, "clean_result_commit": CLEAN_COMMIT,
            "policies": list(POLICIES), "implementation_decisions_sha256": sha256(
                (root / "research/P6_IMPLEMENTATION_DECISIONS.md").read_bytes().replace(b"\r\n", b"\n")).hexdigest()})
        for key in ("config_hash", "protocol_hash", "dataset_sha256", "training_plan_hash"):
            if prov[key] != parent.manifest["provenance"][key]:
                raise ValueError(f"Frozen P5 setting differs: {key}")
        store = open_run(root, run_id, prov, remote)
        store.save("lineage.json", json_bytes({"clean_result_commit": CLEAN_COMMIT,
            "clean_manifest_sha256": sha256((parent.directory / "manifest.json").read_bytes()).hexdigest(),
            "clean_provenance": parent.manifest["provenance"], "selection": require_selection(parent),
            "model_run": PARENT_RUN, "model_refitting": False}))
        bundles = PredictionBundles(model_directory / "p6-artifacts" / run_id, store)
        if stage == "evaluate" and not store.has("preflight-complete.json"):
            raise ValueError("Run the P6 preflight stage first")
        config, plan = prov["config"], prov["training_plan"]
        with temporary_uci_dataset() as (data_root, receipt):
            assert_same_acquisition(receipt, load_receipt(root / "audit/acquisition_receipt.json"))
            development = read_stations(data_root, end=config["data"]["validation_target_end"])
            if stage == "preflight":
                verify_validation(development, ReplayEvidence(parent, store), model_directory / PARENT_RUN)
            # Every invocation checks native model hashes before using any snapshots.
            models = {(family, seed): frozen_model(parent, model_directory / PARENT_RUN, family, seed)
                      for family, seed in model_keys(config) if family != "persistence"}
            train = development.loc[development.timestamp <= pd.Timestamp(config["data"]["train_target_end"])]
            scales = fit_noise_scales(train, config["corruptions"]["noise_channels"])
            store.save("noise-scales.json", json_bytes({"fit_end": config["data"]["train_target_end"], "scales": scales}))
            del development, train
            frame = read_stations(data_root, end=config["data"]["test_target_end"])
            state = parent.load_json("preprocessing.json")
            expected = targets(frame, policy_processor(state, "primary"), config)
            bundles.save("targets", expected)
            if stage == "preflight":
                clean = predict_case(frame, frame, state, "primary", "clean", models, bundles, config, expected, plan)
                reference = read_predictions(parent, "test", round_trip=True)
                for (family, seed), pred in clean.items():
                    saved = reference.loc[(reference.model == family) & (reference.seed == seed)].sort_values(["station", "target_timestamp"])
                    np.testing.assert_array_equal(saved.station.to_numpy(dtype=str), expected["station"])
                    np.testing.assert_array_equal(pd.to_datetime(saved.target_timestamp).to_numpy(dtype="datetime64[ns]").astype("int64"), expected["time"])
                    np.testing.assert_array_equal(saved.y_true.to_numpy(), expected["y"])
                    if not np.allclose(pred, saved.y_pred, atol=1e-5, rtol=1e-6):
                        raise ValueError(f"Accepted clean predictions differ: {family}/{seed}")
                store.save("preflight-complete.json", json_bytes({"passed": True, "development_replay": True,
                    "accepted_clean_replay": True, "persistent_prediction_round_trip": True, "no_stress_evaluated": True}))
            else:
                evaluate_conditions(frame, parent, store, bundles, models, config, plan, scales)
        for name in store.manifest["artifacts"]:
            if name.startswith("figure-"):
                atomic_write(root / "figures/p6-runs" / run_id / name, (store.directory / name).read_bytes())
            elif name == "dashboard-p6.json":
                atomic_write(root / "docs/data/p6-runs" / run_id / name, (store.directory / name).read_bytes())
        return store.directory
