"""Automatic, resumable LOSO execution with an all-fold selection gate."""
from __future__ import annotations

from hashlib import sha256
import logging
from pathlib import Path

import numpy as np
import pandas as pd

from airsense_r.artifacts import RunStore, atomic_write, json_bytes
from airsense_r.checkpoints import open_run
from airsense_r.data.audit import EXPECTED_STATIONS
from airsense_r.data.pipeline import CausalPreprocessor, build_windows, read_stations, target_partition
from airsense_r.data.remote import temporary_uci_dataset, assert_same_acquisition, load_receipt
from airsense_r.evaluation.selection import metric_tables
from airsense_r.evaluation.site_shift import summarize_sites
from airsense_r.models.learned import predict_model
from airsense_r.p5 import (read_predictions, prediction_frame, save_predictions, require_selection,
                           tune_and_select, smoke_run, storage_identity)
from airsense_r.p5_recovery import frozen_model, local_writer_lock, REPLAY_ATOL, REPLAY_RTOL
from airsense_r.training.fold_store import FoldStore
from airsense_r.training.settings import training_provenance

LOG = logging.getLogger(__name__)
RUN_ID = "p7-sites-01"


def development_fold(frame: pd.DataFrame, station: str, stations: list[str], config: dict) -> pd.DataFrame:
    """Remove every held-out row before any fitting, tuning or selection."""
    if set(frame.station) != set(stations) or station not in stations:
        raise ValueError("Unexpected LOSO station inventory")
    if frame.timestamp.max() > pd.Timestamp(config["data"]["validation_target_end"]):
        raise ValueError("Development fold must not receive test rows")
    return frame.loc[frame.station != station].copy()


def require_fold_selection(fold: FoldStore, stations: list[str], station: str) -> dict:
    """Validate saved decision, station exclusion and fitted temporal cutoff."""
    decision = require_selection(fold)
    config = fold.manifest["provenance"]["config"]
    state = fold.load_json("preprocessing.json")
    if (set(state["fit_stations"]) != set(stations)-{station}
            or pd.Timestamp(state["fit_end"]) != pd.Timestamp(config["data"]["train_target_end"])):
        raise ValueError("LOSO preprocessing station/time exclusion failed")
    predictions = read_predictions(fold, "validation", round_trip=True)
    if set(predictions.station) != set(stations)-{station}:
        raise ValueError("Held-out station leaked into clean selection")
    return decision


def replay_fold(frame: pd.DataFrame, fold: FoldStore, models: Path) -> None:
    """Verify serialized native models on development predictions without fitting."""
    prov = fold.manifest["provenance"]
    config, plan = prov["config"], prov["training_plan"]
    if frame.timestamp.max() > pd.Timestamp(config["data"]["validation_target_end"]):
        raise ValueError("Replay must not receive test rows")
    processor = CausalPreprocessor.from_state(fold.load_json("preprocessing.json"))
    if set(frame.station) != set(processor.state["fit_stations"]):
        raise ValueError("Replay station set differs from training stations")
    reference = read_predictions(fold, "validation", round_trip=True)
    for family in config["models"]["candidates"]:
        windows = build_windows(frame, processor, scaled=family in {"mlp", "gru"})
        indices = np.flatnonzero(target_partition(windows.keys, config, "validation"))
        for seed in ([-1] if family == "persistence" else config["seeds"]["training"]):
            LOG.info("Development replay: %s / %s / seed %s", prov["parameters"]["held_out_station"], family, seed)
            model = None if family == "persistence" else frozen_model(fold, models, family, seed)
            predicted = predict_model(family, model, windows, indices, plan["prediction_batch_size"])
            saved = reference.loc[(reference.model == family) & (reference.seed == seed)].copy()
            saved["target_timestamp"] = pd.to_datetime(saved.target_timestamp)
            saved = saved.sort_values(["station", "target_timestamp"]).reset_index(drop=True)
            pd.testing.assert_frame_equal(windows.keys.iloc[indices].reset_index(drop=True), saved[["station", "target_timestamp"]])
            np.testing.assert_array_equal(windows.y[indices], saved.y_true.to_numpy())
            if not np.allclose(predicted, saved.y_pred, atol=REPLAY_ATOL, rtol=REPLAY_RTOL):
                raise ValueError("Native model replay differs; test remains locked")
            del model
        del windows
    fold.save("replay-complete.json", json_bytes({"passed": True, "model_refitting": False,
              "atol": REPLAY_ATOL, "rtol": REPLAY_RTOL}))


def freeze_selections(parent: RunStore, folds: dict[str, FoldStore]) -> dict:
    """Lock the complete twelve-fold decision ledger before test acquisition."""
    stations = sorted(folds)
    decisions = {s: require_fold_selection(folds[s], stations, s) for s in stations}
    ledger = {s: {"selected_family": decisions[s]["selected_family"],
                  "selection_sha256": folds[s].manifest["artifacts"]["selection.json"]["sha256"]}
              for s in stations}
    parent.save("all-selections-frozen.json", json_bytes(ledger))
    return decisions


def score_station(frame: pd.DataFrame, station: str, fold: FoldStore, models: Path) -> None:
    """Predict only the held-out station's test targets with frozen native models."""
    if set(frame.station) != {station} or not fold.has("replay-complete.json"):
        raise ValueError("Held-out scoring requires a passed development replay")
    prov = fold.manifest["provenance"]
    config, plan = prov["config"], prov["training_plan"]
    processor = CausalPreprocessor.from_state(fold.load_json("preprocessing.json"))
    if station in processor.state["fit_stations"]:
        raise ValueError("Cannot score a seen station as LOSO")
    for family in config["models"]["candidates"]:
        windows = build_windows(frame, processor, scaled=family in {"mlp", "gru"})
        indices = np.flatnonzero(target_partition(windows.keys, config, "test"))
        for seed in ([-1] if family == "persistence" else config["seeds"]["training"]):
            name = f"done-test-{family}-{seed}.json"
            if fold.has(name):
                continue
            LOG.info("Held-out scoring: %s / %s / seed %s", station, family, seed)
            model = None if family == "persistence" else frozen_model(fold, models, family, seed)
            predicted = predict_model(family, model, windows, indices, plan["prediction_batch_size"])
            save_predictions(fold, "test", prediction_frame(windows, indices, family, seed, "test", predicted), plan)
            fold.save(name, json_bytes({"complete": True, "held_out_station": station}))
            del model
        del windows
    fold.save("test-complete.json", json_bytes({"held_out_station": station, "complete": True}))


def finish_run(parent: RunStore, folds: dict[str, FoldStore], decisions: dict) -> None:
    """Publish cross-site outputs; execution completion still requires independent review."""
    for fold in folds.values():
        if not fold.has("test-complete.json"):
            raise ValueError("A held-out station is incomplete")
    predictions = pd.concat([read_predictions(f, "test", round_trip=True) for f in folds.values()], ignore_index=True)
    report = summarize_sites(predictions, decisions, parent.manifest["provenance"]["config"])
    table, aggregate = metric_tables(predictions)
    parent.save("metrics-test-station-seed.csv", table.to_csv(index=False, float_format="%.17g").encode())
    parent.save("metrics-test-aggregate.csv", aggregate.to_csv(index=False, float_format="%.17g").encode())
    parent.save("site-shift-report.json", json_bytes(report))
    parent.save("dashboard-test.json", json_bytes({"phase": "P7", "status": "awaiting_independent_review", **report}))
    import io
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    station_metrics = table.groupby(["station", "model"]).mae.mean().unstack()
    fig, ax = plt.subplots(figsize=(12, 5))
    station_metrics.plot.bar(ax=ax)
    ax.set(ylabel="Held-out MAE (micrograms/m3)", xlabel="Held-out station",
           title="Cross-site generalization: mean metric across training seeds")
    fig.tight_layout()
    output = io.BytesIO()
    fig.savefig(output, format="png", dpi=150, metadata={"Software": "AirSense-R"})
    plt.close(fig)
    parent.save("figure-site-mae.png", output.getvalue())
    parent.save("complete.json", json_bytes({"phase": "P7", "execution_complete": True,
        "scientifically_accepted": False, "held_out_stations": sorted(folds),
        "report_sha256": sha256(json_bytes(report)).hexdigest()}))


def export_run(root: Path, parent: RunStore) -> None:
    """Copy registered plot and explorer payloads to their public artifact locations."""
    parent.verify()
    for name, destination in [("figure-site-mae.png", root / "figures/p7-runs" / RUN_ID / "site-mae.png"),
                              ("dashboard-test.json", root / "docs/data/p7-runs" / RUN_ID / "test.json")]:
        atomic_write(destination, parent._path(name).read_bytes())


def run_site_shift(root: Path, model_directory: Path, remote: str) -> Path:
    """Run smoke, all-fold development, replay and held-out evaluation automatically."""
    if not remote:
        raise ValueError("P7 requires remote checkpoint synchronization")
    with local_writer_lock(root / ".tmp" / "p7-writer.lock"):
        storage = storage_identity(model_directory)
        prov = training_provenance(root, {"phase": "P7", "model_storage_id": storage,
            "run_id": RUN_ID, "stations": sorted(EXPECTED_STATIONS), "selection_gate": "all_folds_before_test"})
        parent = open_run(root, RUN_ID, prov, remote)
        model_root = model_directory / RUN_ID
        folds = {s: FoldStore(parent, s, model_root / "predictions") for s in sorted(EXPECTED_STATIONS)}
        if parent.has("complete.json"):
            export_run(root, parent)
            LOG.info("P7 execution already complete; verified saved artifacts. No training repeated.")
            return parent.directory
        with temporary_uci_dataset() as (data_root, receipt):
            assert_same_acquisition(receipt, load_receipt(root / "audit/acquisition_receipt.json"))
            d, spec = prov["config"]["data"], prov["training_plan"]["smoke"]
            if not parent.has("smoke-complete.json"):
                LOG.info("Automatic training-only runtime and persistent-model recovery check")
                smoke = read_stations(data_root, end=spec["score_end"])
                smoke_run(smoke.loc[smoke.station == spec["station"]].copy(), parent, model_root / "smoke")
                del smoke
            development = read_stations(data_root, end=d["validation_target_end"])
            for index, (station, fold) in enumerate(folds.items(), 1):
                LOG.info("P7 development fold %s/%s: hold out %s", index, len(folds), station)
                frame = development_fold(development, station, sorted(folds), prov["config"])
                if not fold.has("selection.json"):
                    tune_and_select(frame, fold, model_root / station)
                require_fold_selection(fold, sorted(folds), station)
                del frame
            decisions = freeze_selections(parent, folds)
            for station, fold in folds.items():
                replay_fold(development_fold(development, station, sorted(folds), prov["config"]),
                            fold, model_root / station)
            del development
            LOG.info("All selections frozen and native development replays passed. Test scoring is unlocked.")
            test = read_stations(data_root, end=d["test_target_end"])
            for index, (station, fold) in enumerate(folds.items(), 1):
                LOG.info("P7 held-out test fold %s/%s: %s", index, len(folds), station)
                score_station(test.loc[test.station == station].copy(), station, fold, model_root / station)
            finish_run(parent, folds, decisions)
        export_run(root, parent)
        LOG.info("P7 EXECUTION COMPLETE. Save the notebook for independent scientific review.")
        return parent.directory
