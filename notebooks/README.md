# Research notebooks

The naming sequence and required conventions are defined in [the notebook guide](../docs/NOTEBOOK_GUIDE.md).

Build notebooks 01–03 during P4, and notebooks 04–07 alongside P5–P8. The P2 notebook reviews saved evidence; it does not perform the authoritative audit. Reusable implementation belongs in the package and reproducible execution in scripts.

Notebooks 01–03 and shared checkpoint synchronization/resume support are implemented. They push checkpoints when a remote and credentials are configured; local/CI tests use temporary bare Git remotes. User-run live Colab publication and notebook 03 fresh-runtime recovery were reviewed on 2026-10-09. The import workaround is now standardized in bootstrap and tested locally. See `docs/P4_WORKFLOW.md`.

Google Colab is the intended execution environment. Every notebook starts with a bootstrap section that clones the repository in a fresh runtime, verifies a recorded code revision, installs dependencies and the package, and initializes or restores run checkpoints. Rerunning setup must preserve existing work. Follow the guide's Colab bootstrap requirements.


## Canonical title and historical execution evidence

The canonical study title comes from CITATION.cff. Current notebook title pages
are generated from it. The title-generator update changes the recorded source
fingerprint; use the same commit as the opened notebook and a new run ID.
Successful executed notebooks remain preserved at
[commit c28c02b](https://github.com/Engr-Daniel/airsense-r/tree/c28c02b87dca1c82c480cd24e7ccd6271792369d/notebooks)
and checkpoint artifacts remain in results/p4/colab-archive/.
Current source notebooks are regenerated without historical outputs to avoid
attributing old executions to updated source. No additional user rerun is needed.

## P5 notebook

04_p5_clean_benchmark_analysis.ipynb runs one explicit stage: training-only smoke, train/validation selection, or gated final-test scoring. It requires the P5 environment and persistent model storage. Corrected P5 results have passed independent review; see [P5_COMPLETION_REPORT.md](../research/P5_COMPLETION_REPORT.md). Follow [P5_WORKFLOW.md](../docs/P5_WORKFLOW.md).

For the existing `p5-clean-01` run, use **04b_p5_corrected_test.ipynb** and
[P5_RECOVERY.md](../docs/P5_RECOVERY.md). Its original test predictions require
correction of restored scaled-feature order. The `_smoke`, `_select` and `_test`
notebooks preserve the user's historical executions at their original SHA; their
outputs are not evidence that the corrected source has already run. Do not rerun
the old test notebook, retune models or delete the original Drive snapshots.

Successful corrected execution is preserved byte-for-byte in `04b_p5_corrected_test_executed.ipynb`; the unsuffixed notebook remains the source template. Its recorded SHA identifies the generating code. No additional rerun is needed.

## P6 notebook

`05_p6_sensor_degradation_analysis.ipynb` has explicit `preflight` and `evaluate` stages. It reuses frozen P5 models, verifies development and clean-test replay, and stores lossless predictions in Drive with Git references. Follow [P6_WORKFLOW.md](../docs/P6_WORKFLOW.md). Local tests and preflight are engineering acceptance, not completed stress findings.

The accepted Colab preflight is preserved byte-for-byte in
`05_p6_sensor_degradation_preflight_executed.ipynb`. Its review is recorded in
`results/p6/preflight_acceptance.json`. Continue evaluation at its original
source commit and run ID; the unsuffixed notebook remains the unexecuted template.
