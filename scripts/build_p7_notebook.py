"""Build the automatic four-cell Colab LOSO workflow."""
import argparse
import json
from pathlib import Path
import re

import yaml

from airsense_r.artifacts import source_hash
from scripts.build_notebooks import BOOTSTRAP, md, code

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    """Embed a reviewed source revision and the fixed P7 run settings."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--revision", required=True)
    revision = parser.parse_args().revision
    if not re.fullmatch(r"[a-f0-9]{40}", revision):
        raise ValueError("Full source commit required")
    bootstrap = BOOTSTRAP.replace(
        'CODE_REVISION = (os.environ.get("AIRSENSE_CODE_REVISION") or input("Code version: full 40-character Git commit SHA (not a run ID): ")).strip().lower()',
        f'CODE_REVISION = "{revision}"')
    bootstrap = bootstrap.replace('ROOT = Path.cwd() / "airsense-r"', f'ROOT = Path.cwd() / "airsense-r-p7-{revision[:12]}"')
    bootstrap = bootstrap.replace('requirements-p4.txt', 'requirements-p5.txt')
    bootstrap += f'''\nfrom airsense_r.artifacts import source_hash
if source_hash(ROOT) != "{source_hash(ROOT)}":
    raise RuntimeError("Notebook/source mismatch; reopen the published P7 notebook")
print("P7 setup ready. Code revision and run settings are already configured.")
'''
    setup = '''from airsense_r.colab import configure_github_secret
RUN_ID = "p7-sites-01"
if TEST_MODE:
    MODEL_DIRECTORY = Path(os.environ["AIRSENSE_P7_TEST_MODELS"])
    RUN_ID = os.environ["AIRSENSE_P7_TEST_RUN"]
    REMOTE = os.environ.get("AIRSENSE_P7_TEST_REMOTE", "unused-fixture")
else:
    from google.colab import drive, userdata
    drive.mount("/content/drive")
    MODEL_DIRECTORY = Path("/content/drive/MyDrive/AirSense-R/model-checkpoints")
    configure_github_secret(ROOT, userdata.get("AIRSENSE_GITHUB_TOKEN"))
    REMOTE = REPOSITORY
if not (MODEL_DIRECTORY / "storage.json").is_file() and not TEST_MODE:
    raise FileNotFoundError("Existing AirSense-R Drive storage is unavailable; check the mounted account")
JOB_DIRECTORY = ROOT / ".tmp/notebook-jobs" / RUN_ID
print("Ready: automatic P7 run/resume. Use one Colab runtime at a time.")
'''
    run = '''from airsense_r.notebook_job import run_and_watch
command = [sys.executable, str(ROOT / "scripts/run_site_shift.py"),
           "--model-directory", str(MODEL_DIRECTORY), "--remote", REMOTE]
if TEST_MODE:
    import json
    command = json.loads(os.environ["AIRSENSE_P7_TEST_COMMAND"])
run_and_watch(command, JOB_DIRECTORY, ROOT)
'''
    inspect = '''import json
from airsense_r.artifacts import RunStore
from airsense_r.notebook_job import status
if status(JOB_DIRECTORY)["state"] != "complete":
    raise RuntimeError("P7 is not finished. Rerun the preceding cell to reconnect or resume.")
output = ROOT / ".tmp/checkpoint-checkouts" / RUN_ID / "results" / RUN_ID
manifest = json.loads((output / "manifest.json").read_bytes())
store = RunStore(output, manifest["provenance"])
completion = store.load_json("complete.json")
if completion.get("execution_complete") is not True:
    raise RuntimeError("P7 execution completion record is missing")
display(completion)
display(store.load_json("site-shift-report.json"))
print("P7 EXECUTION COMPLETE. Save this executed notebook separately for independent review.")
'''
    title = yaml.safe_load((ROOT / "CITATION.cff").read_text(encoding="utf-8"))["title"]
    cells = [md(f"# {title}\n\n## 06 P7 site-shift analysis\n\n"
        "**Permitted partitions: TRAIN + VALIDATION for fitting/selection; FINAL TEST — READ ONLY after all 12 fold selections and development replays pass.**\n\n"
        "Choose a CPU runtime and **Runtime → Run all**. No SHA, stage or run-name entry is needed. "
        "Colab still requires Drive and `AIRSENSE_GITHUB_TOKEN` authorization. "
        "This repeats the frozen tuning plan for all 12 held-out stations: 756 learned-model fits. "
        "Expect substantially more computation than P6, potentially many sessions. Do not reduce the settings to speed up a final run.\n\n"
        "Completed training units and predictions are saved to Drive, with compact evidence and checksums "
        "pushed to the single `results/p7-sites-01` branch. An interrupted in-flight unit can be repeated. "
        "After a browser disconnect, rerun cell 3 to attach to the existing worker. If Colab replaced the runtime, "
        "run all cells to restore checkpoints. Use only one runtime and never delete lock files. "
        "P5/P6 models are preserved. P7 completion still requires independent scientific review."),
        md("## 1. Automatic setup\nThe matching code revision is embedded in this notebook."), code(bootstrap),
        md("## 2. Connect persistent storage\nAuthorize your existing Drive and GitHub secret when Colab asks."), code(setup),
        md("## 3. Run, resume or reconnect\nProgress identifies the station, model, seed and epoch/round checkpoint. "
           "RUNNING confirms the worker is present, not that a specific fit has completed. "
           "Stopping this display leaves the worker running. A FAILED message retains the log; inspect its cause before retrying."), code(run),
        md("## 4. Inspect completion\nThis runs only after the worker exits successfully. "
           "Cross-site generalization is not a causal site-shift penalty or inter-city transfer."), code(inspect)]
    for i, cell in enumerate(cells):
        cell["id"] = f"p7-{i:02d}"
    notebook = {"cells": cells, "nbformat": 4, "nbformat_minor": 5, "metadata": {
        "title": title, "airsense_code_revision": revision,
        "kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
        "language_info": {"name": "python"}}}
    (ROOT / "notebooks/06_p7_site_shift_analysis.ipynb").write_text(json.dumps(notebook, indent=1)+"\n", encoding="utf-8")


if __name__ == "__main__":
    main()
