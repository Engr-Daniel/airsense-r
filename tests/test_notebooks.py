"""Offline fresh-kernel equivalents: execute real cells with explicit synthetic mode."""
import json
from pathlib import Path
import subprocess
import sys
from hashlib import sha256

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("cached_other_checkout", [False, True])
def test_bootstrap_without_editable_install_activation(tmp_path, cached_other_checkout):
    """A live kernel can lack the newly installed .pth; refuse stale imports too."""
    import os
    notebook = json.loads((ROOT / "notebooks/03_p4_pipeline_validation.ipynb").read_text())
    bootstrap = next("".join(c["source"]) for c in notebook["cells"] if c["cell_type"] == "code")
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env.update(AIRSENSE_NOTEBOOK_TEST_MODE="1", AIRSENSE_NOTEBOOK_TEST_ROOT=str(ROOT))
    program = "import sys\nfrom pathlib import Path\n"
    if cached_other_checkout:
        program += "import types\nm = types.ModuleType('airsense_r')\nm.__file__ = str(Path.cwd() / 'other/airsense_r/__init__.py')\nsys.modules['airsense_r'] = m\n"
    program += bootstrap
    program += "\n" + bootstrap  # Rerunning setup must remain safe.
    program += "\nassert Path(airsense_r.__file__).resolve() == PACKAGE_DIR / '__init__.py'\nassert sys.path.count(str(SOURCE_DIR)) == 1\n"
    result = subprocess.run([sys.executable, "-S", "-c", program], cwd=tmp_path,
                            env=env, capture_output=True, text=True, timeout=30)
    if cached_other_checkout:
        assert result.returncode != 0
        assert "Another airsense_r checkout is already imported" in result.stderr
    else:
        assert result.returncode == 0, result.stderr


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
