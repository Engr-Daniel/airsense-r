import pandas as pd
import pytest

from airsense_r.data.splits import leave_one_station_out, temporal_split


def test_temporal_split_preserves_order_and_nonempty_blocks():
    frame = pd.DataFrame({
        "timestamp": pd.date_range("2026-01-01", periods=20, freq="h"),
        "x": range(20),
    })
    train, val, test = temporal_split(frame, timestamp_col="timestamp")
    assert len(train) > 0 and len(val) > 0 and len(test) > 0
    assert train["timestamp"].max() < val["timestamp"].min()
    assert val["timestamp"].max() < test["timestamp"].min()


def test_temporal_split_rejects_unsorted_frame():
    frame = pd.DataFrame({"timestamp": pd.to_datetime(["2026-01-02", "2026-01-01", "2026-01-03"])})
    with pytest.raises(ValueError):
        temporal_split(frame, 0.34, 0.33, timestamp_col="timestamp")


def test_leave_one_station_out_isolates_station():
    frame = pd.DataFrame({"station": ["A", "A", "B", "C"], "x": [1, 2, 3, 4]})
    dev, held = leave_one_station_out(frame, "station", "B")
    assert "B" not in set(dev["station"])
    assert set(held["station"]) == {"B"}
