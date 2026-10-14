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
