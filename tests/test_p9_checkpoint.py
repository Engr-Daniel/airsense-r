"""Post-results extension: paired inputs, immutable labels, fallback and resume."""
from copy import deepcopy
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from airsense_r.artifacts import RunStore, json_bytes
from airsense_r.data.pipeline import CausalPreprocessor, build_windows
from airsense_r.evaluation.threshold_sensitivity import select, tables
from airsense_r.p4 import synthetic_stream
from airsense_r.p6 import targets, aligned_indices
from airsense_r.p6_storage import PredictionBundles
from airsense_r.target_history import cases, corrupt_history, evaluate

ROOT = Path(__file__).resolve().parents[1]


def fixture():
    """Small chronological fixture with real decimal labels and natural gaps."""
    config = yaml.safe_load((ROOT / "configs/experiment.yaml").read_text())
    frame = synthetic_stream()
    frame.loc[frame.timestamp == "2014-01-03 12:00", "PM2.5"] = 74.3
    frame.loc[frame.timestamp == "2014-01-03 13:00", "PM2.5"] = 81.8
    config["data"].update(test_target_start="2014-01-03 00:00", test_target_end="2014-01-04 23:00")
    config["seeds"]["training"] = [42]
    config["uncertainty"]["n_bootstrap"] = 12
    return frame, config


@pytest.mark.parametrize("spec", cases())
def test_target_stream_preserves_labels_pairing_and_boundaries(spec):
    frame, config = fixture()
    original, frozen = frame.copy(deep=True), deepcopy(config)
    stressed, events, audit = corrupt_history(frame, config, spec, 101)
    again, _, repeated = corrupt_history(frame, config, spec, 101)
    pd.testing.assert_frame_equal(frame, original)
    pd.testing.assert_frame_equal(stressed, again)
    assert config == frozen and audit == repeated
    pd.testing.assert_frame_equal(frame.drop(columns="PM2.5"), stressed.drop(columns="PM2.5"))
    outside = ~frame.timestamp.between("2014-01-02", "2014-01-04 22:00")
    pd.testing.assert_series_equal(frame.loc[outside, "PM2.5"], stressed.loc[outside, "PM2.5"])
    processor = CausalPreprocessor().fit(frame, "2014-01-02 23:00")
    restored = CausalPreprocessor.from_state(json.loads(json_bytes(processor.state)))
    expected = targets(frame, restored, config)
    for scaled in (False, True):
        windows = build_windows(stressed, restored, scaled=scaled, targets=frame)
        indices = aligned_indices(windows, expected, config)
        assert 74.3 in windows.y[indices] and 81.8 in windows.y[indices]
        np.testing.assert_array_equal(windows.features, build_windows(stressed, processor,
            scaled=scaled, targets=frame).features)
    assert audit["changed_pm25_cells"] > 0
    if events:
        assert all((pd.Timestamp(e["end"])-pd.Timestamp(e["start"])).total_seconds()/3600+1 == spec["severity"] for e in events)


def test_persistence_uses_same_six_hour_fill_then_training_median():
    frame, _ = fixture()
    prep = CausalPreprocessor().fit(frame, "2014-01-02 23:00")
    frame = frame.loc[frame.station == frame.station.iloc[0]].reset_index(drop=True)
    observed = frame.copy()
    observed.loc[47, "PM2.5"] = 81.8
    observed.loc[48:59, "PM2.5"] = np.nan
    windows = build_windows(observed, prep, targets=frame)
    for origin in range(48, 54):
        assert windows.features[origin, 0] == np.float32(81.8)
    for origin in range(54, 60):
        assert windows.features[origin, 0] == np.float32(prep.state["medians"]["PM2.5"])
    # Column zero is the same unscaled imputed PM2.5 supplied to learned models.
    np.testing.assert_array_equal(windows.persistence, windows.features[windows.origins, 0])
    assert windows.features[48:60, prep.state["feature_names"].index("missing_PM2.5")].all()


def test_tolerance_changes_selection_only_from_validation():
    validation = {"persistence": 10.8, "xgboost": 10., "mlp": 11., "gru": 12.}
    assert select(validation, .5) == "xgboost"
    assert select(validation, 1.) == "persistence"
    clean = {"metrics": [{"model": m, "mae": s} for m, s in validation.items()],
             "uncertainty": {"selection_regret": {"estimate": .8, "ci_low": .4, "ci_high": 1.2}}}
    first, second = tables({"selected_family": "persistence", "validation_mae": validation},
                           clean, {"stations": {}}, [])
    assert set(first.selected_family) == {"persistence"}
    assert second.iloc[0].selected_family == "xgboost" and second.iloc[0].regret == 0
    assert first.iloc[0].interval_relative_to_tolerance == "crosses"
    assert not first.iloc[0].point_within
    with pytest.raises(ValueError):
        select({**validation, "gru": float("nan")}, 1.)


def test_threshold_runner_rejects_unaccepted_manifest(tmp_path):
    from scripts.run_threshold_sensitivity import run
    (tmp_path / "manifest.json").write_text('{}')
    with pytest.raises(ValueError, match="Unaccepted"):
        run(ROOT, tmp_path, tmp_path, tmp_path / "output")
    assert not (tmp_path / "output").exists()


def test_prediction_interrupt_resume_and_corruption_detection(tmp_path, monkeypatch):
    import airsense_r.p6 as p6
    frame, config = fixture()
    prep = CausalPreprocessor().fit(frame, "2014-01-02 23:00")
    parent = RunStore(tmp_path / "parent", {"fixture": True})
    parent.save("preprocessing.json", json_bytes(prep.state))
    parent.save("selection.json", json_bytes({"selected_family": "persistence"}))
    store = RunStore(tmp_path / "output", {"fixture": True})
    bundles = PredictionBundles(tmp_path / "arrays", store)
    bundles.save("targets", targets(frame, prep, config))
    calls = []
    def predict(family, model, windows, indices, batch_size):
        calls.append(family)
        if len(calls) == 7:
            raise InterruptedError("fixture interruption after persisted predictions")
        return windows.persistence[indices].astype(float) + {"persistence": 0, "xgboost": 1, "mlp": 2, "gru": 3}[family]
    monkeypatch.setattr(p6, "predict_model", predict)
    with pytest.raises(InterruptedError):
        evaluate(frame, parent, store, bundles, {}, config, {"prediction_batch_size": 16})
    before = dict(store.manifest["artifacts"])
    evaluate(frame, parent, store, bundles, {}, config, {"prediction_batch_size": 16})
    assert store.load_json("complete.json")["execution_complete"]
    assert all(store.manifest["artifacts"][k] == v for k, v in before.items())
    count = len(calls)
    evaluate(frame, parent, store, bundles, {}, config, {"prediction_batch_size": 16})
    assert len(calls) == count
    path = next((tmp_path / "arrays").glob("pred-primary-pm25-*.npz"))
    path.write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="corrupt"):
        evaluate(frame, parent, store, bundles, {}, config, {"prediction_batch_size": 16})
