# Post-results threshold sensitivity

Analysis date: 29 October 2026. Primary 1.0 µg/m³ rule unchanged.
Inputs are the exact accepted P5 and P8 manifests; generated tables and their
checksums are in [results/p9-threshold-sensitivity](../results/p9-threshold-sensitivity/).
The two tables contain 220 rows each: 55 evaluation scopes × four tolerances.

## Interpretation of the original selection

| Tolerance (µg/m³) | Clean point regret within tolerance | Auxiliary-stress full-period conditions within, per policy | LOSO station point regrets within |
|---|---|---|---|
| 0.5 | No | 8/15 under each policy | 5/12 |
| 1.0 — primary | Yes | 15/15 under each policy | 11/12 |
| 1.5 | Yes | 15/15 under each policy | 12/12 |
| 2.0 | Yes | 15/15 under each policy | 12/12 |

Clean regret is 0.5688 with pointwise 95% CI [0.3400, 0.7632]. At tolerance 0.5,
the point exceeds the tolerance but the interval crosses it. The original LOSO
mean regret is 0.5504 with CI [0.4004, 0.7388], also crossing 0.5.
Point near-tie counts are descriptive; they are not equivalence-test outcomes
or simultaneous-confidence statements. Full-period counts above exclude the
separately retained affected-window outage scopes in the CSV.

## Counterfactual validation selection

The clean P5 validation gap between persistence and XGBoost is approximately
0.3688. Persistence is therefore selected at all four tolerances; it remains
the hypothetical choice for P6 too, regardless of stressed-test rankings.

At tolerance 0.5, only the Nongzhanguan LOSO fold changes selection, from
persistence to XGBoost, using its saved validation scores alone. Mean
station-specific test regret becomes 0.4978 and six station point estimates
meet that tolerance. At 1.0, 1.5 and 2.0, all folds retain persistence, with
mean regret 0.5504. These alternative-policy values are descriptive: new
intervals were not computed, and original-policy intervals must not be reused
for the changed selection.

Thus selection is largely unchanged over this range, while the judgment of
practical adequacy is threshold-dependent. We do not select a preferred
tolerance from these test results. Low selection regret does not establish
adequate absolute accuracy or a validated deployment policy.

## Reproduction

Run `python scripts/run_threshold_sensitivity.py --p5-directory PATH_TO_ACCEPTED_P5
--p8-directory PATH_TO_ACCEPTED_P8` from the repository root (as one command).
The script checks pinned manifest hashes and all registered artifact bytes;
it never trains or writes to upstream snapshots. `summary.json` records input
commits, source/plan hashes, table checksums and descriptive-analysis status.
