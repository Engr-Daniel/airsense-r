# P5 final-test review and preprocessing correction

Final disposition (2026-10-12): corrected run `p5-clean-01-corrected-02` has
passed independent review and P5 is complete. See [P5_COMPLETION_REPORT.md](P5_COMPLETION_REPORT.md).
The incident history below records the original rejected outputs and subsequent
recovery steps; it does not revoke their invalidation.

Reviewed 2026-10-12. Run: `p5-clean-01`. Source:
`2201c0ff6d30cd40898cda1716b1b15b47e92bf8`. Reviewed result commit:
`b4fbfa73d55c83bc4de1a2f3c7db9eb16a306683` on `results/p5-clean-01`.

## Verdict

Execution completed, but scientific acceptance is **withheld**. The saved test
notebook shows return code zero and successful fifth-cell verification. All 1,217
registered remote artifacts passed byte-size and SHA-256 checks. All artifacts
present before test scoring at `ebfa23aa48dce3fa4f148f1d9c0131bd0ea70620`
remain unchanged, including the selection and frozen refit records. Test metrics
and the 2,000-replicate bootstrap were independently reproduced from predictions.
Nevertheless, a reproducible preprocessing defect invalidates the neural test
predictions and therefore the complete comparative test report.

## Defect and evidence

`json_bytes` sorts dictionary keys when saving preprocessing state. After loading,
the means and standard-deviation mappings are alphabetically ordered. Subtracting
a pandas Series constructed from those mappings reorders the numeric DataFrame
columns. Training and validation use the freshly fitted processor in its original
order; test scoring restores the saved processor and therefore supplies a different
numeric channel order to MLP and GRU. The recorded feature-name list stays unchanged,
which previously concealed the discrepancy.

Synthetic reproduction: after a real sorted-JSON round trip, scaled features differ
(maximum absolute difference 1.2176214 on the fixture), while unscaled features are
identical. This establishes a software defect independently of test accuracy.
The new regression test failed on the original implementation for scaled inputs.
The correction explicitly aligns both statistic Series to the numeric input columns.
No fitting statistics, target values, hyperparameters or selection rules change.

Local validation: all 10 pipeline tests pass, including scaled and unscaled
JSON-round-trip sequence/tabular comparisons. The expanded suite passed 60 tests
and exposed one unrelated reused notebook-fixture run-ID collision. After making
that fixture ID unique across pytest temporary roots, its notebook execution and
resume check passed separately (1 test). Source notebook fingerprints were
regenerated; the user's executed smoke/select/test copies remain untouched.

The original test MAEs were XGBoost 9.710861, persistence 10.279643,
GRU 36.194381 and MLP 39.010941. These numbers are recorded only as incident
evidence. Do not cite the neural scores, comparative rankings or selection-regret
interval as accepted scientific findings. Although the unscaled paths are
unaffected, the retrospective oracle and complete comparison must be recomputed.

## Preserved decisions and recovery requirements

The original 54 tuning fits and nine learned-model refits remain frozen. The
validation-based selection of persistence remains unchanged: XGBoost had validation
MAE 9.532510 and persistence 9.901272, within the frozen 1.0 near-tie threshold.
The defect is in restoring scaled inputs, not a reason to retrain or retune after
observing test outcomes.

Keep the original result branch, executed smoke/select/test notebooks and all
Google Drive native model snapshots. Do not overwrite the completed old test
artifacts or bypass their provenance guards. In particular, rerunning the old
`test` command will skip completed outputs; changing the source with the old run
ID will correctly fail provenance validation.

Corrected scoring requires a separately versioned evaluation with explicit lineage
to the original selection, preprocessing statistics and exact native model hashes.
Before any corrected test access, verify corrected restored inputs equal the
original fitted representation on development data and compare reloaded-model
validation predictions with the saved validation predictions. This also checks
the preserved models after the earlier overlapping-process incident. Recompute
all test predictions, aggregate metrics and uncertainty without fitting models.

The recovery workflow is now implemented in `p5_recovery.py`,
`scripts/recover_p5_test.py` and notebook `04b_p5_corrected_test.ipynb`.
It uses a separate correction provenance record and run branch, preserves the
parent selection and model hashes, and gates test access on full development replay
with numerical tolerances `atol=1e-5`, `rtol=1e-6`. The original environment is
retained in lineage and the new environment is recorded; compatibility is checked
by replay rather than assumed. No model fitting is permitted. See
[P5_RECOVERY.md](../docs/P5_RECOVERY.md).

Corrected live scoring remains pending. P5 is not closed and P6 must wait.
Final-test results have now been inspected; any
further methodological change must be recorded as post-results, not pre-results.

Recovery verification: 25 relevant tests passed across two targeted runs, including
real XGBoost/MLP/GRU save/load and synthetic correction replay, unchanged model
pointers, exclusion of old test artifacts, rejection of deliberately changed
validation predictions, test-access ordering, duplicate-writer locking, and source
notebook checks. Notebook 04b validates and its five code cells compile; its actual
Drive/GitHub execution is still a user-run acceptance step. Existing notebook
execution/resume checks also pass. No real corrected test results were generated
locally and no cloud-model access is claimed by these tests.

## Recovery CSV precision follow-up (2026-10-12)

The first live correction attempt stopped during persistence validation replay,
before neural replay or corrected test scoring. Two of 103,287 labels differed by
at most 1.42108547e-14. This was reproduced from original validation CSV shards:
the default pandas parser reads the serialized 74.3 and 81.8 values as
74.29999999999998 and 81.79999999999998. `float_precision="round_trip"` restores
the saved double values exactly. Recovery now explicitly opts into that reader;
ordinary metric/selection readers retain their original behavior. Exact target
comparison, model hashes, fitting settings and replay tolerances are unchanged.
Regression fixtures now include both affected noninteger labels, including the
real-model synthetic recovery test. The updated source needs a new correction ID
(`p5-clean-01-corrected-02`); preserve the first attempt as incident evidence.

Follow-up validation: 16 recovery/training/selection tests passed, including the
full synthetic correction with those decimal labels. The round-trip reader also
matched Python's correctly rounded float conversion for all 103,287 original
persistence validation labels. No corrected test performance was used to choose
this parser or change any tolerance.
