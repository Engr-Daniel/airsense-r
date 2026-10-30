"""Publish the read-only P9 saved-prediction verifier with pinned source."""
import argparse
import json
from pathlib import Path

from scripts.build_target_history_notebook import build as experiment_notebook


def build(revision: str) -> dict:
    """Reuse the tested bootstrap and reconnectable job; never run inference."""
    notebook = experiment_notebook(revision)
    cells = notebook["cells"]
    cells[0]["source"] = (
        "# " + notebook["metadata"]["title"] + "\n\n"
        "## 08b Independent saved-prediction verification\n\n"
        "**Permitted partitions: FINAL TEST — READ ONLY.**\n\n"
        "Use a CPU runtime and Run all. Mount the same Drive account and enable "
        "the AIRSENSE_GITHUB_TOKEN Colab secret. No SHA or stage entry is needed. "
        "This checks the 261 saved prediction bundles, recomputes metrics and "
        "paired uncertainty, and publishes separate review checkpoints. "
        "It does not train models, run inference or change experiment outputs. "
        "Drive reads and 2,000-replicate bootstrap calculations can take time; "
        "progress is printed per file batch and condition. After disconnection "
        "rerun cell 3 to reconnect; after runtime replacement use Run all. "
        "Completed condition reviews resume after all saved file hashes are rechecked. "
        "Never delete a lock. Save this notebook with outputs when finished."
    )
    for cell in cells:
        cell["id"] = cell["id"].replace("p9-", "p9-review-")
        if cell["cell_type"] != "code":
            continue
        source = cell["source"]
        source = source.replace('[train,notebooks]', '[notebooks]')
        source = source.replace('airsense-r-p9-', 'airsense-r-p9-review-')
        source = source.replace('from airsense_r.target_history import RUN_ID',
                                'RUN_ID = "p9-target-history-review-01"')
        source = source.replace('AIRSENSE_P9_TEST_', 'AIRSENSE_P9_REVIEW_TEST_')
        source = source.replace('scripts/run_target_history.py', 'scripts/verify_target_history.py')
        source = source.replace('Ready: frozen-model replay, then five PM2.5-history conditions. No training.',
                                'Ready: verify saved predictions and uncertainty. No training or inference.')
        if 'store = RunStore' in source:
            source = '''import json
from airsense_r.artifacts import RunStore, source_hash
from airsense_r.notebook_job import status
if status(JOB_DIRECTORY)["state"] != "complete":
    raise RuntimeError("Review incomplete; rerun cell 3 to reconnect or inspect its error")
directory = ROOT / ".tmp/checkpoint-checkouts" / RUN_ID / "results" / RUN_ID
manifest = json.loads((directory / "manifest.json").read_bytes())
provenance = manifest["provenance"]
if provenance["verifier_source_hash"] != source_hash(ROOT):
    raise RuntimeError("Verifier provenance mismatch")
store = RunStore(directory, provenance)
completion = store.load_json("complete.json")
if not completion["passed"]:
    raise RuntimeError("Verification did not pass")
display(completion)
print("VERIFICATION COMPLETE. Save this notebook with outputs for final review.")
'''
        cell["source"] = source
    cells[5]["source"] = "## 3. Verify saved predictions and publish review checkpoints"
    return notebook


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--revision", required=True)
    args = parser.parse_args()
    path = Path(__file__).resolve().parents[1] / "notebooks/08b_p9_saved_prediction_verification.ipynb"
    path.write_text(json.dumps(build(args.revision), indent=1) + "\n", encoding="utf-8")
