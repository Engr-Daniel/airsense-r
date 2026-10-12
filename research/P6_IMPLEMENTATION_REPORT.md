# P6 implementation and handoff record

2026-10-12. **Implementation verified locally; real P6 experiments pending.**

Notebook 05 and `scripts/run_sensor_degradation.py` implement the frozen sensor
degradation matrix with separate `preflight` and `evaluate` stages. All 15
conditions and 63 realizations per imputation policy are included. No model is
retrained or reselected. The original P5 native models and accepted corrected
results remain the source of truth.

## Verification evidence

- The regression suite excluding the separately run P6 lifecycle test passed:
  **75 tests in 184 seconds**. Together with the lifecycle test, all 76 tests
  passed. Keras emitted dependency deprecation warnings; no tests failed.
- All six current source notebook templates passed format and source-fingerprint
  checks. Historical executed copies, frozen YAML and the protocol are unchanged;
  the complete staged patch passed `git diff --check`.
- The production accepted-parent loader opened the pinned corrected P5 commit
  `118ae94a23517319d1c31b1159f25a9b77f6b230`, verified its 160 artifact checksums
  and confirmed the persistence selection.
- Eight focused unit tests cover the frozen condition matrix, lossless prediction
  storage, corruption/provenance rejection, failed publication, outage boundaries,
  preserved training statistics, equal-station/seed aggregation and paired
  bootstrap calculations against an independent explicit resampling calculation.
- A fresh-process notebook/CLI integration test uses real native models for all
  four families, all three training seeds, noninteger targets (including 74.3 and
  81.8), missing values and categorical inputs on a small synthetic dataset.
  It exercises preflight, all four corruption types, both imputation policies,
  deliberate interruption, resume and a completed rerun with prediction forbidden.
  It confirms saved prediction bytes survive resume, parent artifacts and model
  pointers remain unchanged, and the local result branch matches a bare Git remote.
- The lifecycle test passed in 519 seconds. Its earlier attempt exceeded the
  fixture's 300-second subprocess allowance during evaluation. The allowance was
  increased to 600 seconds for Windows Git checkpoint operations; completed
  condition summaries now resume after verifying their backing artifacts.
  This does not change experiment settings or scientific tolerances.

## Limits and next gate

The integration fixture uses a reduced synthetic matrix and bootstrap count; it
does not establish runtime or scientific findings on the real dataset. The
full frozen matrix is separately checked by unit tests. Google Drive durability,
live Colab execution and access to the user's original models still need the
user-run preflight. No real sensor-degradation scores have been generated here.

Use the published revision of notebook 05 with run ID `p6-sensors-01`, stage
`preflight`, and the existing model-checkpoints directory. Save and review all
five executed cells before choosing `evaluate`. See `docs/P6_WORKFLOW.md`.

Completion requires every real condition and policy, verified lineage/checksums,
and independent recomputation of headline metrics and uncertainty. Keep the
Drive prediction arrays as well as the Git results: independent uncertainty
review needs the underlying predictions, not only summary intervals.
