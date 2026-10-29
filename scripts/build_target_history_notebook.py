"""Publish the bounded P9 extension with a pinned, reconnectable Colab workflow."""
import argparse
import json
from pathlib import Path
import re

import yaml

from airsense_r.artifacts import source_hash
from scripts.build_notebooks import BOOTSTRAP, md, code

ROOT = Path(__file__).resolve().parents[1]


def build(revision: str) -> dict:
    """Embed immutable source and run settings; no manual SHA/stage entry."""
    if not re.fullmatch(r"[a-f0-9]{40}", revision):
        raise ValueError("Full commit required")
    bootstrap = BOOTSTRAP.replace(
        'CODE_REVISION = (os.environ.get("AIRSENSE_CODE_REVISION") or input("Code version: full 40-character Git commit SHA (not a run ID): ")).strip().lower()',
        f'CODE_REVISION = "{revision}"').replace('ROOT = Path.cwd() / "airsense-r"',
        f'ROOT = Path.cwd() / "airsense-r-p9-{revision[:12]}"').replace('[notebooks]', '[train,notebooks]')
    bootstrap += f'\nfrom airsense_r.artifacts import source_hash\nif source_hash(ROOT) != "{source_hash(ROOT)}":\n    raise RuntimeError("Notebook/source mismatch; reopen the pinned notebook")\n'
    setup = '''from airsense_r.colab import configure_github_secret
from airsense_r.target_history import RUN_ID
if TEST_MODE:
    MODEL_DIRECTORY = Path(os.environ["AIRSENSE_P9_TEST_MODELS"])
    RUN_ID = os.environ["AIRSENSE_P9_TEST_RUN"]
    REMOTE = "fixture"
else:
    from google.colab import drive, userdata
    drive.mount("/content/drive")
    MODEL_DIRECTORY = Path("/content/drive/MyDrive/AirSense-R/model-checkpoints")
    configure_github_secret(ROOT, userdata.get("AIRSENSE_GITHUB_TOKEN"))
    REMOTE = REPOSITORY
if not (MODEL_DIRECTORY / "storage.json").is_file():
    raise FileNotFoundError("Original model storage missing; check the Drive account")
JOB_DIRECTORY = ROOT / ".tmp/notebook-jobs" / RUN_ID
print("Ready: frozen-model replay, then five PM2.5-history conditions. No training.")
'''
    run = '''from airsense_r.notebook_job import run_and_watch
command = [sys.executable, str(ROOT / "scripts/run_target_history.py"),
           "--model-directory", str(MODEL_DIRECTORY), "--remote", REMOTE]
if TEST_MODE:
    import json
    command = json.loads(os.environ["AIRSENSE_P9_TEST_COMMAND"])
run_and_watch(command, JOB_DIRECTORY, ROOT)
'''
    inspect = '''import json
from airsense_r.artifacts import RunStore, source_hash
from airsense_r.notebook_job import status
if status(JOB_DIRECTORY)["state"] != "complete":
    raise RuntimeError("Job incomplete; rerun cell 3 to reconnect or read its error")
directory = ROOT / ".tmp/checkpoint-checkouts" / RUN_ID / "results" / RUN_ID
manifest = json.loads((directory / "manifest.json").read_bytes())
provenance = manifest["provenance"]
if provenance["source_hash"] != source_hash(ROOT) or provenance["parameters"]["run_id"] != RUN_ID:
    raise RuntimeError("Extension provenance mismatch")
store = RunStore(directory, provenance)
if not store.load_json("preflight-complete.json")["passed"] or not store.load_json("complete.json")["execution_complete"]:
    raise RuntimeError("Replay or execution record missing")
display(store.load_json("complete.json"))
display(store.load_json("dashboard-target-history.json"))
print("EXECUTION COMPLETE; scientific acceptance awaits review. Save this notebook with outputs.")
'''
    title = yaml.safe_load((ROOT / "CITATION.cff").read_text(encoding="utf-8"))["title"]
    cells = [md(f"# {title}\n\n## 08 Post-results target-history checkpoint\n\n"
        "**Permitted partitions: TRAIN/VALIDATION — REPLAY ONLY; FINAL TEST — FROZEN-MODEL INFERENCE.**\n\n"
        "This is an explicitly post-results extension, separate from accepted P5–P8. "
        "Use a CPU runtime and **Run all**. Only Drive/GitHub authorization is needed; no SHA or stage entry. "
        "Requires the original P5 native models on Drive and the AIRSENSE_GITHUB_TOKEN Colab secret. "
        "Replays validation and accepted clean predictions before PM2.5 dropout (10/30/50%) and outages (6/12 hours). "
        "All models share each corrupted stream and primary causal imputation; future labels stay original. "
        "No training, new model selection, drift or noise. Original primary results remain unchanged.\n\n"
        "Expect hours rather than minutes; duration depends on CPU and Drive. New predictions save after each "
        "model/seed to a separate Drive directory; compact evidence pushes to results/p9-target-history-01. "
        "One runtime only. After a network disconnect rerun cell 3; after runtime replacement Run all. "
        "Never delete a lock. Only confirmed saved checkpoints survive runtime loss. "
        "Execution completion is followed by independent evidence review. "
        "Low regret does not establish acceptable absolute forecast accuracy. "
        "See research/P9_CHECKPOINT_PLAN.md for the pre-execution extension plan."),
        md("## 1. Clone and verify source"), code(bootstrap), md("## 2. Connect storage"), code(setup),
        md("## 3. Replay, evaluate and publish incrementally"), code(run), md("## 4. Inspect completion"), code(inspect)]
    for i, cell in enumerate(cells):
        cell["id"] = f"p9-{i:02d}"
        if isinstance(cell["source"], list):
            cell["source"] = "".join(cell["source"])
    return {"cells": cells, "nbformat": 4, "nbformat_minor": 5, "metadata": {
        "title": title, "airsense_code_revision": revision,
        "kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
        "language_info": {"name": "python"}}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--revision", required=True)
    args = parser.parse_args()
    (ROOT / "notebooks/08_p9_target_history_checkpoint.ipynb").write_text(
        json.dumps(build(args.revision), indent=1) + "\n", encoding="utf-8")
