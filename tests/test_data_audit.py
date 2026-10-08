from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from airsense_r.data.audit import audit_station, run_structural_audit


def _frame(station: str, n: int = 30) -> pd.DataFrame:
    ts = pd.date_range("2020-01-01", periods=n, freq="h")
    return pd.DataFrame({
        "No": np.arange(n),
        "year": ts.year,
        "month": ts.month,
        "day": ts.day,
        "hour": ts.hour,
        "PM2.5": np.arange(n, dtype=float) + 10,
        "PM10": np.arange(n, dtype=float) + 20,
        "SO2": np.arange(n, dtype=float) + 1,
        "NO2": np.arange(n, dtype=float) + 2,
        "CO": np.arange(n, dtype=float) + 100,
        "O3": np.arange(n, dtype=float) + 3,
        "TEMP": np.arange(n, dtype=float),
        "PRES": np.arange(n, dtype=float) + 1000,
        "DEWP": np.arange(n, dtype=float) - 5,
        "RAIN": np.zeros(n),
        "wd": ["N"] * n,
        "WSPM": np.ones(n),
        "station": [station] * n,
    })


def test_audit_station_detects_missing_run_and_preserves_timestamps(tmp_path: Path):
    df = _frame("Demo", 30)
    df.loc[5:7, "NO2"] = np.nan
    path = tmp_path / "PRSA_Data_Demo.csv"
    df.to_csv(path, index=False)
    summary, missing = audit_station(path, lookback_hours=4, horizon_hours=1)
    row = missing[(missing.station == "Demo") & (missing.variable == "NO2")].iloc[0]
    assert row.missing_count == 3
    assert row.max_missing_run_rows == 3
    assert row.max_missing_run_hours == 3
    assert summary["duplicate_timestamps"] == 0
    assert summary["sorted_non_hourly_steps"] == 0
    assert summary["original_non_hourly_steps"] == 0


def test_window_requires_every_internal_step_to_be_hourly(tmp_path: Path):
    df = _frame("Demo", 10)
    # Duplicate 03:00 and remove 04:00 while keeping later endpoints unchanged.
    df.loc[4, ["year", "month", "day", "hour"]] = df.loc[3, ["year", "month", "day", "hour"]]
    path = tmp_path / "PRSA_Data_Demo.csv"
    df.to_csv(path, index=False)
    summary, _ = audit_station(path, lookback_hours=4, horizon_hours=1)
    assert summary["duplicate_timestamps"] == 1
    assert summary["sorted_non_hourly_steps"] >= 2
    assert summary["pm25_complete_history_windows"] < 6


def test_original_backward_step_is_not_erased_by_sorting(tmp_path: Path):
    df = _frame("Demo", 10)
    row3 = df.iloc[3].copy()
    row4 = df.iloc[4].copy()
    df.iloc[3] = row4
    df.iloc[4] = row3
    path = tmp_path / "PRSA_Data_Demo.csv"
    df.to_csv(path, index=False)
    summary, _ = audit_station(path, lookback_hours=4, horizon_hours=1)
    assert summary["original_backward_steps"] == 1
    assert summary["duplicate_timestamps"] == 0
    assert summary["sorted_non_hourly_steps"] == 0


def test_missing_run_hours_breaks_across_timestamp_gap(tmp_path: Path):
    df = _frame("Demo", 10)
    df.loc[2:5, "NO2"] = np.nan
    # Create a two-hour jump inside the missing block.
    shifted = pd.Timestamp("2020-01-01 06:00")
    df.loc[5, ["year", "month", "day", "hour"]] = [shifted.year, shifted.month, shifted.day, shifted.hour]
    path = tmp_path / "PRSA_Data_Demo.csv"
    df.to_csv(path, index=False)
    _, missing = audit_station(path, lookback_hours=4, horizon_hours=1)
    row = missing[(missing.station == "Demo") & (missing.variable == "NO2")].iloc[0]
    assert row.max_missing_run_hours < row.missing_count


def test_audit_station_counts_complete_target_windows(tmp_path: Path):
    df = _frame("Demo", 10)
    path = tmp_path / "PRSA_Data_Demo.csv"
    df.to_csv(path, index=False)
    summary, _ = audit_station(path, lookback_hours=4, horizon_hours=1)
    assert summary["pm25_complete_history_windows"] == 6
    assert summary["all_numeric_complete_history_windows"] == 6


def test_structural_audit_aggregates_multiple_stations_when_inventory_check_disabled(tmp_path: Path):
    for name in ["A", "B"]:
        _frame(name, 10).to_csv(tmp_path / f"PRSA_Data_{name}.csv", index=False)
    audit = run_structural_audit(
        tmp_path, lookback_hours=4, horizon_hours=1, expected_stations=None
    )
    assert audit["station_count"] == 2
    assert audit["rows_total"] == 20


def test_structural_audit_rejects_missing_expected_station(tmp_path: Path):
    _frame("A", 10).to_csv(tmp_path / "PRSA_Data_A.csv", index=False)
    with pytest.raises(ValueError, match="Station inventory mismatch"):
        run_structural_audit(
            tmp_path, lookback_hours=4, horizon_hours=1, expected_stations=["A", "B"]
        )


def test_structural_audit_rejects_repeated_station_identity(tmp_path: Path):
    _frame("A", 10).to_csv(tmp_path / "PRSA_Data_A_one.csv", index=False)
    _frame("A", 10).to_csv(tmp_path / "PRSA_Data_A_two.csv", index=False)
    with pytest.raises(ValueError, match="Repeated station identities"):
        run_structural_audit(
            tmp_path, lookback_hours=4, horizon_hours=1, expected_stations=None
        )
