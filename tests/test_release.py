"""P11 core-rerun comparison: exact structure, explicit tolerance only for float moments."""
from copy import deepcopy

from scripts.verify_core_rerun import MOMENT_RTOL, compare_state

STATE = {"schema": 1, "fit_end": "2015-02-28 23:00:00", "medians": {"PM2.5": 74.3, "TEMP": 81.8},
         "means": {"PM2.5": 84.14482258371388}, "stds": {"PM2.5": 79.37114741619021},
         "categories": ["E", "MISSING", "OTHER"], "feature_names": ["PM2.5", "TEMP"]}


def test_identical_state_passes_bitwise():
    result = compare_state(deepcopy(STATE), STATE)
    assert result["passed"] and result["bitwise_identical"]


def test_unexpected_fields_and_nonfinite_moments_fail():
    refit = deepcopy(STATE)
    refit["unexpected"] = True
    assert not compare_state(refit, STATE)["passed"]
    refit = deepcopy(STATE)
    refit["means"]["extra"] = 0
    assert not compare_state(refit, STATE)["passed"]
    refit = deepcopy(STATE)
    refit["means"]["PM2.5"] = float("nan")
    assert not compare_state(refit, STATE)["passed"]


def test_last_bit_moment_differences_pass_but_are_reported():
    refit = deepcopy(STATE)
    refit["means"]["PM2.5"] = 84.14482258371385
    result = compare_state(refit, STATE)
    assert result["passed"] and not result["bitwise_identical"]
    assert 0 < result["moment_max_relative_difference"]["means"] <= MOMENT_RTOL


def test_moment_difference_beyond_tolerance_fails():
    refit = deepcopy(STATE)
    refit["stds"]["PM2.5"] *= 1 + 10 * MOMENT_RTOL
    assert not compare_state(refit, STATE)["passed"]


def test_any_median_category_or_feature_order_change_fails():
    for key, value in [("medians", {"PM2.5": 74.30000000001, "TEMP": 81.8}),
                       ("categories", ["MISSING", "E", "OTHER"]),
                       ("feature_names", ["TEMP", "PM2.5"])]:
        refit = deepcopy(STATE)
        refit[key] = value
        assert not compare_state(refit, STATE)["passed"], key
