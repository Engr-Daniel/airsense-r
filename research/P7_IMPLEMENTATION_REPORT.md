# P7 implementation and handoff review

Date: 2026-10-14. **Engineering implementation; real P7 results are pending.**

The frozen 12-station LOSO workflow is implemented in `src/airsense_r/p7.py`,
with reusable training/storage/statistics modules, a script entry point and
the four-cell `06_p7_site_shift_analysis.ipynb` Colab notebook. The notebook
embeds its matching source revision and fixed run settings. It automatically
performs smoke, development, replay and held-out test stages without prompting
for a SHA or stage.

Every held-out station is removed before tuning, preprocessing fitting and
validation selection. All fold selections are frozen before test access.
Native development replay precedes evaluation, including resumed evaluation;
test rows never trigger fitting or selection. The complete frozen search entails
756 learned-model fits, plus a bounded engineering smoke check.

One result branch holds all compact outputs. Immutable prediction CSVs and
native model checkpoints reside in the existing Drive storage under a new P7
directory. Hash references are pushed incrementally. A reconnectable worker
owns execution and exposes progress, failure and completion. Separate runtimes
are not coordinated by its local OS lock; use only one runtime at a time.

The statistical report distinguishes mean station-specific selection regret
from policy-minus-fixed-family differences. It retains station/seed metrics,
validation/test ranks, descriptive Kendall tau-b, practical near-ties and
paired calendar-block intervals using frozen settings. An independent explicit
row-index bootstrap fixture checks the prefix-sum implementation, including
missing target hours and differing fold selections.

## Verification scope

Local fixtures cover all 12 station exclusions, all four candidate families,
native serialization, categorical/missing inputs, and exact 74.3/81.8 labels.
The process lifecycle fixture uses two synthetic stations and reduced training
budgets solely for engineering checks. It interrupts after a native checkpoint
is pushed, discards the disposable checkout, restores from a bare Git remote,
and resumes with retained persistent storage. It also interrupts evaluation,
forbids fitting on recovery, checks unchanged refit pointers, and reuses a
completed run without acquiring data. All four actual P7 notebook cells run
in fresh processes with installation/authentication substituted by fixture setup.

Shared regression checks cover failed pushes, unrelated staged files, large
artifact inventories, duplicate job launch, and the P5/P6 workflows. Testing
caught and corrected byte-changing Git checkout conversion, recovery after
staging but before committing, and compatibility with P6's read-only evidence
wrapper. Historical executed notebooks and the pinned P6 verifier are preserved.

All **94 collected tests** are covered by passing local runs: the 91-test main
regression run, two subsequently added regression cases, and the separate P6
native-model/interruption/Git lifecycle test (757.30 seconds). Six focused P7
checks passed, followed by ten notebook/bootstrap/worker checks after the final
results-cell provenance guard. Those focused sets overlap the 94-test total.
Only existing Keras deprecation warnings remain. The final results cell checks
source revision, frozen protocol/configuration, dataset identity, run identity
and persistent-storage identity before displaying results; its fixture also
proves that mismatched provenance is rejected.

Live Colab installation, authorization, Drive durability and the full 12-station
computation remain to be demonstrated. The notebook embeds the reviewed full
source commit; use the published pinned notebook for the live run.

Published notebook source revision:
`7278ba95c88ea28e8861f59d0a6f8e097087c9d7`. The notebook fingerprint was
checked against an archive of that exact commit, and the final pinned notebook
passed its fresh-process run/resume/provenance-rejection test.

## Acceptance still required

A successful run writes `execution_complete: true` and
`scientifically_accepted: false`. Review the executed notebook and independently
verify prediction/model hashes, selection lineage, per-station metrics, aggregate
regret and bootstrap intervals before closing P7 or interpreting findings.
No P5/P6 experiment rerun is required for this implementation.
# Colab environment recovery verification — 2026-10-20

The original run stopped before further fitting because Colab's full package
inventory changed. Recovery is an external adapter in `scripts/recovery/`,
separately pinned and SHA-256-verified by notebook 06b. It is intentionally
outside the original scientific fingerprint: that fingerprint remains
`9c1237fbbad6e1ca6abe065bbbc9c7f91baf8e2381ed6c86ae50a8df7f6519d3`,
and the original source commit remains
`7278ba95c88ea28e8861f59d0a6f8e097087c9d7`.

The adapter verifies the original Python/source/configuration/storage identity,
restores exact recorded versions of required scientific dependencies and their
active transitive dependencies, and retains the original native model identity.
Actual runtime provenance and the adapter digest are saved as separate immutable
records. Completed station selections undergo development replay before any
remaining training. The final test gate and numerical tolerances are unchanged.

Local validation: **24 targeted tests passed in 233.96 seconds** across
`test_p7_colab_recovery`, `test_p7_workflow`, `test_notebook_job`, `test_p7`,
`test_model_storage`, and `test_p5_recovery`. These cover transitive/extra
dependency resolution, rejection of scientific provenance changes, normalized
date serialization, replay failure blocking, notebook fresh-process execution,
all-family native model and CSV round trips, interruption/restoration through
a bare Git remote, immutable refit checkpoints, and duplicate-writer behavior.
An evolving replay-scope record and Windows path length issue were found and
corrected during verification. Synthetic fixtures use reduced budgets and are
not research results. Package restoration in live Colab and the full-data
recovery replay still require the user's execution; P7 is not yet accepted.
