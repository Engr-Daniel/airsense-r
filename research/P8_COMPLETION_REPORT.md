# P7 verification and P8 completion review — 22 October 2026

**P7 and P8 accepted within the frozen study scope. No experiment rerun required.**

Run `p8-analysis-01` completed at result commit
`296999a0df73363f2922a34fd15cf520f1d75e2d`, using reviewed source
`af76b79578036cfeb8fb614db086975bc88173b8`. The executed notebook has four
completed code cells, no saved error outputs, and code identical to the published
template. Its original bytes are preserved under `notebooks/executed/`.
The machine-readable review receipt is [final_acceptance.json](../results/p8/final_acceptance.json).

## Verification and its limits

- All 226 published P8 artifact checksums and pinned P6/P7 input lineage match.
- The Colab verifier checked 720 P7 prediction CSVs and 108 final native model
  files, reproduced validation choices and test metrics, and independently
  recomputed paired calendar-block uncertainty. The published independent report
  agrees with the original P7 report at the declared numerical tolerances.
- All 1,281 P6 prediction/target bundles were rechecked in Colab. Its 30 accepted
  condition/policy reports retain their original independent-verification lineage;
  P8 does not claim a second P6 bootstrap computation.
- Local review independently reaggregated 66 concentration/season tables across
  33 diagnostic units. Both subgroup partitions reconstruct the same per-station
  total error. P7 reconstructed errors match the original station/seed metrics;
  P6 stress aggregates match the accepted full-period summaries. All 42 sensor
  condition/policy/scope ranking summaries agree with their upstream records.
- All 7,920 exported worst-case rows passed finite-value, unique-target, time-window,
  season, group-size and error-consistency checks. These rows were not independently
  reselected locally from all Drive predictions. Representative figures were
  visually inspected. Final manuscript captions/layout remain part of P9.

Drive prediction and native model bytes were verified by the reviewed Colab
code; they were not downloaded locally. Local review verifies the immutable
published verification evidence and its lineage. The original execution records
still say `scientifically_accepted: false` because acceptance occurred afterward;
the separate review receipt records that decision without rewriting originals.

## Main findings to carry into the manuscript

P7's fold-specific selection rule chose persistence at every station. Mean
station-specific selection regret is **0.5504 µg/m³**, with paired 95% bootstrap
CI **[0.4004, 0.7388]**. Eleven of twelve station point estimates fall within the
predefined 1 µg/m³ practical threshold. Shunyi's point regret is 1.0504, with CI
[0.7417, 1.3109]; this interval crosses the threshold, so the point classification
is not proof of a practically important difference. Near-tie classifications
are not formal equivalence tests.

Under P6, persistence remains within the practical threshold in all 15 full-period
stress conditions under each preprocessing policy. Largest full-period regret is
0.5686 µg/m³ for primary preprocessing and 0.5520 for the no-forward-fill
sensitivity. This is evidence about the predefined non-target sensor interventions;
it does not establish robustness to failure of the PM2.5 target-history channel.

Exploratory P7 concentration diagnostics show XGBoost has lower MAE in the three
bands below 200 µg/m³, while persistence has lower MAE in the ≥200 band
(22.59 versus XGBoost's 25.42 µg/m³). These post-results subgroup summaries do
not carry subgroup confidence intervals or support confirmatory superiority claims.

The largest exported P7 error occurs at Wanshouxigong on 2017-01-04 13:00:
observed target 3 µg/m³ and persistence forecast 621 µg/m³. This is a case for
contextual examination in the paper, not evidence by itself of a sensor fault.
Do not remove the observation, change the evaluation, or assign a physical cause
without supporting evidence. The data and predictions remain unchanged.

The next phase is P9: develop the manuscript around model-selection reliability,
practical regret and bounded generalization, including stable-selection results
and these limitations. P10's public explorer remains separate unfinished work.
