"""Inventory recovery must retain scientific identity and enforce dependency pins."""
from copy import deepcopy
from datetime import date
from types import SimpleNamespace

import pytest

from scripts.recovery.resume_p7_colab import (
    compatible_provenance, dependency_changes, dependency_versions, install_recovery_hooks,
)


def test_dependency_graph_includes_transitive_and_extra_requirements(monkeypatch):
    import scripts.recovery.resume_p7_colab as recovery
    monkeypatch.setattr(recovery, "ROOT_PACKAGES", ("model",))
    distributions = {
        "model": SimpleNamespace(version="1", requires=["backend[cpu]", 'unused; extra == "gpu"']),
        "backend": SimpleNamespace(version="2", requires=['numeric; extra == "cpu"']),
        "numeric": SimpleNamespace(version="3", requires=[]),
    }
    versions = dependency_versions(distributions.__getitem__)
    assert versions == {"backend": "2", "model": "1", "numeric": "3"}
    saved = {"environment": {"installed_packages": {**versions, "unrelated": "1"}}}
    assert dependency_changes(saved, versions) == []
    assert dependency_changes(saved, {**versions, "numeric": "4"}) == ["numeric==3"]
    with pytest.raises(ValueError, match="absent"):
        dependency_changes(saved, {**versions, "unknown": "1"})


def test_only_inventory_changes_are_accepted_and_dates_normalize():
    saved = {
        "config": {"date": "2026-10-08"}, "source_hash": "original",
        "environment": {"python": "3.13.16", "packages": {"numpy": "2.1.3"},
                        "installed_packages": {"unused": "1"}},
        "parameters": {"model_storage_id": "same"},
    }
    current = deepcopy(saved)
    current["config"]["date"] = date(2026, 10, 8)
    current["environment"]["installed_packages"] = {"unused": "2"}
    compatible_provenance(saved, current)
    for section, key, value in [
        ("environment", "python", "3.13.17"),
        ("environment", "packages", {"numpy": "2.2"}),
        ("parameters", "model_storage_id", "wrong"),
        ("config", "date", "2026-10-09"),
    ]:
        changed = deepcopy(current)
        changed[section][key] = value
        with pytest.raises(ValueError, match="Scientific provenance"):
            compatible_provenance(saved, changed)
    changed = deepcopy(current)
    changed["source_hash"] = "modified"
    with pytest.raises(ValueError):
        compatible_provenance(saved, changed)
    assert saved["environment"]["installed_packages"] == {"unused": "1"}


def test_replay_failure_blocks_development_and_preserves_identity(monkeypatch, tmp_path):
    import airsense_r.training.fold_store as storage
    calls = []
    parent = SimpleNamespace(save=lambda name, data: calls.append(name))
    saved = {"environment": {"installed_packages": {"unrelated": "1"}}}
    current = {"environment": {"installed_packages": {"unrelated": "2"}}}
    class Fold:
        def __init__(self, *args):
            pass
        def has(self, name):
            return True
    monkeypatch.setattr(storage, "FoldStore", Fold)
    def fail(*args):
        raise ValueError("Native replay mismatch")
    p7 = SimpleNamespace(
        training_provenance=lambda *args: deepcopy(current),
        open_run=lambda *args: parent,
        development_fold=lambda *args: "development-only",
        require_fold_selection=lambda *args: None,
        replay_fold=fail, RUN_ID="p7-sites-01", REPLAY_ATOL=1e-5, REPLAY_RTOL=1e-6,
    )
    install_recovery_hooks(p7, saved, current, tmp_path, {"actual": current})
    assert p7.training_provenance(None, {}) == saved
    p7.open_run(None, None, None, None)
    with pytest.raises(ValueError, match="Native replay mismatch"):
        p7.development_fold(None, "A", ["A", "B"], {})
    assert len(calls) == 1 and calls[0].startswith("recovery-env-")
    p7.replay_fold = lambda *args: calls.append("replay")
    assert p7.development_fold(None, "A", ["A", "B"], {}) == "development-only"
    assert calls.count("replay") == 2
    assert calls[-1].startswith("recovery-replay-")
    p7.development_fold(None, "B", ["A", "B"], {})
    assert calls.count("replay") == 2


def test_recovery_notebook_preserves_pinned_scientific_checkout(tmp_path):
    import json
    from pathlib import Path
    import subprocess
    import sys
    import nbformat
    from airsense_r.artifacts import source_hash
    from scripts.recovery.build_notebook import build

    root = Path(__file__).resolve().parents[1]
    original = json.loads((root / "notebooks/06_p7_site_shift_analysis.ipynb").read_text())
    notebook = build(original, "a" * 40, "b" * 64)
    nbformat.validate(nbformat.from_dict(notebook))
    cells = [c["source"] for c in notebook["cells"] if c["cell_type"] == "code"]
    assert len(cells) == 4
    assert "7278ba95c88ea28e8861f59d0a6f8e097087c9d7" in cells[0]
    assert "sha256(payload)" in cells[0] and "capture_output=True" in cells[1]
    # Test-mode fixtures execute current local code; the published notebook keeps
    # the original source fingerprint and immutable source revision unchanged.
    cells[0] = cells[0].replace(
        "9c1237fbbad6e1ca6abe065bbbc9c7f91baf8e2381ed6c86ae50a8df7f6519d3",
        source_hash(root),
    )
    import os
    from hashlib import sha256
    run = "p7-recovery-fixture-" + sha256(str(tmp_path).encode()).hexdigest()[:12]
    output = root / ".tmp/checkpoint-checkouts" / run / "results" / run
    (tmp_path / "storage.json").write_text(json.dumps({"storage_id": "fixture"}))
    parameters = {"phase": "P7", "run_id": run, "model_storage_id": "fixture"}
    child = (
        "from pathlib import Path; from airsense_r.artifacts import RunStore,json_bytes,provenance; "
        f"s=RunStore(Path({str(output)!r}),provenance(Path({str(root)!r}),{parameters!r})); "
        "s.save('complete.json',json_bytes({'execution_complete':True})); "
        "s.save('site-shift-report.json',json_bytes({'synthetic_only':True}))"
    )
    env = {**os.environ, "AIRSENSE_NOTEBOOK_TEST_MODE": "1",
        "AIRSENSE_NOTEBOOK_TEST_ROOT": str(root), "AIRSENSE_P7_TEST_MODELS": str(tmp_path),
        "AIRSENSE_P7_TEST_RUN": run,
        "AIRSENSE_P7_TEST_COMMAND": json.dumps([sys.executable, "-c", child])}
    for _ in range(2):
        result = subprocess.run(
            [sys.executable, "-c", "from IPython.display import display\n" + "\n\n".join(cells)],
            env=env, capture_output=True, text=True, timeout=60,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert "P7 EXECUTION COMPLETE" in result.stdout
