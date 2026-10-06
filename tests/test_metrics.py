from airsense_r.evaluation.metrics import relative_performance_degradation


def test_rpd():
    assert relative_performance_degradation(10.0, 14.0) == 40.0
