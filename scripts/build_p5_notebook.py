"""Generate the staged P5 Colab workflow without duplicating scientific logic."""
from pathlib import Path
import json
import runpy

from airsense_r.artifacts import source_hash
import yaml

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    """Reuse verified checkout/bootstrap cells and keep long runs explicitly staged."""
    common = runpy.run_path(str(ROOT / "scripts/build_notebooks.py"))
    md, code = common["md"], common["code"]
    title = yaml.safe_load((ROOT / "CITATION.cff").read_text())["title"]
    cells = [md(f"# {title}\n\n## 04 P5 clean benchmark analysis\n\n"
        "**Permitted partitions by stage:** `smoke`: TRAIN ONLY (engineering check); "
        "`select`: TRAIN + VALIDATION; `test`: FINAL TEST — READ ONLY (plus historical inputs). "
        "Test access requires a completed immutable validation selection. No stage silently tunes on test data.\n\n"
        "Start with smoke in a fresh CPU Colab runtime. Configure `AIRSENSE_GITHUB_TOKEN` "
        "and persistent model storage (for example a dedicated Google Drive directory). "
        "Compact artifacts push to a run branch; large native model files stay in persistent storage. "
        "A full selection run has 54 tuning fits and 9 learned refits, and can take hours on CPU. "
        "Do not use smoke outputs as research results. See `docs/P5_WORKFLOW.md`."),
        md("## 1. Bootstrap\nUse the code SHA from the same GitHub revision as this notebook. "
           "Installing the declared environment can require a kernel restart; preserve the checkout and rerun setup."),
        code(common["BOOTSTRAP"].replace("requirements-p4.txt", "requirements-p5.txt")),
        md("## 2. Provenance and GitHub authentication\nUse a new run ID for new code. "
           "Reuse the benchmark ID for select, test and recovery; use a separate smoke ID."),
        code(common["SETUP"].replace("NOTEBOOK_SOURCE_HASH", source_hash(ROOT)).replace("nb03-validation-01", "p5-smoke-01")),
        md("## 3. Stage and persistent storage\nChoose smoke first. After it passes, rerun this notebook "
           "with a new benchmark run ID and stage select. Later use that same benchmark ID with stage test. "
           "Use the same persistent directory across these stages. Start only one writer per run."),
        code('''STAGE = input("Stage [smoke/select/test] (default smoke): ").strip() or "smoke"
if STAGE not in {"smoke", "select", "test"}:
    raise ValueError("Choose smoke, select, or test")
storage_text = input("Persistent model directory (e.g. /content/drive/MyDrive/AirSense-R/model-checkpoints): ").strip()
if not storage_text:
    raise ValueError("A persistent model directory is required")
MODEL_DIRECTORY = Path(storage_text).expanduser().resolve()
if str(MODEL_DIRECTORY).startswith("/content/drive/"):
    from google.colab import drive
    drive.mount("/content/drive")
    if not Path("/content/drive/MyDrive").is_dir():
        raise RuntimeError("Google Drive is not mounted")
elif str(MODEL_DIRECTORY).startswith("/content/"):
    raise ValueError("Ordinary /content storage is ephemeral; use mounted persistent storage")
print("Stage:", STAGE)
print("Model storage:", MODEL_DIRECTORY)
'''),
        md("## 4. Execute the reproducible script\nProgress is checkpointed each neural epoch or tree-round chunk. "
           "A lost in-flight unit is repeated. GitHub failures stop the run; rerun the same identity to retry. "
           "A Drive mount confirms filesystem access, not a guarantee of immediate cloud-server flush."),
        code('''command = [sys.executable, str(ROOT / "scripts/run_benchmark.py"), "--stage", STAGE,
           "--run-id", RUN_ID, "--model-directory", str(MODEL_DIRECTORY), "--sync-remote", REMOTE]
subprocess.run(command, cwd=ROOT, check=True)
'''),
        md("## 5. Inspect verified evidence\nEngineering smoke reports contain recovery checks, not benchmark scores. "
           "For benchmarks, means are computed over seed metrics within station, then stations equally."),
        code('''import json
import pandas as pd
from airsense_r.artifacts import RunStore
output = ROOT / ".tmp/checkpoint-checkouts" / RUN_ID / "results" / RUN_ID
manifest = json.loads((output / "manifest.json").read_text())
store = RunStore(output, manifest["provenance"])
store.verify()
if STAGE == "smoke":
    display(pd.DataFrame([store.load_json(f"smoke-{family}.json") for family in ("xgboost", "mlp", "gru")]))
else:
    from airsense_r.p5 import require_selection
    display(require_selection(store))
    phase = "test" if STAGE == "test" else "validation"
    display(pd.read_csv(output / f"metrics-{phase}-aggregate.csv"))
    from IPython.display import Image
    display(Image(filename=str(output / f"figure-{phase}-mae.png")))
    if STAGE == "test":
        display(store.load_json("test-uncertainty.json"))
'''),
        md("## Interpretation and next steps\nA numerical rank change is not automatically meaningful. "
           "Interpret errors, the frozen near-tie threshold, paired intervals and selection regret together. "
           "Final-test winners are descriptive oracles only. P6 reuses the fitted models without retraining; "
           "retain their persistent snapshots. A changed configuration/environment requires a new run ID. "
           "Do not delete active result branches or model storage. Historical runs remain tied to their original code.")]
    for i, cell in enumerate(cells):
        cell["id"] = f"cell-{i:02d}"
    notebook = {"cells": cells, "metadata": {"title": title, "kernelspec": {
        "display_name": "Python 3", "language": "python", "name": "python3"}},
        "nbformat": 4, "nbformat_minor": 5}
    (ROOT / "notebooks/04_p5_clean_benchmark_analysis.ipynb").write_text(json.dumps(notebook, indent=1)+"\n", encoding="utf-8")


if __name__ == "__main__":
    main()
