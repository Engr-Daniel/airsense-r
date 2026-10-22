# P7 execution review — 22 October 2026

**Execution complete; scientific acceptance pending.**

The final result snapshot is `73c32f0b2cd7fcf447f9483413561b7104536e7f`.
The user's `notebooks/executed/06b_p7_colab_recovery_runcomplete.ipynb` is preserved
byte-for-byte. All four code cells match the published recovery template and
have executed without saved error outputs. The worker exited successfully,
and the final cell verified and displayed the completion record and report.

## Local evidence checked

- All 13,850 registered Git artifact SHA-256 checksums match exact repository
  bytes. The Windows archive command must use `git -c core.autocrlf=false archive`;
  a default local export converted line endings. This was an export issue, not
  corruption of the saved Git blobs. No result artifact was modified.
- All 756 fits and 120 held-out model/seed evaluations have completion records.
- All 12 selection records match the frozen selection ledger. Each serialized
  preprocessor excludes its held-out station; each fold has a passed development
  replay record and a test-completion record.
- The completion record's report checksum matches the saved report.
- Equal-station aggregate MAE, RMSE and R² were independently recalculated from
  the saved station/model/seed metric table. The point selection-regret estimate
  also agrees with recalculation from that table. These checks do **not** replace
  recalculation from predictions.
- The original scientific source and separately recorded recovery environment
  remain available. Original results and notebook templates were preserved.

The machine-readable receipt is [execution_review.json](../results/p7/execution_review.json).

## Required before acceptance

The 720 registered Drive prediction CSV references cover validation and test
predictions. Their actual file bytes have not been independently read in this
local review. A read-only verification run against mounted Drive must:

1. Verify prediction byte counts/checksums and final native model lineage.
2. Check station/time partitions, aligned labels, families and training seeds.
3. Recompute validation selection and final metrics directly from saved rows.
4. Independently recompute the frozen 2,000-replicate paired calendar-block
   uncertainty, station-specific selection regret, and policy comparisons.

This requires no model fitting or new predictions. It must retain original
artifacts and publish its own verification evidence. P8 and the agreed repository
cleanup follow acceptance, not merely successful notebook execution.
