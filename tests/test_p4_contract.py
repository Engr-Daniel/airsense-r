import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from airsense_r.artifacts import provenance, RunStore
from airsense_r.data.pipeline import CausalPreprocessor, build_windows
from airsense_r.data.stress import stress_stream
from airsense_r.p4 import synthetic_stream

ROOT = Path(__file__).resolve().parents[1]


def test_frozen_identity_rejects_silent_override(tmp_path):
    import shutil
    for name in ["configs/experiment.yaml", "configs/frozen_identity.json", "research/PROTOCOL.md", "audit/acquisition_receipt.json"]:
        dst = tmp_path / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, dst)
    config = tmp_path / "configs/experiment.yaml"
    config.write_text(config.read_text().replace("lookback_hours: 24", "lookback_hours: 48"))
    with pytest.raises(ValueError, match="Frozen configuration"):
        provenance(tmp_path, {})


@pytest.mark.parametrize("condition,severity,channel", [("random_dropout", .3, None), ("noise", .1, None), ("whole_variable", 1, "NO2"), ("outage", 6, "CO")])
def test_stress_shared_seed_target_preservation_and_boundary(condition, severity, channel):
    config = yaml.safe_load((ROOT / "configs/experiment.yaml").read_text())
    # Test-only synthetic dates; never used by the frozen-config runner.
    config["data"]["test_target_start"] = "2014-01-03"
    config["data"]["test_target_end"] = "2014-01-04 23:00"
    frame = synthetic_stream()
    scales = {c: 2.0 for c in config["corruptions"]["noise_channels"]}
    a, events = stress_stream(frame, config, condition, severity, 101, scales, channel)
    b, other_events = stress_stream(frame, config, condition, severity, 101, scales, channel)
    pd.testing.assert_frame_equal(a, b)
    assert events == other_events
    pd.testing.assert_series_equal(a["PM2.5"], frame["PM2.5"])
    pd.testing.assert_frame_equal(a.loc[a.timestamp < "2014-01-02"], frame.loc[frame.timestamp < "2014-01-02"])
    p = CausalPreprocessor().fit(frame, "2014-01-01 23:00")
    clean = build_windows(frame, p)
    corrupted = build_windows(a, p, targets=frame)
    pd.testing.assert_frame_equal(clean.keys, corrupted.keys)
    np.testing.assert_equal(clean.y, corrupted.y)


def test_manifest_failure_is_recoverable(tmp_path, monkeypatch):
    import airsense_r.artifacts as module
    store = RunStore(tmp_path, {})
    original = module.atomic_write
    def fail_manifest(path, data):
        if path.name == "manifest.json":
            raise OSError("interruption")
        original(path, data)
    monkeypatch.setattr(module, "atomic_write", fail_manifest)
    with pytest.raises(OSError):
        store.save("unit.json", b"{}")
    assert not store.has("unit.json")
    monkeypatch.setattr(module, "atomic_write", original)
    resumed = RunStore(tmp_path, {})
    resumed.save("unit.json", b"{}")
    assert resumed.has("unit.json")
