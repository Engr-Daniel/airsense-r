# P5 implementation and validation report

Date: 2026-10-10. Source implementation: fe1d759eb0fbe5e7703617971ef48fbcbaea4ad8.

## Status

P5 implementation is present and locally tested. The full clean benchmark is
**not complete**: live Colab persistent-storage acceptance and the full select/test
runs remain pending. No final-test predictive performance has been inspected.

## Delivered

- A checksum-locked, predeclared two-configuration search for XGBoost, MLP and GRU,
  with all frozen seeds, training-only temporal folds and fixed training budgets.
- CPU model adapters with shared P4 inputs/targets, native model serialization,
  and recovery at completed epoch/boosting-chunk boundaries.
- Persistent model-directory identity, model checksums, atomic progress records,
  and compact Git references; model binaries never enter Git.
- Seed-metric then equal-station aggregation, validation-only family selection,
  the frozen practical near-tie rule, and a saved-selection final-test gate.
- Separate smoke/select/test script stages, aligned prediction shards, metric
  tables, figures and dashboard payloads.
- Timestamp-aware paired calendar-block uncertainty, preserving missing target
  positions and shared station time shocks, including multi-model regret intervals.
- P5 training-plan/environment provenance, deterministic CPU settings, pinned core
  training libraries, and a CI job that installs and tests training dependencies.
- Notebook 04 with explicit stage/partition declarations, the same verified source
  bootstrap, configurable persistent storage, and script-based execution.
- More specific checkout mismatch diagnostics to prevent confusing an old checkout
  with an import failure. A kernel restart alone does not clear an old filesystem.

## Local verification

The full P5 environment suite passed: **59 tests in 107.74 seconds**. Tests include
actual learned-model fitting and save/load; checkpoint interruption/recovery;
a synthetic full tuning-selection-test/export workflow; unequal-station selection
and practical ties; strict target/seed alignment; hourly resampling with missing
target positions checked against manual calendar sampling; and notebook 04 code
cell execution in fresh processes with an explicit offline acquisition fixture.

Keras emitted upstream NumPy copy-keyword deprecation warnings during serialization.
They did not cause test failures. These checks do not assert cross-hardware bitwise
identity or exercise the user's Google Drive credentials.

The P5 notebook fixture uses actual adapters and temporary bare Git remotes; it
substitutes only data acquisition/Colab runtime setup. Synthetic final-test labels
in integration tests are fixture labels, not the held-out UCI final-test year.

## Real-data training-only smoke

The authoritative UCI download timed out on the first attempt and succeeded on an
identical retry. Its SHA-256 and station inventory matched the frozen receipt.
Only Aotizhongxin rows through 2013-03-10 were exposed to smoke fitting/inspection.
Preprocessing and fits used data through 2013-03-08 23:00; 168 training targets and
48 subsequent training-period check targets were used.

XGBoost completed four rounds, and MLP/GRU each completed two epochs. Each adapter
was deliberately interrupted after an intermediate saved unit and resumed. Both
resumed-versus-uninterrupted and saved-versus-reloaded prediction differences were
**0.0** in this check. All three native snapshots were then verified and loaded in
another fresh Python process. Compact evidence is in
`results/p5/p5-local-smoke-20261010/`.

This run was explicitly local-only: no live Colab/Drive or GitHub credential claim
is made from it. Model binaries are in ignored local temporary storage. The
engineering reports contain recovery checks, not publishable accuracy estimates.
The manifest records the generating source commit and complete environment.

## Research and recovery boundaries

The original P3 families, date splits, seeds, target horizon, corruption settings,
and near-tie threshold are unchanged. Additional implementation choices were
recorded before real-data fitting in P5_IMPLEMENTATION_DECISIONS.md and the
deviation log. No ridge baseline or second dataset was silently added.

The completed snapshots support epoch/chunk-boundary recovery, not continuation
inside an unfinished batch. Actual persistent cloud writes depend on the storage
provider. The user must pass the small smoke stage in the real Colab/storage
environment before starting long fits.

Full benchmark metrics, predictive claims and a P5 completion report will be
produced only after select and test stages actually finish.
