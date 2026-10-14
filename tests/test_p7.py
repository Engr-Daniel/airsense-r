"""LOSO exclusions, storage recovery and fold-specific policy estimands."""
from copy import deepcopy
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from airsense_r.artifacts import RunStore, json_bytes
from airsense_r.data.audit import EXPECTED_STATIONS
from airsense_r.evaluation.site_shift import summarize_sites, rank_agreement
from airsense_r.p4 import synthetic_stream
from airsense_r.p7 import development_fold, freeze_selections, score_station
from airsense_r.training.fold_store import FoldStore

ROOT = Path(__file__).resolve().parents[1]


def test_rank_agreement_with_ties():
    assert rank_agreement(np.array([1, 2, 3]), np.array([3, 2, 1])) == -1
    assert rank_agreement(np.array([1, 1, 2]), np.array([1, 1, 2])) == 1
    assert rank_agreement(np.ones(3), np.arange(3)) is None
    np.testing.assert_allclose(rank_agreement(np.array([1, 1, 2]), np.array([1, 2, 3])), 2/np.sqrt(6))


def test_every_station_excluded_before_development():
    config = yaml.safe_load((ROOT / "configs/experiment.yaml").read_text())
    base = synthetic_stream().query("station == 'A'")
    frame = pd.concat([base.assign(station=s) for s in EXPECTED_STATIONS], ignore_index=True)
    for station in EXPECTED_STATIONS:
        fold = development_fold(frame, station, list(EXPECTED_STATIONS), config)
        assert set(fold.station) == set(EXPECTED_STATIONS)-{station}
    late = frame.copy()
    late.loc[0, "timestamp"] = pd.Timestamp("2017-01-01")
    with pytest.raises(ValueError, match="test rows"):
        development_fold(late, station, list(EXPECTED_STATIONS), config)


def test_fold_predictions_survive_branch_restore_and_fail_closed(tmp_path):
    parent = RunStore(tmp_path / "git", {"parameters": {"phase": "P7"}})
    fold = FoldStore(parent, "A", tmp_path / "drive")
    data = b"y_true,y_pred\n74.3,81.8\n"
    fold.save("pred-validation-persistence--1-000.csv", data)
    fold.save("preprocessing.json", json_bytes({"fit_stations": ["B"]}))
    assert not list(parent.directory.glob("*.csv"))
    restored = FoldStore(RunStore(parent.directory, parent.manifest["provenance"]), "A", tmp_path / "drive")
    assert restored._path("pred-validation-persistence--1-000.csv").read_bytes() == data
    assert restored.load_json("preprocessing.json")["fit_stations"] == ["B"]
    with pytest.raises(ValueError, match="overwrite"):
        restored.save("pred-validation-persistence--1-000.csv", b"different")
    restored._path("pred-validation-persistence--1-000.csv").write_bytes(b"broken")
    with pytest.raises(ValueError, match="Corrupt"):
        FoldStore(parent, "A", tmp_path / "drive")
    with pytest.raises(ValueError):
        FoldStore(parent, "../escape", tmp_path / "drive")


def test_read_only_p6_evidence_wrapper_preserves_prediction_access(tmp_path):
    from airsense_r.p6 import ReplayEvidence
    from airsense_r.p5 import read_predictions
    parent = RunStore(tmp_path / "parent", {})
    parent.save("pred-validation-persistence--1-000.csv", b"y_true,y_pred\n74.3,81.8\n")
    output = RunStore(tmp_path / "review", {})
    wrapper = ReplayEvidence(parent, output)
    result = read_predictions(wrapper, "validation", round_trip=True)
    assert result.y_true.iloc[0] == 74.3 and result.y_pred.iloc[0] == 81.8
    assert not output.manifest["artifacts"]


def test_all_fold_gate_rejects_missing_selection(tmp_path):
    parent = RunStore(tmp_path / "git", {"parameters": {}})
    fold = FoldStore(parent, "A", tmp_path / "drive")
    with pytest.raises(ValueError, match="locked"):
        freeze_selections(parent, {"A": fold})
    assert not parent.has("all-selections-frozen.json")
    with pytest.raises(ValueError, match="replay"):
        score_station(synthetic_stream().query("station == 'A'"), "A", fold, tmp_path)


def test_policy_regret_is_station_oracle_not_fixed_family():
    config = yaml.safe_load((ROOT / "configs/experiment.yaml").read_text())
    config["models"]["candidates"] = ["persistence", "xgboost"]
    config["seeds"]["training"] = [42, 31415]
    config["data"].update(test_target_start="2014-01-01", test_target_end="2014-01-03 23:00")
    config["uncertainty"]["n_bootstrap"] = 31
    times = pd.date_range("2014-01-01", periods=72, freq="h")
    rows = []
    # Selected policy is perfect at both sites; no single fixed family is perfect.
    for station, chosen in [("A", "persistence"), ("B", "xgboost")]:
        for model in config["models"]["candidates"]:
            for seed in ([-1] if model == "persistence" else config["seeds"]["training"]):
                for t in times.delete(9 if station == "A" else 12):
                    rows.append({"station": station, "target_timestamp": t, "model": model, "seed": seed,
                                 "partition": "test", "y_true": 74.3, "y_pred": 74.3 if model == chosen else 84.3})
    p = pd.DataFrame(rows)
    decisions = {s: {"selected_family": m, "validation_mae": {"persistence": 1, "xgboost": 2}}
                 for s, m in [("A", "persistence"), ("B", "xgboost")]}
    report = summarize_sites(p, decisions, config)
    assert report["mean_station_selection_regret"] == {"estimate": 0., "ci_low": 0., "ci_high": 0.}
    assert all(v["estimate"] == -5 for v in report["policy_minus_fixed_family"].values())
    # Independent row-index bootstrap: temporal variation, gaps, unequal seed errors.
    p["y_pred"] += (p.target_timestamp.dt.hour % 7) * (p.model == "xgboost") + (p.seed == 31415)*.5
    report = summarize_sites(p, decisions, config)
    errors = (p.assign(error=abs(p.y_true-p.y_pred)).groupby(["station", "model", "target_timestamp"]).error.mean())
    a = np.array([[errors.loc[s, m].reindex(times).to_numpy() for m in ["persistence", "xgboost"]] for s in ["A", "B"]])
    rng = np.random.default_rng(config["seeds"]["bootstrap"])
    regrets = []
    for _ in range(31):
        indices = np.concatenate([np.arange(t, t+24) for t in rng.integers(0, 49, 3)])
        scores = np.nanmean(a[:, :, indices], axis=2)
        regrets.append(np.mean(scores[[0, 1], [0, 1]]-scores.min(axis=1)))
    np.testing.assert_allclose([report["mean_station_selection_regret"][k] for k in ["ci_low", "ci_high"]],
                               np.quantile(regrets, [.025, .975]), rtol=1e-12, atol=1e-12)
    bad = deepcopy(decisions)
    del bad["B"]
    with pytest.raises(ValueError, match="every declared fold"):
        summarize_sites(p, bad, config)
