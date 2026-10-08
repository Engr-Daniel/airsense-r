"""Structural audit utilities for the Beijing Multi-Site Air Quality station files.

P2 deliberately limits itself to structural properties that may be inspected over the
full dataset without using outcome relationships to tune models. Distribution-driven
EDA is deferred until P3 defines the development/test boundary.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable
import json

import pandas as pd

TIME_COLUMNS = ["year", "month", "day", "hour"]
NUMERIC_SENSOR_COLUMNS = [
    "PM2.5", "PM10", "SO2", "NO2", "CO", "O3",
    "TEMP", "PRES", "DEWP", "RAIN", "WSPM",
]
EXPECTED_COLUMNS = [
    "No", *TIME_COLUMNS, "PM2.5", "PM10", "SO2", "NO2", "CO", "O3",
    "TEMP", "PRES", "DEWP", "RAIN", "wd", "WSPM", "station",
]
EXPECTED_STATIONS = (
    "Aotizhongxin", "Changping", "Dingling", "Dongsi", "Guanyuan", "Gucheng",
    "Huairou", "Nongzhanguan", "Shunyi", "Tiantan", "Wanliu", "Wanshouxigong",
)
TARGET = "PM2.5"
HOUR = pd.Timedelta(hours=1)


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


def _original_order_summary(ts: pd.Series) -> dict[str, int]:
    """Diagnose ordering before any sort can erase backwards steps."""
    diffs = ts.reset_index(drop=True).diff().dropna()
    return {
        "original_non_hourly_steps": int((diffs != HOUR).sum()),
        "original_backward_steps": int((diffs < pd.Timedelta(0)).sum()),
        "original_zero_steps": int((diffs == pd.Timedelta(0)).sum()),
    }


def _sorted_grid_summary(ts: pd.Series) -> dict[str, int]:
    ordered = ts.sort_values().reset_index(drop=True)
    diffs = ordered.diff().dropna()
    return {
        "duplicate_timestamps": int(ordered.duplicated().sum()),
        "sorted_non_hourly_steps": int((diffs != HOUR).sum()),
        "forward_gaps_gt_1h": int((diffs > HOUR).sum()),
    }


def _max_missing_run(mask: pd.Series, ts: pd.Series) -> tuple[int, int]:
    """Return longest missing run in rows and verified consecutive hours.

    A missing run is broken by either an observed value or a non-hourly timestamp
    step. This prevents row counts from being mislabeled as hours when the grid is
    irregular.
    """
    mask = mask.reset_index(drop=True)
    ts = ts.reset_index(drop=True)
    max_rows = max_hours = cur_rows = cur_hours = 0
    for i, missing in enumerate(mask):
        if not bool(missing):
            cur_rows = cur_hours = 0
            continue
        if cur_rows == 0:
            cur_rows = cur_hours = 1
        elif ts.iloc[i] - ts.iloc[i - 1] == HOUR:
            cur_rows += 1
            cur_hours += 1
        else:
            cur_rows = cur_hours = 1
        max_rows = max(max_rows, cur_rows)
        max_hours = max(max_hours, cur_hours)
    return int(max_rows), int(max_hours)


def _complete_window_count(
    frame: pd.DataFrame,
    lookback_hours: int = 24,
    horizon_hours: int = 1,
    required_history: Iterable[str] = ("PM2.5",),
) -> int:
    """Count fully observed windows on a strictly consecutive hourly grid.

    Every adjacent timestamp from the start of history through the forecast target
    must be exactly one hour apart. This is stronger than checking only the two
    endpoints, which can miss a duplicate-plus-gap cancellation inside a window.
    """
    f = frame.sort_values("timestamp").reset_index(drop=True)
    required_history = list(required_history)
    minimum = lookback_hours + horizon_hours
    if len(f) < minimum:
        return 0

    valid = 0
    end_offset = lookback_hours - 1
    for end in range(end_offset, len(f) - horizon_hours):
        start = end - lookback_hours + 1
        target_idx = end + horizon_hours
        window_ts = f.loc[start:target_idx, "timestamp"]
        if not window_ts.diff().dropna().eq(HOUR).all():
            continue
        history = f.loc[start:end, required_history]
        if history.isna().any().any():
            continue
        if pd.isna(f.loc[target_idx, TARGET]):
            continue
        valid += 1
    return valid


def audit_station(
    path: Path,
    lookback_hours: int = 24,
    horizon_hours: int = 1,
) -> tuple[dict[str, object], pd.DataFrame]:
    frame = pd.read_csv(path)
    missing_columns = [c for c in EXPECTED_COLUMNS if c not in frame.columns]
    extra_columns = [c for c in frame.columns if c not in EXPECTED_COLUMNS]
    if missing_columns:
        raise ValueError(f"{path.name}: missing expected columns {missing_columns}")

    frame["timestamp"] = _timestamp(frame)
    original_order = _original_order_summary(frame["timestamp"])
    frame = frame.sort_values("timestamp", kind="stable").reset_index(drop=True)

    station_values = sorted(frame["station"].dropna().astype(str).unique().tolist())
    if len(station_values) != 1:
        raise ValueError(f"{path.name}: expected one station label, got {station_values}")
    station = station_values[0]

    missing_rows: list[dict[str, object]] = []
    for column in [*NUMERIC_SENSOR_COLUMNS, "wd"]:
        mask = frame[column].isna()
        run_rows, run_hours = _max_missing_run(mask, frame["timestamp"])
        missing_rows.append({
            "station": station,
            "variable": column,
            "missing_count": int(mask.sum()),
            "missing_pct": float(mask.mean() * 100.0),
            "max_missing_run_rows": run_rows,
            "max_missing_run_hours": run_hours,
            "negative_count": (
                int((pd.to_numeric(frame[column], errors="coerce") < 0).sum())
                if column != "wd" else 0
            ),
        })

    summary = {
        "file": path.name,
        "station": station,
        "rows": int(len(frame)),
        "columns": int(len(frame.columns) - 1),
        "start": frame["timestamp"].min().isoformat(),
        "end": frame["timestamp"].max().isoformat(),
        "target_observed": int(frame[TARGET].notna().sum()),
        "target_missing": int(frame[TARGET].isna().sum()),
        "target_missing_pct": float(frame[TARGET].isna().mean() * 100.0),
        "pm25_complete_history_windows": _complete_window_count(
            frame, lookback_hours, horizon_hours, [TARGET]
        ),
        "all_numeric_complete_history_windows": _complete_window_count(
            frame, lookback_hours, horizon_hours, NUMERIC_SENSOR_COLUMNS
        ),
        "extra_columns": extra_columns,
        **original_order,
        **_sorted_grid_summary(frame["timestamp"]),
    }
    return summary, pd.DataFrame(missing_rows)


def run_structural_audit(
    root: Path,
    lookback_hours: int = 24,
    horizon_hours: int = 1,
    expected_stations: Iterable[str] | None = EXPECTED_STATIONS,
) -> dict[str, object]:
    files = sorted(root.rglob("PRSA_Data_*.csv"))
    if not files:
        raise FileNotFoundError("No PRSA station CSV files found in temporary extraction")

    station_summaries: list[dict[str, object]] = []
    missing_frames: list[pd.DataFrame] = []
    for path in files:
        summary, missing = audit_station(path, lookback_hours, horizon_hours)
        station_summaries.append(summary)
        missing_frames.append(missing)

    labels = [str(s["station"]) for s in station_summaries]
    duplicate_station_labels = sorted({s for s in labels if labels.count(s) > 1})
    if duplicate_station_labels:
        raise ValueError(f"Repeated station identities: {duplicate_station_labels}")

    missing_expected: list[str] = []
    unexpected: list[str] = []
    if expected_stations is not None:
        expected = set(expected_stations)
        observed = set(labels)
        missing_expected = sorted(expected - observed)
        unexpected = sorted(observed - expected)
        if missing_expected or unexpected:
            raise ValueError(
                "Station inventory mismatch: "
                f"missing={missing_expected}, unexpected={unexpected}"
            )

    station_df = pd.DataFrame(station_summaries).sort_values("station")
    missing_df = pd.concat(missing_frames, ignore_index=True).sort_values(
        ["station", "variable"]
    )
    aggregate_missing = (
        missing_df.groupby("variable", as_index=False)["missing_count"].sum()
        .sort_values("variable")
    )
    total_rows = int(station_df["rows"].sum())
    aggregate_missing["missing_pct_of_rows"] = (
        aggregate_missing["missing_count"] / total_rows * 100.0
    )

    return {
        "dataset": "UCI Beijing Multi-Site Air Quality",
        "station_count": int(len(station_df)),
        "rows_total": total_rows,
        "observed_stations": sorted(labels),
        "expected_stations": list(expected_stations) if expected_stations is not None else None,
        "station_inventory_valid": not missing_expected and not unexpected and not duplicate_station_labels,
        "stations": station_df.to_dict(orient="records"),
        "missingness_by_station_variable": missing_df.to_dict(orient="records"),
        "aggregate_missingness": aggregate_missing.to_dict(orient="records"),
        "lookback_hours_for_coverage_check": lookback_hours,
        "forecast_horizon_hours_for_coverage_check": horizon_hours,
    }


def save_audit(audit: dict[str, object], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(audit, indent=2, default=str) + "\n", encoding="utf-8")
