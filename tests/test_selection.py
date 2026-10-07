import pytest

from airsense_r.evaluation.metrics import selection_regret, winner_retained


def test_selection_regret():
    assert selection_regret(15.0, 12.5) == 2.5
    assert selection_regret(12.5, 12.5) == 0.0
    with pytest.raises(ValueError):
        selection_regret(10.0, 11.0)


def test_winner_retention():
    assert winner_retained("gru", "gru") is True
    assert winner_retained("gru", "xgboost") is False
