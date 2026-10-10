# Scripts

## Remote acquisition check

```bash
python scripts/download_data.py
```

This verifies the authoritative UCI archive, writes `audit/acquisition_receipt.json`,
and retains no raw dataset.

## P2 structural audit

```bash
python scripts/run_data_audit.py
```

The script downloads into OS temporary storage only, performs station/timestamp/
missingness/window-coverage checks, saves compact reports under `audit/`, and removes
the raw archive when finished.

## P4 pipeline

Install `requirements-p4.txt` and the editable package, then run:

```bash
python scripts/run_pipeline.py --run-id p4-development
```

This is explicitly local-only. Add `--sync-remote` with a credential-free Git URL for incremental artifact publishing. See `docs/P4_WORKFLOW.md` for LOSO, internal folds, sensitivity preprocessing, resume, and Colab setup. `scripts/build_notebooks.py` regenerates notebooks 01–03 after intentional source updates; their embedded scientific-source fingerprint prevents mixed notebook/package revisions.

## P5 staged benchmark

Install requirements-p5.txt. scripts/run_benchmark.py provides explicit smoke, select and test stages with a required persistent model directory. Test access requires a completed selection record. See [P5_WORKFLOW.md](../docs/P5_WORKFLOW.md). scripts/build_p5_notebook.py generates notebook 04; regenerate all notebooks after a scientific source change.
