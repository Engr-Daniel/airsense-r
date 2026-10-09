"""Offline fresh-kernel equivalents: execute real cells with explicit synthetic mode."""
import json
from pathlib import Path
import subprocess
import sys
from hashlib import sha256

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("filename", [
    "01_p2_dataset_audit_review.ipynb", "02_p3_development_diagnostics.ipynb", "03_p4_pipeline_validation.ipynb"
])
def test_notebook_cells_in_fresh_process(filename, tmp_path):
    # Test-mode substitution skips only installation/authentication, not analysis cells.
    import os
    notebook = json.loads((ROOT / "notebooks" / filename).read_text())
    import nbformat
    nbformat.validate(nbformat.from_dict(notebook))
    remote = tmp_path / "artifacts.git"
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
    env = os.environ.copy()
    env.update(AIRSENSE_NOTEBOOK_TEST_MODE="1", AIRSENSE_NOTEBOOK_TEST_ROOT=str(ROOT),
               AIRSENSE_NOTEBOOK_TEST_RUN=f"test-{sha256(str(tmp_path).encode()).hexdigest()[:16]}", AIRSENSE_NOTEBOOK_TEST_REMOTE=str(remote))
    cells = ["".join(c["source"]) for c in notebook["cells"] if c["cell_type"] == "code"]
    program = "from IPython.display import display\n" + "\n\n".join(cells)
    result = subprocess.run([sys.executable, "-c", program], env=env, capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stderr
    # Same process starts from scratch again and validates/restores existing units.
    resumed = subprocess.run([sys.executable, "-c", program], env=env, capture_output=True, text=True, timeout=120)
    assert resumed.returncode == 0, resumed.stderr
