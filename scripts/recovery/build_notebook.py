"""Build recovery instructions around the unchanged, published P7 notebook."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
ORIGINAL_NOTEBOOK_COMMIT = "1f5e7569f42e91f5cd7e5ad213e92eeb41fbb65f"


def build(original: dict, revision: str, script_hash: str) -> dict:
    """Keep original scientific setup and result guards; replace only recovery entry."""
    if not re.fullmatch(r"[a-f0-9]{40}", revision):
        raise ValueError("Full recovery commit required")
    notebook = json.loads(json.dumps(original))
    for cell in notebook["cells"]:
        if isinstance(cell["source"], list):
            cell["source"] = "".join(cell["source"])
    cells = [cell for cell in notebook["cells"] if cell["cell_type"] == "code"]
    cells[0]["source"] += f'''
# Recovery adapter is separate from the immutable scientific source checkout.
RECOVERY_REVISION = "{revision}"
RECOVERY_SHA256 = "{script_hash}"
RECOVERY_SCRIPT = ROOT / ".tmp" / "p7-recovery" / RECOVERY_REVISION / "resume_p7_colab.py"
if not TEST_MODE:
    import hashlib
    import urllib.request
    url = (
        "https://raw.githubusercontent.com/Engr-Daniel/airsense-r/"
        + RECOVERY_REVISION + "/scripts/recovery/resume_p7_colab.py"
    )
    payload = urllib.request.urlopen(url, timeout=60).read()
    if hashlib.sha256(payload).hexdigest() != RECOVERY_SHA256:
        raise RuntimeError("Recovery download checksum mismatch")
    RECOVERY_SCRIPT.parent.mkdir(parents=True, exist_ok=True)
    RECOVERY_SCRIPT.write_bytes(payload)
'''
    cells[1]["source"] += '''
# Preserve the failed worker's log; the same experiment writer lock is retained.
JOB_DIRECTORY = ROOT / ".tmp/notebook-jobs" / (RUN_ID + "-colab-recovery")
if not TEST_MODE:
    from airsense_r.notebook_job import status
    if status(JOB_DIRECTORY)["state"] != "running":
        print("Checking saved checkpoints and restoring required dependency versions. Please wait.", flush=True)
        preparation = subprocess.run(
            [sys.executable, str(RECOVERY_SCRIPT), "--prepare",
             "--root", str(ROOT), "--model-directory", str(MODEL_DIRECTORY),
             "--remote", REMOTE],
            cwd=ROOT, capture_output=True, text=True,
        )
        print(preparation.stdout, flush=True)
        if preparation.returncode:
            print(preparation.stderr, flush=True)
            raise RuntimeError("Recovery setup stopped; see the error above. No training started.")
print("Ready. Cell 3 will verify saved development predictions before resuming.")
'''
    cells[2]["source"] = '''from airsense_r.notebook_job import run_and_watch
command = [sys.executable, str(RECOVERY_SCRIPT),
           "--root", str(ROOT), "--model-directory", str(MODEL_DIRECTORY),
           "--remote", REMOTE]
if TEST_MODE:
    import json
    command = json.loads(os.environ["AIRSENSE_P7_TEST_COMMAND"])
run_and_watch(command, JOB_DIRECTORY, ROOT)
'''
    notebook["cells"][0]["source"] += (
        "\n\n### Colab environment recovery (20 October 2026)\n"
        "Use **Run all** in a CPU runtime with your original Drive account. "
        "The original run ID, scientific code, models, splits and budgets are retained. "
        "Setup restores required scientific dependency versions only. "
        "The worker records the actual environment and replays completed folds' "
        "development predictions before resuming unfinished training. "
        "Replay may take time; it does not retrain completed models. "
        "Do not run the original notebook simultaneously. Old worker logs are preserved. "
        "This recovery adapter has separate pinned code and a verified download checksum."
    )
    notebook["metadata"]["airsense_recovery_revision"] = revision
    for cell in cells:
        cell["outputs"] = []
        cell["execution_count"] = None
    return notebook


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--revision", required=True)
    args = parser.parse_args()
    original = json.loads(subprocess.check_output([
        "git", "-C", str(ROOT), "show",
        ORIGINAL_NOTEBOOK_COMMIT + ":notebooks/06_p7_site_shift_analysis.ipynb",
    ]))
    digest = sha256((ROOT / "scripts/recovery/resume_p7_colab.py").read_bytes()).hexdigest()
    notebook = build(original, args.revision, digest)
    (ROOT / "notebooks/06b_p7_colab_recovery.ipynb").write_text(
        json.dumps(notebook, indent=1) + "\n", encoding="utf-8"
    )
