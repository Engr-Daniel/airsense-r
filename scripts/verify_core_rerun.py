"""P11 clean-environment rerun of the core data pipeline and deterministic baseline.

Downloads the authoritative UCI archive into temporary storage, checks it against
the frozen acquisition receipt, refits the training-only preprocessing, rebuilds
test windows and regenerates persistence predictions. Every output is compared
with the accepted, checksum-verified corrected P5 artifacts. Learned models are
not refitted here; no selection or test-informed choice is made.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import logging
from pathlib import Path
import platform
import subprocess
import sys

import numpy as np
import pandas as pd
import yaml

from airsense_r.artifacts import json_bytes, source_hash
from airsense_r.data.pipeline import CausalPreprocessor, build_windows, read_stations, target_partition
from airsense_r.data.remote import assert_same_acquisition, load_receipt, temporary_uci_dataset
from airsense_r.explorer import GitSnapshot, P5_DIRECTORY
from airsense_r.models.learned import predict_model

ROOT = Path(__file__).resolve().parents[1]
LOG = logging.getLogger("p11")
KEYS = ["station", "target_timestamp"]
# Means/stds are float reductions whose last bits depend on numpy/pandas summation order.
MOMENT_RTOL = 1e-10


def compare_state(refit: dict, accepted: dict) -> dict:
    """Exact for structure, medians and features; explicit relative tolerance for moments."""
    exact = [k for k in accepted if k not in ("means", "stds")]
    if refit.keys() != accepted.keys() or any(
        refit[k].keys() != accepted[k].keys() for k in ("means", "stds")
    ):
        return {"passed": False, "bitwise_identical": False, "reason": "State keys differ"}
    if any(not np.isfinite(v) for state in (refit, accepted)
           for k in ("means", "stds") for v in state[k].values()):
        return {"passed": False, "bitwise_identical": False, "reason": "Nonfinite moments"}
    rel = {k: max(abs(refit[k][c] - v) / max(abs(v), 1e-300) for c, v in accepted[k].items())
           for k in ("means", "stds")}
    return {"exact_fields_identical": all(refit[k] == accepted[k] for k in exact) and refit.keys() == accepted.keys(),
            "bitwise_identical": refit == accepted,
            "moment_max_relative_difference": rel, "moment_rtol": MOMENT_RTOL,
            "passed": all(refit[k] == accepted[k] for k in exact) and max(rel.values()) <= MOMENT_RTOL}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "results/p11/core_rerun.json")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    receipt = json.loads((ROOT / "results/p5/corrected_acceptance.json").read_bytes())
    if not receipt["accepted"]:
        raise ValueError("P5 evidence must be accepted")
    accepted = GitSnapshot(ROOT, receipt["result_commit"], P5_DIRECTORY)
    config = yaml.safe_load((ROOT / "configs/experiment.yaml").read_text())
    d = config["data"]

    with temporary_uci_dataset() as (data_root, acquisition):
        assert_same_acquisition(acquisition, load_receipt(ROOT / "audit/acquisition_receipt.json"))
        frame = read_stations(data_root, end=d["test_target_end"])
    LOG.info("Loaded %d station-hours from a freshly downloaded archive", len(frame))

    processor = CausalPreprocessor().fit(frame, d["train_target_end"])
    refit_state = json.loads(json_bytes(processor.state))
    accepted_state = accepted.json("preprocessing.json")
    preprocessing = compare_state(refit_state, accepted_state)
    LOG.info("Refitted preprocessing: %s", preprocessing)

    windows = build_windows(frame, processor, scaled=False)
    test = np.flatnonzero(target_partition(windows.keys, config, "test"))
    pred = predict_model("persistence", None, windows, test)
    rerun = windows.keys.iloc[test][KEYS].copy()
    rerun["target_timestamp"] = pd.to_datetime(rerun["target_timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    rerun["y_true"], rerun["y_pred"] = windows.y[test], pred

    saved = pd.concat([accepted.csv(n) for n in sorted(accepted.manifest["artifacts"])
                       if n.startswith("pred-test-persistence-")], ignore_index=True)
    merged = saved.merge(rerun, on=KEYS, how="outer", suffixes=("_saved", "_rerun"),
                         indicator=True, validate="one_to_one")
    same_rows = bool((merged["_merge"] == "both").all())
    max_diff = {c: float(np.nanmax(np.abs(merged[f"{c}_saved"] - merged[f"{c}_rerun"]))) for c in ("y_true", "y_pred")}
    station_mae = rerun.assign(err=(rerun.y_true - rerun.y_pred).abs()).groupby("station").err.mean()
    mae = float(station_mae.mean())
    receipt_mae = next(m["mae"] for m in receipt["metrics"] if m["model"] == "persistence")
    finite = bool(np.isfinite(merged[[f"{c}_{s}" for c in ("y_true", "y_pred")
                                      for s in ("saved", "rerun")]].to_numpy()).all())
    passed = preprocessing["passed"] and same_rows and finite and max(max_diff.values()) == 0 and abs(mae - receipt_mae) <= 1e-9

    result = {
        "phase": "P11", "check": "clean_environment_core_rerun",
        "passed": passed,
        "scope": "Fresh UCI download, training-only preprocessing refit, test window construction and "
                 "deterministic persistence predictions. Learned models were not refitted.",
        "acquisition_matches_frozen_receipt": True,
        "preprocessing": preprocessing,
        "test_targets": int(len(test)), "saved_targets": int(len(saved)),
        "identical_target_rows": same_rows, "max_abs_difference": max_diff,
        "all_predictions_finite": finite,
        "verifier_sha256": sha256(Path(__file__).read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
        "config_sha256": sha256((ROOT / "configs/experiment.yaml").read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
        "source_hash": source_hash(ROOT),
        "persistence_mae_rerun": mae, "persistence_mae_accepted": receipt_mae,
        "accepted_result_commit": receipt["result_commit"],
        "accepted_files_verified": dict(sorted(accepted.used.items())),
        "source_commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                                        text=True).stdout.strip(),
        "environment": {"python": sys.version.split()[0], "platform": platform.platform(),
                        "numpy": np.__version__, "pandas": pd.__version__},
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(json_bytes(result))
    LOG.info("Core rerun %s: persistence MAE %.12f vs accepted %.12f", "PASSED" if passed else "FAILED", mae, receipt_mae)
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
