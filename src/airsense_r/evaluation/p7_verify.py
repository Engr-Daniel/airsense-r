"""Independent verification of P7 saved rows and calendar-frequency uncertainty."""
from __future__ import annotations

from hashlib import sha256
import io
import json
from pathlib import Path
import re

import numpy as np
import pandas as pd
from scipy.stats import kendalltau
from threadpoolctl import threadpool_limits

from airsense_r.artifacts import json_bytes
from airsense_r.evaluation.p6_verify import Snapshot, sampling_weights

ATOL, RTOL = 1e-8, 1e-10


def check(actual, expected, path="result") -> None:
    """Compare complete nested structures, rejecting missing or additional fields."""
    if isinstance(actual, dict):
        if not isinstance(expected, dict) or actual.keys() != expected.keys():
            raise ValueError(f"Different fields: {path}")
        for key in actual:
            check(actual[key], expected[key], f"{path}.{key}")
    elif isinstance(actual, list):
        if len(actual) != len(expected):
            raise ValueError(f"Different length: {path}")
        for index, (a, b) in enumerate(zip(actual, expected)):
            check(a, b, f"{path}[{index}]")
    elif actual is None or isinstance(actual, (str, bool)):
        if actual != expected:
            raise ValueError(f"Different value: {path}")
    else:
        np.testing.assert_allclose(actual, expected, atol=ATOL, rtol=RTOL, err_msg=path)


def read_partition(snapshot: Snapshot, storage: Path, station: str, partition: str) -> pd.DataFrame:
    """Verify immutable Drive CSV bytes before parsing with round-trip precision."""
    prefix = f"fold-{station}--"
    names = sorted(n for n in snapshot.blobs if n.startswith(prefix + f"pred-{partition}-")
                   and n.endswith(".csv.reference.json"))
    if not names:
        raise ValueError("Prediction references missing")
    frames = []
    for name in names:
        filename = name[len(prefix):].removesuffix(".reference.json")
        if not re.fullmatch(r"pred-[A-Za-z0-9_.-]+\.csv", filename):
            raise ValueError("Unsafe prediction reference")
        path = storage / "p7-sites-01" / "predictions" / station / filename
        record = snapshot.json(name)
        raw = path.read_bytes()
        if path.is_symlink() or len(raw) != record["bytes"] or sha256(raw).hexdigest() != record["sha256"]:
            raise ValueError(f"Prediction checksum mismatch: {name}")
        frames.append(pd.read_csv(io.BytesIO(raw), float_precision="round_trip"))
    return pd.concat(frames, ignore_index=True)


def independent_metrics(frame: pd.DataFrame, stations: set[str], partition: str, config: dict) -> tuple:
    """Check full station/model/seed coverage and compute metrics without production helpers."""
    frame = frame.copy()
    frame["target_timestamp"] = pd.to_datetime(frame.target_timestamp)
    if set(frame.station) != stations or set(frame.partition) != {partition}:
        raise ValueError("Unexpected station/partition")
    start, end = (pd.Timestamp(config["data"][f"{partition}_target_{key}"]) for key in ("start", "end"))
    if not frame.target_timestamp.isin(pd.date_range(start, end, freq="h")).all() or not np.isfinite(frame[["y_true", "y_pred"]]).all().all():
        raise ValueError("Invalid values or temporal boundary")
    models = sorted(config["models"]["candidates"])
    expected = {(m, seed) for m in models for seed in
                ([-1] if m == "persistence" else config["seeds"]["training"])}
    if set(frame.groupby(["model", "seed"]).groups) != expected:
        raise ValueError("Incomplete candidate/seed matrix")
    reference, rows = None, []
    for (model, seed), group in frame.groupby(["model", "seed"], sort=True):
        keys = group.sort_values(["station", "target_timestamp"])[["station", "target_timestamp", "y_true"]].reset_index(drop=True)
        if keys.duplicated(["station", "target_timestamp"]).any():
            raise ValueError("Duplicate prediction targets")
        if reference is None:
            reference = keys
        else:
            pd.testing.assert_frame_equal(reference, keys, check_exact=True)
        for station, g in group.groupby("station", sort=True):
            y, pred = g.y_true.to_numpy(), g.y_pred.to_numpy()
            error = pred-y
            sse, sst = float(error @ error), float(np.sum((y-y.mean())**2))
            rows.append({"model": model, "seed": int(seed), "station": station, "n": len(g),
                         "mae": float(np.abs(error).mean()), "rmse": float(np.sqrt(sse/len(g))),
                         "r2": 1-sse/sst if sst else (1.0 if sse == 0 else 0.0)})
    table = pd.DataFrame(rows).sort_values(["model", "seed", "station"]).reset_index(drop=True)
    aggregate = table.groupby(["station", "model"])[["mae", "rmse", "r2"]].mean().groupby("model").mean().reset_index()
    return frame, table, aggregate


def verify_models(snapshot: Snapshot, storage: Path, station: str, decision: dict) -> int:
    """Verify final native bytes and identities without importing any model framework."""
    original = snapshot.manifest["provenance"]
    fold_prov = {**original, "parameters": {**original["parameters"], "held_out_station": station}}
    if set(decision["selected_configs"]) != set(original["config"]["models"]["candidates"])-{"persistence"}:
        raise ValueError("Incomplete final native model families")
    count = 0
    for family, candidate in decision["selected_configs"].items():
        for seed in original["config"]["seeds"]["training"]:
            task = f"refit-{family}-seed{seed}"
            identity = snapshot.json(f"fold-{station}--done-{task}.json")["checkpoint_identity"]
            if (identity["provenance_hash"] != sha256(json_bytes(fold_prov)).hexdigest()
                    or identity["family"] != family or identity["candidate"] != candidate or identity["seed"] != seed
                    or identity["processor"] != snapshot.json(f"fold-{station}--preprocessing.json")):
                raise ValueError("Final model identity differs")
            directory = storage / "p7-sites-01" / station / task
            if json.loads((directory / "identity.json").read_bytes()) != identity:
                raise ValueError("Drive model identity differs")
            progress = json.loads((directory / "progress.json").read_bytes())
            total = candidate["rounds" if family == "xgboost" else "epochs"]
            ref = snapshot.json(f"fold-{station}--model-{task}-{total:05d}.json")
            if {**progress, "task": task} != ref or progress["identity_hash"] != sha256(json_bytes(identity)).hexdigest():
                raise ValueError("Final native reference differs")
            if not re.fullmatch(r"step-[0-9]+-[a-f0-9]+\.(keras|ubj)", progress["file"]):
                raise ValueError("Unsafe native reference")
            path = directory / progress["file"]
            raw = path.read_bytes()
            if path.is_symlink() or len(raw) != progress["bytes"] or sha256(raw).hexdigest() != progress["sha256"]:
                raise ValueError("Native model checksum differs")
            count += 1
    return count


def independent_report(predictions: pd.DataFrame, decisions: dict, config: dict) -> dict:
    """Use explicit calendar-frequency weights, independent of prefix-sum bootstrap."""
    p, _, aggregate = independent_metrics(predictions, set(decisions), "test", config)
    models, stations = sorted(config["models"]["candidates"]), sorted(decisions)
    calendar = pd.date_range(config["data"]["test_target_start"], config["data"]["test_target_end"], freq="h")
    p["error"] = np.abs(p.y_true-p.y_pred)
    mean = p.groupby(["station", "model", "target_timestamp"]).error.mean()
    errors = np.array([[mean.loc[s, m].reindex(calendar).to_numpy() for m in models] for s in stations])
    valid = np.isfinite(errors)
    weights = sampling_weights(len(calendar), config)
    with threadpool_limits(limits=2):
        denominator = weights @ valid.reshape(-1, len(calendar)).astype(float).T
        if not (denominator > 0).all():
            raise ValueError("Empty bootstrap station")
        numerator = weights @ np.nan_to_num(errors).reshape(-1, len(calendar)).T
    reps = (numerator / denominator).reshape(len(weights), len(stations), len(models))
    point = np.nanmean(errors, axis=2)
    chosen = np.array([models.index(decisions[s]["selected_family"]) for s in stations])
    rows = np.arange(len(stations)); selected = point[rows, chosen]; samples = reps[:, rows, chosen]
    regrets = selected-point.min(axis=1); regret_samples = samples-reps.min(axis=2)
    alpha = (1-config["uncertainty"]["confidence"])/2
    def interval(estimate, values):
        low, high = np.quantile(values, [alpha, 1-alpha])
        return {"estimate": float(estimate), "ci_low": float(low), "ci_high": float(high)}
    reports = {}
    for j, s in enumerate(stations):
        validation = pd.Series(decisions[s]["validation_mae"]).reindex(models)
        test = pd.Series(point[j], index=models)
        tau = float(kendalltau(validation.to_numpy(), test.to_numpy()).statistic)
        reports[s] = {"selected_family": decisions[s]["selected_family"],
            "validation_mae": validation.to_dict(), "test_mae": test.to_dict(),
            "validation_ranks": validation.rank().to_dict(), "test_ranks": test.rank().to_dict(),
            "kendall_tau_b": tau if np.isfinite(tau) else None,
            "numerical_winner_retained": bool(selected[j] == point[j].min()),
            "within_practical_near_tie": bool(regrets[j] <= config["near_tie"]["absolute_threshold_ug_m3"]),
            "selection_regret": interval(regrets[j], regret_samples[:, j]),
            "differences": {m: interval(selected[j]-point[j,i], samples[:,j]-reps[:,j,i]) for i,m in enumerate(models)}}
    u = config["uncertainty"]
    return {"phase":"P7", "estimand":"cross_site_generalization_not_causal_penalty", "stations":reports,
        "fixed_family_metrics":aggregate.to_dict(orient="records"), "selected_policy_mae":float(selected.mean()),
        "mean_station_selection_regret":interval(regrets.mean(),regret_samples.mean(axis=1)),
        "policy_minus_fixed_family":{m:interval((selected-point[:,i]).mean(),(samples-reps[:,:,i]).mean(axis=1)) for i,m in enumerate(models)},
        "uncertainty":{"method":"paired_calendar_moving_block_bootstrap", "block_hours":u["block_length_hours"],
            "replicates":u["n_bootstrap"],"confidence":u["confidence"],"seed":config["seeds"]["bootstrap"],
            "conditional_on":"fitted_seeds_and_observed_stations"},
        "practical_threshold_ug_m3":config["near_tie"]["absolute_threshold_ug_m3"]}


def verify_run(snapshot: Snapshot, storage: Path, output, progress=print) -> pd.DataFrame:
    """Verify every file again on resume; checkpoint each fold and independent report."""
    prov = snapshot.manifest["provenance"]; config = prov["config"]
    ledger = snapshot.json("all-selections-frozen.json")
    if not snapshot.json("complete.json")["execution_complete"] or set(ledger) != set(prov["parameters"]["stations"]):
        raise ValueError("Incomplete P7 execution")
    if json.loads((storage / "storage.json").read_bytes())["storage_id"] != prov["parameters"]["model_storage_id"]:
        raise ValueError("Wrong Drive storage")
    if sha256(snapshot.blobs["site-shift-report.json"]).hexdigest() != snapshot.json("complete.json")["report_sha256"]:
        raise ValueError("Final report lineage differs")
    decisions, tests = {}, []
    for s in sorted(ledger):
        progress(f"P7 verification: {s} — checking saved CSVs, metrics and native model bytes")
        prefix = f"fold-{s}--"; decision = snapshot.json(prefix+"selection.json")
        if sha256(snapshot.blobs[prefix+"selection.json"]).hexdigest() != ledger[s]["selection_sha256"]:
            raise ValueError("Frozen selection ledger differs")
        prep = snapshot.json(prefix+"preprocessing.json")
        if set(prep["fit_stations"]) != set(ledger)-{s} or pd.Timestamp(prep["fit_end"]) != pd.Timestamp(config["data"]["train_target_end"]):
            raise ValueError("LOSO fitting station/time violation")
        if not snapshot.json(prefix+"replay-complete.json")["passed"] or not snapshot.json(prefix+"test-complete.json")["complete"]:
            raise ValueError("Missing replay/test gate")
        fold_prov={**prov,"parameters":{**prov["parameters"],"held_out_station":s}}
        if decision["provenance_hash"] != sha256(json_bytes(fold_prov)).hexdigest():
            raise ValueError("Selection provenance differs")
        validation = read_partition(snapshot, storage, s, "validation")
        _, _, aggregate = independent_metrics(validation, set(ledger)-{s}, "validation", config)
        scores = dict(zip(aggregate.model, aggregate.mae.astype(float)))
        check(scores, decision["validation_mae"])
        tied = [m for m in config["models"]["near_tie_tiebreak_order"] if scores[m] <= min(scores.values())+config["near_tie"]["absolute_threshold_ug_m3"]]
        if decision["near_ties"] != tied or decision["selected_family"] != tied[0] or ledger[s]["selected_family"] != tied[0]:
            raise ValueError("Frozen validation choice differs")
        refs = {n[len(prefix):].removesuffix('.reference.json'):snapshot.json(n)["sha256"] for n in snapshot.blobs if n.startswith(prefix+'pred-validation-') and n.endswith('.reference.json')}
        if refs != decision["validation_artifacts"]:
            raise ValueError("Validation prediction lineage differs")
        del validation
        native = verify_models(snapshot, storage, s, decision)
        test = read_partition(snapshot, storage, s, "test")
        test, table, _ = independent_metrics(test, {s}, "test", config)
        saved = pd.read_csv(io.BytesIO(snapshot.blobs["metrics-test-station-seed.csv"]), float_precision="round_trip")
        saved = saved.loc[saved.station==s].sort_values(["model","seed","station"]).reset_index(drop=True)
        check(table.to_dict('records'),saved.to_dict('records'))
        output.save(f"p7-verified-{s}.json",json_bytes({"passed":True,"native_models":native,"target_count":int(table.n.iloc[0])}))
        decisions[s]=decision;tests.append(test)
    predictions=pd.concat(tests,ignore_index=True)
    progress("P7 verification: independently recomputing paired calendar-block uncertainty")
    report=independent_report(predictions,decisions,config)
    check(report,snapshot.json("site-shift-report.json"))
    aggregate = pd.read_csv(io.BytesIO(snapshot.blobs["metrics-test-aggregate.csv"]), float_precision="round_trip")
    check(report["fixed_family_metrics"], aggregate.to_dict("records"))
    output.save("p7-independent-report.json",json_bytes(report))
    output.save("p7-verification.json",json_bytes({"passed":True,"prediction_files":sum(n.endswith('.csv.reference.json') for n in snapshot.blobs),
        "native_models":sum(len(decisions[s]["selected_configs"])*len(config['seeds']['training']) for s in ledger),
        "independent_metrics":True,"independent_bootstrap":True,"no_fitting_or_inference":True,"atol":ATOL,"rtol":RTOL}))
    return predictions
