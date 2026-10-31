"""Export checksum-verified accepted evidence for the static reliability explorer.

The explorer is presentation only. This module reads accepted result commits from
local Git objects, verifies every artifact it uses against the accepted manifests
and receipts, and writes compact JSON for ``docs/data/``. It never fits, selects
or runs inference. Clean test metrics are independently recomputed from the saved
prediction CSVs and compared with the acceptance receipt before export.
"""
from __future__ import annotations

from hashlib import sha256
import io
import json
import math
from pathlib import Path
import re
import subprocess
from typing import Any, Callable

import numpy as np
import pandas as pd

MODELS = ("persistence", "xgboost", "mlp", "gru")
THRESHOLD = 1.0
SENSITIVITY_TOLERANCES = (0.5, 1.0, 1.5, 2.0)
TRAINING_SEEDS = (42, 31415, 27182)
# Fixed calendar weeks, chosen by date (first seven days of a mid-season month),
# never by error, so the windows cannot cherry-pick favourable behaviour.
PREDICTION_WINDOWS = (
    ("spring", "2016-04-01 00:00:00", "2016-04-07 23:00:00"),
    ("summer", "2016-07-01 00:00:00", "2016-07-07 23:00:00"),
    ("autumn", "2016-10-01 00:00:00", "2016-10-07 23:00:00"),
    ("winter", "2017-01-01 00:00:00", "2017-01-07 23:00:00"),
)
P5_DIRECTORY = "results/p5-clean-01-corrected-02"
P8_DIRECTORY = "results/p8-analysis-01"
METRIC_TOLERANCE = 1e-9


class GitSnapshot:
    """Read checksum-verified artifacts of one accepted result commit."""

    def __init__(self, root: Path, commit: str, directory: str,
                 manifest_sha256: str | None = None):
        self.root, self.commit, self.directory = root, commit, directory
        self.raw_manifest = self._git_bytes("manifest.json")
        if manifest_sha256 and sha256(self.raw_manifest).hexdigest() != manifest_sha256:
            raise ValueError(f"{directory}@{commit} manifest is not the accepted manifest")
        self.manifest = json.loads(self.raw_manifest)
        self.used: dict[str, str] = {}

    def _git_bytes(self, name: str) -> bytes:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", name):
            raise ValueError(f"Unsafe artifact name: {name}")
        return subprocess.run(["git", "show", f"{self.commit}:{self.directory}/{name}"],
                              cwd=self.root, check=True, capture_output=True).stdout

    def bytes(self, name: str) -> bytes:
        """Return artifact bytes after checking them against the manifest."""
        record = self.manifest["artifacts"].get(name)
        if record is None:
            raise ValueError(f"{name} is not listed in the accepted manifest")
        raw = self._git_bytes(name)
        digest = sha256(raw).hexdigest()
        if digest != record["sha256"]:
            raise ValueError(f"Checksum mismatch: {name}")
        self.used[name] = digest
        return raw

    def json(self, name: str) -> Any:
        return json.loads(self.bytes(name))

    def csv(self, name: str) -> pd.DataFrame:
        return pd.read_csv(io.BytesIO(self.bytes(name)), float_precision="round_trip")


def _read_receipt(root: Path, relative: str) -> tuple[dict, str]:
    raw = (root / relative).read_bytes()
    return json.loads(raw), sha256(raw).hexdigest()


def _close(a: float, b: float, tolerance: float = METRIC_TOLERANCE) -> bool:
    return math.isclose(a, b, rel_tol=0, abs_tol=tolerance)


def regret_status(estimate: float, ci_low: float | None, ci_high: float | None,
                  threshold: float = THRESHOLD) -> str:
    """Classify a regret estimate and interval relative to a practical threshold.

    The point estimate decides "within" versus "above", following the frozen
    protocol; the interval only qualifies that decision.
    """
    within = estimate <= threshold
    if ci_low is None or ci_high is None:
        return "within" if within else "above"
    if within:
        return "within" if ci_high <= threshold else "within_ci_crosses"
    return "above" if ci_low > threshold else "above_ci_crosses"


def _interval(record: dict | None) -> dict | None:
    if not record:
        return None
    return {"estimate": record["estimate"], "ci_low": record["ci_low"], "ci_high": record["ci_high"]}


def _scope_summary(scope: dict) -> dict:
    """Compact one sensor/target-history scope summary without changing values."""
    unc = scope["uncertainty"]
    available = bool(unc.get("available", True))
    regret = scope["selection_regret"]
    ci = unc["selection_regret"] if available else None
    metrics = []
    for m in sorted(scope["metrics"], key=lambda r: MODELS.index(r["model"])):
        metrics.append({k: m[k] for k in ("model", "mae", "rmse", "r2", "clean_mae", "rpd_percent",
                                           "clean_rank", "stress_rank")}
                       | {"selected_minus_model": _interval(unc["differences"][m["model"]]) if available else None})
    best = min(m["mae"] for m in metrics)
    return {"selected_family": scope.get("selected_family", unc.get("selected_family")),
            "selection_regret": regret,
            "regret_ci": [ci["ci_low"], ci["ci_high"]] if ci else None,
            "kendall_tau_b": scope["kendall_tau_b"],
            "oracle_families": [m["model"] for m in metrics if _close(m["mae"], best)],
            "status": regret_status(regret, *(([ci["ci_low"], ci["ci_high"]]) if ci else [None, None])),
            "metrics": metrics}


def _condition_meta(identifier: str) -> dict:
    """Readable grouping/labels for an internal condition identifier."""
    parts = identifier.split("-")
    names = {"TEMP": "Temperature", "NO2": "NO₂", "CO": "CO"}
    if parts[0] == "random_dropout":
        return {"group": "random_dropout", "label": f"Random dropout {int(parts[1])}%",
                "channel": None, "severity": f"{int(parts[1])}%"}
    if parts[0] == "noise":
        return {"group": "noise", "label": f"Measurement noise {int(parts[1])}%",
                "channel": None, "severity": f"{int(parts[1])}%"}
    if parts[0] == "whole":
        return {"group": "channel_loss", "label": f"Loss of {names[parts[1]]}",
                "channel": names[parts[1]], "severity": "Whole channel"}
    if parts[0] == "outage":
        return {"group": "outage", "label": f"{names[parts[1]]} outage {parts[2]} h",
                "channel": names[parts[1]], "severity": f"{parts[2]} h"}
    if parts[0] == "pm25":
        kind = "PM₂.₅ dropout" if parts[1] == "dropout" else "PM₂.₅ outage"
        unit = "%" if parts[1] == "dropout" else " h"
        return {"group": f"pm25_{parts[1]}", "label": f"{kind} {parts[2]}{unit}",
                "channel": "PM₂.₅", "severity": f"{parts[2]}{unit}"}
    raise ValueError(f"Unknown condition: {identifier}")


def recompute_clean_metrics(p5: GitSnapshot) -> tuple[dict[str, float], pd.DataFrame]:
    """Recompute station-equal clean test MAE from every saved prediction CSV."""
    frames = [p5.csv(name) for name in sorted(p5.manifest["artifacts"]) if name.startswith("pred-test-")]
    predictions = pd.concat(frames, ignore_index=True)
    predictions["absolute_error"] = (predictions["y_true"] - predictions["y_pred"]).abs()
    station_seed = predictions.groupby(["model", "seed", "station"])["absolute_error"].mean()
    station = station_seed.groupby(["model", "station"]).mean()
    return station.groupby("model").mean().to_dict(), predictions


def prediction_windows(predictions: pd.DataFrame) -> dict:
    """Extract fixed calendar windows for display, keeping every learned-model seed separate.

    Seeds are never averaged: an averaged prediction is an ensemble the study did not evaluate.
    """
    out: dict[str, Any] = {}
    rounded = lambda s: [None if pd.isna(v) else round(float(v), 2) for v in s]
    for window, start, end in PREDICTION_WINDOWS:
        part = predictions[(predictions["target_timestamp"] >= start) & (predictions["target_timestamp"] <= end)]
        if part.duplicated(["station", "model", "seed", "target_timestamp"]).any():
            raise ValueError("Duplicate display predictions")
        index = pd.date_range(start, end, freq="h").strftime("%Y-%m-%d %H:%M:%S")
        stations = {}
        for station, rows in part.groupby("station"):
            if rows.groupby("target_timestamp")["y_true"].nunique().max() != 1:
                raise ValueError(f"Inconsistent observed targets: {station}")
            truth = rows.drop_duplicates("target_timestamp").set_index("target_timestamp")["y_true"].reindex(index)
            record: dict[str, Any] = {"actual": rounded(truth)}
            for model in MODELS:
                model_rows = rows[rows["model"] == model]
                if model_rows.empty:
                    raise ValueError(f"Missing model in display window: {station} {model}")
                wide = model_rows.pivot(index="target_timestamp", columns="seed", values="y_pred").reindex(index)
                record[model] = ({str(int(seed)): rounded(wide[seed]) for seed in sorted(wide.columns)}
                                 if model != "persistence" else rounded(wide.iloc[:, 0]))
            stations[station] = record
        out[window] = {"start": start, "end": end, "stations": stations}
    return out


def _band_records(frame: pd.DataFrame, key: str) -> list[dict]:
    return [{"model": r.model, key: getattr(r, key), "mae": r.mae, "bias": r.bias,
             "targets": int(r.targets)} for r in frame.itertuples()]


def build_payload(root: Path) -> tuple[dict, dict]:
    """Verify accepted evidence and return (explorer payload, prediction windows)."""
    p5_receipt, p5_receipt_sha = _read_receipt(root, "results/p5/corrected_acceptance.json")
    p8_receipt, p8_receipt_sha = _read_receipt(root, "results/p8/final_acceptance.json")
    p9_receipt, p9_receipt_sha = _read_receipt(root, "results/p9-target-history/final_acceptance.json")
    if not p5_receipt["accepted"] or p8_receipt["status"] != "P7_and_P8_accepted" \
            or p9_receipt["status"] != "P9_target_history_accepted" or not p9_receipt["independent_bootstrap"]:
        raise ValueError("Explorer may only present accepted evidence")

    p5 = GitSnapshot(root, p5_receipt["result_commit"], P5_DIRECTORY)
    p8 = GitSnapshot(root, p8_receipt["result_commit"], P8_DIRECTORY, p8_receipt["manifest_sha256"])
    selection = p5.json("selection.json")
    if selection["selected_family"] != p5_receipt["uncertainty"]["selected_family"]:
        raise ValueError("Selection record disagrees with the clean receipt")

    recomputed, predictions = recompute_clean_metrics(p5)
    receipt_mae = {m["model"]: m["mae"] for m in p5_receipt["metrics"]}
    for model in MODELS:
        if not _close(recomputed[model], receipt_mae[model]):
            raise ValueError(f"Recomputed clean MAE differs for {model}")

    clean_unc = p5_receipt["uncertainty"]
    clean_regret = clean_unc["selection_regret"]
    best_test = min(receipt_mae, key=receipt_mae.get)
    if not _close(receipt_mae[clean_unc["selected_family"]] - receipt_mae[best_test], clean_regret["estimate"]):
        raise ValueError("Clean regret is inconsistent with clean metrics")
    validation = selection["validation_mae"]
    best_validation = min(validation.values())
    clean = {
        "selected_family": selection["selected_family"],
        "rule": "Lowest station-equal validation MAE; candidates within 1.0 µg/m³ resolved by "
                "simplicity order persistence → XGBoost → MLP → GRU",
        "simplicity_order": list(MODELS),
        "near_ties": selection["near_ties"],
        "validation_mae": validation,
        "validation_winner": min(validation, key=validation.get),
        "validation_gap_to_best": {m: v - best_validation for m, v in validation.items()},
        "test": [{"model": m["model"], "mae": m["mae"], "rmse": m["rmse"], "r2": m["r2"],
                  "selected_minus_model": _interval(clean_unc["differences"][m["model"]])}
                 for m in sorted(p5_receipt["metrics"], key=lambda r: MODELS.index(r["model"]))],
        "test_winner": best_test,
        "selection_regret": clean_regret["estimate"],
        "regret_ci": [clean_regret["ci_low"], clean_regret["ci_high"]],
        "status": regret_status(clean_regret["estimate"], clean_regret["ci_low"], clean_regret["ci_high"]),
        "test_period": [p5_receipt["test_start"], p5_receipt["test_end"]],
        "stations": p5_receipt["stations"],
        "selected_configs": selection["selected_configs"],
    }

    sensor_reports = p8.json("sensor-accepted-uncertainty.json")["reports"]
    sensors = []
    for report in sensor_reports:
        identifier = report["condition"]["id"]
        sensors.append({"id": identifier, "policy": report["policy"], **_condition_meta(identifier),
                        "seeds": report["condition"]["seeds"],
                        "scopes": {name: _scope_summary(scope) for name, scope in report["scopes"].items()}})
    target = []
    for summary in p9_receipt["summaries"]:
        compact = _scope_summary(summary)
        compact["selected_family"] = compact["selected_family"] or clean["selected_family"]
        target.append({"id": summary["condition"], "scope": summary["scope"],
                       **_condition_meta(summary["condition"]), **compact})

    p7 = p8.json("p7-independent-report.json")
    site_csv = p8.csv("site-selection-regret.csv").set_index("station")
    stations = []
    for name, record in sorted(p7["stations"].items()):
        regret = record["selection_regret"]
        if not _close(regret["estimate"], float(site_csv.loc[name, "estimate"])):
            raise ValueError(f"Station regret mismatch: {name}")
        stations.append({
            "station": name, "selected_family": record["selected_family"],
            "selection_regret": regret["estimate"], "regret_ci": [regret["ci_low"], regret["ci_high"]],
            "status": regret_status(regret["estimate"], regret["ci_low"], regret["ci_high"]),
            "kendall_tau_b": record["kendall_tau_b"],
            "validation_mae": record["validation_mae"], "test_mae": record["test_mae"],
            "validation_ranks": record["validation_ranks"], "test_ranks": record["test_ranks"],
            "selected_minus_model": {m: _interval(v) for m, v in record["differences"].items()}})
    mean_regret = p7["mean_station_selection_regret"]
    if not _close(mean_regret["estimate"], p8_receipt["mean_station_selection_regret"]["estimate"]):
        raise ValueError("Mean station regret disagrees with the acceptance receipt")
    within = sum(s["selection_regret"] <= THRESHOLD for s in stations)
    if within != p8_receipt["stations_within_practical_near_tie"]:
        raise ValueError("Station threshold count disagrees with the acceptance receipt")
    site = {"stations": stations, "mean_selection_regret": _interval(mean_regret),
            "within_threshold": within,
            "fixed_family_metrics": sorted(p7["fixed_family_metrics"], key=lambda r: MODELS.index(r["model"])),
            "selected_policy_mae": p7["selected_policy_mae"],
            "uncertainty": p7["uncertainty"]}

    failure = {
        "boundaries_ug_m3": p8.json("analysis-config.json").get("pollution_boundaries_ug_m3", [50.0, 100.0, 200.0]),
        "clean_bands": _band_records(p8.csv("p6-primary-clean-concentration_band.csv"), "concentration_band"),
        "clean_seasons": _band_records(p8.csv("p6-primary-clean-season.csv"), "season"),
        "site_bands": _band_records(p8.csv("p7-site-shift-concentration_band.csv"), "concentration_band"),
        "site_seasons": _band_records(p8.csv("p7-site-shift-season.csv"), "season"),
        "site_worst_cases": p8.csv("p7-site-shift-worst-cases.csv")
            .sort_values("absolute_error", ascending=False).head(12).to_dict("records"),
    }

    _cross_check_sensitivity(root, clean, sensors, stations)
    sensitivity, sensitivity_sha = _read_sensitivity(root)

    windows = prediction_windows(predictions)
    windows_bytes = _dump(windows, indent=None)
    payload = {
        "schema": "airsense-r-explorer/1",
        "threshold_ug_m3": THRESHOLD,
        "sensitivity_tolerances": list(SENSITIVITY_TOLERANCES),
        "clean": clean, "sensors": sensors, "target_history": target, "site_shift": site,
        "failure_analysis": failure, "loso_tolerance_sensitivity": sensitivity,
        "prediction_windows": {"file": "clean-prediction-windows.json",
                               "sha256": sha256(windows_bytes).hexdigest(),
                               "training_seeds": list(TRAINING_SEEDS),
                               "windows": [w[0] for w in PREDICTION_WINDOWS]},
        "provenance": {
            "statement": "Presentation of accepted evidence only: no fitting, selection or inference.",
            "p5": {"result_commit": p5.commit, "receipt_sha256": p5_receipt_sha,
                   "manifest_sha256": sha256(p5.raw_manifest).hexdigest(),
                   "prediction_files_recomputed": sum(n.startswith("pred-test-") for n in p5.used),
                   "recomputed_mae": recomputed},
            "p8": {"result_commit": p8.commit, "receipt_sha256": p8_receipt_sha,
                   "manifest_sha256": p8_receipt["manifest_sha256"],
                   "artifacts": {k: v for k, v in sorted(p8.used.items())}},
            "p9_target_history": {"result_commit": p9_receipt["result_commit"],
                                  "review_commit": p9_receipt["review_commit"],
                                  "receipt_sha256": p9_receipt_sha},
            "tolerance_sensitivity_sha256": sensitivity_sha,
        },
    }
    return payload, windows


def _read_sensitivity(root: Path) -> tuple[list[dict], str]:
    raw = (root / "results/p9-threshold-sensitivity/summary.json").read_bytes()
    return json.loads(raw)["loso_counterfactual"], sha256(raw).hexdigest()


def _cross_check_sensitivity(root: Path, clean: dict, sensors: list[dict], stations: list[dict]) -> None:
    """Ensure client-side threshold logic reproduces the accepted interpretation table."""
    table = pd.read_csv(root / "results/p9-threshold-sensitivity/interpretation.csv",
                        float_precision="round_trip")
    lookup: dict[tuple, tuple[float, list | None]] = {("P5", "primary", "clean", "full"):
                                                      (clean["selection_regret"], clean["regret_ci"])}
    for s in sensors:
        for scope, v in s["scopes"].items():
            lookup[("P6", s["policy"], s["id"], scope)] = (v["selection_regret"], v["regret_ci"])
    for s in stations:
        lookup[("P7", "primary", s["station"], "station")] = (s["selection_regret"], s["regret_ci"])
    relative = {"within": "within", "within_ci_crosses": "crosses", "above_ci_crosses": "crosses", "above": "above"}
    for row in table.itertuples():
        regret, ci = lookup[(row.phase, row.policy, row.condition, row.scope)]
        status = regret_status(regret, *(ci or [None, None]), threshold=row.tolerance)
        if not _close(regret, row.regret) or (status in ("within", "within_ci_crosses")) != bool(row.point_within) \
                or relative[status] != row.interval_relative_to_tolerance:
            raise ValueError(f"Threshold interpretation mismatch: {row.phase} {row.condition} {row.tolerance}")
    if len(table) != len(lookup) * len(SENSITIVITY_TOLERANCES):
        raise ValueError("Threshold interpretation table does not cover every exported scope")


def _clean_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _clean_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_clean_json(v) for v in value]
    if isinstance(value, (np.floating, float)):
        return None if math.isnan(value) else float(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.bool_):
        return bool(value)
    return value


def _dump(value: Any, indent: int | None = 1) -> bytes:
    separators = None if indent else (",", ":")
    return (json.dumps(_clean_json(value), indent=indent, separators=separators, ensure_ascii=False,
                       allow_nan=False) + "\n").encode("utf-8")


def write_explorer_data(root: Path, out: Path, log: Callable[[str], None] = print) -> dict:
    """Build, verify and write the explorer data files; return the payload."""
    payload, windows = build_payload(root)
    out.mkdir(parents=True, exist_ok=True)
    (out / "clean-prediction-windows.json").write_bytes(_dump(windows, indent=None))
    (out / "explorer.json").write_bytes(_dump(payload))
    log(f"Exported {len(payload['sensors'])} sensor reports, {len(payload['target_history'])} target-history "
        f"scopes, {len(payload['site_shift']['stations'])} stations; recomputed clean MAE from "
        f"{payload['provenance']['p5']['prediction_files_recomputed']} prediction files.")
    return payload
