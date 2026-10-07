# P1 Completion Report — Literature Reconnaissance and Novelty Stress-Test

**Project:** AirSense-R  
**Checkpoint:** P1  
**Status:** COMPLETE  
**Date:** 2026-10-07

## Objective

Determine whether the initial AirSense-R idea is sufficiently differentiated from existing air-quality forecasting research before final experiments are designed or executed.

## Work completed

- Searched recent PM2.5/air-quality forecasting benchmark literature.
- Searched missing-sensor and incomplete-observation forecasting literature.
- Searched low-cost sensor reliability/fault/calibration literature for adjacent deployment evidence.
- Searched cross-site, transfer-learning and distribution-shift literature.
- Searched broader time-series work on model-ranking heterogeneity and evaluation beyond aggregate clean metrics.
- Identified and compared ten especially relevant studies, with emphasis on 2024-2026 work.
- Constructed a dimension-by-dimension overlap matrix.
- Rejected over-broad novelty claims.
- Froze a narrower P1 contribution statement and revised research questions.
- Added rank-oriented evaluation requirements for the future P3 protocol.

## Critical finding

The initial framing — "air-quality forecasting under missing observations and unseen-site shift" — is **not sufficiently novel by itself**.

Two especially close 2026 studies already cover much of that ground:

1. Alvarado-Alcon et al. evaluate cross-location air-quality forecasting under sparse/missing sensor streams and held-out stations.
2. Chowdhury et al. compare ML/DL PM2.5 forecasting under varying missingness and imputation strategies.

Other recent studies also evaluate ranking heterogeneity across countries/station types, distribution shift, cross-station transfer and operational IoT forecasting.

## Revised scientific focus

AirSense-R v1 will focus on **model-selection reliability under deployment stress**:

> Does the model that wins on clean data remain the preferred model when the same frozen candidates face random feature dropout, complete channel loss, controlled measurement noise, or an unseen monitoring site?

The project is therefore primarily an **evaluation methodology / empirical reliability study**, not a new forecasting-architecture paper.

## What is potentially distinctive

Within the scoped rapid reconnaissance, no identified paper made the exact following combination its central question:

- one common PM2.5 forecasting task;
- same frozen candidate models;
- clean benchmark;
- random feature loss;
- complete sensor-channel loss;
- controlled measurement noise;
- unseen-site evaluation;
- explicit clean-to-stress model-rank stability / winner retention analysis.

This supports a **moderate, conditional novelty position**, not an absolute first-of-its-kind claim.

## Scientific guardrails added

- Do not claim missing-data forecasting itself as novel.
- Do not claim unseen-station evaluation itself as novel.
- Do not claim that "beyond clean accuracy" is a new general principle.
- Distinguish controlled synthetic input corruption from real sensor physics/calibration faults.
- Freeze any rank-stability statistic before final evaluation.
- Do not invent a composite score after viewing outcomes.

## Files updated in P1

- `research/LITERATURE_NOTES.md` — complete targeted reconnaissance, evidence matrix, novelty verdict, RQs.
- `research/P1_COMPLETION_REPORT.md` — this checkpoint record.
- `paper/references.bib` — seed bibliography for the closest prior work.
- `research/PROTOCOL.md` — objective/RQs/hypotheses revised to match P1 while retaining DRAFT status.
- `README.md` — public-facing scientific focus updated.
- `MEMORY.md` — durable P1 decisions recorded.
- `TASK.md` — P1 checklist marked complete.

## Exit criterion

P1 exit criterion is satisfied: the project now has a literature-constrained contribution statement that can guide dataset audit and protocol design.

## Next checkpoint

**P2 — Dataset acquisition and audit.**

The UCI Beijing Multi-Site Air Quality dataset must be downloaded and audited before exact feature policy, missing-value handling, temporal split, held-out station strategy, corruption severities or final model inputs are frozen.
