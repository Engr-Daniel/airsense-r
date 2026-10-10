"""P5 clean benchmark: train-only tuning, locked selection, separate test access."""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
import logging
from pathlib import Path
import re
from uuid import uuid4

import numpy as np
import pandas as pd

from airsense_r.artifacts import RunStore, atomic_write, json_bytes
from airsense_r.checkpoints import open_run
from airsense_r.data.pipeline import CausalPreprocessor, build_windows
from airsense_r.data.pipeline import read_stations, target_partition
from airsense_r.data.remote import temporary_uci_dataset, assert_same_acquisition, load_receipt
from airsense_r.evaluation.selection import metric_tables, select_family
from airsense_r.evaluation.hourly_bootstrap import paired_hourly_intervals
from airsense_r.models.learned import data_identity, fit_model, load_model, predict_model
from airsense_r.training.settings import training_provenance
from airsense_r.training.storage import ModelCheckpoint

LOG = logging.getLogger(__name__)


def compatibility(prov: dict) -> str:
    """Identity required to promote a smoke-checked runtime to benchmark execution."""
    return sha256(json_bytes({k: prov[k] for k in ("source_hash", "environment", "training_plan_hash",
                                                 "config_hash", "protocol_hash", "dataset_sha256")})).hexdigest()


def storage_identity(directory: Path) -> str:
    """Create or verify a persistent destination marker without placing secrets in Git."""
    directory.mkdir(parents=True, exist_ok=True)
    marker = directory / "storage.json"
    if not marker.exists():
        atomic_write(marker, json_bytes({"storage_id": uuid4().hex}))
    identity = json.loads(marker.read_text())["storage_id"]
    if not re.fullmatch(r"[a-f0-9]{32}", identity):
        raise ValueError("Invalid persistent storage identity")
    return identity


def read_predictions(store: RunStore, phase: str) -> pd.DataFrame:
    """Load registered prediction shards only, validating every checksum first."""
    store.verify()
    names = sorted(n for n in store.manifest["artifacts"] if n.startswith(f"pred-{phase}-") and n.endswith(".csv"))
    if not names:
        raise ValueError(f"No {phase} predictions")
    return pd.concat([pd.read_csv(store.directory / n) for n in names], ignore_index=True)


def prediction_frame(windows, indices, family: str, seed: int, phase: str, predicted) -> pd.DataFrame:
    """Attach immutable original target keys/values to one candidate's predictions."""
    output = windows.keys.iloc[indices].copy().reset_index(drop=True)
    output["y_true"] = windows.y[indices]
    output["y_pred"] = predicted
    output["model"], output["seed"], output["partition"] = family, seed, phase
    return output


def save_predictions(store: RunStore, phase: str, frame: pd.DataFrame, plan: dict) -> None:
    """Publish bounded CSV shards during evaluation, preserving aligned target keys."""
    family, seed = frame.model.iloc[0], int(frame.seed.iloc[0])
    size = plan["prediction_shard_rows"]
    for part, start in enumerate(range(0, len(frame), size)):
        name = f"pred-{phase}-{family}-{seed}-{part:03d}.csv"
        store.save(name, frame.iloc[start:start+size].to_csv(index=False, float_format="%.17g").encode())


def unit_checkpoint(root: Path, task: str, identity: dict) -> ModelCheckpoint:
    """Resolve a controlled unit name under persistent model storage."""
    if not re.fullmatch(r"[A-Za-z0-9_-]+", task):
        raise ValueError("Invalid model unit name")
    return ModelCheckpoint(root / task, identity)


def train_unit(store: RunStore, model_root: Path, task: str, family: str, candidate: dict,
               seed: int, windows, train_indices, processor, plan: dict):
    """Train/resume one unit while publishing each persistent-model reference."""
    identity = {"provenance_hash": sha256(json_bytes(store.manifest["provenance"])).hexdigest(),
                "family": family, "candidate": candidate, "seed": seed,
                "data_hash": data_identity(windows, train_indices), "processor": processor.state}
    checkpoint = unit_checkpoint(model_root, task, identity)

    def publish(record: dict) -> None:
        store.save(f"model-{task}-{record['completed_units']:05d}.json",
                   json_bytes({"task": task, **record}))

    model = fit_model(family, candidate, seed, windows, train_indices, checkpoint, plan, publish)
    return model, checkpoint


def tune_and_select(frame: pd.DataFrame, store: RunStore, model_root: Path) -> dict:
    """Select family without loading final-test rows or using them for fitting."""
    prov = store.manifest["provenance"]
    config, plan = prov["config"], prov["training_plan"]
    d = config["data"]
    if frame.timestamp.max() > pd.Timestamp(d["validation_target_end"]):
        raise ValueError("Development runner must not receive final-test rows")
    selected_configs = {}
    for family, candidates in plan["families"].items():
        scores = {c["id"]: [] for c in candidates}
        for fold_index, fold in enumerate(config["models"]["internal_folds"]):
            processor = CausalPreprocessor().fit(frame, fold["fit_end"])
            fold_frame = frame.loc[frame.timestamp <= pd.Timestamp(fold["validation_end"])].copy()
            windows = build_windows(fold_frame, processor, scaled=family != "xgboost")
            ts = windows.keys.target_timestamp
            train = np.flatnonzero(ts.between(d["train_target_start"], fold["fit_end"]))
            score = np.flatnonzero(ts.between(fold["validation_start"], fold["validation_end"]))
            for candidate in candidates:
                for seed in config["seeds"]["training"]:
                    task = f"tune-{candidate['id']}-fold{fold_index}-seed{seed}"
                    done = f"score-{task}.json"
                    if store.has(done):
                        result = store.load_json(done)
                    else:
                        model, _ = train_unit(store, model_root, task, family, candidate, seed,
                                              windows, train, processor, plan)
                        pred = predict_model(family, model, windows, score, plan["prediction_batch_size"])
                        table, agg = metric_tables(prediction_frame(windows, score, family, seed, "internal", pred))
                        result = {"candidate": candidate["id"], "fold": fold_index, "seed": seed,
                                  "mean_station_mae": float(agg.mae.iloc[0]),
                                  "station_metrics": json.loads(table.to_json(orient="records"))}
                        store.save(done, json_bytes(result))
                        del model
                    scores[candidate["id"]].append(result["mean_station_mae"])
            del windows
        chosen = min(candidates, key=lambda c: float(np.mean(scores[c["id"]])))
        selected_configs[family] = chosen
        store.save(f"tuning-{family}.json", json_bytes({"selected_config": chosen,
                   "scores": {name: float(np.mean(values)) for name, values in scores.items()},
                   "tiebreak": "listed order", "target_scope": "training only"}))
    processor = CausalPreprocessor().fit(frame, d["train_target_end"])
    store.save("preprocessing.json", json_bytes(processor.state))
    for family in config["models"]["candidates"]:
        windows = build_windows(frame, processor, scaled=family in {"mlp", "gru"})
        train = np.flatnonzero(target_partition(windows.keys, config, "train"))
        val = np.flatnonzero(target_partition(windows.keys, config, "validation"))
        for seed in ([-1] if family == "persistence" else config["seeds"]["training"]):
            task = f"refit-{family}-seed{seed}"
            if store.has(f"done-{task}.json"):
                continue
            model = None
            metadata = {"family": family, "seed": seed}
            if family != "persistence":
                model, checkpoint = train_unit(store, model_root, task, family, selected_configs[family],
                                                seed, windows, train, processor, plan)
                metadata["checkpoint_identity"] = checkpoint.identity
                metadata["checkpoint_record"] = json.loads(checkpoint.pointer.read_text())
            pred = predict_model(family, model, windows, val, plan["prediction_batch_size"])
            save_predictions(store, "validation", prediction_frame(windows, val, family, seed, "validation", pred), plan)
            store.save(f"done-{task}.json", json_bytes(metadata))
            del model
        del windows
    predictions = read_predictions(store, "validation")
    decision = select_family(predictions, config)
    decision["selected_configs"] = selected_configs
    decision["provenance_hash"] = sha256(json_bytes(prov)).hexdigest()
    decision["validation_artifacts"] = {n: entry["sha256"] for n, entry in store.manifest["artifacts"].items()
                                         if n.startswith("pred-validation-")}
    store.save("selection.json", json_bytes(decision))
    export_summary(store, "validation", decision)
    return decision


def require_selection(store: RunStore) -> dict:
    """Verify a complete validation selection before final-test acquisition."""
    if not store.has("selection.json"):
        raise ValueError("Final test is locked: complete and save clean validation selection first")
    decision = store.load_json("selection.json")
    if decision["provenance_hash"] != sha256(json_bytes(store.manifest["provenance"])).hexdigest():
        raise ValueError("Selection provenance mismatch")
    for name, digest in decision["validation_artifacts"].items():
        if store.manifest["artifacts"].get(name, {}).get("sha256") != digest:
            raise ValueError("Selection evidence changed")
    recomputed = select_family(read_predictions(store, "validation"), store.manifest["provenance"]["config"])
    if any(decision[k] != value for k, value in recomputed.items()):
        raise ValueError("Selection decision disagrees with validated predictions")
    return decision


def evaluate_test(frame: pd.DataFrame, store: RunStore, model_root: Path, decision: dict) -> None:
    """Load frozen fitted states and score test targets; never fit during test access."""
    prov = store.manifest["provenance"]
    config, plan = prov["config"], prov["training_plan"]
    processor = CausalPreprocessor.from_state(store.load_json("preprocessing.json"))
    for family in config["models"]["candidates"]:
        windows = build_windows(frame, processor, scaled=family in {"mlp", "gru"})
        test = np.flatnonzero(target_partition(windows.keys, config, "test"))
        for seed in ([-1] if family == "persistence" else config["seeds"]["training"]):
            task = f"refit-{family}-seed{seed}"
            if store.has(f"done-test-{family}-{seed}.json"):
                continue
            model = None
            if family != "persistence":
                metadata = store.load_json(f"done-{task}.json")
                checkpoint = unit_checkpoint(model_root, task, metadata["checkpoint_identity"])
                if json.loads(checkpoint.pointer.read_text()) != metadata["checkpoint_record"]:
                    raise ValueError("Frozen refit model changed since validation")
                model = load_model(family, checkpoint)
            pred = predict_model(family, model, windows, test, plan["prediction_batch_size"])
            save_predictions(store, "test", prediction_frame(windows, test, family, seed, "test", pred), plan)
            store.save(f"done-test-{family}-{seed}.json", json_bytes({"complete": True}))
            del model
        del windows
    export_summary(store, "test", decision)
    settings = config["uncertainty"]
    intervals = paired_hourly_intervals(read_predictions(store, "test"), decision["selected_family"],
        start=config["data"]["test_target_start"], end=config["data"]["test_target_end"],
        block_hours=settings["block_length_hours"], n_bootstrap=settings["n_bootstrap"],
        seed=config["seeds"]["bootstrap"], confidence=settings["confidence"])
    store.save("test-uncertainty.json", json_bytes(intervals))
    store.save("complete.json", json_bytes({"phase": "P5", "clean_benchmark_complete": True,
                                            "selected_family": decision["selected_family"]}))


def export_summary(store: RunStore, phase: str, decision: dict) -> None:
    """Save publication-ready metric tables, a plot and a portable explorer payload."""
    table, aggregate = metric_tables(read_predictions(store, phase))
    store.save(f"metrics-{phase}-station-seed.csv", table.to_csv(index=False).encode())
    store.save(f"metrics-{phase}-aggregate.csv", aggregate.to_csv(index=False).encode())
    payload = {"phase": "P5", "partition": phase, "selected_family": decision["selected_family"],
               "metrics": json.loads(aggregate.to_json(orient="records")),
               "provenance": store.manifest["provenance"], "benchmark_status": "partial" if phase == "validation" else "scored"}
    store.save(f"dashboard-{phase}.json", json_bytes(payload))
    import io
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(aggregate.model, aggregate.mae)
    ax.set(ylabel="Equal-station MAE (micrograms/m3)", title=f"Clean {phase}: mean metric across seeds")
    fig.tight_layout()
    output = io.BytesIO()
    fig.savefig(output, format="png", dpi=150, metadata={"Software": "AirSense-R"})
    plt.close(fig)
    store.save(f"figure-{phase}-mae.png", output.getvalue())


def smoke_run(frame: pd.DataFrame, store: RunStore, model_root: Path) -> None:
    """Exercise actual adapters and interrupted-fit recovery using training-period data."""
    prov = store.manifest["provenance"]
    plan = deepcopy(prov["training_plan"])
    spec = plan["smoke"]
    if frame.timestamp.max() > pd.Timestamp(spec["score_end"]):
        raise ValueError("Smoke run must not expose later data")
    processor = CausalPreprocessor().fit(frame, spec["fit_end"])
    plan["xgboost_checkpoint_rounds"] = 2
    for family, candidates in plan["families"].items():
        if store.has(f"smoke-{family}.json"):
            continue
        candidate = {**candidates[0], "epochs": spec["epochs"], "rounds": spec["rounds"]}
        windows = build_windows(frame, processor, scaled=family != "xgboost")
        ts = windows.keys.target_timestamp
        train = np.flatnonzero(ts <= pd.Timestamp(spec["fit_end"]))
        score = np.flatnonzero(ts.between(spec["score_start"], spec["score_end"]))
        identity = {"provenance": prov, "candidate": candidate, "seed": spec["seed"],
                    "data_hash": data_identity(windows, train), "processor": processor.state}
        checkpoint = unit_checkpoint(model_root, f"smoke-{family}", identity)
        if checkpoint.restore()[0] == 0:
            try:
                fit_model(family, candidate, spec["seed"], windows, train, checkpoint, plan, stop_after=1)
            except InterruptedError:
                pass
        resumed = fit_model(family, candidate, spec["seed"], windows, train, checkpoint, plan)
        reference = unit_checkpoint(model_root, f"reference-{family}", identity)
        uninterrupted = fit_model(family, candidate, spec["seed"], windows, train, reference, plan)
        a = predict_model(family, resumed, windows, score)
        b = predict_model(family, uninterrupted, windows, score)
        restored = load_model(family, checkpoint)
        c = predict_model(family, restored, windows, score)
        np.testing.assert_allclose(a, b, rtol=1e-5, atol=1e-5)
        np.testing.assert_allclose(a, c, rtol=1e-6, atol=1e-6)
        store.save(f"smoke-{family}.json", json_bytes({"family": family, "engineering_only": True,
            "training_targets": len(train), "score_targets": len(score),
            "resume_max_abs_difference": float(np.max(np.abs(a-b))), "save_load_max_abs_difference": float(np.max(np.abs(a-c))),
            "complete_units": checkpoint.restore()[0]}))
        del resumed, uninterrupted, restored
    store.save("smoke-complete.json", json_bytes({"engineering_only": True, "compatibility": compatibility(prov)}))


def run_benchmark(root: Path, run_id: str, model_directory: Path, *, stage: str,
                  remote: str | None = None, local_only: bool = False) -> Path:
    """Execute smoke, development selection, or explicitly gated final-test scoring."""
    if stage not in {"smoke", "select", "test"}:
        raise ValueError("Unknown P5 stage")
    if not remote and not local_only:
        raise ValueError("Supply a Git remote or explicitly acknowledge --local-only")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", run_id):
        raise ValueError("Invalid run ID")
    storage_id = storage_identity(model_directory)
    prov = training_provenance(root, {"phase": "P5", "mode": "smoke" if stage == "smoke" else "benchmark",
                                     "model_storage_id": storage_id})
    acceptance = model_directory / "smoke-acceptance.json"
    if stage != "smoke":
        if not acceptance.exists() or json.loads(acceptance.read_text()).get("compatibility") != compatibility(prov):
            raise ValueError("Run training-only smoke on this code/environment/storage before a benchmark")
    if remote:
        store = open_run(root, run_id, prov, remote)
    else:
        LOG.warning("LOCAL ONLY: Git result backup is disabled for this run")
        store = RunStore(root / "results/p5" / run_id, prov)
    decision = require_selection(store) if stage == "test" else None
    if stage == "select" and store.has("selection.json"):
        require_selection(store)
        return store.directory
    if stage == "test" and store.has("complete.json"):
        return store.directory
    spec, d = prov["training_plan"]["smoke"], prov["config"]["data"]
    end = spec["score_end"] if stage == "smoke" else d["test_target_end" if stage == "test" else "validation_target_end"]
    with temporary_uci_dataset() as (data_root, receipt):
        assert_same_acquisition(receipt, load_receipt(root / "audit/acquisition_receipt.json"))
        frame = read_stations(data_root, end=end)
        if stage == "smoke":
            frame = frame.loc[frame.station == spec["station"]].reset_index(drop=True)
            smoke_run(frame, store, model_directory / run_id)
            atomic_write(acceptance, json_bytes({"compatibility": compatibility(prov), "smoke_run": run_id,
                                               "storage_id": storage_id}))
        elif stage == "select":
            tune_and_select(frame, store, model_directory / run_id)
        else:
            evaluate_test(frame, store, model_directory / run_id, decision)
    return store.directory


def export_run(root: Path, directory: Path) -> None:
    """Copy verified compact outputs to established figure and dashboard directories."""
    manifest = json.loads((directory / "manifest.json").read_text())
    store = RunStore(directory, manifest["provenance"])
    store.verify()
    for name in manifest["artifacts"]:
        if name.startswith("figure-"):
            target = root / "figures/p5-runs" / directory.name / name
        elif name.startswith("dashboard-"):
            target = root / "docs/data/p5-runs" / directory.name / name
        else:
            continue
        atomic_write(target, (directory / name).read_bytes())
