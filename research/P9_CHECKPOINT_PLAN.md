# P9 post-results methodological checkpoint

Declared 2026-10-29, after inspection of P5–P8 outcomes. This is a bounded
post-results extension, not part of the original confirmatory protocol.
Primary protocol, accepted predictions, models and acceptance receipts remain
immutable. No retraining, tuning, new model, city, horizon or adaptive policy.

## MC2: tolerance sensitivity using accepted evidence

Evaluate 0.5, 1.0, 1.5 and 2.0 micrograms/m³; 1.0 remains primary.
Keep two tables separate:

1. Interpretation: retain the original selected family and compare its accepted
   regret and existing pointwise interval with each tolerance. Report point
   membership and whether the interval is below, above or crosses the tolerance.
2. Counterfactual selection: use saved clean-validation family MAE only, with
   the original simplicity order, to choose at each tolerance. Report the chosen
   family's saved test MAE and regret for clean, auxiliary stress and LOSO.
   These are descriptive point estimates; existing intervals for another
   selection must never be relabelled as intervals for the counterfactual choice.

LOSO selection remains fold-specific. Aggregate LOSO regret is the mean of
station-specific regrets, not the difference from one globally best family.
No tolerance is selected on test performance. No new equivalence claim.

## MC1: target-history degradation

Use the accepted corrected P5 models and training-fitted preprocessing.
Retain the original validation-selected family, all four candidate families,
training seeds, five corruption seeds, target split and 24-hour history.
Only primary imputation is used in this extension: within-station causal
forward-fill up to six hours, then the original training median. Persistence
uses the resulting unscaled PM2.5 at forecast origin, exactly as implemented
by the existing pipeline; no bespoke fallback or clean-history bypass.

Exactly five conditions: PM2.5 Bernoulli dropout at 10%, 30%, 50%, and PM2.5
outages of 6 or 12 hours, one start per station per test calendar month.
The original deterministic station/seed scheduling algorithm and stress-history
boundary are reused. Auxiliary channels are unchanged. Noise, drift and combined
target-plus-auxiliary corruption are excluded from this checkpoint.

Create one corrupted chronological observation stream per condition/seed before
window construction; all candidates see that identical stream. Store original
labels separately. Never corrupt/impute evaluation labels or drop scored rows
because input PM2.5 becomes missing. Preserve missingness indicators.

Report full-period metrics and outage-affected-history metrics separately,
including MAE, RMSE, R², matched-clean RPD, ranks, selection regret and the
original 1.0 tolerance. Reuse the frozen paired 24-hour calendar bootstrap,
2,000 replicates, seed 424242 and 95% pointwise intervals, conditional on the
fitted models and corruption seeds. Disclose unavailable sparse-scope intervals.
Compare the production calculation with an independent frequency-weight
implementation before recording a condition as verified.

## Execution and evidence requirements

- Replay saved validation predictions with native models before test access,
  then reproduce accepted clean predictions at the original tolerances.
- Publish only to a separate checkpoint run/branch; persistent new prediction
  arrays live in a separate Drive directory with checksummed Git references.
- Save after every model/seed prediction and completed condition. Use one
  writer lock and the reconnectable notebook worker; never delete locks.
- Validate lineage, checksums and source/settings identity on resume.
- Test label/feature round trips, pairing, fallback, fresh-process execution,
  duplicate-writer refusal and interruption/resume before Colab handoff.
- Execution complete is not scientific acceptance. Review real completion
  evidence and recompute reported metrics/intervals before updating conclusions.

## Interpretation and stopping rule

Selection regret measures model-choice cost relative to the available
alternatives; it does not establish absolute forecasting adequacy. High regret
does not validate switching, retraining or a fallback policy. Keep adverse,
null and favorable outcomes alike. No changes to severities, models or tolerance
in response to extension outcomes. After the five conditions, MC2 and the
literature comparison, return to manuscript work; no automatic scope expansion.

Large native models remain in the user's original Google Drive. Local synthetic
tests cannot replace executing and reviewing the extension in that environment.
