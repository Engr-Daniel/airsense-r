"""Selection must use validation, equal stations, complete seeds and frozen ties."""
from copy import deepcopy
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from airsense_r.evaluation.selection import metric_tables, select_family, validate_predictions
from airsense_r.evaluation.hourly_bootstrap import paired_hourly_intervals
from airsense_r.artifacts import RunStore
from airsense_r.p5 import require_selection

ROOT = Path(__file__).resolve().parents[1]


def predictions():
    """Unequal station counts expose accidentally row-weighted selection."""
    rows = []
    # Persistence equal-station MAE=5; tree=4.5 (near tie), MLP=7, GRU=8.
    for model, errors in {"persistence": (0., 10.), "xgboost": (4.5, 4.5), "mlp": (7., 7.), "gru": (8., 8.)}.items():
        for seed in ([-1] if model == "persistence" else [42, 31415, 27182]):
            for station, n, error in zip(["A", "B"], [48, 96], errors):
                for i, ts in enumerate(pd.date_range("2015-03-01", periods=n, freq="h")):
                    rows.append({"station": station, "target_timestamp": ts, "model": model,
                                 "seed": seed, "partition": "validation", "y_true": float(i), "y_pred": i+error})
    return pd.DataFrame(rows)


def test_equal_station_aggregation_and_practical_tie():
    config = yaml.safe_load((ROOT / "configs/experiment.yaml").read_text())
    p = predictions()
    result = select_family(p, config)
    assert result["validation_mae"]["persistence"] == 5
    assert result["selected_family"] == "persistence"
    assert result["near_ties"] == ["persistence", "xgboost"]
    # Stronger tree improvement exceeds the practical threshold.
    p.loc[p.model == "xgboost", "y_pred"] = p.loc[p.model == "xgboost", "y_true"] + 3
    assert select_family(p, config)["selected_family"] == "xgboost"


def test_selection_rejects_test_labels_missing_seeds_and_keys():
    config = yaml.safe_load((ROOT / "configs/experiment.yaml").read_text())
    p = predictions()
    with pytest.raises(ValueError, match="validation only"):
        select_family(p.assign(partition="test"), config)
    with pytest.raises(ValueError, match="seeds"):
        select_family(p.loc[~((p.model == "gru") & (p.seed == 42))], config)
    with pytest.raises(ValueError, match="identical target"):
        validate_predictions(p.iloc[1:])
    with pytest.raises(ValueError, match="Nonfinite"):
        validate_predictions(p.assign(y_pred=np.nan).fillna({"y_pred": np.inf}))


def test_metrics_average_seed_errors_not_predictions():
    p = predictions()
    p = p.loc[p.model == "xgboost"].copy()
    p.loc[p.seed == 42, "y_pred"] = p.loc[p.seed == 42, "y_true"] - 4.5
    _, aggregate = metric_tables(p)
    assert aggregate.mae.iloc[0] == pytest.approx(4.5)


def test_test_gate_requires_saved_selection(tmp_path):
    with pytest.raises(ValueError, match="locked"):
        require_selection(RunStore(tmp_path, {}))


def test_hourly_bootstrap_preserves_gaps_and_is_paired():
    p = predictions()
    # Preserve irregular missing target positions identically across every model/seed.
    p = p.loc[(p.target_timestamp.dt.hour != 12) & (p.target_timestamp < "2015-03-03")].copy()
    args = dict(start="2015-03-01", end="2015-03-02 23:00", n_bootstrap=40, seed=12)
    a = paired_hourly_intervals(p, "persistence", **args)
    b = paired_hourly_intervals(p.sample(frac=1, random_state=17), "persistence", **args)
    assert a == b
    assert a["selection_regret"]["estimate"] == pytest.approx(.5)
    assert a["differences"]["xgboost"]["ci_low"] == pytest.approx(.5)
    with pytest.raises(ValueError, match="calendar"):
        paired_hourly_intervals(p, "persistence", start="2015-03-02", end="2015-03-04")


def test_calendar_bootstrap_matches_manual_hour_sampling():
    calendar = pd.date_range("2015-03-01", periods=12, freq="h")
    observed = np.array([0, 1, 3, 4, 6, 7, 9, 10, 11])
    rows = []
    for model in ["a", "b"]:
        for hour in observed:
            rows.append({"station": "A", "target_timestamp": calendar[hour], "model": model,
                         "seed": -1, "partition": "test", "y_true": 1.,
                         "y_pred": 1.+(hour if model == "a" else 0.)})
    result = paired_hourly_intervals(pd.DataFrame(rows), "a", start=str(calendar[0]), end=str(calendar[-1]),
                                    block_hours=3, n_bootstrap=1, seed=19)
    starts = np.random.default_rng(19).integers(0, 10, size=4)
    sampled = np.concatenate([np.arange(s, s+3) for s in starts])
    expected = sampled[np.isin(sampled, observed)].mean()
    assert result["differences"]["b"]["ci_low"] == pytest.approx(expected)
