# P11 release verification

Verification performed 2026-11-02; final audit review 2026-11-03. Technical verification is complete; this is not a
declaration that `v1.0.0` has been published or that the manuscript is submission-ready.

## Fresh-environment core rerun

Created a new Python 3.11.17 virtual environment and installed the core package
from `pyproject.toml`. Ran `python scripts/verify_core_rerun.py` against a fresh
UCI download whose checksum and inventory match the frozen acquisition receipt.
The script refits preprocessing on training data only and rebuilds persistence
predictions, comparing them with the accepted corrected P5 Git artifacts.

- 420,768 station-hours loaded; 102,753 scored targets.
- Target keys, observed values and persistence predictions match exactly.
- Persistence MAE: 10.27964339759353, identical to the acceptance receipt.
- Preprocessing structure, medians, categories and feature order match exactly.
- Standard-deviation reductions differ by at most 2.195379881861135e-12 relative.
  The verifier's predeclared moment-only tolerance is 1e-10; this was not adjusted
  after observing the rerun. Means match exactly. All differences are disclosed.

The verifier rejects unexpected state fields, nonfinite moments, duplicate target
keys and nonfinite predictions. See [the machine-readable receipt](../results/p11/core_rerun.json),
including the verifier/config/source fingerprints and accepted artifact hashes.
Its source commit identifies the base checkout; the recorded source fingerprint
also covers the then-uncommitted release script and metadata edits.

This is a core-pipeline and deterministic-baseline reproduction, **not** a repeat
of every learned-model training, sensor experiment, LOSO fold or bootstrap.
Accepted P5–P9 evidence remains unchanged. No protocol or evaluation tolerance was
modified. Historical notebook revisions and their provenance remain pinned.

## Other checks

- Fresh-environment explorer export recomputes clean MAE from 60 accepted
  prediction files and exports 30 sensor reports, seven target-history scopes,
  and 12 station summaries. Outputs are directed to temporary storage.
- All three diagnostic vector figures match the recorded PDF hashes; their
  acceptance-receipt hashes also match.
- Main paper and supplement compile locally to eight pages and one page.
  Author blocks visually reviewed: Daniel Oyewale, Ormedian Research Group,
  oyewaledanieloyewola@gmail.com. Existing nonfatal font/spacing warnings remain;
  no unresolved references or overfull boxes.
- Full regression suite: **143 passed**, no failures or skips, in 1,789.86 seconds.
  The 247 warnings are Keras/NumPy `__array__` copy-keyword deprecations.
  See [verification summary](../results/p11/verification.json).
- All 11 archived notebook hashes match; all 12 active notebook title updates
  preserve executable cells and valid notebook structure.
- Fresh-environment explorer JSON and prediction-window JSON are byte-identical
  to the published data. Installed core dependencies pass consistency checks;
  exact installed versions are in [environment.json](../results/p11/environment.json).
- Full structural audit completed; reviewed 2026-11-03. Its parsed JSON matches
  the frozen audit exactly: 420,768 rows, 12 stations, valid inventory and all
  historical-window/missingness results unchanged. The original audit was not
  overwritten; verification hashes are recorded in the summary.

- Canonical title confirmed and aligned across active documents and notebook title
  pages: **AirSense-R: Evaluating PM2.5 Forecaster Selection Under Sensor Degradation and Unseen-Station Shift**. Historical executed notebooks remain unchanged.

## Remaining release and submission decisions

- Review author contributions and remaining declarations; finish journal-specific
  formatting and citation/novelty checks.
- Document public archival access for the large prediction/native-model files;
  a checksum reference alone is not public artifact availability.
- Review verification results, set final package/citation version and release date,
  and create the versioned release only after the release gates are satisfied.

The confirmed publication name is Daniel Oyewale. The existing citation release
date and package version describe the previous software state; they are not a
claim that this verification work has already been released as `v1.0.0`.
