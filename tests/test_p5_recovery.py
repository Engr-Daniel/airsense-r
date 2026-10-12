"""Recovery exclusivity and notebook structure checks."""
import pytest

from airsense_r.p5_recovery import local_writer_lock, recover_test


def test_recovery_lock_rejects_second_writer_and_releases(tmp_path):
    path = tmp_path / "recovery.lock"
    with local_writer_lock(path):
        with pytest.raises(RuntimeError, match="already running"):
            with local_writer_lock(path):
                pytest.fail("Second writer acquired lock")
    with local_writer_lock(path):
        pass


def test_recovery_refuses_original_run_id_before_io(tmp_path):
    with pytest.raises(ValueError, match="new correction run ID"):
        recover_test(tmp_path, "p5-clean-01", tmp_path / "models", "unused")


@pytest.mark.parametrize("replay_fails", [False, True])
def test_test_rows_only_loaded_after_validation_gate(tmp_path, monkeypatch, replay_fails):
    """The entry point must not expose final-test rows when replay fails."""
    import json
    from contextlib import contextmanager
    from types import SimpleNamespace
    import airsense_r.p5_recovery as recovery
    calls = []
    config = {"data": {"validation_target_end": "validation", "test_target_end": "test"}}
    parent = SimpleNamespace(manifest={"provenance": {"parameters": {"model_storage_id": "original"}}})
    store = SimpleNamespace(directory=tmp_path / "results", has=lambda name: False)
    models = tmp_path / "models"
    models.mkdir()
    (models / "storage.json").write_text(json.dumps({"storage_id": "original"}))
    monkeypatch.setattr(recovery, "parent_store", lambda *a: parent)
    monkeypatch.setattr(recovery, "training_provenance", lambda *a: {"config": config})
    monkeypatch.setattr(recovery, "open_run", lambda *a: store)
    monkeypatch.setattr(recovery, "migrate_evidence", lambda *a: {"selected_family": "persistence"})
    @contextmanager
    def dataset():
        yield tmp_path, {}
    monkeypatch.setattr(recovery, "temporary_uci_dataset", dataset)
    monkeypatch.setattr(recovery, "load_receipt", lambda *a: {})
    monkeypatch.setattr(recovery, "assert_same_acquisition", lambda *a: None)
    monkeypatch.setattr(recovery, "read_stations", lambda root, end: calls.append(end))
    def verify(*a):
        calls.append("replay")
        if replay_fails:
            raise ValueError("Replay failed")
    monkeypatch.setattr(recovery, "verify_validation", verify)
    monkeypatch.setattr(recovery, "evaluate_test", lambda *a: calls.append("evaluate"))
    monkeypatch.setattr(recovery, "export_run", lambda *a: None)
    if replay_fails:
        with pytest.raises(ValueError, match="Replay failed"):
            recover_test(tmp_path, "corrected", models, "unused")
        assert calls == ["validation", "replay"]
    else:
        recover_test(tmp_path, "corrected", models, "unused")
        assert calls == ["validation", "replay", "test", "evaluate"]


def test_recovery_notebook_is_valid_and_uses_current_source():
    from pathlib import Path
    import nbformat
    from airsense_r.artifacts import source_hash
    root = Path(__file__).resolve().parents[1]
    notebook = nbformat.read(root / "notebooks/04b_p5_corrected_test.ipynb", as_version=4)
    nbformat.validate(notebook)
    cells = [c.source for c in notebook.cells if c.cell_type == "code"]
    assert len(cells) == 5
    assert source_hash(root) in cells[1]
    assert "recover_p5_test.py" in cells[3] and "process.terminate()" in cells[3]
    for cell in cells:
        compile(cell, "recovery-notebook", "exec")
