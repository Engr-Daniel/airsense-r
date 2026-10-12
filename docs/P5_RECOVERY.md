# Corrected P5 test evaluation

Update 2026-10-12: the first correction attempt (`p5-clean-01-corrected-01`)
stopped before test scoring because the default CSV reader altered two decimal
labels by one floating-point rounding step. Replay now uses round-trip float
parsing and retains exact target equality and the original prediction tolerances.
Use the updated notebook/code revision and new correction ID ending in `-02`.
Preserve the failed correction branch as diagnostic evidence; no retraining is needed.

Use `notebooks/04b_p5_corrected_test.ipynb` for the documented 2026-10-12
preprocessing incident. Do not rerun the old test notebook or retrain the models.

1. Open notebook 04b at its published code revision in a fresh CPU Colab runtime.
   Use the same full revision SHA at bootstrap. Allow access to the
   `AIRSENSE_GITHUB_TOKEN` Colab Secret.
2. Enter a **new** run ID: `p5-clean-01-corrected-02`.
3. Mount the original directory:
   `/content/drive/MyDrive/AirSense-R/model-checkpoints`.
4. Run the fourth cell once. It verifies and copies frozen development evidence
   from original result commit `b4fbfa73d55c83bc4de1a2f3c7db9eb16a306683`.
   The original result branch is read-only. Initial evidence publication can take
   several minutes before prediction progress appears.
5. The script reconstructs training-only preprocessing statistics and requires exact
   agreement with the saved state. Corrected restored features must equal those
   produced by the freshly fitted representation. All original native model hashes
   must match, and every model/seed must reproduce the saved validation predictions
   with `atol=1e-5`, `rtol=1e-6`. Those are numerical replay tolerances, not accuracy
   or model-selection thresholds. A mismatch stops the workflow before test access.
6. After all checks pass, corrected test prediction and uncertainty computation
   proceed automatically. Models are loaded, never fitted. The original selected
   family remains persistence. Run cell five, then save the executed notebook.

No `smoke/select/test` choice is needed in this notebook. The guarded recovery
workflow replaces those steps for this specific incident. New environment metadata
and original lineage are both retained; development replay provides the explicit
compatibility check rather than silently treating changed environments as identical.

Only one session may execute the correction. A runtime-local OS lock rejects
duplicate recovery scripts on the same machine; it cannot lock other Colab runtimes
through Google Drive. Interrupting the notebook cell terminates its child process.
If the session disconnects, inspect running processes before rerunning. Resume with
the same correction run ID, code SHA, environment and Drive directory. Validation
predictions are rechecked on an incomplete resume; completed test shards are reused.
An environment/provenance or model mismatch requires investigation, not an override.

Compact correction artifacts publish to `results/p5-clean-01-corrected-02`.
Native models stay in the original `p5-clean-01` Drive subdirectory. No corrected
model copies or new training runs are needed. Preserve both result branches and
all original executed notebooks. Corrected run `p5-clean-01-corrected-02` was
accepted on 2026-10-12; no further rerun is needed. See the
[completion report](../research/P5_COMPLETION_REPORT.md) and
[incident review](../research/P5_TEST_REVIEW.md).
