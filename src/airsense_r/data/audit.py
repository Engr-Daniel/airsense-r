"""Structural audit utilities for the raw UCI station files."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
import json

import numpy as np
import pandas as pd

TIME_COLUMNS = ["year", "month", "day", "hour"]
NUMERIC_SENSOR_COLUMNS = [
    "PM2.5", "PM10", "SO2", "NO2", "CO", "O3",
    "TEMP", "PRES", "DEWP", "RAIN", "WSPM",
]
EXPECTED_COLUMNS = ["No", *TIME_COLUMNS, *NUMERIC_SENSOR_COLUMNS[:6], "TEMP", "PRES", "DEWP", "RAIN", "wd", "WSPM", "station"]
TARGET = "PM2.5"


def _timestamp(frame: pd.DataFrame) -> pd.Series:
    return pd.to_datetime(
        {
            "year": frame["year"],
            "month": frame["month"],
            "day": frame["day"],
            "hour": frame["hour"],
        },
        errors="raise",
    )


def _max_true_run(mask: pd.Series) -> int:
    if mask.empty or not bool(mask.any()):
        return 0
    groups = mask.ne(mask.shift()).cumsum()
    runs = mask.groupby(groups).sum()
    return int(runs.max())


def _gap_summary(ts: pd.Series) -> dict[str, int]:
    ordered = ts.sort_values().reset_index(drop=True)
    diffs = ordered.diff().dropna()
    expected = pd.Timedelta(hours=1)
    return {
        "duplicate_timestamps": int(ordered.duplicated().sum()),
        "non_hourly_steps": int((diffs != expected).sum()),
        "forward_gaps_gt_1h": int((diffs > expected).sum()),
        "backward_or_zero_steps": int((diffs <= pd.Timedelta(0)).sum()),
    }


def _complete_window_count(
    frame: pd.DataFrame,
    lookback_hours: int = 24,
    horizon_hours: int = 1,
    required_history: Iterable[str] = ("PM2.5",),
) -> int:
    """Count windows with complete required history and an observed future target.

    This is an audit diagnostic, not the final modeling sample rule. It intentionally
    requires consecutive hourly timestamps and does not impute missing values.
    """
    f = frame.sort_values("timestamp").reset_index(drop=True)
    if len(f) < lookback_hours + horizon_hours:
        return 0
    ts = f["timestamp"]
    target = f[TARGET]
    required_history = list(required_history)
    valid = 0
    end_offset = lookback_hours - 1
    for end in range(end_offset, len(f) - horizon_hours):
        start = end - lookback_hours + 1
        target_idx = end + horizon_hours
        if ts.iloc[target_idx] - ts.iloc[start] != pd.Timedelta(hours=lookback_hours + horizon_hours - 1):
            continue
        history = f.iloc[start : end + 1]
        if history[required_history].isna().any().any():
            continue
        if pd.isna(target.iloc[target_idx]):
            continue
        valid += 1
    return valid


def audit_station(path: Path, lookback_hours: int = 24, horizon_hours: int = 1) -> tuple[dict[str, object], pd.DataFrame]:
    frame = pd.read_csv(path)
    missing_columns = [c for c in EXPECTED_COLUMNS if c not in frame.columns]
    extra_columns = [c for c in frame.columns if c not in EXPECTED_COLUMNS]
    if missing_columns:
        raise ValueError(f"{path.name}: missing expected columns {missing_columns}")
    frame["timestamp"] = _timestamp(frame)
    frame = frame.sort_values("timestamp").reset_index(drop=True)
    station_values = sorted(frame["station"].dropna().astype(str).unique().tolist())
    if len(station_values) != 1:
        raise ValueError(f"{path.name}: expected one station label, got {station_values}")
    station = station_values[0]

    missing_rows = []
    for column in [*NUMERIC_SENSOR_COLUMNS, "wd"]:
        mask = frame[column].isna()
        missing_rows.append({
            "station": station,
            "variable": column,
            "missing_count": int(mask.sum()),
            "missing_pct": float(mask.mean() * 100.0),
            "max_missing_run_hours": _max_true_run(mask),
            "negative_count": int((pd.to_numeric(frame[column], errors="coerce") < 0).sum()) if column != "wd" else 0,
        })

    gaps = _gap_summary(frame["timestamp"])
    summary = {
        "file": path.name,
        "station": station,
        "rows": int(len(frame)),
        "columns": int(len(frame.columns) - 1),  # exclude constructed timestamp
        "start": frame["timestamp"].min().isoformat(),
        "end": frame["timestamp"].max().isoformat(),
        "target_observed": int(frame[TARGET].notna().sum()),
        "target_missing": int(frame[TARGET].isna().sum()),
        "target_missing_pct": float(frame[TARGET].isna().mean() * 100.0),
        "pm25_complete_history_windows": _complete_window_count(
            frame,
            lookback_hours=lookback_hours,
            horizon_hours=horizon_hours,
            required_history=[TARGET],
        ),
        "all_numeric_complete_history_windows": _complete_window_count(
            frame,
            lookback_hours=lookback_hours,
            horizon_hours=horizon_hours,
            required_history=NUMERIC_SENSOR_COLUMNS,
        ),
        "extra_columns": extra_columns,
        **gaps,
    }
    return summary, pd.DataFrame(missing_rows)


def run_structural_audit(root: Path, lookback_hours: int = 24, horizon_hours: int = 1) -> dict[str, object]:
    files = sorted(root.rglob("PRSA_Data_*.csv"))
    if not files:
        raise FileNotFoundError("No PRSA station CSV files found in temporary UCI extraction")

    station_summaries: list[dict[str, object]] = []
    missing_frames: list[pd.DataFrame] = []
    for path in files:
        summary, missing = audit_station(path, lookback_hours, horizon_hours)
        station_summaries.append(summary)
        missing_frames.append(missing)

    station_df = pd.DataFrame(station_summaries).sort_values("station")
    missing_df = pd.concat(missing_frames, ignore_index=True).sort_values(["station", "variable"])
    aggregate_missing = (
        missing_df.groupby("variable", as_index=False)["missing_count"].sum()
        .sort_values("variable")
    )
    total_rows = int(station_df["rows"].sum())
    aggregate_missing["missing_pct_of_rows"] = aggregate_missing["missing_count"] / total_rows * 100.0

    return {
        "dataset": "UCI Beijing Multi-Site Air Quality",
        "station_count": int(len(station_df)),
        "rows_total": total_rows,
        "stations": station_df.to_dict(orient="records"),
        "missingness_by_station_variable": missing_df.to_dict(orient="records"),
        "aggregate_missingness": aggregate_missing.to_dict(orient="records"),
        "lookback_hours_for_coverage_check": lookback_hours,
        "forecast_horizon_hours_for_coverage_check": horizon_hours,
    }


def save_audit(audit: dict[str, object], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(audit, indent=2, default=str) + "\n", encoding="utf-8")
