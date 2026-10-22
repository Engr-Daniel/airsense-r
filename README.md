# AirSense-R: Do Air-Quality Forecasters Keep Their Rank Under Sensor Degradation and Site Shift?

AirSense-R is a research-grade machine-learning study of **model-selection reliability under deployment stress**. Rather than asking only which model is most accurate on clean historical data, the project tests whether that clean-data winner remains the preferred model when the same frozen candidates face sensor dropout, complete channel loss, controlled measurement noise, or monitoring-site shift. The initial task is short-horizon PM2.5 forecasting using the UCI Beijing Multi-Site Air Quality dataset.

## Research question

> Does the model selected as best under clean one-hour-ahead PM2.5 forecasting remain the best choice under sensor degradation and monitoring-site shift?

## Initial scope

- Target: PM2.5 one-hour-ahead forecasting
- Lookback: 24 hours (default; frozen in protocol before final experiments)
- Data: UCI Beijing Multi-Site Air Quality dataset
- Baselines/models: persistence, tree-based ML, MLP, compact GRU
- Reliability tests: random dropout, whole-variable dropout, contiguous outages, measurement noise, repeated unseen-site evaluation
- Metrics: MAE, RMSE, R², Relative Performance Degradation (RPD), clean-to-stress rank changes/winner retention, mandatory paired temporal-block bootstrap confidence intervals for headline comparisons
- Interface: static GitHub Pages reliability explorer using precomputed results

## Scientific workflow

The project follows a pre-specified workflow. Before final model evaluation, freeze the research questions, hypotheses, split logic, model families, corruption levels, metrics, and random seeds in `research/PROTOCOL.md`.

| Phase | Work | Status |
|---|---|---|
| P0–P1.5 | Setup, literature review, methodology hardening | Complete |
| P2 | Dataset acquisition and structural audit | Complete |
| P3 | Freeze research protocol | Complete |
| P4 | Causal pipeline, Colab notebooks, checkpoint recovery | Complete |
| P5 | Clean forecasting benchmark | Complete after corrected evaluation; see [report](research/P5_COMPLETION_REPORT.md) |
| P6 | Sensor degradation | Complete; predictions, metrics and uncertainty independently verified; see [report](research/P6_COMPLETION_REPORT.md) |
| P7 | Leave-one-station-out evaluation | Execution complete; local evidence review passed. Independent prediction/uncertainty verification pending; see [review](research/P7_EXECUTION_REVIEW.md) |
| P8 | Statistical and failure analysis | Implemented; live verification/analysis pending; [workflow](docs/P8_WORKFLOW.md) |
| P9 | Manuscript | Planned |
| P10 | Reliability explorer | Planned |
| P11 | Reproducibility release | Planned |

## Temporal splits and unseen sites

Partitions use the forecast **target timestamp**:

- Training: 2013-03-02 00:00 through 2015-02-28 23:00.
- Validation: 2015-03-01 00:00 through 2016-02-29 23:00.
- Final test: 2016-03-01 00:00 through 2017-02-28 23:00.

Each target uses the preceding 24 hours. Hyperparameter tuning uses expanding
windows within training only. Preprocessing is fitted only on the permitted
training period. In each of 12 site-holdout runs, the held-out station is excluded
from fitting, tuning, preprocessing fitting, and model selection. Other stations'
future data are not used for training. Recent observations from the held-out
station are allowed as causal inference inputs.

All candidates use the frozen common missing-input policy: causal forward fill
capped at six hours, then training-only fallback, with missingness indicators.
See [the protocol](research/PROTOCOL.md) for sensitivity and statistical rules.

## Limits of the study

The 12 stations are all in Beijing. This tests within-city unseen-station
generalization, not transfer to another city, climate, or instrument type.
Synthetic degradation of regulatory monitoring data is not evidence of real
device failure or embedded deployment. P5/P6 findings have passed independent
review; P7 execution is complete but prediction-level acceptance is still pending.
P8 subgroup diagnostics are explicitly post-results descriptive analyses.

## Repository map

| Location | Contents |
|---|---|
| `src/airsense_r/` | Reusable scientific implementation |
| `scripts/`, `notebooks/` | Execution entry points and Colab workflows |
| `notebooks/executed/` | Preserved execution evidence and checksum index |
| `configs/`, `research/` | Frozen settings, methodology and phase reports |
| `audit/`, `results/`, `figures/` | Dataset receipts, reviewed results and figures |
| `docs/`, `paper/` | Workflow guides, explorer and manuscript |
| `tests/` | Scientific and recovery regression checks |

`AGENTS.md`, `MEMORY.md` and `TASK.md` remain at the root for contributor and
IDE discovery. Large models and prediction arrays remain in persistent Drive
storage, with checksum references in result branches.


## Quick start

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
python scripts/download_data.py   # verify/hash remote UCI archive; retain no raw data
python scripts/run_data_audit.py  # full structural audit via temporary storage
```

The raw dataset is remote-only by default: acquisition uses temporary storage and retains only compact audit evidence. Do not run final experiments until `research/PROTOCOL.md` is frozen.

## GitHub Pages

The static dashboard lives in `docs/`. Configure GitHub Pages to deploy from the `main` branch `/docs` folder. The dashboard initially displays placeholder content and will later load exported JSON/CSV artifacts from `docs/data/`.

## Research integrity

- Do not tune on the final test set.
- Do not redefine hypotheses after viewing final results.
- Distinguish clean IID performance from robustness/generalization performance and report selection regret when the validation-selected model is no longer test-optimal.
- Treat Edge-ML as future work unless actual embedded deployment is completed.
- Record deviations from the frozen protocol in `research/PROTOCOL_DEVIATIONS.md`.

## Current next step

Run **[notebook 07](notebooks/07_p8_statistical_failure_analysis.ipynb)** in Colab
using the original Drive account and existing GitHub secret. Choose a CPU runtime
and Run all; no SHA or stage entry is needed. It verifies P7's saved predictions
and uncertainty before producing P6/P7 failure-analysis tables and figures.
It does not retrain models. See [P8 instructions](docs/P8_WORKFLOW.md).

Dependency versions are defined once in `pyproject.toml`. `requirements.txt`
installs the full research environment; `pip install -e ".[notebooks]"` installs
the smaller analysis environment. Historical pinned notebooks keep their original
environments. Executed notebooks are preserved in [notebooks/executed](notebooks/executed/)
with a checksum index; they are evidence, not runnable templates.

## Earlier completed workflow

P0–P3 are complete and the protocol is frozen. P4's causal data pipeline, provenance checks, incremental Git checkpoints, resume support, and first three Colab notebooks are implemented and locally verified. Authoritative UCI coverage checkpoints are saved under `results/p4/p4-final/`. User-run Colab execution and fresh-runtime checkpoint recovery have been reviewed successfully. See [the P4 workflow](docs/P4_WORKFLOW.md) and [completion report](research/P4_COMPLETION_REPORT.md). P5 model adapters, training-only tuning, validation selection, persistent model checkpoints and notebook 04 are implemented. The corrected clean benchmark is complete, with frozen-model validation replay and independently reproduced test metrics/uncertainty. See [P5 completion and correction disclosures](research/P5_COMPLETION_REPORT.md). See [the P5 workflow](docs/P5_WORKFLOW.md).

Completed P4 Colab outputs are preserved in
[the checkpoint archive](results/p4/colab-archive/README.md). Their temporary
result branches were consolidated after checksum verification.

The canonical study title is recorded in `CITATION.cff`. See the [pre-results research rationale](research/RESEARCH_RATIONALE.md) for evidence of the problem, limits of novelty, and criteria for a useful study.
