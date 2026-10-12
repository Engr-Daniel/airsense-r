"""Generate P6 Colab preflight/evaluation with shared verified bootstrap."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    """Keep execution in the package/script and interpretation in the notebook."""
    notebook = json.loads((ROOT / "notebooks/04b_p5_corrected_test.ipynb").read_text())
    cells = notebook["cells"]
    def replace(index, text):
        cells[index]["source"] = text.splitlines(keepends=True)
    replace(0, f"# {notebook['metadata']['title']}\n\n## 05 P6 sensor degradation\n\n"
        "**Permitted partitions:** preflight uses TRAIN + VALIDATION only to reproduce original "
        "preprocessing and frozen predictions, then FINAL TEST — READ ONLY to replay accepted clean "
        "predictions. Evaluation uses the final test with predefined synthetic observation stresses. "
        "No model fitting, tuning or selection occurs.\n\n"
        "Run preflight first in a fresh CPU runtime with your original model directory and "
        "AIRSENSE_GITHUB_TOKEN secret. The full evaluation covers 15 conditions, 63 realizations, "
        "and primary/no-forward-fill policies; allow hours for inference and bootstrap. "
        "Predictions persist in Drive with GitHub checksum references and compact results. "
        "No raw dataset is retained. Use one session only. See `docs/P6_WORKFLOW.md`.")
    replace(3, "## 2. Provenance and authentication\nUse a new P6 run ID, for example `p6-sensors-01`. "
        "Reuse it for preflight, evaluation and resume at exactly the same revision/environment.")
    replace(4, ''.join(cells[4]["source"]).replace("p5-clean-01-corrected-02", "p6-sensors-01"))
    replace(5, "## 3. Stage and persistent storage\nChoose `preflight` first. After it passes and is "
        "reviewed, rerun setup with the same ID and choose `evaluate`. Use the original model directory; "
        "P6 predictions are saved separately under its `p6-artifacts/<run-id>` subdirectory.")
    storage = ''.join(cells[6]["source"])
    replace(6, '''STAGE = input("P6 stage [preflight/evaluate] (default preflight): ").strip() or "preflight"
if STAGE not in {"preflight", "evaluate"}:
    raise ValueError("Choose preflight or evaluate")
''' + storage[storage.index("storage_text ="):])
    replace(7, "## 4. Execute with incremental checkpoints\n"
        "Do not start another copy if this cell appears quiet. Duplicate scripts in this runtime "
        "are rejected by a lock; other runtimes must also remain stopped. On interruption, only "
        "the current unconfirmed prediction unit needs repeating. Git failures stop computation. "
        "Drive filesystem writes do not guarantee immediate server-side upload; preserve the mount.")
    command = ''.join(cells[8]["source"]).replace('"scripts/recover_p5_test.py"', '"scripts/run_sensor_degradation.py"')
    command = command.replace('"--run-id", RUN_ID,', '"--stage", STAGE, "--run-id", RUN_ID,')
    replace(8, command.replace("Recovery stopped", "P6 stopped"))
    replace(9, "## 5. Inspect verified outputs\nRun only after execution succeeds. "
        "Preflight is an engineering acceptance check; it is not a degradation result. "
        "For completed evaluation, interpret near-ties and paired uncertainty alongside ranks.")
    replace(10, '''import json
import pandas as pd
from airsense_r.artifacts import RunStore
from IPython.display import Image
output = ROOT / ".tmp/checkpoint-checkouts" / RUN_ID / "results" / RUN_ID
manifest = json.loads((output / "manifest.json").read_text())
store = RunStore(output, manifest["provenance"])
display(store.load_json("preflight-complete.json"))
if STAGE == "evaluate":
    display(store.load_json("complete.json"))
    payload = store.load_json("dashboard-p6.json")
    rows = []
    for report in payload["reports"]:
        for scope, summary in report["scopes"].items():
            for metric in summary["metrics"]:
                rows.append({"policy": report["policy"], "condition": report["condition"]["id"],
                             "scope": scope, **metric})
    display(pd.DataFrame(rows))
    display(Image(filename=str(output / "figure-p6-primary.png")))
    print("Paired intervals and selection regret are in each dashboard report's scopes.")
''')
    replace(11, "## Interpretation and retention\n"
        "Synthetic stresses do not establish physical sensor-fault realism or embedded deployment. "
        "Whole-channel loss is deterministic; do not count its one realization as five replications. "
        "The no-forward-fill arm changes inference imputation only, with the same trained models "
        "and its own matched clean comparator. Sparse outage-affected uncertainty may be explicitly "
        "unavailable; never substitute independent-row intervals. Full-period headline intervals "
        "are mandatory. Preserve model snapshots, P6 Drive arrays and result branches. Save the "
        "executed notebook separately and request review before declaring P6 complete.")
    (ROOT / "notebooks/05_p6_sensor_degradation_analysis.ipynb").write_text(json.dumps(notebook, indent=1)+"\n", encoding="utf-8")


if __name__ == "__main__":
    main()
