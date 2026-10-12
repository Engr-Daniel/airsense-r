"""Generate the dedicated evaluation-only P5 correction notebook."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    """Reuse current bootstrap/storage cells and expose the guarded recovery script."""
    notebook = json.loads((ROOT / "notebooks/04_p5_clean_benchmark_analysis.ipynb").read_text())
    cells = notebook["cells"]
    def replace(index, text):
        cells[index]["source"] = text.splitlines(keepends=True)
    title = notebook["metadata"]["title"]
    replace(0, f"# {title}\n\n## 04b Corrected P5 test evaluation\n\n"
        "**Permitted partitions:** TRAIN + VALIDATION for preprocessing identity and frozen-model "
        "prediction replay; then FINAL TEST — READ ONLY after every replay passes. "
        "No model training, tuning or model selection is performed.\n\n"
        "This corrects the documented 2026-10-12 restored-feature-order defect. The original "
        "`p5-clean-01` artifacts and Google Drive models remain untouched. Use a fresh CPU runtime, "
        "the same original Drive directory and a new correction run ID. Allow time for downloading "
        "the original evidence and replaying all models; this does not repeat 54 tuning fits. "
        "Only one Colab session may run this recovery. See `docs/P5_RECOVERY.md`.")
    replace(3, "## 2. Provenance and GitHub authentication\n"
        "New correction run: `p5-clean-01-corrected-01`. Reuse this ID only to resume this correction "
        "at the same code revision/environment. Never enter `p5-clean-01` here.")
    replace(4, ''.join(cells[4]["source"]).replace("p5-smoke-01", "p5-clean-01-corrected-01"))
    replace(5, "## 3. Original persistent model storage\n"
        "Use `/content/drive/MyDrive/AirSense-R/model-checkpoints`, the original parent directory. "
        "The script reads the existing `p5-clean-01` model subdirectory without modifying it.")
    storage = ''.join(cells[6]["source"])
    replace(6, 'STAGE = "corrected-test"\n' + storage[storage.index('storage_text ='):])
    replace(7, "## 4. Verify development predictions, then rescore\n"
        "Output is streamed below. Each passed model replay and completed test shard is backed up "
        "to the correction result branch. The script locks out a second recovery in this runtime. "
        "If any check fails, stop and share the error; do not change tolerances or retrain. "
        "A runtime interruption may require repeating prediction work, but never model fitting.")
    replace(8, '''command = [sys.executable, str(ROOT / "scripts/recover_p5_test.py"),
           "--run-id", RUN_ID, "--model-directory", str(MODEL_DIRECTORY), "--sync-remote", REMOTE]
with subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                      text=True, bufsize=1, env={**os.environ, "PYTHONUNBUFFERED": "1"}) as process:
    try:
        for line in process.stdout:
            print(line, end="", flush=True)
        return_code = process.wait()
    except KeyboardInterrupt:
        process.terminate()
        process.wait()
        raise
if return_code:
    raise RuntimeError(f"Recovery stopped ({return_code}). Read the error above; do not start another copy.")
''')
    replace(9, "## 5. Verify and display corrected evidence\n"
        "Run after cell 4 succeeds. Save this executed notebook separately from the original run.")
    replace(10, '''import json
import pandas as pd
from airsense_r.artifacts import RunStore
from airsense_r.p5 import require_selection
from IPython.display import Image
output = ROOT / ".tmp/checkpoint-checkouts" / RUN_ID / "results" / RUN_ID
manifest = json.loads((output / "manifest.json").read_text())
store = RunStore(output, manifest["provenance"])
decision = require_selection(store)
print("Frozen selected family:", decision["selected_family"])
display(store.load_json("validation-replay-complete.json"))
display(store.load_json("complete.json"))
display(pd.read_csv(output / "metrics-test-aggregate.csv"))
display(store.load_json("test-uncertainty.json"))
display(Image(filename=str(output / "figure-test-mae.png")))
''')
    replace(11, "## Interpretation\n"
        "The original test report is invalidated; retain it as incident evidence. Corrected results "
        "must cite the correction lineage and post-results disclosure. Keep models and selection "
        "frozen. Send the executed recovery notebook for review before P6.")
    (ROOT / "notebooks/04b_p5_corrected_test.ipynb").write_text(json.dumps(notebook, indent=1)+"\n", encoding="utf-8")


if __name__ == "__main__":
    main()
