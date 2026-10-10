# P5 implementation decisions

Declared 2026-10-10 before fitting models or inspecting tuning scores. The P3
protocol and four candidate families remain unchanged. `configs/p5_training.yaml`
records the bounded search; its identity is locked in `configs/p5_identity.json`.

- Two listed configurations per learned family; three expanding folds and all
  three training seeds. Mean seed metric within station, equal station mean within
  fold, then equal fold mean chooses the configuration. Exact score ties follow
  listed order. Refit that configuration under all seeds on full training data.
- Neural targets remain in original units, numeric inputs use P4 standardization.
  MLP flattens histories and concatenates target calendar features. GRU consumes
  histories and concatenates calendar features at its dense output head. ReLU
  hidden dense layers, linear scalar outputs, Adam, MSE loss; no dropout/batchnorm,
  target transformation, or prediction clipping. Fixed 20 epochs; no early stopping
  or outer-validation training-duration selection. Limited search is a limitation,
  not a claim of globally optimal tuning.
- XGBoost uses CPU histogram trees, squared-error objective, full row/column
  sampling, lambda 1, alpha 0 and min_child_weight 1. All seeds are recorded, even
  though full sampling can yield identical predictions. No artificial persistence
  seed replication. Hyperparameters and checkpoints use native UBJSON serialization.
- CPU with two threads is the initial reproducible target for local/Colab runs;
  do not silently switch backend/device. Neural epoch order is generated from
  seed plus epoch so an epoch-boundary restart preserves the schedule. Keras saves
  optimizer state. Save once per epoch and every 25 tree rounds; interrupted units
  are recomputed from the previous confirmed checkpoint, not resumed mid-batch.
- Model files live in a user-configured persistent directory (Drive in Colab).
  A checksum-verified checkpoint pointer is written after the immutable model
  snapshot; only then is its compact reference pushed to Git. Mounted-filesystem
  write/read confirmation is not a guarantee of the provider's server-side flush.
  One writer per run; completed snapshots are not overwritten. Model identity
  includes settings, preprocessing, data keys/labels/features and run provenance.
- Persist one selection record containing all four validation scores and the P3
  1.0 MAE simplicity tiebreak before opening final-test rows. Test evaluation is a
  separate explicit command; it never tunes, refits or chooses the deployed family.
  Metrics average seeds within station then stations equally, not seed predictions.
- Save original targets and station/timestamp/model/seed/partition in prediction
  shards. Test uncertainty samples the common hourly calendar in 24-hour moving
  blocks, using the same sampled hours for all stations and candidates. Missing
  targets keep their calendar positions and masks; station metrics use sampled
  observed targets. Seeds are averaged before time resampling; intervals describe
  temporal variability conditional on the fitted seed set, not all training risk.
  The retrospective minimum is recomputed per replicate for selection regret.
- Smoke data are restricted to one station in March 2013 and two epochs/four
  rounds, under a separate run identity. Smoke metrics are engineering evidence,
  never benchmark results, model selection evidence, or a reason to tune settings.
- P5 full runs require a successful smoke marker with matching source/environment
  and checkpoint storage identity. Live Colab/Drive confirmation remains necessary
  before long user runs; local checks do not pretend to exercise Colab credentials.

API references checked: [Keras whole-model serialization](https://keras.io/api/models/model_saving_apis/model_saving_and_loading/)
and [XGBoost 3.0 API](https://xgboost.readthedocs.io/en/release_3.0.0/python/python_api.html).
