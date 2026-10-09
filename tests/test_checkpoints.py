from pathlib import Path
import json
import subprocess

import pytest

from airsense_r.artifacts import RunStore, atomic_write, json_bytes
from airsense_r.checkpoints import GitCheckpointSync, git


def test_provenance_resume_and_corruption(tmp_path):
    store = RunStore(tmp_path, {"config": "a"})
    store.save("unit.json", json_bytes({"done": True}))
    assert RunStore(tmp_path, {"config": "a"}).load_json("unit.json") == {"done": True}
    with pytest.raises(ValueError, match="provenance"):
        RunStore(tmp_path, {"config": "b"})
    with pytest.raises(ValueError, match="overwrite"):
        store.save("unit.json", b"changed")
    (tmp_path / "unit.json").write_text("corrupt")
    with pytest.raises(ValueError, match="corrupt"):
        RunStore(tmp_path, {"config": "a"})


def test_interrupted_write_preserves_previous_file(tmp_path, monkeypatch):
    path = tmp_path / "value.json"
    atomic_write(path, b"old")
    def fail(*args):
        raise OSError("simulated interruption")
    monkeypatch.setattr("airsense_r.artifacts.os.replace", fail)
    with pytest.raises(OSError):
        atomic_write(path, b"new")
    assert path.read_bytes() == b"old"
    assert not list(tmp_path.glob(".checkpoint-*"))


def test_path_traversal_and_unregistered_file(tmp_path):
    store = RunStore(tmp_path, {})
    with pytest.raises(ValueError):
        store.save("../escape.json", b"{}")
    with pytest.raises(ValueError, match="reserved"):
        store.save("manifest.json", b"{}")
    (tmp_path / "orphan.json").write_text("{}")
    assert not store.has("orphan.json")


def test_git_publish_restore_and_failed_push(tmp_path):
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
    sync = GitCheckpointSync(str(remote), tmp_path / "first", "run1", retries=1)
    store = RunStore(sync.directory, {"source": "same"}, sync.publish)
    sync.preflight()
    store.save("unit.json", b'{"value": 1}')
    resumed = GitCheckpointSync(str(remote), tmp_path / "second", "run1", retries=1)
    restored = RunStore(resumed.directory, {"source": "same"}, resumed.publish)
    assert restored.load_json("unit.json") == {"value": 1}
    # An unrelated file is neither staged nor published.
    (sync.checkout / "secret.txt").write_text("not for publication")
    store.save("second.json", b"{}")
    assert "secret.txt" not in git(sync.checkout, "ls-tree", "-r", "--name-only", "HEAD")
    git(sync.checkout, "remote", "set-url", "origin", str(tmp_path / "missing.git"))
    with pytest.raises(RuntimeError, match="local checkpoint retained"):
        store.save("pending.json", b"{}")
    assert store.has("pending.json")
    git(sync.checkout, "remote", "set-url", "origin", str(remote))
    sync.publish()
    assert git(sync.checkout, "rev-parse", "HEAD") in git(sync.checkout, "ls-remote", "origin", "refs/heads/results/run1")


def test_reject_unrelated_staged_file(tmp_path):
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
    sync = GitCheckpointSync(str(remote), tmp_path / "checkout", "run", retries=1)
    store = RunStore(sync.directory, {})
    sync.preflight()
    (sync.checkout / "other.json").write_text("{}")
    git(sync.checkout, "add", "other.json")
    with pytest.raises(ValueError, match="Unrelated"):
        sync.publish()
