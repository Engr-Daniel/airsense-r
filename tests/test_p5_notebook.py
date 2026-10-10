"""Fresh-process execution of notebook 04 with explicit offline smoke acquisition."""
from pathlib import Path
from importlib.util import find_spec
import json
import os
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_p5_notebook_smoke_cells(tmp_path):
    if not find_spec("tensorflow") or not find_spec("xgboost"):
        pytest.skip("P5 training dependencies required")
    import nbformat
    notebook = nbformat.read(ROOT / "notebooks/04_p5_clean_benchmark_analysis.ipynb", as_version=4)
    nbformat.validate(notebook)
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
    env = os.environ.copy()
    run_id = "p5-notebook-" + tmp_path.name[-15:]
    # Temp names can contain underscores/hyphens, both accepted by the run store.
    env.update(AIRSENSE_NOTEBOOK_TEST_MODE="1", AIRSENSE_NOTEBOOK_TEST_ROOT=str(ROOT),
               AIRSENSE_NOTEBOOK_TEST_RUN=run_id, AIRSENSE_NOTEBOOK_TEST_REMOTE=str(remote))
    fixture = '''
from IPython.display import display
import builtins
answers = iter(["smoke", MODEL_TEST_ROOT])
builtins.input = lambda prompt="": next(answers)
import subprocess
original_run = subprocess.run
def fixture_run(command, *args, **kwargs):
    if len(command) > 1 and str(command[1]).endswith("run_benchmark.py"):
        import numpy as np
        import pandas as pd
        from airsense_r.p4 import synthetic_stream
        from airsense_r.p5 import smoke_run
        from airsense_r.training.settings import training_provenance
        from airsense_r.checkpoints import open_run
        prov = training_provenance(ROOT, {"phase": "P5", "synthetic_notebook_fixture": True})
        store = open_run(ROOT, RUN_ID, prov, REMOTE)
        group = synthetic_stream().query("station == 'A'")
        frame = group.iloc[np.arange(240) % len(group)].copy().reset_index(drop=True)
        frame["timestamp"] = pd.date_range("2013-03-01", periods=240, freq="h")
        smoke_run(frame, store, Path(MODEL_TEST_ROOT) / RUN_ID)
        return subprocess.CompletedProcess(command, 0)
    return original_run(command, *args, **kwargs)
subprocess.run = fixture_run
'''
    code = "\n\n".join(c.source for c in notebook.cells if c.cell_type == "code")
    program = f"MODEL_TEST_ROOT = {str(tmp_path / 'models')!r}\n" + fixture + code
    for _ in range(2):
        result = subprocess.run([sys.executable, "-c", program], env=env, capture_output=True,
                                text=True, timeout=180)
        assert result.returncode == 0, result.stdout + result.stderr
