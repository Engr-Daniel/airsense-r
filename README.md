# AirSense-R

**Reliability-Aware Air-Quality Forecasting Under Sensor Degradation and Site Shift**

AirSense-R is a research-grade machine-learning project that studies whether air-quality forecasting models remain reliable when deployment conditions differ from clean historical test data. The initial study focuses on short-horizon PM2.5 forecasting using the UCI Beijing Multi-Site Air Quality dataset, with controlled tests for sensor dropout, measurement noise, and monitoring-site shift.

## Research question

> How reliable are machine-learning and deep-learning air-quality forecasting models when sensor observations are incomplete/noisy or come from an unseen monitoring site?

## Initial scope

- Target: PM2.5 one-hour-ahead forecasting
- Lookback: 24 hours (default; frozen in protocol before final experiments)
- Data: UCI Beijing Multi-Site Air Quality dataset
- Baselines/models: persistence, tree-based ML, MLP, compact GRU
- Reliability tests: random dropout, whole-variable dropout, measurement noise, unseen-site evaluation
- Metrics: MAE, RMSE, R², Relative Performance Degradation (RPD), bootstrap confidence intervals where practical
- Interface: static GitHub Pages reliability explorer using precomputed results

## Scientific workflow

The project follows a pre-specified workflow. Before final model evaluation, freeze the research questions, hypotheses, split logic, model families, corruption levels, metrics, and random seeds in `research/PROTOCOL.md`.

1. Literature reconnaissance
2. Dataset acquisition and audit
3. Protocol freeze
4. Preprocessing and feature construction
5. Baseline + clean benchmark
6. Sensor-degradation tests
7. Site-shift tests
8. Statistical/failure analysis
9. Paper figures and manuscript
10. GitHub Pages explorer + reproducibility release

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
├── data/
├── docs/                # GitHub Pages reliability explorer
├── experiments/
├── figures/
├── paper/
├── research/
├── results/
├── scripts/
├── src/airsense_r/
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
python scripts/download_data.py
python scripts/run_data_audit.py
```

Do not run final experiments until `research/PROTOCOL.md` is frozen.

## GitHub Pages

The static dashboard lives in `docs/`. Configure GitHub Pages to deploy from the `main` branch `/docs` folder. The dashboard initially displays placeholder content and will later load exported JSON/CSV artifacts from `docs/data/`.

## Research integrity

- Do not tune on the final test set.
- Do not redefine hypotheses after viewing final results.
- Distinguish clean IID performance from robustness/generalization performance.
- Treat Edge-ML as future work unless actual embedded deployment is completed.
- Record deviations from the frozen protocol in `research/PROTOCOL_DEVIATIONS.md`.

## Status

Project scaffold created. See `TASK.md` for the two-day execution plan.
