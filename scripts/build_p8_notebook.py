"""Publish a four-cell, pinned, read-only verification and failure-analysis notebook."""
import argparse
import json
from pathlib import Path
import re
import yaml
from airsense_r.artifacts import source_hash
from scripts.build_notebooks import BOOTSTRAP, md, code

ROOT=Path(__file__).resolve().parents[1]


def build(revision: str) -> dict:
    """Embed every run setting so users can Run all without SHA/stage prompts."""
    if not re.fullmatch('[a-f0-9]{40}',revision):raise ValueError('Full commit required')
    bootstrap=BOOTSTRAP.replace(
        'CODE_REVISION = (os.environ.get("AIRSENSE_CODE_REVISION") or input("Code version: full 40-character Git commit SHA (not a run ID): ")).strip().lower()',
        f'CODE_REVISION = "{revision}"').replace('ROOT = Path.cwd() / "airsense-r"',f'ROOT = Path.cwd() / "airsense-r-p8-{revision[:12]}"')
    bootstrap+=f'''\nfrom airsense_r.artifacts import source_hash
if source_hash(ROOT) != "{source_hash(ROOT)}":
    raise RuntimeError("Notebook/source mismatch; reopen the matching published notebook")
'''
    setup='''from airsense_r.colab import configure_github_secret
RUN_ID = "p8-analysis-01"
if TEST_MODE:
    MODEL_DIRECTORY = Path(os.environ["AIRSENSE_P8_TEST_MODELS"])
    RUN_ID = os.environ["AIRSENSE_P8_TEST_RUN"]
    REMOTE = "fixture"
else:
    from google.colab import drive, userdata
    drive.mount("/content/drive")
    MODEL_DIRECTORY = Path("/content/drive/MyDrive/AirSense-R/model-checkpoints")
    configure_github_secret(ROOT, userdata.get("AIRSENSE_GITHUB_TOKEN"))
    REMOTE = REPOSITORY
if not (MODEL_DIRECTORY / "storage.json").is_file():
    raise FileNotFoundError("Original Drive storage is missing; check the mounted account")
JOB_DIRECTORY = ROOT / ".tmp/notebook-jobs" / RUN_ID
print("Ready: verify saved P7 predictions, then analyze P6/P7 failures. No training.")
'''
    run='''from airsense_r.notebook_job import run_and_watch
command = [sys.executable, str(ROOT / "scripts/run_failure_analysis.py"),
           "--model-directory", str(MODEL_DIRECTORY), "--remote", REMOTE]
if TEST_MODE:
    import json
    command = json.loads(os.environ["AIRSENSE_P8_TEST_COMMAND"])
run_and_watch(command, JOB_DIRECTORY, ROOT)
'''
    inspect='''import json
from airsense_r.artifacts import RunStore, source_hash
from airsense_r.notebook_job import status
if status(JOB_DIRECTORY)["state"] != "complete":
    raise RuntimeError("Analysis is not complete; rerun cell 3 to reconnect or inspect its error")
directory = ROOT / ".tmp/checkpoint-checkouts" / RUN_ID / "results" / RUN_ID
manifest = json.loads((directory / "manifest.json").read_bytes())
store = RunStore(directory, manifest["provenance"])
if manifest["provenance"].get("source_hash") != source_hash(ROOT) or manifest["provenance"].get("run_id") != RUN_ID:
    raise RuntimeError("Analysis provenance mismatch")
if not store.load_json("p7-verification.json").get("passed") or not store.load_json("complete.json").get("execution_complete"):
    raise RuntimeError("Verification/analysis completion record missing")
display(store.load_json("p7-verification.json"))
display(store.load_json("dashboard-p8.json"))
print("P8 EXECUTION COMPLETE. Save this notebook with outputs for independent review.")
'''
    title=yaml.safe_load((ROOT/'CITATION.cff').read_text(encoding='utf-8'))['title']
    cells=[md(f'# {title}\n\n## 07 Statistical and failure analysis\n\n'
        '**Permitted partitions: saved VALIDATION and FINAL TEST — READ ONLY.**\n\n'
        'Choose a CPU runtime and **Run all**. Authorize the original Drive account and GitHub secret. '
        'No SHA, stage or run name is required. This verifies P7 prediction files, final native model bytes, '
        'validation selection, metrics and independent block-bootstrap intervals before failure analysis. '
        'It then checks saved P6 arrays and reports concentration bands, seasons, worst errors and rank stability. '
        'It never trains, predicts again or downloads raw data. Allow substantial Drive reading time; '
        'completed units publish incrementally to one analysis branch.\n\n'
        'Concentration bands and seasonal/worst-case analyses are **post-results exploratory diagnostics**, '
        'not health categories or additional confirmatory hypotheses. Results remain within-Beijing evidence. '
        'After disconnection rerun cell 3; if the runtime was replaced, Run all. Never delete locks. '
        'Use only one runtime. Scientific acceptance follows review of the completed evidence.'),
        md('## 1. Setup'),code(bootstrap),md('## 2. Connect original saved evidence'),code(setup),
        md('## 3. Verify, analyze and save incrementally'),code(run),
        md('## 4. Review completion'),code(inspect)]
    for i,c in enumerate(cells):c['id']=f'p8-{i:02d}'
    return {'cells':cells,'nbformat':4,'nbformat_minor':5,'metadata':{'title':title,'airsense_code_revision':revision,
        'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'},'language_info':{'name':'python'}}}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--revision',required=True);args=p.parse_args()
    (ROOT/'notebooks/07_p8_statistical_failure_analysis.ipynb').write_text(json.dumps(build(args.revision),indent=1)+'\n',encoding='utf-8')
