"""Actual model training, native serialization and boundary-resume equivalence."""
from pathlib import Path

import numpy as np
import pytest

from importlib.util import find_spec
if not find_spec("tensorflow") or not find_spec("xgboost"):
    pytest.skip("P5 training dependencies not installed", allow_module_level=True)

from airsense_r.data.pipeline import CausalPreprocessor, build_windows
from airsense_r.models.learned import fit_model, predict_model, load_model
from airsense_r.p4 import synthetic_stream
from airsense_r.training.settings import configure_cpu, load_plan
from airsense_r.training.storage import ModelCheckpoint

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("family", ["xgboost", "mlp", "gru"])
def test_interrupted_fit_matches_uninterrupted(family, tmp_path):
    configure_cpu()
    plan = load_plan(ROOT)
    plan.update(batch_size=16, xgboost_checkpoint_rounds=2)
    candidate = {**plan["families"][family][0], "epochs": 2, "rounds": 4}
    frame = synthetic_stream()
    prep = CausalPreprocessor().fit(frame, "2014-01-02 23:00")
    windows = build_windows(frame, prep, scaled=family != "xgboost")
    train, score = np.arange(24), np.arange(24, 36)
    a = ModelCheckpoint(tmp_path / "resumed", {"family": family, "seed": 42})
    with pytest.raises(InterruptedError):
        fit_model(family, candidate, 42, windows, train, a, plan, stop_after=1)
    b = ModelCheckpoint(tmp_path / "reference", {"family": family, "seed": 42})
    resumed = fit_model(family, candidate, 42, windows, train, a, plan)
    reference = fit_model(family, candidate, 42, windows, train, b, plan)
    predicted = predict_model(family, resumed, windows, score)
    np.testing.assert_allclose(predicted, predict_model(family, reference, windows, score), rtol=1e-5, atol=1e-5)
    np.testing.assert_allclose(predicted, predict_model(family, load_model(family, a), windows, score), rtol=1e-6, atol=1e-6)


def test_full_selection_then_test_workflow_on_synthetic_fixture(tmp_path):
    """Exercise real adapters, shards, saved selection, test-only loading and exports."""
    import pandas as pd
    import yaml
    from airsense_r.artifacts import RunStore
    from airsense_r.p5 import tune_and_select, require_selection, evaluate_test, read_predictions
    configure_cpu()
    config = yaml.safe_load((ROOT / "configs/experiment.yaml").read_text())
    for key, value in {"train_target_start": "2014-01-02 00:00", "train_target_end": "2014-01-03 23:00",
                       "validation_target_start": "2014-01-04 00:00", "validation_target_end": "2014-01-04 23:00",
                       "test_target_start": "2014-01-05 00:00", "test_target_end": "2014-01-06 23:00"}.items():
        config["data"][key] = value
    config["models"]["internal_folds"] = [{"fit_end": "2014-01-02 23:00",
        "validation_start": "2014-01-03 00:00", "validation_end": "2014-01-03 23:00"}]
    config["uncertainty"]["n_bootstrap"] = 10
    plan = load_plan(ROOT)
    for family in plan["families"]:
        plan["families"][family] = [{**plan["families"][family][0], "epochs": 1, "rounds": 2}]
    plan["prediction_shard_rows"] = 25
    parts = []
    for _, group in synthetic_stream().groupby("station"):
        part = group.iloc[np.arange(144) % len(group)].copy().reset_index(drop=True)
        part["timestamp"] = pd.date_range("2014-01-01", periods=144, freq="h")
        parts.append(part)
    frame = pd.concat(parts, ignore_index=True)
    store = RunStore(tmp_path / "results", {"config": config, "training_plan": plan, "synthetic_only": True})
    models = tmp_path / "models"
    development = frame.loc[frame.timestamp <= "2014-01-04 23:00"].copy()
    decision = tune_and_select(development, store, models)
    assert require_selection(store) == decision
    assert set(read_predictions(store, "validation").model) == {"persistence", "xgboost", "mlp", "gru"}
    # Reentry must use existing scores/predictions, not silently replace a completed unit.
    assert tune_and_select(development, store, models) == decision
    evaluate_test(frame, store, models, decision)
    assert store.load_json("complete.json")["clean_benchmark_complete"]
    assert store.has("test-uncertainty.json")
    assert store.has("dashboard-test.json")
    assert read_predictions(store, "test").target_timestamp.str.startswith("2014-01-0").all()
    # Tampering with a saved score is detected before allowing further test work.
    (store.directory / "selection.json").write_text("{}")
    with pytest.raises(ValueError, match="corrupt"):
        require_selection(store)
