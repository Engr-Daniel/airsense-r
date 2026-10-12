# P6 sensor degradation workflow

Use notebook `05_p6_sensor_degradation_analysis.ipynb` in a fresh **CPU** Colab
runtime, opened from its published full commit SHA. Enter that same SHA during
bootstrap. Give the notebook access to `AIRSENSE_GITHUB_TOKEN`.

## First run: preflight

- New run ID: `p6-sensors-01`.
- Stage: `preflight`.
- Original model directory: `/content/drive/MyDrive/AirSense-R/model-checkpoints`.
- Run the five cells in order, once. Do not start a second session/copy.

Preflight verifies the pinned accepted P5 artifacts and selection, checks every
original native model hash, reproduces all development predictions and then matches
the accepted clean-test predictions. It also validates exact target and persistent
array round trips. It evaluates no new sensor stresses and fits no models.
Save the executed preflight notebook and have its evidence reviewed before proceeding.

## Full evaluation

After preflight acceptance, rerun setup with the **same** run ID, source SHA,
environment and Drive directory, choosing stage `evaluate`.

This executes 15 stress settings: random dropout 10/30/50%, whole-channel loss of
NO2/CO/TEMP, Gaussian noise at 5/10/20% of frozen training scales, and 6/12-hour
monthly outages for NO2/CO/TEMP. Randomized conditions use all five frozen seeds;
whole-channel loss is deterministic. Both primary imputation and the frozen
no-forward-fill inference sensitivity are included. This is 63 realizations per
policy, plus each policy's clean comparator. Nine trained models and persistence
are evaluated. Allow hours on CPU and several GB of free Drive/runtime storage.

The no-forward-fill arm uses the same trained models and training-derived numeric
statistics. Its clean comparator also uses no forward fill. It does not represent
a separately trained/tuned alternative pipeline. Full-period results are primary;
outage-affected windows are additional matched sensitivity reports.

## Checkpoints and resume

Original P5 models stay read-only in their `p5-clean-01` subdirectory. P6 creates
`p6-artifacts/<run-id>` under the model-directory root, containing lossless compressed
target/key and prediction arrays. Git stores checksummed references plus compact
seed/station metrics, corruption events/hashes, summaries, plots and dashboard data
on `results/<run-id>`. Preserve both storage locations; a Git reference alone cannot
restore a deleted Drive prediction file. Raw data remain temporary and immutable.

Each model/seed prediction unit is saved and remotely referenced before the next
unit. Failed Git publication stops execution. A runtime interruption may repeat
the in-flight prediction unit. Resume at the same identity; confirmed arrays are
loaded only after checksum validation. Missing/corrupt arrays or changed native
models fail clearly rather than silently mixing results.

The script has a runtime-local writer lock; it cannot lock another Colab runtime
through Google Drive. Run only one session. On a browser disconnect, check running
processes before starting another copy. A notebook interrupt terminates its child
script; saved artifacts remain. An environment/provenance mismatch requires review,
not overriding validation. Drive mount acknowledgement does not prove immediate
server-side flush of every file.

Completed outputs include metrics per station/training seed/corruption seed, clean
and stress ranks, winner retention, RPD, practical near-ties, selection regret,
paired 95% intervals and descriptive Kendall tau-b. Matched station-level changes
use a shared 24-hour calendar bootstrap. A sparse affected-window sensitivity may
report unavailable intervals if resampling produces an empty station/realization;
full-period headline intervals are required. No independent-row substitution is allowed.

The fifth notebook cell verifies and displays the saved outputs. Save its executed
copy separately. Do not declare P6 scientifically complete until every setting and
policy is finished and the artifacts and headline computations have been reviewed.
See `research/P6_IMPLEMENTATION_DECISIONS.md` for predeclared details and limitations.

## Script equivalent

```bash
python scripts/run_sensor_degradation.py --stage preflight --run-id p6-sensors-01 --model-directory MODEL_DIRECTORY --sync-remote https://github.com/Engr-Daniel/airsense-r.git
python scripts/run_sensor_degradation.py --stage evaluate --run-id p6-sensors-01 --model-directory MODEL_DIRECTORY --sync-remote https://github.com/Engr-Daniel/airsense-r.git
```

Stage choice is explicit. Preflight never starts the expensive stress matrix
automatically. Environment dependencies are the pinned P5 inference environment;
P6 adds no training library or new model family.
