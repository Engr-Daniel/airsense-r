"""P4 execution and inspection shared by scripts and notebooks."""
from __future__ import annotations

from pathlib import Path
import json
import logging

import numpy as np
import pandas as pd

from airsense_r.artifacts import provenance, json_bytes, RunStore
from airsense_r.checkpoints import open_run
from airsense_r.corruption.noise import fit_noise_scales
from airsense_r.data.pipeline import CausalPreprocessor, build_windows, read_stations, target_partition, NUMERIC
from airsense_r.data.remote import temporary_uci_dataset, assert_same_acquisition, load_receipt

LOG = logging.getLogger(__name__)


def inspect_training_diagnostics(root: Path, directory: Path) -> pd.DataFrame:
    """Load verified training-only station means for notebook inspection."""
    manifest = json.loads((directory / "manifest.json").read_text())
    params = manifest["provenance"]["parameters"]
    if params.get("phase") != "P4" or not params.get("training_diagnostics") or params.get("structural_test_coverage"):
        raise ValueError("Expected a development-only diagnostics run")
    store = RunStore(directory, provenance(root, params))
    rows = []
    for name in sorted(store.manifest["artifacts"]):
        if name.startswith("training-diagnostics-"):
            item = store.load_json(name)
            if item["partition"] != "TRAIN ONLY":
                raise ValueError("Unexpected diagnostics partition")
            rows.append({"station": item["station"], "fit_end": item["end"],
                         **{col: values["mean"] for col, values in item["summary"].items()}})
    return pd.DataFrame(rows)


def review_audit(root: Path) -> pd.DataFrame:
    """Verify existing authoritative evidence and return structural station summaries."""
    receipt = load_receipt(root / "audit/acquisition_receipt.json")
    audit = json.loads((root / "audit/structural_audit.json").read_text())
    if audit["acquisition"]["sha256"] != receipt.sha256 or not audit["station_inventory_valid"]:
        raise ValueError("Invalid audit identity/inventory")
    station = pd.read_csv(root / "audit/station_summary.csv")
    from_json = pd.DataFrame(audit["stations"])
    fields = ["station", "rows", "target_missing", "pm25_complete_history_windows", "all_numeric_complete_history_windows"]
    pd.testing.assert_frame_equal(station[fields], from_json[fields], check_dtype=False)
    if station.rows.sum() != audit["rows_total"] or len(station) != 12:
        raise ValueError("Audit coverage mismatch")
    return station


def synthetic_stream() -> pd.DataFrame:
    """Small labelled fixture for fresh-kernel notebook smoke checks, never real evidence."""
    parts = []
    for station, offset in [("A", 0), ("B", 100)]:
        n = 96
        f = pd.DataFrame({"timestamp": pd.date_range("2014-01-01", periods=n, freq="h"), "station": station})
        for col in NUMERIC:
            f[col] = offset + np.arange(n, dtype=float) + 1
        f["wd"] = "N"
        f.loc[30:38, "NO2"] = np.nan
        f.loc[50, "PM2.5"] = np.nan
        parts.append(f)
    return pd.concat(parts, ignore_index=True)


def validate_synthetic_pipeline() -> dict:
    """Demonstrate causal transforms, shared keys and model input shapes on a fixture."""
    frame = synthetic_stream()
    processor = CausalPreprocessor().fit(frame, "2014-01-02 23:00", held_out_station="B")
    windows = build_windows(frame, processor)
    scaled = build_windows(frame, processor, scaled=True)
    pd.testing.assert_frame_equal(windows.keys, scaled.keys)
    selected = np.arange(min(4, len(windows.y)))
    sequence, cal = scaled.batch(selected)
    tabular, _ = windows.batch(selected, tabular=True)
    assert "B" not in processor.state["fit_stations"]
    assert np.isfinite(sequence).all()
    return {"synthetic_only": True, "samples": len(windows.y), "sequence_shape": list(sequence.shape),
            "tabular_shape": list(tabular.shape), "calendar_shape": list(cal.shape),
            "fit_stations": processor.state["fit_stations"]}


def run_pipeline(root: Path, run_id: str, *, remote: str | None = None,
                 held_out: str | None = None, policy: str = "primary",
                 internal_fold: int | None = None, training_diagnostics: bool = False,
                 structural_test_coverage: bool = False) -> Path:
    """Execute verified temporary acquisition, preprocessing and incremental coverage export.

    Default access ends at validation. Optional final-test access emits structural
    counts only, never metrics or test-distribution summaries.
    """
    params = {"phase": "P4", "held_out": held_out, "policy": policy,
              "internal_fold": internal_fold, "training_diagnostics": training_diagnostics,
              "structural_test_coverage": structural_test_coverage}
    prov = provenance(root, params)
    config = prov["config"]
    if policy not in {"primary", "sensitivity"}:
        raise ValueError("Unknown imputation policy")
    if internal_fold is not None and internal_fold not in (0, 1, 2):
        raise ValueError("Internal fold must be 0, 1 or 2")
    from airsense_r.data.audit import EXPECTED_STATIONS
    if held_out is not None and held_out not in EXPECTED_STATIONS:
        raise ValueError("Unknown held-out station")
    store = open_run(root, run_id, prov, remote)
    if store.has("complete.json"):
        LOG.info("Run already complete and provenance verified: %s", run_id)
        return store.directory
    cutoff = config["data"]["train_target_end"]
    if internal_fold is not None:
        cutoff = config["models"]["internal_folds"][internal_fold]["fit_end"]
    exposure_end = config["data"]["test_target_end" if structural_test_coverage else "validation_target_end"]
    with temporary_uci_dataset() as (data_root, receipt):
        assert_same_acquisition(receipt, load_receipt(root / "audit/acquisition_receipt.json"))
        frame = read_stations(data_root, end=exposure_end)
        processor = CausalPreprocessor(6 if policy == "primary" else 0).fit(frame, cutoff, held_out)
        training = frame.loc[(frame.timestamp <= pd.Timestamp(cutoff)) & (frame.station != held_out)]
        scales = fit_noise_scales(training, config["corruptions"]["noise_channels"])
        store.save("preprocessing.json", json_bytes({"processor": processor.state, "noise_scales": scales}))
        for station, part in frame.groupby("station", sort=True):
            filename = f"coverage-{station}.json"
            if store.has(filename):
                continue
            windows = build_windows(part.reset_index(drop=True), processor)
            counts = {p: int(target_partition(windows.keys, config, p).sum())
                      for p in ("train", "validation", "test")}
            if station == held_out:
                # Held-out windows are never offered as training/selection samples.
                counts["train"] = counts["validation"] = 0
            sample = np.arange(min(2, len(windows.y)))
            seq, _ = windows.batch(sample)
            report = {"station": station, "held_out": station == held_out,
                      "eligible_target_counts": counts, "history_shape": list(seq.shape[1:]),
                      "feature_names": processor.state["feature_names"],
                      "target_imputation": False, "final_test_analysis": "structural counts only"}
            store.save(filename, json_bytes(report))
            LOG.info("Saved station coverage: %s", station)
        if training_diagnostics:
            for station, part in training.groupby("station", sort=True):
                name = f"training-diagnostics-{station}.json"
                if store.has(name):
                    continue
                stats = part[list(NUMERIC)].describe().replace([np.inf, -np.inf], np.nan)
                payload = json.loads(stats.to_json())
                store.save(name, json_bytes({"partition": "TRAIN ONLY", "end": cutoff,
                                             "station": station, "summary": payload}))
        store.save("complete.json", json_bytes({"status": "complete", "stations": len(frame.station.unique()),
                                                "raw_data_retained": False, "model_experiments_run": False}))
    return store.directory
