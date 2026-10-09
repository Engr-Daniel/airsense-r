"""Generate the three P4 notebooks with consistent standalone Colab bootstrap."""
from pathlib import Path
import json
from airsense_r.artifacts import source_hash


ROOT = Path(__file__).resolve().parents[1]

BOOTSTRAP = '''from pathlib import Path
import os, subprocess, sys

REPOSITORY = "https://github.com/Engr-Daniel/airsense-r.git"
# For Colab: paste the full P4 commit SHA from GitHub when prompted.
# Resume using the SAME revision and run ID as the original execution.
TEST_MODE = os.environ.get("AIRSENSE_NOTEBOOK_TEST_MODE") == "1"
if TEST_MODE:
    ROOT = Path(os.environ["AIRSENSE_NOTEBOOK_TEST_ROOT"]).resolve()
else:
    CODE_REVISION = os.environ.get("AIRSENSE_CODE_REVISION") or input("Full P4 code commit SHA: ").strip()
    if len(CODE_REVISION) != 40 or any(c not in "0123456789abcdef" for c in CODE_REVISION.lower()):
        raise ValueError("Use a full Git commit SHA, not a moving branch name")
    ROOT = Path.cwd() / "airsense-r"
    if not ROOT.exists():
        subprocess.run(["git", "clone", REPOSITORY, str(ROOT)], check=True)
        subprocess.run(["git", "-C", str(ROOT), "checkout", "--detach", CODE_REVISION], check=True)
    else:
        remote = subprocess.check_output(["git", "-C", str(ROOT), "remote", "get-url", "origin"], text=True).strip()
        head = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
        dirty = subprocess.check_output(["git", "-C", str(ROOT), "status", "--porcelain"], text=True).strip()
        if remote != REPOSITORY or head != CODE_REVISION or dirty:
            raise RuntimeError("Existing checkout differs or has edits; preserve it and use a fresh runtime")
    if sys.version_info < (3, 11):
        raise RuntimeError("Python 3.11+ required")
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", str(ROOT / "requirements-p4.txt"), "-e", str(ROOT)], check=True)
    print("Code revision:", CODE_REVISION)
print("Workspace:", ROOT)
'''

SETUP = '''import logging
from airsense_r.artifacts import provenance, json_bytes
from airsense_r.artifacts import source_hash
from airsense_r.checkpoints import open_run
from airsense_r.colab import configure_github_secret

logging.basicConfig(level=logging.INFO)
if source_hash(ROOT) != "NOTEBOOK_SOURCE_HASH":
    raise RuntimeError("Notebook and scientific source revisions differ; open the matching notebook revision")
if TEST_MODE:
    RUN_ID = os.environ["AIRSENSE_NOTEBOOK_TEST_RUN"]
    REMOTE = os.environ.get("AIRSENSE_NOTEBOOK_TEST_REMOTE")
else:
    from google.colab import userdata
    configure_github_secret(ROOT, userdata.get("AIRSENSE_GITHUB_TOKEN"))
    RUN_ID = input("Run ID (reuse only to resume compatible checkpoints): ").strip()
    REMOTE = REPOSITORY
'''


def md(text: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": text.splitlines(keepends=True)}


def code(text: str) -> dict:
    return {"cell_type": "code", "metadata": {}, "source": text.splitlines(keepends=True),
            "outputs": [], "execution_count": None}


def main() -> None:
    descriptions = [
        ("01_p2_dataset_audit_review", "STRUCTURAL AUDIT ARTIFACTS ONLY",
         "Inspect authoritative station coverage without downloading raw data or repeating the P2 audit.",
         '''from airsense_r.p4 import review_audit
store = open_run(ROOT, RUN_ID, provenance(ROOT, {"notebook": "01", "partition": "structural-only"}), REMOTE)
summary = review_audit(ROOT)
store.save("audit-review.csv", summary.to_csv(index=False).encode())
display(summary[["station", "rows", "target_missing_pct", "pm25_complete_history_windows"]])
'''),
        ("02_p3_development_diagnostics", "TRAIN ONLY",
         "Inspect training-only diagnostics without revising the frozen protocol. Real runs fetch the verified archive temporarily; only development rows are exposed.",
         '''from airsense_r.p4 import run_pipeline, synthetic_stream
if TEST_MODE:
    store = open_run(ROOT, RUN_ID, provenance(ROOT, {"notebook": "02", "synthetic_only": True}), REMOTE)
    data = synthetic_stream()
    summary = data.groupby("station")["PM2.5"].agg(["count", "mean"])
    store.save("synthetic-diagnostics.csv", summary.to_csv().encode())
    display(summary)
else:
    output = run_pipeline(ROOT, RUN_ID, remote=REMOTE, training_diagnostics=True)
    print("Verified training summaries saved incrementally:", output)
    from airsense_r.p4 import inspect_training_diagnostics
    display(inspect_training_diagnostics(ROOT, output))
'''),
        ("03_p4_pipeline_validation", "TRAIN + VALIDATION (synthetic fixture for executable checks)",
         "Validate causality, station exclusion and input layouts on synthetic data. This is not a forecasting benchmark and reports no final-test performance.",
         '''from airsense_r.p4 import validate_synthetic_pipeline
store = open_run(ROOT, RUN_ID, provenance(ROOT, {"notebook": "03", "synthetic_only": True}), REMOTE)
report = validate_synthetic_pipeline()
store.save("pipeline-validation.json", json_bytes(report))
display(report)
''')]
    for name, partition, purpose, analysis in descriptions:
        cells = [md(f"# {name.replace('_', ' ')}\n\n**Permitted partitions: {partition}**\n\n{purpose}\n\n"
                    "Protocol: frozen 2026-10-08; provenance uses exact content hashes. "
                    "Training targets end 2015-02-28; validation ends 2016-02-29. "
                    "Final test outcomes are not analyzed here.\n\n"
                    "Prerequisites: open this notebook from the same P4 Git revision you will enter below. "
                    "In Colab Secrets, set `AIRSENSE_GITHUB_TOKEN` with write access to this repository. "
                    "Outputs go to `results/<run-id>` on a dedicated Git branch after every checkpoint. "
                    "Expect setup/download to take minutes; no forecasting model training occurs. "
                    "If dependency installation requires a runtime restart, restart and rerun setup.\n"),
                 md("## Runtime bootstrap\nClone a pinned revision in a fresh runtime; preserve existing work on rerun."), code(BOOTSTRAP),
                 md("## Artifact authentication and run identity\nThe secret is never printed or written into Git configuration. Use the same run ID only for compatible resumes."), code(SETUP.replace("NOTEBOOK_SOURCE_HASH", source_hash(ROOT))),
                 md("## Evidence and validation\nProvenance is checked before restoring outputs. Each completed artifact is saved and pushed before continuing."), code(analysis),
                 md("## Interpretation and limitations\nReview the displayed evidence before drawing conclusions. Synthetic checks establish implementation behavior, not predictive performance. "
                    "Training diagnostics cannot justify silently changing frozen settings. Audit missingness is structural evidence. "
                    "A failed push stops execution with a local checkpoint retained; restart with the same revision/run ID to restore remotely confirmed work. "
                    "In-flight work not yet uploaded can be lost on runtime termination. See `docs/P4_WORKFLOW.md` for commands and validation limits.")]
        for i, cell in enumerate(cells):
            cell["id"] = f"cell-{i:02d}"
        notebook = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                    "language_info": {"name": "python", "version": "3.11"}}, "nbformat": 4, "nbformat_minor": 5}
        (ROOT / "notebooks" / f"{name}.ipynb").write_text(json.dumps(notebook, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
