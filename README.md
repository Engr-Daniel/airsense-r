# AirSense-R

**Model-Selection Reliability for Air-Quality Forecasting Under Deployment Stress**

AirSense-R is a research-grade machine-learning study of **model-selection reliability under deployment stress**. Rather than asking only which model is most accurate on clean historical data, the project tests whether that clean-data winner remains the preferred model when the same frozen candidates face sensor dropout, complete channel loss, controlled measurement noise, or monitoring-site shift. The initial task is short-horizon PM2.5 forecasting using the UCI Beijing Multi-Site Air Quality dataset.

## Research question

> Does the model selected as best under clean one-hour-ahead PM2.5 forecasting remain the best choice under sensor degradation and monitoring-site shift?

## Initial scope

- Target: PM2.5 one-hour-ahead forecasting
- Lookback: 24 hours (default; frozen in protocol before final experiments)
- Data: UCI Beijing Multi-Site Air Quality dataset
- Baselines/models: persistence, tree-based ML, MLP, compact GRU
- Reliability tests: random dropout, whole-variable dropout, contiguous outages, measurement noise, repeated unseen-site evaluation
- Metrics: MAE, RMSE, R², Relative Performance Degradation (RPD), clean-to-stress rank changes/winner retention, bootstrap confidence intervals where practical
- Interface: static GitHub Pages reliability explorer using precomputed results

## Scientific workflow

The project follows a pre-specified workflow. Before final model evaluation, freeze the research questions, hypotheses, split logic, model families, corruption levels, metrics, and random seeds in `research/PROTOCOL.md`.

1. Literature reconnaissance
2. P1.5 methodology hardening
3. Dataset acquisition and audit
4. Protocol freeze
5. Preprocessing and feature construction
6. Baseline + clean benchmark
7. Sensor-degradation tests
8. Repeated site-shift tests
9. Statistical/failure analysis
10. Paper figures and manuscript
11. GitHub Pages explorer + reproducibility release

## Repository map

```text
airsense-r/
├── AGENTS.md
├── MEMORY.md
├── TASK.md
├── README.md
├── LICENSE
├── CITATION.cff
├── pyproject.toml
├── requirements.txt
├── configs/
├── artifacts/models/      # fitted model artifacts (generated later)
├── data/
├── docs/                # GitHub Pages reliability explorer
├── experiments/
├── figures/
├── paper/
├── research/
├── results/
├── scripts/
├── src/airsense_r/
│   ├── models/            # model definitions (persistence now; ML/DL after P3)
│   ├── data/
│   ├── features/
│   ├── corruption/
│   ├── evaluation/
│   └── visualization/
└── tests/
```

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

## Status

P0, P1, P1.5 and **P2 are complete**. The authoritative UCI archive was verified under Python 3.11, with frozen SHA-256 `b04da438b2f331ac0ffd45aebdfec0d20d2367feb5f6948c4b1f7ce1191e33c4`; all 12 expected stations and the complete hourly grid were confirmed, and compact audit evidence is retained in `audit/`. Next: P3 protocol freeze.
