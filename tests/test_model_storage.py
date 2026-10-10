"""Persistent model snapshots reject corruption and never advance on failed writes."""
import json

import pytest

from airsense_r.training.storage import ModelCheckpoint


def test_failed_model_write_and_provenance(tmp_path):
    c = ModelCheckpoint(tmp_path, {"seed": 42})
    c.save(1, "ubj", lambda p: p.write_bytes(b"first model"))

    def fail(p):
        p.write_bytes(b"partial")
        raise InterruptedError()

    with pytest.raises(InterruptedError):
        c.save(2, "ubj", fail)
    assert c.restore()[0] == 1
    assert c.restore()[1].read_bytes() == b"first model"
    with pytest.raises(ValueError, match="identity"):
        ModelCheckpoint(tmp_path, {"seed": 43})
    c.restore()[1].write_bytes(b"modified")
    with pytest.raises(ValueError, match="Corrupt"):
        c.restore()


def test_model_pointer_traversal_rejected(tmp_path):
    c = ModelCheckpoint(tmp_path, {})
    c.save(1, "ubj", lambda p: p.write_bytes(b"model"))
    metadata = json.loads(c.pointer.read_text())
    metadata["file"] = "../model.ubj"
    c.pointer.write_text(json.dumps(metadata))
    with pytest.raises(ValueError, match="filename"):
        c.restore()
