# P7 execution decisions

Declared 2026-10-14, after P5/P6 results and before any P7 results. These
operational details implement frozen protocol section 12; they do not revise
the candidate families, search spaces, seeds, time boundaries or near-tie rule.

All 12 verified stations are held out in alphabetical order. Each fold repeats
the complete P5 training plan on the other 11 stations: 54 internal tuning fits
and nine learned-model refits, or 756 fits overall. Persistence has no fit.
No all-station P5 model or selected hyperparameters are reused. This can take
many Colab sessions; no duration guarantee or reduced scientific budget applies.

All 12 clean-validation selections must be saved before final-test scoring.
Each resumed evaluation process replays saved development predictions using
the exact native models and serialized preprocessing before exposing test rows.
Replay preserves exact keys/labels and uses the established prediction tolerances
`atol=1e-5`, `rtol=1e-6`. It does not refit models or redo model selection.
Held-out development rows are excluded before calling the shared tuning code.
Only held-out final-test targets are scored; earlier local observations provide
causal input history. The primary six-hour carry-forward policy is used here;
the predefined no-forward-fill observation sensitivity was evaluated in P6.

The selected family may differ across LOSO folds. Report each station's
validation ranks, test ranks, descriptive Kendall tau-b (undefined for an
all-tied ranking), numerical winner retention, practical near-ties,
and selection regret. The primary aggregate regret is the equal-station mean
of **station-specific selected-minus-station-specific oracle MAE**. This is
nonnegative and differs from subtracting the best fixed-family aggregate MAE
from the fold-specific selection policy. Also report the policy's paired MAE
difference against each fixed family. Do not call the latter regret.

For uncertainty, sample the frozen 24-hour moving blocks 2,000 times with seed
424242. Use the same calendar samples for all stations/models; preserve missing
target hours. Average errors across training seeds within each station, then
weight stations equally. Recompute each station's oracle within each replicate
before averaging regret. Intervals are conditional on fitted seeds and these
12 stations, not evidence of transfer to another city. Rank comparisons are
descriptive; uncertainty and the frozen 1.0 microgram/m3 threshold govern claims.

Use one result branch (`results/p7-sites-01`) for all folds. Native model state
and losslessly serialized prediction CSVs live under the existing persistent
Drive root in a new P7 directory; compact outputs and SHA-256 references are
pushed at completed units. Never overwrite earlier P5/P6 artifacts. The notebook
embeds its matching source revision and run settings. A file-log worker allows
reattachment after browser disconnect; a replacement runtime restores published
checkpoints. Drive authorization is still required by Colab. Use one runtime
at a time; a local OS lock does not coordinate separate Colab machines.

Completed execution is not scientific acceptance. Independently verify all
prediction/model references, lineage, metrics and uncertainty after the live
run. Preserve the executed notebook separately. No P7 result is claimed here.
