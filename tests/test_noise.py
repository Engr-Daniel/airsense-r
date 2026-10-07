import numpy as np
import pandas as pd

from airsense_r.corruption.noise import fit_noise_scales, gaussian_relative_noise


def test_noise_uses_frozen_training_scales_and_is_reproducible():
    train = pd.DataFrame({"x": [0.0, 1.0, 2.0, 3.0]})
    test = pd.DataFrame({"x": [100.0, 100.0, 100.0, 100.0]})
    scales = fit_noise_scales(train, ["x"])
    a = gaussian_relative_noise(test, ["x"], 0.5, scales, seed=7)
    b = gaussian_relative_noise(test, ["x"], 0.5, scales, seed=7)
    assert scales["x"] > 0
    assert np.allclose(a["x"], b["x"])
    assert not np.allclose(a["x"], test["x"])


def test_zero_training_scale_adds_no_noise():
    train = pd.DataFrame({"x": [2.0, 2.0, 2.0]})
    test = pd.DataFrame({"x": [9.0, 9.0]})
    scales = fit_noise_scales(train, ["x"])
    out = gaussian_relative_noise(test, ["x"], 1.0, scales, seed=1)
    assert np.allclose(out["x"], test["x"])
