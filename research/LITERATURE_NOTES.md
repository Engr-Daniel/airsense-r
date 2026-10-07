# Literature Reconnaissance and Novelty Stress-Test

**Checkpoint:** P1  
**Status:** COMPLETE  
**Search date:** 2026-10-07  
**Study stage:** Targeted rapid reconnaissance before dataset audit and protocol freeze.

## 1. Purpose

P1 tests whether the original AirSense-R idea is sufficiently differentiated from existing work before any final experiment is run. The search focused on the closest methodological neighbours rather than producing a broad narrative review.

The original idea combined:

1. short-horizon PM2.5 forecasting;
2. machine-learning/deep-learning comparison;
3. missing/degraded sensor observations;
4. monitoring-site shift; and
5. deployment-oriented reliability evaluation.

The reconnaissance shows that items 1-4 already have substantial direct prior art. AirSense-R therefore **must not claim novelty merely from forecasting under missing data or unseen stations**.

## 2. Search themes

Searches were organized around five themes:

1. **PM2.5 / air-quality forecasting benchmarks** — statistical, tabular ML and sequence DL comparisons.
2. **Missing observations / sensor dropout** — forecasting when sensor streams contain gaps or are unavailable.
3. **Measurement quality and sensor faults** — imputation, fault reconstruction, calibration and degradation of low-cost sensors.
4. **Cross-site / spatial generalization / distribution shift** — held-out stations, new locations, temporal shift and transfer learning.
5. **Evaluation beyond a clean leaderboard** — whether aggregate clean rankings are stable or informative under deployment-relevant heterogeneity.

This was a targeted novelty reconnaissance, **not a systematic review**. It is intended to identify close prior work and constrain defensible claims for the two-day study.

## 3. Closest literature

### L1 — Alvarado-Alcon et al. (2026)
**Citywide Air Quality Forecasting over Sparse Sensor Networks: Cross-Location Generalization and Deep Learning Reliability Under Missing Data.** Journal of Sensor and Actuator Networks, 15(4), 52. DOI: 10.3390/jsan15040052.

- Forecasts O3, NO2, PM2.5 and PM10 across horizons from 1 h to 10 days.
- Benchmarks multiple recurrent, convolutional and multilayer architectures against classical baselines.
- Uses Madrid and Cali monitoring networks.
- Holds out stations to study cross-location generalization.
- Explicitly studies reliability under missing streams / sparse sensor networks.
- **Threat to original novelty:** very high. Missing-data reliability + held-out station generalization is already a central contribution.
- **Difference retained for AirSense-R:** our intended contribution is not a new citywide forecasting architecture. We will focus on whether the *model-selection decision made on clean data* remains stable under several controlled deployment stresses using frozen models.

### L2 — Chowdhury, Ejaz & Choudhury (2026)
**PM2.5 performance analysis under varying imputation strategies for incomplete sensor data.** Scientific Reports. DOI: 10.1038/s41598-026-55848-4.

- Eight low-cost sensors in Edmonton; one-hour-ahead PM2.5 forecasting with a 24 h history.
- Compares RF, XGBoost, CNN, LSTM and LSTM-attention.
- Evaluates mean, KNN and Kriging imputation under 30%, 60% and 90% data availability/missingness scenarios.
- Reports model/imputation combinations and statistical comparisons.
- **Threat:** very high for any claim that comparing ML/DL under missing data is novel.
- **Difference:** AirSense-R does not make imputation the primary intervention. The planned question is whether clean model rankings and deployment choices survive distinct perturbation types (random feature loss, whole-channel loss, measurement noise, site shift).

### L3 — Chisilev & Pelican (2026)
**Assessment of machine learning methods for urban air pollution forecasting.** Stochastic Environmental Research and Risk Assessment, 40, 205. DOI: 10.1007/s00477-026-03331-x.

- European multi-country PM2.5 benchmark across 1/3/6/12/24 h horizons.
- Compares statistical, boosted-tree and sequence-DL families under reproducible protocols.
- Reports skill vs persistence, paired significance tests and stratified results.
- Explicitly asks how stable model rankings are across countries and station-area types; also evaluates spatial transfer and alternative temporal splits.
- Finds model-family performance depends on horizon/context.
- **Threat:** high for a generic "ranking stability across sites" claim.
- **Difference:** AirSense-R narrows ranking reliability to **controlled observation degradation + site shift** under a common one-hour-ahead task, and measures rank reversals/degradation relative to the clean selection decision.

### L4 — Psomadakis et al. (2026)
**Forecasting of PM2.5/PM10 Using Machine Learning: A Benchmarking Study Based on Open Air Quality IoT Datasets.** Electronics, 15(19), 4496. DOI: 10.3390/electronics15194496.

- Frames particulate forecasting as an operational sensor-infrastructure problem.
- Uses open IoT air-quality datasets and emphasizes heterogeneous, imperfect real-world data rather than a single curated station.
- Highlights that conclusions from one chronological split can be unrepresentative.
- **Threat:** moderate-high to any claim that operationally motivated open-IoT benchmarking itself is novel.
- **Difference:** AirSense-R uses a deliberately controlled stress-test design and treats *selection robustness* as the outcome.

### L5 — Liu et al. (2024)
**PM2.5 forecasting under distribution shift: A graph learning approach.** AI Open, 5, 23-29. DOI: 10.1016/j.aiopen.2023.11.001.

- Introduces a PM2.5 forecasting benchmark specifically under distribution shift.
- Compares graph and non-graph models under split designs with/without temporal distribution shift.
- Finds graph models can suffer more under shift than non-graph alternatives.
- **Threat:** high for generic "models behave differently under shift" novelty.
- **Difference:** AirSense-R combines multiple deployment stresses and explicitly tests whether the clean winner remains the deployment winner.

### L6 — Wang et al. (2025)
**Quickly forecasting the future state of urban sensors by the missing-data-tolerant deep learning approach.** Sustainable Cities and Society, 118, 106044. DOI: 10.1016/j.scs.2024.106044.

- Proposes a lightweight imputer-predictor architecture designed to tolerate missing sensor data.
- Validates on traffic, PM2.5 and temperature datasets across four missing scenarios.
- Optimizes both forecasting quality and inference speed.
- **Threat:** high to any claim that missing-data-tolerant PM2.5 forecasting or lightweight operational forecasting is new.
- **Difference:** AirSense-R is an evaluation study, not a new missingness-aware architecture.

### L7 — Yao et al. (2024)
**Multi-source variational mode transfer learning for enhanced PM2.5 concentration forecasting at data-limited monitoring stations.** Expert Systems with Applications, 238A, 121714. DOI: 10.1016/j.eswa.2023.121714.

- Uses 12 Beijing air-quality monitoring sites.
- Develops multi-source transfer learning for target stations with limited historical data.
- Demonstrates the usefulness of source-station knowledge transfer.
- **Threat:** high to any novelty claim based on the Beijing multi-site dataset + cross-station transfer/generalization alone.
- **Difference:** AirSense-R does not propose transfer learning; held-out-site evaluation is one stress condition in a broader model-selection reliability study.

### L8 — Adong & Bainomugisha (2026)
**Transferability of Machine Learning-Based Calibration Models for Low-Cost PM2.5 Sensors Across Heterogeneous African Cities.** Meteorological Applications, 33(4), e70228. DOI: 10.1002/met.70228.

- Evaluates low-cost-sensor calibration transfer across five sites in four African cities.
- Compares local calibration, direct transfer, multicity pooled LOOCV and environmentally clustered LOOCV.
- Shows direct transfer can fail under environmental/domain mismatch, while diverse pooled training improves generalization.
- **Relevance:** calibration rather than forecasting, but exceptionally important deployment evidence for African sensor networks.
- **Difference:** reinforces why site/domain shift should remain in AirSense-R, but not as the sole novelty claim.

### L9 — Feng et al. (2026)
**Beyond Model Ranking: Predictability-Aligned Evaluation for Time Series Forecasting.** ICML 2026, PMLR 306:30490-30509.

- Argues that leaderboard-style aggregate scores can hide differences in task difficulty and architectural strengths.
- Introduces predictability-aligned diagnostics and identifies "predictability drift".
- Shows architectural strengths vary across predictability/frequency regimes.
- **Threat:** important conceptual prior art against claiming that "going beyond model ranking" is itself new.
- **Use for AirSense-R:** motivates making ranking *stability under concrete deployment stresses* an explicit diagnostic rather than claiming a general new evaluation philosophy.

### L10 — Wathore et al. (2026)
**Exploring Environmental and Temporal Performances of Machine Learning Models for Calibration of a Low-Cost PM2.5 Sensor.** Aerosol and Air Quality Research, 26, article 12.

- Evaluates calibration performance across environmental and temporal regimes.
- Compares RF/XGB and regression-based approaches and reports performance heterogeneity.
- **Relevance:** calibration, not forecasting; nevertheless demonstrates that average clean scores can hide regime-dependent behaviour.
- **Use for AirSense-R:** supports stratified, deployment-oriented interpretation rather than a single global score.

## 4. Evidence matrix

Legend: ✓ explicitly evaluated; ~ partially/adjacent; — not a central evaluated dimension in the scoped evidence.

| Study | PM forecasting | ML vs DL comparison | Missing/random loss | Whole-stream/channel loss | Measurement noise/fault stress | Held-out/new site or spatial transfer | Explicit ranking/context stability | Primary goal |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Alvarado-Alcon et al. 2026 | ✓ | ✓ | ✓ | ~ | — | ✓ | ~ | Citywide sparse-network forecasting |
| Chowdhury et al. 2026 | ✓ | ✓ | ✓ | — | — | — | ~ | Imputation under missingness |
| Chisilev & Pelican 2026 | ✓ | ✓ | ~ | — | — | ✓ | ✓ | Multi-country benchmark |
| Psomadakis et al. 2026 | ✓ | ✓ | ~ | — | ~ | ~ | ~ | Open-IoT benchmarking |
| Liu et al. 2024 | ✓ | ✓ | — | — | — | ~ (distribution shift) | ~ | Shift-aware graph benchmark |
| Wang et al. 2025 | ✓ | ✓ | ✓ | ~ | — | — | ~ | Missing-data-tolerant architecture |
| Yao et al. 2024 | ✓ | ~ | — | — | — | ✓ | — | Cross-station transfer learning |
| Adong & Bainomugisha 2026 | — (calibration) | ~ | — | — | ~ | ✓ | ~ | Cross-city calibration transfer |
| Feng et al. 2026 | general TS | ✓ | — | — | — | distribution/context shifts | ✓ | Predictability-aligned evaluation |
| **AirSense-R planned** | ✓ | ✓ | ✓ | ✓ | ✓ (controlled noise) | ✓ | **✓ — central endpoint** | Selection reliability under deployment stress |

## 5. Novelty stress-test verdict

### Claims that are **not defensible as novel**

AirSense-R must not claim novelty merely because it:

- forecasts PM2.5 with ML/DL;
- uses one-hour-ahead forecasting with a 24 h history;
- compares XGBoost/RF with neural sequence models;
- evaluates random missingness;
- tests unseen stations / cross-site generalization;
- studies distribution shift;
- uses the Beijing multi-site dataset; or
- argues that clean accuracy alone is insufficient in a broad sense.

Each of those ideas has direct recent prior art.

### Defensible positioning after P1

The strongest tractable contribution for the two-day v1 is a **controlled model-selection reliability study**:

> **AirSense-R evaluates whether the model selected as best under clean, in-distribution PM2.5 forecasting remains the preferred model when the same frozen candidates are exposed to distinct deployment stresses: random feature dropout, complete sensor-channel loss, controlled measurement noise, and monitoring-site shift.**

The emphasis is therefore on the **stability of the model-selection decision**, not on inventing a new forecasting architecture.

This positioning is deliberately narrower than claiming that no prior study has ever compared rankings under shift. Recent work already studies ranking heterogeneity across countries, horizons and predictability regimes. The specific contribution to test is the **joint, controlled clean-to-stress ranking behaviour across several sensor/deployment failure modes within one frozen experimental protocol**.

### Novelty confidence

**Moderate / conditional.** The rapid reconnaissance did not identify a paper with the exact AirSense-R combination as its central experimental question, but this is **not an exhaustive systematic review**. The paper should therefore use wording such as:

- "we investigate..."
- "we provide a controlled comparison..."
- "we focus specifically on..."

and avoid absolute claims such as "the first study to..." unless a later systematic search substantiates them.

## 6. Frozen P1 contribution statement

P1 freezes the following study contribution statement for use in P2/P3:

> **AirSense-R is a deployment-stress evaluation of PM2.5 forecasting model selection. Using a common forecasting task and frozen candidate models, it quantifies how absolute performance, relative degradation, and model ordering change between clean evaluation and four stress families: random feature dropout, whole-channel loss, controlled measurement noise, and unseen-site evaluation. The goal is to determine when a clean validation winner is, or is not, a reliable deployment choice.**

The implementation details (exact split, held-out station, severities, imputation policy, model hyperparameters and seeds) remain **DRAFT until P2 dataset audit and P3 protocol freeze**.

## 7. Research questions after P1

### Primary RQ

**RQ1.** Does the model selected as best under clean one-hour-ahead PM2.5 forecasting remain the best choice under sensor degradation and monitoring-site shift?

### Secondary RQs

**RQ2.** How much does each model's forecast error increase under random feature dropout, complete channel loss and controlled measurement noise relative to its own clean baseline?

**RQ3.** Which stress conditions produce statistically or practically meaningful model-rank reversals?

**RQ4.** How large is the generalization penalty at an unseen monitoring site, and does site shift alter the clean model ordering?

**RQ5.** Do simpler/tabular models and sequence deep-learning models exhibit different accuracy-versus-robustness trade-offs?

## 8. Evaluation implications for P3

To make the contribution match the literature gap, P3 should include explicit rank-oriented outputs in addition to MAE/RMSE/R²:

1. **Clean rank** of every candidate model.
2. **Stress-condition rank** at each severity/site condition.
3. **Rank change** from clean to stress condition.
4. **Winner retention indicator**: whether the clean winner remains rank 1.
5. **Relative Performance Degradation (RPD)** based on MAE.
6. **Pairwise error comparison / bootstrap interval** where feasible.
7. Optional compact summary such as **rank-stability rate** across pre-specified stress conditions; if used, its definition must be frozen in P3 before final results.

A new composite robustness score should **not** be invented after seeing results.

## 9. Scope constraints retained

- Primary target remains PM2.5 one hour ahead unless P2 reveals a data-integrity reason to change it.
- Edge deployment remains future work.
- No transformer/large architecture search in v1.
- No anomaly-detection sub-study in v1.
- No claim that synthetic corruption perfectly represents all real sensor failures.
- The study evaluates **forecast-model sensitivity to controlled input degradation**, not physical sensor calibration accuracy.

## 10. P1 decision

**P1 COMPLETE.** Proceed to P2 dataset acquisition and audit. Do not freeze the final experimental protocol until the actual UCI dataset has been downloaded and audited.
