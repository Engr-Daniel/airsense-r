"""Generate a four-cell, no-prompt saved-result review notebook."""
import argparse
import json
from pathlib import Path
import re
import subprocess

import yaml

from airsense_r.artifacts import source_hash
from scripts.build_notebooks import BOOTSTRAP, md, code

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    """Embed the verifier revision; never ask the user to type SHA or stage."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--revision')
    args = parser.parse_args()
    revision = args.revision or subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    if not re.fullmatch('[a-f0-9]{40}', revision):
        raise ValueError('Full source commit required')
    bootstrap = BOOTSTRAP.replace(
        'CODE_REVISION = (os.environ.get("AIRSENSE_CODE_REVISION") or input("Code version: full 40-character Git commit SHA (not a run ID): ")).strip().lower()',
        f'CODE_REVISION = "{revision}"')
    bootstrap = bootstrap.replace('ROOT = Path.cwd() / "airsense-r"', f'ROOT = Path.cwd() / "airsense-r-review-{revision[:12]}"')
    bootstrap = bootstrap.replace('requirements-p4.txt', 'requirements-p6-review.txt')
    bootstrap += f'''\nfrom airsense_r.artifacts import source_hash
if source_hash(ROOT) != "{source_hash(ROOT)}":
    raise RuntimeError("Verification notebook/source mismatch; reopen the published notebook")
print("Setup ready. The completed P6 experiment will not be rerun.")
'''
    setup = '''from airsense_r.colab import configure_github_secret
REVIEW_RUN = "p6-sensors-01-review-01"
if TEST_MODE:
    MODEL_DIRECTORY = Path(os.environ["AIRSENSE_REVIEW_TEST_MODELS"])
    REVIEW_RUN = os.environ["AIRSENSE_REVIEW_TEST_RUN"]
    REMOTE = os.environ.get("AIRSENSE_REVIEW_TEST_REMOTE", "unused-fixture")
else:
    from google.colab import drive, userdata
    drive.mount("/content/drive")
    MODEL_DIRECTORY = Path("/content/drive/MyDrive/AirSense-R/model-checkpoints")
    configure_github_secret(ROOT, userdata.get("AIRSENSE_GITHUB_TOKEN"))
    REMOTE = REPOSITORY
if not MODEL_DIRECTORY.is_dir():
    raise FileNotFoundError("Original model-checkpoints directory is unavailable; check the Drive mount")
JOB_DIRECTORY = ROOT / ".tmp" / "notebook-jobs" / REVIEW_RUN
print("Ready: verify saved P6 results. Run settings are already filled in.")
'''
    run = '''from airsense_r.notebook_job import run_and_watch
command = [sys.executable, str(ROOT / "scripts/verify_p6_saved_results.py"),
           "--model-directory", str(MODEL_DIRECTORY), "--remote", REMOTE]
if TEST_MODE:
    import json
    command = json.loads(os.environ["AIRSENSE_REVIEW_TEST_COMMAND"])
run_and_watch(command, JOB_DIRECTORY, ROOT)
'''
    inspect = '''import json
from airsense_r.artifacts import RunStore
from airsense_r.notebook_job import status
if status(JOB_DIRECTORY)["state"] != "complete":
    raise RuntimeError("Verification is not complete yet. Run the preceding cell to reconnect or resume.")
output = ROOT / ".tmp/checkpoint-checkouts" / REVIEW_RUN / "results" / REVIEW_RUN
manifest = json.loads((output / "manifest.json").read_bytes())
store = RunStore(output, manifest["provenance"])
report = store.load_json("complete.json")
if report.get("passed") is not True:
    raise RuntimeError("Verification has not passed")
display(report)
print("VERIFICATION COMPLETE. Save this executed notebook for review. No P6 rerun is required.")
'''
    title = yaml.safe_load((ROOT/'CITATION.cff').read_text(encoding='utf-8'))['title']
    cells = [md(f'# {title}\n\n## 05b Verify saved P6 results\n\n'
        '**Permitted partitions: FINAL TEST — READ ONLY, existing saved predictions.**\n\n'
        'Choose **Runtime → Run all** in a CPU Colab runtime. Settings are built in: no SHA, stage or run-name entry. '
        'Approve Drive and the existing `AIRSENSE_GITHUB_TOKEN` secret when Colab requests access. '
        'This checks saved files and independently recomputes statistics; it never fits models, predicts again, or downloads raw data. '
        'Expect minutes to tens of minutes, depending on Drive and CPU. Each completed condition review is pushed to GitHub.\n\n'
        'After a browser disconnect, reconnect and rerun the verification cell: it attaches to the existing worker. '
        'If the runtime was replaced, run all four cells to restore completed review checkpoints. '
        'Use only one runtime. Never delete lock files. Original P6 artifacts remain read-only.'),
        md('## 1. Automatic setup\nThe matching source revision is embedded here; existing experiment checkouts are preserved.'),code(bootstrap),
        md('## 2. Connect your saved files\nDrive may request authorization in a fresh runtime. Your paths and run identity are already configured.'),code(setup),
        md('## 3. Verify or reconnect\nLive progress appears below. Stopping this display leaves the worker running; rerun this cell to reconnect. '
           'If the worker fails, the cell says FAILED and retains its log and completed checkpoints. A missing/corrupt file must be reviewed, not bypassed.'),code(run),
        md('## 4. Verified outcome\nRuns after the worker finishes. Save this executed notebook separately; the report is also checkpointed on GitHub.'),code(inspect)]
    for i, cell in enumerate(cells): cell['id']=f'p6-review-{i:02d}'
    notebook={'cells':cells,'nbformat':4,'nbformat_minor':5,'metadata':{
        'title':title,'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'},
        'language_info':{'name':'python'},'airsense_verifier_revision':revision}}
    (ROOT/'notebooks/05b_p6_saved_result_verification.ipynb').write_text(json.dumps(notebook,indent=1)+'\n',encoding='utf-8')


if __name__ == '__main__':
    main()
