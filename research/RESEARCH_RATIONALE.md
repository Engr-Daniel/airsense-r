# AirSense-R: Do Air-Quality Forecasters Keep Their Rank Under Sensor Degradation and Site Shift?

## Pre-results research rationale

**Prepared:** 2026-10-09, before P5 model results. **Verdict:** worth executing as a bounded model-selection reliability study; publication merit remains conditional on evidence and differentiation. This is an independent targeted review, not proof of novelty or a systematic literature review. The user's problem-and-significance document and subsequent reviewer comments have been assessed and incorporated into this canonical pre-results record.

## 1. What problem are we solving?

A researcher or monitoring-system developer chooses a PM2.5 forecaster using clean validation error. That choice may be suboptimal when input channels become unavailable/noisy, or when the model is applied at a station excluded from fitting. AirSense-R measures the consequence of that selection decision, rather than merely reporting which architecture has the lowest average error. Here, **clean** means no added synthetic degradation; naturally missing observations remain and are handled by the frozen preprocessing policy.

The proposed output is evidence about the conditions under which a clean-selected model remains competitive, loses an important amount of accuracy relative to available alternatives, or cannot be distinguished from them. This helps developers decide what must be stress-tested before trusting a clean leaderboard. It does not automatically implement model switching, repair instruments, or deliver a public warning system.

## 2. Is this a real problem? Evidence and boundaries

| Proposition | Evidence | What it does not establish |
|---|---|---|
| Air pollution is an important application domain. | WHO estimates 4.2 million premature deaths attributable to ambient air pollution in 2019 [S1]. | Our experiment will prevent deaths or improve public-health outcomes. |
| Air-quality forecasts inform practical decisions. | AirNow describes forecasts used to plan outdoor activities and reduce exposure [S2]. | A one-hour concentration forecast is interchangeable with daily AQI forecasts. |
| Observation-quality problems occur in practice. | EPA lists missing data, drift, inaccuracy, outliers and interferents among sensor-data problems [S3]. | Independent Gaussian noise reproduces drift, or low-cost sensor evidence directly characterizes Beijing reference monitors. |
| Our chosen dataset actually contains missing observations. | The frozen audit records 8,739 missing PM2.5 values (2.0769%) and 20,701 missing CO values (4.9198%) across 420,768 rows [R1]. | Missing values prove physical sensor failure, or their mechanism is random. |
| Missingness and cross-location prediction are established research issues. | Alvarado-Alcon et al. study sparse networks, missing data and cross-location forecasting [S4]. | These topics alone are novel contributions from AirSense-R. |
| Clean benchmark performance can be an incomplete evaluation target. | AirQualityBench reports evaluation on fragmented global monitoring streams [S5]. | Our four candidate models must reverse ranks under our particular stresses. |
| Forecast usefulness is not exhausted by average error. | Berlinghieri et al. evaluate hourly PM2.5 forecasts for individual timing decisions [S6]. | Our MAE and regret metrics measure health benefit or decision utility directly. |

**Inference:** these sources establish a credible motivation for testing selection reliability. They do not establish that rank reversal is common in our setting. That is the empirical question.

## 3. Why does the problem matter?

The immediate stakeholder is a forecasting-system developer choosing among feasible models. Clean validation accuracy is available at selection time; future stressed-test performance is not. A model can look best at selection time yet have a larger error penalty under a particular observation condition. Quantifying that penalty is more informative than a rank flip alone.

Conceptual illustration only: if two models swap ranks while differing by 0.1 microgram per cubic metre MAE, calling this a major reliability failure would exaggerate the evidence. Conversely, retaining a clean-selected model with a substantial excess error deserves attention even if it remains second rather than falling to last place. Neither example is an AirSense-R result.

The public-health context makes careful forecasting relevant, but does not make every forecasting benchmark important. This project's value must come from an actionable, reproducible comparison that reveals meaningful boundaries of a model-selection rule.

The importance of this problem does not follow merely from the importance of air pollution. Forecasting comparisons support a model-selection decision. If changed observation conditions alter relative performance, choosing solely from clean validation can be fragile. The scientific object is therefore the reliability of the selection rule, as measured by its forecasting-error consequences. This is not a claim to measure economic or health utility.

## 4. What exactly is being tested?

The frozen protocol selects a family using equal-station clean-validation MAE after training-only temporal tuning. Under observation degradation, fitted models and learned preprocessing remain fixed. Shared corrupted input streams and identical original target rows support paired comparisons.

The decision structure separates selection-time information from retrospective evaluation:

```text
Clean validation performance
    -> candidate ranking and predefined near-tie tiebreak
    -> selected model family (fixed before test inspection)
    -> evaluation of all candidates under the test condition
    -> retrospective selection regret with paired uncertainty
```

A rank is an ordering, a selection is an action, and regret measures the excess loss associated with that action relative to the tested alternatives. Degraded MAE alone does not identify this excess loss.

Selection regret is the stressed error of the validation-selected model minus the smallest stressed error among the candidate models. The latter is a retrospective oracle reference, not an implementable selection rule or a bound on all possible models.

**Illustration only, not results:** suppose clean-validation MAEs for A, B, C and D are 18, 20, 23 and 25. A is selected without invoking the 1.0 near-tie tiebreak. Under a stress, MAEs of 31, 24, 26 and 29 give regret of 31 - 24 = 7 micrograms per cubic metre for retaining A. Whether such a difference is statistically supported requires the paired analysis; the arithmetic alone does not demonstrate reliability failure in our data.

Site shift is a separate leave-one-station-out procedure: each fold refits and selects using only the other stations. It is not the identical fitted model from the pooled benchmark moved to a new city. Recent held-out-station observations are available as causal inference inputs. Report unseen-station performance and selection reliability; do not interpret an unmatched difference as a causal site-shift penalty.

The title uses **sensor degradation** for controlled observation interventions and **site shift** for within-Beijing unseen-station generalization. Those definitions must accompany the title in the abstract.

## 5. Is the contribution already solved?

Substantial overlap exists. S4 already addresses missing data and held-out locations; its task includes targets without local sensors, unlike our local-history forecasting setup. S5 is a 2026 preprint covering 3,720 stations and is a strong warning against claiming a novel realistic benchmark merely from including missingness. S6 already connects evaluation to decisions.

**Reusable contribution statement:** AirSense-R evaluates whether a model family selected under clean validation remains a practically defensible choice under predefined observation degradation and unseen-station conditions, using paired comparisons, selection regret, practical near-ties, and dependence-aware uncertainty. For unseen stations, selection is repeated separately within each holdout fold.

Our candidate contribution is narrower: a pre-specified, paired comparison of clean-selection regret across distinct controlled observation stresses and repeated station holdouts, with common preprocessing and practical/statistical interpretation. It is an empirical evaluation contribution, not an architectural invention.

The current search does not prove that no prior paper measures this exact combination. Before submission, compare the full methods and endpoints of the closest studies against ours, and conduct forward/backward citation searching. Do not claim "first," "unique," or superiority to these studies based on this memo. Abstract-level evidence is identified below.

## 6. What would make the work worth publishing?

These are interpretation criteria, not additions to the frozen protocol:

- Complete all predefined comparisons, seeds, severities and station holdouts; do not showcase only dramatic reversals.
- Publish matched predictions and provenance so others can reproduce paired comparisons.
- Interpret headline differences with the frozen 24-hour block bootstrap, 2,000 replicates and 95% intervals, alongside the 1.0 microgram per cubic metre practical near-tie rule.
- Explain whether conclusions recur across stations/seeds and survive the already specified imputation sensitivity.
- Report both absolute errors and regret; low regret can coexist with poor absolute forecasting.
- Distinguish systematic failure, practical ties, wide uncertainty, and genuinely stable rankings. An interval including zero is not proof of equivalence.
- Demonstrate an insight beyond "missing inputs increase errors" and beyond unqualified architecture rankings.

Stable rankings would still be informative if the tested range is clearly defined and uncertainty is sufficiently narrow to support a useful conclusion. Wide intervals, weak baselines or inconsistent effects would limit the claim. A null result is not a reason to change severities or hypotheses after inspecting test outcomes.

## 7. Limitations and adversarial checks

One city, an older four-year dataset, four frozen candidate families, and a one-hour horizon limit generalization. The 12 stations share regional conditions; stability here cannot establish stability across cities. Synthetic dropout/noise are controlled interventions, not validated physical failure models. Historical target PM2.5 is excluded from the primary corruption channels, so persistence retains a deliberate advantage in information availability that must be discussed.

Common imputation controls one confound but conclusions remain about complete model-plus-preprocessing pipelines. Correlated hours and stations do not supply thousands of independent replications. The frozen block length is an assumption, not a universal dependence guarantee.

Hardware access is unnecessary for this offline study. Actual sensor behavior, energy use, embedded feasibility, and health benefits remain outside its evidence.

## 8. Decision before P5

Proceed with P5 under the current frozen protocol. Finish the planned evidence before expanding scope. A ridge baseline or second dataset may strengthen the study, but neither is silently adopted here: each needs an explicit pre-results design decision and, where required, a protocol amendment. The user's document strengthened the decision-level explanation and contributed S7 and S8 below. Its unconditional conclusion that all study-worthiness criteria are satisfied is not adopted: nonredundancy, adequate precision and empirical insight remain conditional. We describe the protocol as pre-specified and repository-frozen, not formally preregistered.

## 9. Additional evidence from the user's rationale

The 2025 EPA Inspector General evaluation reports associations between offline periods and higher pollution at some US monitoring sites [S7]. It covers scheduled intermittent operation as well as offline periods at daily sites. This motivates concerns about observation representativeness; it neither establishes physical sensor failure as the cause nor validates independent random dropout as a model of that missingness. It also motivates a limitation: this study does not model pollution-dependent missingness comprehensively.

Han, Huang and Wang explicitly study model assessment and selection under temporal distribution shift [S8]. This supports the broader statistical motivation, but their adaptive selection method is not an AirSense-R method or proof of our novelty. We evaluate a fixed validation-based selection rule under pre-specified stresses rather than implementing their adaptation procedure.

The user's Nigeria context is relevant motivation but is not evidence of transferability from Beijing. Additional unspecified data-quality studies in that document are not treated as verified claims without identifiable references. The central scientific question does not depend on adding unverified examples.

**Core motivation:** AirSense-R tests whether selecting a model from clean validation remains reliable when observation conditions or the evaluated station change, and quantifies the excess forecasting error associated with retaining that choice. It does not require ranking failure to occur.

## Sources and search record

Targeted web searches on 2026-10-09 covered air-quality forecasting missing observations, cross-site generalization, official sensor QA, forecast use, and health importance. Official agency sources and original research records were preferred. No exhaustive screening or systematic-review claim is made.

- **S1:** WHO, [Ambient (outdoor) air pollution](https://www.who.int/en/news-room/fact-sheets/detail/ambient-%28outdoor%29-air-quality-and-health). Agency fact sheet; cited estimate explicitly refers to 2019.
- **S2:** AirNow, [Using the Air Quality Index](https://www.airnow.gov/aqi/aqi-basics/using-air-quality-index/). Official operational explanation; daily AQI and hourly concentration forecasts are distinct.
- **S3:** US EPA, [Quality Assurance for Air Sensors](https://www.epa.gov/air-sensor-toolbox/quality-assurance-air-sensors). Official sensor QA guidance, not a Beijing instrument audit.
- **S4:** Alvarado-Alcon et al. (2026), [Citywide Air Quality Forecasting over Sparse Sensor Networks](https://doi.org/10.3390/jsan15040052). Publisher-indexed abstract/excerpts reviewed in this refresh; direct full-page retrieval failed. Existing P1 notes provide additional context, not independently revalidated full-text claims here.
- **S5:** [AirQualityBench: A Realistic Evaluation Benchmark for Global Air Quality Forecasting](https://arxiv.org/abs/2605.05854), v1, 2026-05-07. Author-hosted research abstract reviewed; preprint, peer-review status not established.
- **S6:** [Are Hourly PM2.5 Forecasts Sufficiently Accurate to Plan Your Day? Individual Decision Making in the Face of Increasing Wildfire Smoke](https://arxiv.org/abs/2409.05866), v2, 2025-09-01. Research abstract reviewed. Earlier v1 used a different title; this memo uses the current v2 title.
- **S7:** US EPA Office of Inspector General, [Evaluation of the EPA's Oversight of State and Local Ambient Air Monitoring Operating Schedules](https://www.epa.gov/system/files/documents/2025-09/epaoig_20250917-25-e-0051_cert_redacted.pdf), report 25-E-0051, 2025-09-17. Public redacted report and findings summary checked; association is not proof that outages caused increased pollution.
- **S8:** Han, Elise; Huang, Chengpiao; Wang, Kaizheng (2024), [Model Assessment and Selection under Temporal Distribution Shift](https://proceedings.mlr.press/v235/han24b.html), ICML, PMLR 235:17374-17392. Official proceedings abstract and bibliographic record checked; no claim of reproducing its theoretical results.
- **R1:** [Frozen aggregate missingness audit](../audit/aggregate_missingness.csv), [dataset card](DATASET.md), and [protocol](PROTOCOL.md). Local structural evidence and pre-specified methods, not forecasting findings.
