"""Frozen conditions, lossless recovery, matched aggregation and paired inference."""
from copy import deepcopy
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from airsense_r.artifacts import RunStore
from airsense_r.p6 import conditions, outage_affected, policy_processor, ReplayEvidence
from airsense_r.p6_storage import PredictionBundles
from airsense_r.evaluation.stress_summary import stress_intervals, reliability_summary, rank_tau

ROOT = Path(__file__).resolve().parents[1]


def config():
    return yaml.safe_load((ROOT / "configs/experiment.yaml").read_text())


def test_frozen_matrix_all_seeds_and_deterministic_channel_loss():
    cases = conditions(config())
    assert len(cases) == 15 and sum(len(c["seeds"]) for c in cases) == 63
    assert len({c["id"] for c in cases}) == 15
    assert all(c["seeds"] == [-1] for c in cases if c["kind"] == "whole_variable")
    assert all(c["seeds"] == [101, 202, 303, 404, 505] for c in cases if c["kind"] != "whole_variable")


def test_bundle_exact_roundtrip_corruption_and_provenance(tmp_path):
    store = RunStore(tmp_path / "git", {"source": "fixture"})
    bundles = PredictionBundles(tmp_path / "drive", store)
    values = {"y": np.array([74.3, 81.8]), "time": np.array([1456790400000000000], dtype="int64"),
              "station": np.array(["A", "B"])}
    bundles.save("decimal-targets", values)
    restored = PredictionBundles(tmp_path / "drive", RunStore(tmp_path / "git", {"source": "fixture"}))
    for name, value in values.items():
        np.testing.assert_array_equal(value, restored.load("decimal-targets")[name])
    with pytest.raises(ValueError, match="provenance"):
        PredictionBundles(tmp_path / "drive", RunStore(tmp_path / "other", {"source": "changed"}))
    (tmp_path / "drive/decimal-targets.npz").write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="corrupt"):
        restored.load("decimal-targets")
    with pytest.raises(ValueError, match="Invalid"):
        bundles.reference("../escape")
    with pytest.raises(ValueError, match="Object"):
        bundles.save("unsafe", {"objects": np.array([{}], dtype=object)})


def test_bundle_failed_write_and_failed_publication(tmp_path, monkeypatch):
    import airsense_r.p6_storage as module
    store = RunStore(tmp_path / "git", {})
    bundles = PredictionBundles(tmp_path / "drive", store)
    original = module.atomic_write
    def fail(path, data):
        if path.suffix == ".npz":
            raise OSError("Interrupted array write")
        original(path, data)
    monkeypatch.setattr(module, "atomic_write", fail)
    with pytest.raises(OSError):
        bundles.save("prediction", {"prediction": np.array([74.3])})
    assert not bundles.has("prediction")
    monkeypatch.setattr(module, "atomic_write", original)
    store.sync = lambda: (_ for _ in ()).throw(RuntimeError("Git unavailable"))
    with pytest.raises(RuntimeError, match="Git unavailable"):
        bundles.save("prediction", {"prediction": np.array([74.3])})
    # A saved but unconfirmed unit remains checksum-verifiable for publication retry.
    reopened = PredictionBundles(tmp_path / "drive", RunStore(tmp_path / "git", {}))
    np.testing.assert_array_equal(reopened.load("prediction")["prediction"], [74.3])


def test_affected_history_exact_event_boundaries():
    times = pd.date_range("2016-03-01", periods=60, freq="h")
    targets = {"station": np.array(["A"]*60), "time": times.to_numpy().astype("int64")}
    mask = outage_affected(targets, [{"station": "A", "start": str(times[10]), "end": str(times[15])}])
    assert np.flatnonzero(mask).tolist() == list(range(11, 40))
    assert not outage_affected(targets, [{"station": "B", "start": str(times[10]), "end": str(times[15])}]).any()


def test_no_fill_policy_preserves_training_statistics():
    from airsense_r.data.pipeline import CausalPreprocessor
    from airsense_r.p4 import synthetic_stream
    p = CausalPreprocessor().fit(synthetic_stream(), "2014-01-02 23:00")
    before = deepcopy(p.state)
    sensitivity = policy_processor(p.state, "no_ffill")
    assert sensitivity.limit == 0 and p.state == before
    assert {k: v for k, v in sensitivity.state.items() if k != "forward_fill_hours"} == {
        k: v for k, v in before.items() if k != "forward_fill_hours"}


def test_reliability_equal_seed_and_station_not_row_weighted():
    rows = []
    for model, offset in [("persistence", 0), ("xgboost", -0.5)]:
        for seed in [42, 43]:
            for corruption, delta in [(101, 0), (202, 2)]:
                for station, error, n in [("A", 2, 1000), ("B", 10, 1)]:
                    rows.append(dict(model=model, seed=seed, corruption_seed=corruption, station=station,
                        n=n, mae=error+offset+delta, rmse=error+offset+delta, r2=0.5,
                        clean_mae=error, clean_rmse=error, clean_r2=0.6))
    result = reliability_summary(pd.DataFrame(rows), "persistence", 1)
    scores = {m["model"]: m for m in result["metrics"]}
    assert scores["persistence"]["mae"] == 7
    assert scores["persistence"]["rpd_percent"] == pytest.approx(100/6)
    assert result["selection_regret"] == 0.5 and result["selected_within_practical_near_tie"]
    assert rank_tau(np.array([1, 2, 3]), np.array([3, 2, 1])) == -1


def test_bootstrap_matches_manual_masked_realization_sampling():
    c = config(); c["uncertainty"].update(n_bootstrap=20, block_length_hours=3)
    rng = np.random.default_rng(7)
    clean = rng.uniform(1, 4, (2, 2, 2, 12))
    stressed = clean + rng.uniform(-0.5, 1, clean.shape)
    # Different outage-seed masks, same model/clean/stress observations per seed.
    clean[0, :, :, 2] = np.nan; stressed[0, :, :, 2] = np.nan
    clean[1, :, :, 7] = np.nan; stressed[1, :, :, 7] = np.nan
    result = stress_intervals(clean, stressed, ["persistence", "xgboost"], "persistence", ["A", "B"], c)
    rng = np.random.default_rng(c["seeds"]["bootstrap"])
    deltas, regrets, station_change = [], [], []
    for _ in range(20):
        starts = rng.integers(0, 10, 4)
        sampled = np.concatenate([np.arange(s, s+3) for s in starts])
        a = np.nanmean(clean[..., sampled], axis=-1).mean(axis=0)
        b = np.nanmean(stressed[..., sampled], axis=-1).mean(axis=0)
        score = b.mean(axis=-1)
        deltas.append(score[0]-score[1]); regrets.append(score[0]-score.min())
        station_change.append(b[0, 0]-a[0, 0])
    for field, samples in [(result["differences"]["xgboost"], deltas),
                            (result["selection_regret"], regrets),
                            (result["station_changes"]["persistence"]["A"], station_change)]:
        np.testing.assert_allclose([field["ci_low"], field["ci_high"]], np.quantile(samples, [.025, .975]), atol=1e-12)
    bad = stressed.copy(); bad[0, 0, 0, 0] = np.nan
    with pytest.raises(ValueError, match="misaligned"):
        stress_intervals(clean, bad, ["persistence", "xgboost"], "persistence", ["A", "B"], c)


def test_replay_proxy_never_modifies_parent(tmp_path):
    parent = RunStore(tmp_path / "parent", {})
    output = RunStore(tmp_path / "new", {})
    before = parent.manifest_path.read_bytes()
    proxy = ReplayEvidence(parent, output)
    proxy.save("replay-persistence--1.json", b'{"passed":true}')
    assert parent.manifest_path.read_bytes() == before
    assert output.has("development-replay-persistence--1.json")
    with pytest.raises(ValueError, match="Only replay"):
        proxy.save("preprocessing.json", b"{}")
