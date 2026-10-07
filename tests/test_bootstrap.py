import numpy as np

from airsense_r.evaluation.bootstrap import paired_block_bootstrap_mae_difference


def test_paired_block_bootstrap_is_reproducible():
    y = np.arange(48, dtype=float)
    a = y + 2.0
    b = y + 1.0
    r1 = paired_block_bootstrap_mae_difference(y, a, b, block_length=6, n_bootstrap=100, seed=4)
    r2 = paired_block_bootstrap_mae_difference(y, a, b, block_length=6, n_bootstrap=100, seed=4)
    assert r1 == r2
    assert r1["difference"] > 0
