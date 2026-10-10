# P5 clean benchmark workflow

P5 code implements the four frozen families, bounded training-only tuning, clean
validation selection, separate test scoring, prediction exports and model recovery.
Implementation and smoke checks are not a completed scientific benchmark.

## Environment and declared training plan

Use Python 3.11+ in a fresh environment:

```bash
python -m pip install -e . -r requirements-p5.txt
python -m pytest -q
```

Training uses deterministic CPU execution with two threads. GPU speedups are not
silently substituted. Exact installed versions, runtime class and full effective
settings are included in each run's provenance. A changed environment requires a
new run ID. The search is specified in `configs/p5_training.yaml`; its recorded
identity rejects silent edits. Decisions are documented in
`research/P5_IMPLEMENTATION_DECISIONS.md` before model scores.

Two configurations per learned family, three temporal folds and three seeds produce
54 tuning fits; nine full-training refits follow. Persistence is computed once.
Expect hours for the full CPU workflow, not the few minutes needed for a smoke run.
The XGBoost adapter builds its flattened matrix in a temporary memory-mapped file
and constructs a quantile matrix. Allow several GB of free RAM/disk; no raw data
are retained. Neural histories are materialized batch by batch.

## Colab procedure

Open notebook `04_p5_clean_benchmark_analysis.ipynb` from a pinned published commit,
and enter that same full SHA during bootstrap. Give the notebook access to the
`AIRSENSE_GITHUB_TOKEN` Colab Secret. Use a new ID for P5, not a retired P4 branch.

The notebook asks for a persistent model directory. For Google Drive, an example is
`/content/drive/MyDrive/AirSense-R/model-checkpoints`; mounting requests your normal
Colab/Google consent. Do not place model recovery files in ordinary `/content`.
The same model directory is used across smoke, selection and test stages.

1. Stage `smoke`, run ID such as `p5-smoke-01`: acquire the checksum-verified data
   temporarily, train all three learned adapters on an early training-only slice,
   intentionally interrupt at a saved boundary, resume, and compare predictions to
   uninterrupted fits and saved-model reloads. Metrics are not used to tune choices.
2. Stage `select`, a different ID such as `p5-clean-01`: perform tuning, full-training
   refits and clean validation selection. The script requires a matching successful
   smoke marker from this environment and model-storage destination.
3. Stage `test`, reuse `p5-clean-01`: verify the saved selection and its exact evidence
   before acquiring/exposing final-test rows. Load the frozen refit models; no model
   training or parameter selection occurs in this stage.

The current working notebook executes one chosen stage. A smoke stage does not
automatically launch the expensive benchmark. After changing code/environment,
repeat the small smoke check using a new ID; older results retain their identity.

## Script equivalents

Replace MODEL_DIRECTORY with your persistent destination:

```bash
python scripts/run_benchmark.py --stage smoke --run-id p5-smoke-01 --model-directory MODEL_DIRECTORY --sync-remote https://github.com/Engr-Daniel/airsense-r.git
python scripts/run_benchmark.py --stage select --run-id p5-clean-01 --model-directory MODEL_DIRECTORY --sync-remote https://github.com/Engr-Daniel/airsense-r.git
python scripts/run_benchmark.py --stage test --run-id p5-clean-01 --model-directory MODEL_DIRECTORY --sync-remote https://github.com/Engr-Daniel/airsense-r.git
```

For explicit local engineering checks, replace `--sync-remote URL` with
`--local-only`. This stores compact outputs in `results/p5/<run-id>` and does not
claim remote durability. No full-run command should silently fall back to local-only.

## Recovery and output contract

One writer per run. Models are saved to immutable native `.keras`/`.ubj` snapshots,
then an atomic progress pointer advances only after checksum verification. Neural
snapshots include optimizer state; epoch-specific shuffling is derived from seed
and epoch number. Tree training checkpoints every 25 rounds. Completed boundary
references publish to the Git result branch before training continues. A lost
in-flight epoch/chunk is recomputed. Failed Git pushes stop computation and retain
the model snapshot for retry. The smoke stage additionally retains its native model
states while publishing compact recovery reports after each family.

Cloud-mounted filesystem confirmation does not prove that Drive has flushed every
byte to its servers. Never disconnect immediately after a pending cloud upload.
Local integration tests establish serialization/recovery behavior; the user's real
Drive mount and GitHub credential path must pass the Colab smoke stage too.

Each run preserves config/environment provenance, fitted preprocessing, tuning
scores, training checkpoints and validation/test prediction shards. CSV shards
include station, original target timestamp/value, model family, seed and partition.
Scores average metrics over seeds within station, then stations equally.
`selection.json` locks the family and references its exact validation artifacts.

Compact figures and dashboard payloads are stored on the result branch. The script
also exports verified copies under `figures/p5-runs/<run-id>/` and
`docs/data/p5-runs/<run-id>/` in the working checkout. These derived working copies
are ignored by Git so they do not invalidate notebook bootstrap on resume; their
authoritative copies remain on the result branch. Curate publication exports later.
No automatic merge into main or deployment is performed.
Do not delete result branches or persistent model storage while P5-P8 need them.

## Interpretation

Headline uncertainty uses a shared hourly calendar with missing-target masks,
24-hour blocks, 2,000 replicates and the frozen seed. It averages seed errors before
time resampling and is conditional on this fitted seed set. Regret's retrospective
best model is recomputed in each replicate. Ranking changes within the 1.0 MAE
near-tie threshold are not automatically meaningful. Stable ranks with wide intervals
are not proof of equivalence. No P6 degradation or P7 station-holdout fitting is run
by the P5 command.
