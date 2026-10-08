from pathlib import Path

import numpy as np
import pandas as pd

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
    assert row.max_missing_run_hours == 3
    assert summary["duplicate_timestamps"] == 0
    assert summary["non_hourly_steps"] == 0


def test_audit_station_counts_complete_target_windows(tmp_path: Path):
    df = _frame("Demo", 10)
    path = tmp_path / "PRSA_Data_Demo.csv"
    df.to_csv(path, index=False)
    summary, _ = audit_station(path, lookback_hours=4, horizon_hours=1)
    assert summary["pm25_complete_history_windows"] == 6
    assert summary["all_numeric_complete_history_windows"] == 6


def test_structural_audit_aggregates_multiple_stations(tmp_path: Path):
    for name in ["A", "B"]:
        _frame(name, 10).to_csv(tmp_path / f"PRSA_Data_{name}.csv", index=False)
    audit = run_structural_audit(tmp_path, lookback_hours=4, horizon_hours=1)
    assert audit["station_count"] == 2
    assert audit["rows_total"] == 20
