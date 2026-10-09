import numpy as np
import pandas as pd
import pytest

from airsense_r.data.pipeline import CausalPreprocessor, build_windows, calendar_features, validate_stream, target_partition
from airsense_r.p4 import synthetic_stream
from airsense_r.corruption.dropout import random_feature_dropout
from airsense_r.corruption.noise import fit_noise_scales, gaussian_relative_noise


def test_training_statistics_ignore_future_and_held_out_station():
    frame = synthetic_stream()
    first = CausalPreprocessor().fit(frame, "2014-01-02 23:00", "B")
    frame.loc[(frame.station == "B") | (frame.timestamp > "2014-01-02 23:00"), "NO2"] = 1e10
    second = CausalPreprocessor().fit(frame, "2014-01-02 23:00", "B")
    assert first.state == second.state


def test_fill_cap_causality_and_station_isolation():
    frame = synthetic_stream()
    processor = CausalPreprocessor().fit(frame, "2014-01-02 23:00", "B")
    _, features, _ = processor.transform(frame)
    col = processor.state["feature_names"].index("NO2")
    assert features[35, col] == 30  # sixth missing hour carries the actual past reading
    assert features[36, col] == processor.state["medians"]["NO2"]
    changed = frame.copy()
    changed.loc[39, "NO2"] = 9999
    _, future_changed, _ = processor.transform(changed)
    np.testing.assert_equal(features[:39], future_changed[:39])
    frame.loc[96, "NO2"] = np.nan
    _, separated, _ = processor.transform(frame)
    assert separated[96, col] == processor.state["medians"]["NO2"]


def test_windows_preserve_targets_and_history_layout():
    frame = synthetic_stream()
    processor = CausalPreprocessor().fit(frame, "2014-01-02 23:00")
    clean = build_windows(frame, processor)
    stressed = random_feature_dropout(frame, ["NO2", "wd"], 1.0)
    stress = build_windows(stressed, processor, targets=frame)
    pd.testing.assert_frame_equal(clean.keys, stress.keys)
    np.testing.assert_equal(clean.y, stress.y)
    assert len(clean.y) == 2 * (96 - 24 - 1)
    seq, cal = clean.batch(np.array([0]))
    flat, _ = clean.batch(np.array([0]), tabular=True)
    np.testing.assert_equal(seq.reshape(1, -1), flat[:, :-4])
    assert seq[0, -1, 0] == 24
    assert clean.y[0] == 25
    assert clean.persistence[0] == 24


def test_unknown_wind_direction_and_scaling():
    frame = synthetic_stream()
    processor = CausalPreprocessor().fit(frame, "2014-01-02 23:00", "B")
    frame.loc[96, "wd"] = "UNSEEN"
    _, features, _ = processor.transform(frame, scaled=True)
    assert features[96, processor.state["feature_names"].index("wd_OTHER")] == 1
    assert np.isfinite(features).all()
    restored = CausalPreprocessor.from_state(processor.state)
    np.testing.assert_equal(restored.transform(frame)[1], processor.transform(frame)[1])


def test_reject_duplicate_or_gapped_grid():
    frame = synthetic_stream()
    with pytest.raises(ValueError, match="Duplicate"):
        validate_stream(pd.concat([frame, frame.iloc[:1]]))
    with pytest.raises(ValueError, match="Non-hourly"):
        validate_stream(frame.drop(index=5))


def test_calendar_leap_year_and_target_cutoffs():
    ts = pd.Series(pd.to_datetime(["2016-01-01", "2016-12-31", "2017-01-01"]))
    cal = calendar_features(ts)
    np.testing.assert_allclose(cal[0], cal[2])
    assert cal[1, 2] == pytest.approx(np.sin(2*np.pi*365/366))
    config = {"data": {"train_target_start": "2016-01-01", "train_target_end": "2016-12-31"}}
    assert target_partition(pd.DataFrame({"target_timestamp": ts}), config, "train").tolist() == [True, True, False]


def test_robust_noise_and_nonnegative_clipping():
    frame = pd.DataFrame({"NO2": [0., 1., 2., 3., 1000.]})
    scales = fit_noise_scales(frame, ["NO2"])
    assert scales["NO2"] == pytest.approx(2 / 1.349)
    out = gaussian_relative_noise(pd.DataFrame({"NO2": np.zeros(100)}), ["NO2"], 20, scales)
    assert (out.NO2 >= 0).all()


def test_sensitivity_uses_median_without_forward_fill():
    frame = synthetic_stream()
    processor = CausalPreprocessor(0).fit(frame, "2014-01-02 23:00", "B")
    _, features, _ = processor.transform(frame)
    col = processor.state["feature_names"].index("NO2")
    flag = processor.state["feature_names"].index("missing_NO2")
    assert features[30, col] == processor.state["medians"]["NO2"]
    assert features[30, flag] == 1
    assert features[29, flag] == 0
