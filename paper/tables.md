# Supplementary result tables

Generated from accepted artifacts. MAE/RMSE/regret are in µg/m³. Confidence intervals are pointwise, conditional paired 24-hour block-bootstrap intervals; subgroup bands have no confidence intervals.

## S1. Corrected clean test

| model | mae | rmse | r2 |
| --- | --- | --- | --- |
| xgboost | 9.7109 | 18.9209 | 0.9466 |
| persistence | 10.2796 | 19.6549 | 0.9422 |
| mlp | 10.8102 | 18.9385 | 0.9463 |
| gru | 15.9574 | 37.1660 | 0.6884 |

## S2. LOSO fixed-family metrics

| model | mae | rmse | r2 |
| --- | --- | --- | --- |
| xgboost | 9.7492 | 19.0915 | 0.9456 |
| persistence | 10.2797 | 19.6549 | 0.9422 |
| gru | 10.3019 | 19.4106 | 0.9408 |
| mlp | 10.9470 | 19.1289 | 0.9451 |

## S3. All sensor conditions and scopes

| policy | condition | scope | selected_MAE | regret | CI_low | CI_high | tau_b | within_near_tie |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| primary | random_dropout-10 | full | 10.2796 | 0.0000 | 0.0000 | 0.0000 | 0.6667 | True |
| primary | random_dropout-30 | full | 10.2796 | 0.0000 | 0.0000 | 0.0000 | 0.6667 | True |
| primary | random_dropout-50 | full | 10.2796 | 0.0000 | 0.0000 | 0.0000 | 0.6667 | True |
| primary | noise-05 | full | 10.2796 | 0.4965 | 0.2705 | 0.6912 | 1.0000 | True |
| primary | noise-10 | full | 10.2796 | 0.1917 | 0.0000 | 0.4135 | 1.0000 | True |
| primary | noise-20 | full | 10.2796 | 0.0000 | 0.0000 | 0.0000 | 0.6667 | True |
| primary | whole-NO2 | full | 10.2796 | 0.5405 | 0.3405 | 0.7153 | 1.0000 | True |
| primary | whole-CO | full | 10.2796 | 0.4379 | 0.2634 | 0.5945 | 1.0000 | True |
| primary | whole-TEMP | full | 10.2796 | 0.0000 | 0.0000 | 0.0000 | 0.3333 | True |
| primary | outage-NO2-6 | affected | 10.6099 | 0.5059 | 0.1702 | 0.7631 | 1.0000 | True |
| primary | outage-NO2-6 | full | 10.2796 | 0.5686 | 0.3398 | 0.7631 | 1.0000 | True |
| primary | outage-NO2-12 | affected | 10.5653 | 0.5442 | 0.2465 | 0.7755 | 1.0000 | True |
| primary | outage-NO2-12 | full | 10.2796 | 0.5673 | 0.3387 | 0.7619 | 1.0000 | True |
| primary | outage-CO-6 | affected | 10.6099 | 0.4936 | 0.1727 | 0.7404 | 1.0000 | True |
| primary | outage-CO-6 | full | 10.2796 | 0.5681 | 0.3396 | 0.7620 | 1.0000 | True |
| primary | outage-CO-12 | affected | 10.5653 | 0.5376 | 0.2967 | 0.7418 | 1.0000 | True |
| primary | outage-CO-12 | full | 10.2796 | 0.5670 | 0.3390 | 0.7596 | 1.0000 | True |
| primary | outage-TEMP-6 | affected | 10.6099 | 0.0791 | 0.0000 | 0.3505 | 1.0000 | True |
| primary | outage-TEMP-6 | full | 10.2796 | 0.5516 | 0.3232 | 0.7460 | 1.0000 | True |
| primary | outage-TEMP-12 | affected | 10.5653 | 0.0000 | 0.0000 | 0.0000 | 0.6667 | True |
| primary | outage-TEMP-12 | full | 10.2796 | 0.5277 | 0.3001 | 0.7212 | 1.0000 | True |
| no_ffill | random_dropout-10 | full | 10.5213 | 0.0000 | 0.0000 | 0.0000 | 0.6667 | True |
| no_ffill | random_dropout-30 | full | 10.5213 | 0.0000 | 0.0000 | 0.0000 | 0.3333 | True |
| no_ffill | random_dropout-50 | full | 10.5213 | 0.0000 | 0.0000 | 0.0000 | 0.3333 | True |
| no_ffill | noise-05 | full | 10.5213 | 0.4813 | 0.2394 | 0.6784 | 1.0000 | True |
| no_ffill | noise-10 | full | 10.5213 | 0.1801 | 0.0000 | 0.4070 | 1.0000 | True |
| no_ffill | noise-20 | full | 10.5213 | 0.0000 | 0.0000 | 0.0000 | 0.6667 | True |
| no_ffill | whole-NO2 | full | 10.5213 | 0.5260 | 0.3130 | 0.7038 | 1.0000 | True |
| no_ffill | whole-CO | full | 10.5213 | 0.4266 | 0.2417 | 0.5848 | 0.6667 | True |
| no_ffill | whole-TEMP | full | 10.5213 | 0.0000 | 0.0000 | 0.0000 | 0.3333 | True |
| no_ffill | outage-NO2-6 | affected | 10.8786 | 0.5560 | 0.2550 | 0.7901 | 1.0000 | True |
| no_ffill | outage-NO2-6 | full | 10.5213 | 0.5520 | 0.3120 | 0.7501 | 1.0000 | True |
| no_ffill | outage-NO2-12 | affected | 10.8202 | 0.5700 | 0.2949 | 0.7925 | 1.0000 | True |
| no_ffill | outage-NO2-12 | full | 10.5213 | 0.5508 | 0.3115 | 0.7495 | 1.0000 | True |
| no_ffill | outage-CO-6 | affected | 10.8786 | 0.5166 | 0.2487 | 0.7335 | 1.0000 | True |
| no_ffill | outage-CO-6 | full | 10.5213 | 0.5504 | 0.3113 | 0.7480 | 1.0000 | True |
| no_ffill | outage-CO-12 | affected | 10.8202 | 0.5320 | 0.2859 | 0.7220 | 1.0000 | True |
| no_ffill | outage-CO-12 | full | 10.5213 | 0.5490 | 0.3095 | 0.7462 | 1.0000 | True |
| no_ffill | outage-TEMP-6 | affected | 10.8786 | 0.1064 | 0.0000 | 0.3642 | 1.0000 | True |
| no_ffill | outage-TEMP-6 | full | 10.5213 | 0.5341 | 0.2934 | 0.7327 | 1.0000 | True |
| no_ffill | outage-TEMP-12 | affected | 10.8202 | 0.0000 | 0.0000 | 0.0000 | 0.6667 | True |
| no_ffill | outage-TEMP-12 | full | 10.5213 | 0.5096 | 0.2676 | 0.7076 | 1.0000 | True |

## S4. Station-specific selection regret

| station | selected_family | kendall_tau_b | within_practical_near_tie | ci_high | ci_low | estimate |
| --- | --- | --- | --- | --- | --- | --- |
| Aotizhongxin | persistence | 0.6667 | True | 1.0482 | 0.4756 | 0.7953 |
| Changping | persistence | 1.0000 | True | 0.5461 | 0.0000 | 0.3058 |
| Dingling | persistence | 0.6667 | True | 0.3957 | 0.0833 | 0.2366 |
| Dongsi | persistence | 1.0000 | True | 0.8479 | 0.0000 | 0.3936 |
| Guanyuan | persistence | 1.0000 | True | 0.9909 | 0.5793 | 0.8003 |
| Gucheng | persistence | 0.6667 | True | 0.5941 | 0.0000 | 0.0000 |
| Huairou | persistence | 0.3333 | True | 0.5518 | 0.2449 | 0.3968 |
| Nongzhanguan | persistence | 1.0000 | True | 0.9739 | 0.5293 | 0.7460 |
| Shunyi | persistence | 1.0000 | False | 1.3109 | 0.7417 | 1.0504 |
| Tiantan | persistence | 1.0000 | True | 0.9235 | 0.2821 | 0.6273 |
| Wanliu | persistence | 1.0000 | True | 0.8357 | 0.4432 | 0.6391 |
| Wanshouxigong | persistence | 1.0000 | True | 0.9223 | 0.3798 | 0.6134 |

## S5. Exploratory concentration bands

| model | concentration_band | mae | bias | stations | targets |
| --- | --- | --- | --- | --- | --- |
| gru | 100 to <200 | 14.2762 | -1.6897 | 12 | 18840 |
| gru | 50 to <100 | 9.9294 | 1.1182 | 12 | 25539 |
| gru | <50 | 6.3199 | 2.4469 | 12 | 49592 |
| gru | >=200 | 25.8142 | -13.2650 | 12 | 8782 |
| mlp | 100 to <200 | 14.9322 | -1.0810 | 12 | 18840 |
| mlp | 50 to <100 | 10.9233 | 1.2746 | 12 | 25539 |
| mlp | <50 | 6.9216 | 2.6210 | 12 | 49592 |
| mlp | >=200 | 25.3117 | -10.4988 | 12 | 8782 |
| persistence | 100 to <200 | 14.7725 | -2.2696 | 12 | 18840 |
| persistence | 50 to <100 | 10.5290 | 0.1773 | 12 | 25539 |
| persistence | <50 | 6.2910 | 1.6929 | 12 | 49592 |
| persistence | >=200 | 22.5879 | -5.3807 | 12 | 8782 |
| xgboost | 100 to <200 | 13.3989 | -2.2551 | 12 | 18840 |
| xgboost | 50 to <100 | 9.3107 | 1.2061 | 12 | 25539 |
| xgboost | <50 | 5.8046 | 2.4659 | 12 | 49592 |
| xgboost | >=200 | 25.4248 | -13.3813 | 12 | 8782 |

## S6. All sensor model comparisons

Paired differences are selected-family minus comparator MAE; positive values favor the comparator. Clean metrics are matched to each scope.

| policy | condition | scope | model | MAE | clean_MAE | RPD_percent | clean_rank | stress_rank | selected_minus_model | CI_low | CI_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| primary | random_dropout-10 | full | gru | 17.5516 | 15.9574 | 9.9905 | 4.0000 | 4.0000 | -7.2720 | -9.0618 | -5.6535 |
| primary | random_dropout-10 | full | mlp | 13.4222 | 10.8102 | 24.1625 | 3.0000 | 3.0000 | -3.1426 | -3.3523 | -2.9367 |
| primary | random_dropout-10 | full | persistence | 10.2796 | 10.2796 | 0.0000 | 2.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 |
| primary | random_dropout-10 | full | xgboost | 10.8078 | 9.7109 | 11.2957 | 1.0000 | 2.0000 | -0.5281 | -0.7647 | -0.3264 |
| primary | random_dropout-30 | full | gru | 20.3194 | 15.9574 | 27.3349 | 4.0000 | 4.0000 | -10.0397 | -11.6471 | -8.6096 |
| primary | random_dropout-30 | full | mlp | 17.3236 | 10.8102 | 60.2519 | 3.0000 | 3.0000 | -7.0439 | -7.3176 | -6.7778 |
| primary | random_dropout-30 | full | persistence | 10.2796 | 10.2796 | 0.0000 | 2.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 |
| primary | random_dropout-30 | full | xgboost | 13.3701 | 9.7109 | 37.6822 | 1.0000 | 2.0000 | -3.0905 | -3.3857 | -2.8396 |
| primary | random_dropout-50 | full | gru | 23.9033 | 15.9574 | 49.7944 | 4.0000 | 4.0000 | -13.6237 | -14.9984 | -12.3975 |
| primary | random_dropout-50 | full | mlp | 20.8360 | 10.8102 | 92.7439 | 3.0000 | 3.0000 | -10.5564 | -10.8751 | -10.2396 |
| primary | random_dropout-50 | full | persistence | 10.2796 | 10.2796 | 0.0000 | 2.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 |
| primary | random_dropout-50 | full | xgboost | 16.3975 | 9.7109 | 68.8569 | 1.0000 | 2.0000 | -6.1178 | -6.5194 | -5.7525 |
| primary | noise-05 | full | gru | 16.2156 | 15.9574 | 1.6179 | 4.0000 | 4.0000 | -5.9359 | -7.7824 | -4.2482 |
| primary | noise-05 | full | mlp | 11.0098 | 10.8102 | 1.8465 | 3.0000 | 3.0000 | -0.7302 | -0.9351 | -0.5291 |
| primary | noise-05 | full | persistence | 10.2796 | 10.2796 | 0.0000 | 2.0000 | 2.0000 | 0.0000 | 0.0000 | 0.0000 |
| primary | noise-05 | full | xgboost | 9.7831 | 9.7109 | 0.7439 | 1.0000 | 1.0000 | 0.4965 | 0.2705 | 0.6912 |
| primary | noise-10 | full | gru | 16.9227 | 15.9574 | 6.0493 | 4.0000 | 4.0000 | -6.6431 | -8.5036 | -4.9265 |
| primary | noise-10 | full | mlp | 11.6237 | 10.8102 | 7.5254 | 3.0000 | 3.0000 | -1.3441 | -1.5522 | -1.1438 |
| primary | noise-10 | full | persistence | 10.2796 | 10.2796 | 0.0000 | 2.0000 | 2.0000 | 0.0000 | 0.0000 | 0.0000 |
| primary | noise-10 | full | xgboost | 10.0879 | 9.7109 | 3.8830 | 1.0000 | 1.0000 | 0.1917 | -0.0707 | 0.4135 |
| primary | noise-20 | full | gru | 19.0566 | 15.9574 | 19.4217 | 4.0000 | 4.0000 | -8.7770 | -10.7027 | -7.0032 |
| primary | noise-20 | full | mlp | 13.6942 | 10.8102 | 26.6781 | 3.0000 | 3.0000 | -3.4145 | -3.6579 | -3.1810 |
| primary | noise-20 | full | persistence | 10.2796 | 10.2796 | 0.0000 | 2.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 |
| primary | noise-20 | full | xgboost | 11.0439 | 9.7109 | 13.7273 | 1.0000 | 2.0000 | -0.7643 | -1.1331 | -0.4545 |
| primary | whole-NO2 | full | gru | 14.0505 | 15.9574 | -11.9502 | 4.0000 | 4.0000 | -3.7708 | -5.2651 | -2.4203 |
| primary | whole-NO2 | full | mlp | 11.0315 | 10.8102 | 2.0470 | 3.0000 | 3.0000 | -0.7519 | -0.9394 | -0.5655 |
| primary | whole-NO2 | full | persistence | 10.2796 | 10.2796 | 0.0000 | 2.0000 | 2.0000 | 0.0000 | 0.0000 | 0.0000 |
| primary | whole-NO2 | full | xgboost | 9.7391 | 9.7109 | 0.2913 | 1.0000 | 1.0000 | 0.5405 | 0.3405 | 0.7153 |
| primary | whole-CO | full | gru | 11.0949 | 15.9574 | -30.4719 | 4.0000 | 4.0000 | -0.8152 | -1.2383 | -0.4448 |
| primary | whole-CO | full | mlp | 10.7736 | 10.8102 | -0.3389 | 3.0000 | 3.0000 | -0.4939 | -0.6754 | -0.3143 |
| primary | whole-CO | full | persistence | 10.2796 | 10.2796 | 0.0000 | 2.0000 | 2.0000 | 0.0000 | 0.0000 | 0.0000 |
| primary | whole-CO | full | xgboost | 9.8417 | 9.7109 | 1.3476 | 1.0000 | 1.0000 | 0.4379 | 0.2634 | 0.5945 |
| primary | whole-TEMP | full | gru | 17.5942 | 15.9574 | 10.2570 | 4.0000 | 3.0000 | -7.3145 | -9.1275 | -5.6919 |
| primary | whole-TEMP | full | mlp | 21.8081 | 10.8102 | 101.7363 | 3.0000 | 4.0000 | -11.5285 | -12.5717 | -10.5425 |
| primary | whole-TEMP | full | persistence | 10.2796 | 10.2796 | 0.0000 | 2.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 |
| primary | whole-TEMP | full | xgboost | 13.0156 | 9.7109 | 34.0312 | 1.0000 | 2.0000 | -2.7359 | -3.1453 | -2.3688 |
| primary | outage-NO2-6 | affected | gru | 16.3553 | 16.4451 | -0.5465 | 4.0000 | 4.0000 | -5.7453 | -7.7948 | -3.8296 |
| primary | outage-NO2-6 | affected | mlp | 11.2033 | 11.0967 | 0.9605 | 3.0000 | 3.0000 | -0.5933 | -0.8430 | -0.3774 |
| primary | outage-NO2-6 | affected | persistence | 10.6099 | 10.6099 | 0.0000 | 2.0000 | 2.0000 | 0.0000 | 0.0000 | 0.0000 |
| primary | outage-NO2-6 | affected | xgboost | 10.1040 | 10.0994 | 0.0450 | 1.0000 | 1.0000 | 0.5059 | 0.1702 | 0.7631 |
| primary | outage-NO2-6 | full | gru | 15.9538 | 15.9574 | -0.0224 | 4.0000 | 4.0000 | -5.6742 | -7.5142 | -4.0030 |
| primary | outage-NO2-6 | full | mlp | 10.8145 | 10.8102 | 0.0393 | 3.0000 | 3.0000 | -0.5348 | -0.7414 | -0.3332 |
| primary | outage-NO2-6 | full | persistence | 10.2796 | 10.2796 | 0.0000 | 2.0000 | 2.0000 | 0.0000 | 0.0000 | 0.0000 |
| primary | outage-NO2-6 | full | xgboost | 9.7110 | 9.7109 | 0.0018 | 1.0000 | 1.0000 | 0.5686 | 0.3398 | 0.7631 |
| primary | outage-NO2-12 | affected | gru | 16.0454 | 16.3891 | -2.0968 | 4.0000 | 4.0000 | -5.4801 | -7.4695 | -3.6605 |
| primary | outage-NO2-12 | affected | mlp | 11.2232 | 11.0196 | 1.8477 | 3.0000 | 3.0000 | -0.6579 | -0.8874 | -0.4531 |
| primary | outage-NO2-12 | affected | persistence | 10.5653 | 10.5653 | 0.0000 | 2.0000 | 2.0000 | 0.0000 | 0.0000 | 0.0000 |
| primary | outage-NO2-12 | affected | xgboost | 10.0212 | 9.9902 | 0.3093 | 1.0000 | 1.0000 | 0.5442 | 0.2465 | 0.7755 |
| primary | outage-NO2-12 | full | gru | 15.9409 | 15.9574 | -0.1034 | 4.0000 | 4.0000 | -5.6613 | -7.4989 | -3.9957 |
| primary | outage-NO2-12 | full | mlp | 10.8200 | 10.8102 | 0.0903 | 3.0000 | 3.0000 | -0.5403 | -0.7473 | -0.3389 |
| primary | outage-NO2-12 | full | persistence | 10.2796 | 10.2796 | 0.0000 | 2.0000 | 2.0000 | 0.0000 | 0.0000 | 0.0000 |
| primary | outage-NO2-12 | full | xgboost | 9.7123 | 9.7109 | 0.0151 | 1.0000 | 1.0000 | 0.5673 | 0.3387 | 0.7619 |
| primary | outage-CO-6 | affected | gru | 16.2720 | 16.4451 | -1.0530 | 4.0000 | 4.0000 | -5.6620 | -7.7032 | -3.7634 |
| primary | outage-CO-6 | affected | mlp | 11.1753 | 11.0967 | 0.7082 | 3.0000 | 3.0000 | -0.5653 | -0.8095 | -0.3442 |
| primary | outage-CO-6 | affected | persistence | 10.6099 | 10.6099 | 0.0000 | 2.0000 | 2.0000 | 0.0000 | 0.0000 | 0.0000 |
| primary | outage-CO-6 | affected | xgboost | 10.1163 | 10.0994 | 0.1669 | 1.0000 | 1.0000 | 0.4936 | 0.1727 | 0.7404 |
| primary | outage-CO-6 | full | gru | 15.9505 | 15.9574 | -0.0431 | 4.0000 | 4.0000 | -5.6709 | -7.5125 | -4.0005 |
| primary | outage-CO-6 | full | mlp | 10.8133 | 10.8102 | 0.0290 | 3.0000 | 3.0000 | -0.5337 | -0.7400 | -0.3324 |
| primary | outage-CO-6 | full | persistence | 10.2796 | 10.2796 | 0.0000 | 2.0000 | 2.0000 | 0.0000 | 0.0000 | 0.0000 |
| primary | outage-CO-6 | full | xgboost | 9.7115 | 9.7109 | 0.0070 | 1.0000 | 1.0000 | 0.5681 | 0.3396 | 0.7620 |
| primary | outage-CO-12 | affected | gru | 15.5388 | 16.3891 | -5.1883 | 4.0000 | 4.0000 | -4.9734 | -6.8035 | -3.2724 |
| primary | outage-CO-12 | affected | mlp | 11.2104 | 11.0196 | 1.7312 | 3.0000 | 3.0000 | -0.6451 | -0.8917 | -0.4191 |
| primary | outage-CO-12 | affected | persistence | 10.5653 | 10.5653 | 0.0000 | 2.0000 | 2.0000 | 0.0000 | 0.0000 | 0.0000 |
| primary | outage-CO-12 | affected | xgboost | 10.0277 | 9.9902 | 0.3748 | 1.0000 | 1.0000 | 0.5376 | 0.2967 | 0.7418 |
| primary | outage-CO-12 | full | gru | 15.9166 | 15.9574 | -0.2560 | 4.0000 | 4.0000 | -5.6369 | -7.4712 | -3.9770 |
| primary | outage-CO-12 | full | mlp | 10.8194 | 10.8102 | 0.0847 | 3.0000 | 3.0000 | -0.5397 | -0.7472 | -0.3381 |
| primary | outage-CO-12 | full | persistence | 10.2796 | 10.2796 | 0.0000 | 2.0000 | 2.0000 | 0.0000 | 0.0000 | 0.0000 |
| primary | outage-CO-12 | full | xgboost | 9.7126 | 9.7109 | 0.0184 | 1.0000 | 1.0000 | 0.5670 | 0.3390 | 0.7596 |
| primary | outage-TEMP-6 | affected | gru | 16.8949 | 16.4451 | 2.7350 | 4.0000 | 4.0000 | -6.2850 | -8.3395 | -4.3679 |
| primary | outage-TEMP-6 | affected | mlp | 11.8592 | 11.0967 | 6.8718 | 3.0000 | 3.0000 | -1.2493 | -1.5247 | -0.9933 |
| primary | outage-TEMP-6 | affected | persistence | 10.6099 | 10.6099 | 0.0000 | 2.0000 | 2.0000 | 0.0000 | 0.0000 | 0.0000 |
| primary | outage-TEMP-6 | affected | xgboost | 10.5308 | 10.0994 | 4.2710 | 1.0000 | 1.0000 | 0.0791 | -0.2604 | 0.3505 |
| primary | outage-TEMP-6 | full | gru | 15.9753 | 15.9574 | 0.1122 | 4.0000 | 4.0000 | -5.6957 | -7.5398 | -4.0238 |
| primary | outage-TEMP-6 | full | mlp | 10.8405 | 10.8102 | 0.2805 | 3.0000 | 3.0000 | -0.5609 | -0.7649 | -0.3590 |
| primary | outage-TEMP-6 | full | persistence | 10.2796 | 10.2796 | 0.0000 | 2.0000 | 2.0000 | 0.0000 | 0.0000 | 0.0000 |
| primary | outage-TEMP-6 | full | xgboost | 9.7280 | 9.7109 | 0.1769 | 1.0000 | 1.0000 | 0.5516 | 0.3232 | 0.7460 |
| primary | outage-TEMP-12 | affected | gru | 17.2246 | 16.3891 | 5.0980 | 4.0000 | 4.0000 | -6.6593 | -8.6325 | -4.8002 |
| primary | outage-TEMP-12 | affected | mlp | 13.0281 | 11.0196 | 18.2268 | 3.0000 | 3.0000 | -2.4628 | -2.8163 | -2.1305 |
| primary | outage-TEMP-12 | affected | persistence | 10.5653 | 10.5653 | 0.0000 | 2.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 |
| primary | outage-TEMP-12 | affected | xgboost | 10.8461 | 9.9902 | 8.5673 | 1.0000 | 2.0000 | -0.2808 | -0.5961 | -0.0100 |
| primary | outage-TEMP-12 | full | gru | 15.9976 | 15.9574 | 0.2518 | 4.0000 | 4.0000 | -5.7180 | -7.5597 | -4.0491 |
| primary | outage-TEMP-12 | full | mlp | 10.9066 | 10.8102 | 0.8918 | 3.0000 | 3.0000 | -0.6270 | -0.8323 | -0.4268 |
| primary | outage-TEMP-12 | full | persistence | 10.2796 | 10.2796 | 0.0000 | 2.0000 | 2.0000 | 0.0000 | 0.0000 | 0.0000 |
| primary | outage-TEMP-12 | full | xgboost | 9.7519 | 9.7109 | 0.4231 | 1.0000 | 1.0000 | 0.5277 | 0.3001 | 0.7212 |
| no_ffill | random_dropout-10 | full | gru | 20.0175 | 16.0955 | 24.3671 | 4.0000 | 4.0000 | -9.4962 | -11.2706 | -7.8726 |
| no_ffill | random_dropout-10 | full | mlp | 17.9263 | 11.3038 | 58.5870 | 3.0000 | 3.0000 | -7.4050 | -7.8101 | -7.0215 |
| no_ffill | random_dropout-10 | full | persistence | 10.5213 | 10.5213 | 0.0000 | 2.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 |
| no_ffill | random_dropout-10 | full | xgboost | 12.1509 | 9.9693 | 21.8826 | 1.0000 | 2.0000 | -1.6296 | -1.9877 | -1.3406 |
| no_ffill | random_dropout-30 | full | gru | 23.9859 | 16.0955 | 49.0218 | 4.0000 | 3.0000 | -13.4645 | -14.7705 | -12.2710 |
| no_ffill | random_dropout-30 | full | mlp | 24.5961 | 11.3038 | 117.5919 | 3.0000 | 4.0000 | -14.0748 | -14.7606 | -13.4257 |
| no_ffill | random_dropout-30 | full | persistence | 10.5213 | 10.5213 | 0.0000 | 2.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 |
| no_ffill | random_dropout-30 | full | xgboost | 16.9028 | 9.9693 | 69.5480 | 1.0000 | 2.0000 | -6.3815 | -6.9537 | -5.8938 |
| no_ffill | random_dropout-50 | full | gru | 27.0988 | 16.0955 | 68.3620 | 4.0000 | 3.0000 | -16.5774 | -17.4798 | -15.7565 |
| no_ffill | random_dropout-50 | full | mlp | 28.1203 | 11.3038 | 148.7694 | 3.0000 | 4.0000 | -17.5990 | -18.4317 | -16.8200 |
| no_ffill | random_dropout-50 | full | persistence | 10.5213 | 10.5213 | 0.0000 | 2.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 |
| no_ffill | random_dropout-50 | full | xgboost | 22.5596 | 9.9693 | 126.2891 | 1.0000 | 2.0000 | -12.0382 | -12.8059 | -11.3925 |
| no_ffill | noise-05 | full | gru | 16.3473 | 16.0955 | 1.5639 | 4.0000 | 4.0000 | -5.8259 | -7.6745 | -4.1407 |
| no_ffill | noise-05 | full | mlp | 11.5019 | 11.3038 | 1.7529 | 3.0000 | 3.0000 | -0.9806 | -1.2283 | -0.7414 |
| no_ffill | noise-05 | full | persistence | 10.5213 | 10.5213 | 0.0000 | 2.0000 | 2.0000 | 0.0000 | 0.0000 | 0.0000 |
| no_ffill | noise-05 | full | xgboost | 10.0401 | 9.9693 | 0.7092 | 1.0000 | 1.0000 | 0.4813 | 0.2394 | 0.6784 |
| no_ffill | noise-10 | full | gru | 17.0408 | 16.0955 | 5.8732 | 4.0000 | 4.0000 | -6.5195 | -8.3749 | -4.8064 |
| no_ffill | noise-10 | full | mlp | 12.1017 | 11.3038 | 7.0591 | 3.0000 | 3.0000 | -1.5804 | -1.8298 | -1.3390 |
| no_ffill | noise-10 | full | persistence | 10.5213 | 10.5213 | 0.0000 | 2.0000 | 2.0000 | 0.0000 | 0.0000 | 0.0000 |
| no_ffill | noise-10 | full | xgboost | 10.3412 | 9.9693 | 3.7302 | 1.0000 | 1.0000 | 0.1801 | -0.0923 | 0.4070 |
| no_ffill | noise-20 | full | gru | 19.1520 | 16.0955 | 18.9898 | 4.0000 | 4.0000 | -8.6307 | -10.5397 | -6.8492 |
| no_ffill | noise-20 | full | mlp | 14.1237 | 11.3038 | 24.9472 | 3.0000 | 3.0000 | -3.6024 | -3.8780 | -3.3314 |
| no_ffill | noise-20 | full | persistence | 10.5213 | 10.5213 | 0.0000 | 2.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 |
| no_ffill | noise-20 | full | xgboost | 11.2913 | 9.9693 | 13.2599 | 1.0000 | 2.0000 | -0.7700 | -1.1427 | -0.4532 |
| no_ffill | whole-NO2 | full | gru | 14.1587 | 16.0955 | -12.0333 | 4.0000 | 4.0000 | -3.6374 | -5.1222 | -2.2878 |
| no_ffill | whole-NO2 | full | mlp | 11.5495 | 11.3038 | 2.1742 | 3.0000 | 3.0000 | -1.0282 | -1.2704 | -0.7927 |
| no_ffill | whole-NO2 | full | persistence | 10.5213 | 10.5213 | 0.0000 | 2.0000 | 2.0000 | 0.0000 | 0.0000 | 0.0000 |
| no_ffill | whole-NO2 | full | xgboost | 9.9953 | 9.9693 | 0.2603 | 1.0000 | 1.0000 | 0.5260 | 0.3130 | 0.7038 |
| no_ffill | whole-CO | full | gru | 11.2487 | 16.0955 | -30.1128 | 4.0000 | 3.0000 | -0.7274 | -1.1586 | -0.3386 |
| no_ffill | whole-CO | full | mlp | 11.2840 | 11.3038 | -0.1752 | 3.0000 | 4.0000 | -0.7627 | -0.9849 | -0.5321 |
| no_ffill | whole-CO | full | persistence | 10.5213 | 10.5213 | 0.0000 | 2.0000 | 2.0000 | 0.0000 | 0.0000 | 0.0000 |
| no_ffill | whole-CO | full | xgboost | 10.0947 | 9.9693 | 1.2573 | 1.0000 | 1.0000 | 0.4266 | 0.2417 | 0.5848 |
| no_ffill | whole-TEMP | full | gru | 17.6940 | 16.0955 | 9.9310 | 4.0000 | 3.0000 | -7.1727 | -8.9799 | -5.5446 |
| no_ffill | whole-TEMP | full | mlp | 22.3769 | 11.3038 | 97.9598 | 3.0000 | 4.0000 | -11.8556 | -12.9119 | -10.8278 |
| no_ffill | whole-TEMP | full | persistence | 10.5213 | 10.5213 | 0.0000 | 2.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 |
| no_ffill | whole-TEMP | full | xgboost | 13.2621 | 9.9693 | 33.0288 | 1.0000 | 2.0000 | -2.7408 | -3.1487 | -2.3792 |
| no_ffill | outage-NO2-6 | affected | gru | 16.2141 | 16.5624 | -2.1031 | 4.0000 | 4.0000 | -5.3355 | -7.2940 | -3.5143 |
| no_ffill | outage-NO2-6 | affected | mlp | 11.7569 | 11.6275 | 1.1130 | 3.0000 | 3.0000 | -0.8784 | -1.1502 | -0.6267 |
| no_ffill | outage-NO2-6 | affected | persistence | 10.8786 | 10.8786 | 0.0000 | 2.0000 | 2.0000 | 0.0000 | 0.0000 | 0.0000 |
| no_ffill | outage-NO2-6 | affected | xgboost | 10.3226 | 10.3225 | 0.0008 | 1.0000 | 1.0000 | 0.5560 | 0.2550 | 0.7901 |
| no_ffill | outage-NO2-6 | full | gru | 16.0817 | 16.0955 | -0.0861 | 4.0000 | 4.0000 | -5.5603 | -7.4036 | -3.8941 |
| no_ffill | outage-NO2-6 | full | mlp | 11.3089 | 11.3038 | 0.0456 | 3.0000 | 3.0000 | -0.7876 | -1.0327 | -0.5449 |
| no_ffill | outage-NO2-6 | full | persistence | 10.5213 | 10.5213 | 0.0000 | 2.0000 | 2.0000 | 0.0000 | 0.0000 | 0.0000 |
| no_ffill | outage-NO2-6 | full | xgboost | 9.9693 | 9.9693 | -0.0001 | 1.0000 | 1.0000 | 0.5520 | 0.3120 | 0.7501 |
| no_ffill | outage-NO2-12 | affected | gru | 15.8929 | 16.5068 | -3.7191 | 4.0000 | 4.0000 | -5.0727 | -6.9770 | -3.3476 |
| no_ffill | outage-NO2-12 | affected | mlp | 11.7250 | 11.5166 | 1.8091 | 3.0000 | 3.0000 | -0.9048 | -1.1640 | -0.6641 |
| no_ffill | outage-NO2-12 | affected | persistence | 10.8202 | 10.8202 | 0.0000 | 2.0000 | 2.0000 | 0.0000 | 0.0000 | 0.0000 |
| no_ffill | outage-NO2-12 | affected | xgboost | 10.2502 | 10.2264 | 0.2324 | 1.0000 | 1.0000 | 0.5700 | 0.2949 | 0.7925 |
| no_ffill | outage-NO2-12 | full | gru | 16.0660 | 16.0955 | -0.1833 | 4.0000 | 4.0000 | -5.5447 | -7.3819 | -3.8836 |
| no_ffill | outage-NO2-12 | full | mlp | 11.3138 | 11.3038 | 0.0884 | 3.0000 | 3.0000 | -0.7924 | -1.0368 | -0.5506 |
| no_ffill | outage-NO2-12 | full | persistence | 10.5213 | 10.5213 | 0.0000 | 2.0000 | 2.0000 | 0.0000 | 0.0000 | 0.0000 |
| no_ffill | outage-NO2-12 | full | xgboost | 9.9705 | 9.9693 | 0.0114 | 1.0000 | 1.0000 | 0.5508 | 0.3115 | 0.7495 |
| no_ffill | outage-CO-6 | affected | gru | 15.7741 | 16.5624 | -4.7597 | 4.0000 | 4.0000 | -4.8955 | -6.7018 | -3.2031 |
| no_ffill | outage-CO-6 | affected | mlp | 11.7489 | 11.6275 | 1.0436 | 3.0000 | 3.0000 | -0.8703 | -1.1388 | -0.6245 |
| no_ffill | outage-CO-6 | affected | persistence | 10.8786 | 10.8786 | 0.0000 | 2.0000 | 2.0000 | 0.0000 | 0.0000 | 0.0000 |
| no_ffill | outage-CO-6 | affected | xgboost | 10.3620 | 10.3225 | 0.3823 | 1.0000 | 1.0000 | 0.5166 | 0.2487 | 0.7335 |
| no_ffill | outage-CO-6 | full | gru | 16.0641 | 16.0955 | -0.1951 | 4.0000 | 4.0000 | -5.5428 | -7.3829 | -3.8807 |
| no_ffill | outage-CO-6 | full | mlp | 11.3086 | 11.3038 | 0.0426 | 3.0000 | 3.0000 | -0.7873 | -1.0308 | -0.5449 |
| no_ffill | outage-CO-6 | full | persistence | 10.5213 | 10.5213 | 0.0000 | 2.0000 | 2.0000 | 0.0000 | 0.0000 | 0.0000 |
| no_ffill | outage-CO-6 | full | xgboost | 9.9709 | 9.9693 | 0.0157 | 1.0000 | 1.0000 | 0.5504 | 0.3113 | 0.7480 |
| no_ffill | outage-CO-12 | affected | gru | 15.0289 | 16.5068 | -8.9533 | 4.0000 | 4.0000 | -4.2087 | -5.8057 | -2.7232 |
| no_ffill | outage-CO-12 | affected | mlp | 11.6525 | 11.5166 | 1.1793 | 3.0000 | 3.0000 | -0.8323 | -1.0938 | -0.5863 |
| no_ffill | outage-CO-12 | affected | persistence | 10.8202 | 10.8202 | 0.0000 | 2.0000 | 2.0000 | 0.0000 | 0.0000 | 0.0000 |
| no_ffill | outage-CO-12 | affected | xgboost | 10.2882 | 10.2264 | 0.6045 | 1.0000 | 1.0000 | 0.5320 | 0.2859 | 0.7220 |
| no_ffill | outage-CO-12 | full | gru | 16.0246 | 16.0955 | -0.4410 | 4.0000 | 4.0000 | -5.5032 | -7.3339 | -3.8546 |
| no_ffill | outage-CO-12 | full | mlp | 11.3103 | 11.3038 | 0.0576 | 3.0000 | 3.0000 | -0.7890 | -1.0329 | -0.5469 |
| no_ffill | outage-CO-12 | full | persistence | 10.5213 | 10.5213 | 0.0000 | 2.0000 | 2.0000 | 0.0000 | 0.0000 | 0.0000 |
| no_ffill | outage-CO-12 | full | xgboost | 9.9723 | 9.9693 | 0.0298 | 1.0000 | 1.0000 | 0.5490 | 0.3095 | 0.7462 |
| no_ffill | outage-TEMP-6 | affected | gru | 17.1346 | 16.5624 | 3.4546 | 4.0000 | 4.0000 | -6.2560 | -8.2831 | -4.3326 |
| no_ffill | outage-TEMP-6 | affected | mlp | 12.5952 | 11.6275 | 8.3220 | 3.0000 | 3.0000 | -1.7166 | -2.0600 | -1.4045 |
| no_ffill | outage-TEMP-6 | affected | persistence | 10.8786 | 10.8786 | 0.0000 | 2.0000 | 2.0000 | 0.0000 | 0.0000 | 0.0000 |
| no_ffill | outage-TEMP-6 | affected | xgboost | 10.7722 | 10.3225 | 4.3562 | 1.0000 | 1.0000 | 0.1064 | -0.2067 | 0.3642 |
| no_ffill | outage-TEMP-6 | full | gru | 16.1183 | 16.0955 | 0.1413 | 4.0000 | 4.0000 | -5.5970 | -7.4469 | -3.9277 |
| no_ffill | outage-TEMP-6 | full | mlp | 11.3423 | 11.3038 | 0.3404 | 3.0000 | 3.0000 | -0.8209 | -1.0653 | -0.5788 |
| no_ffill | outage-TEMP-6 | full | persistence | 10.5213 | 10.5213 | 0.0000 | 2.0000 | 2.0000 | 0.0000 | 0.0000 | 0.0000 |
| no_ffill | outage-TEMP-6 | full | xgboost | 9.9872 | 9.9693 | 0.1793 | 1.0000 | 1.0000 | 0.5341 | 0.2934 | 0.7327 |
| no_ffill | outage-TEMP-12 | affected | gru | 17.2297 | 16.5068 | 4.3797 | 4.0000 | 4.0000 | -6.4095 | -8.3898 | -4.5841 |
| no_ffill | outage-TEMP-12 | affected | mlp | 13.6987 | 11.5166 | 18.9471 | 3.0000 | 3.0000 | -2.8785 | -3.3164 | -2.4710 |
| no_ffill | outage-TEMP-12 | affected | persistence | 10.8202 | 10.8202 | 0.0000 | 2.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 |
| no_ffill | outage-TEMP-12 | affected | xgboost | 11.1090 | 10.2264 | 8.6306 | 1.0000 | 2.0000 | -0.2888 | -0.5963 | -0.0341 |
| no_ffill | outage-TEMP-12 | full | gru | 16.1302 | 16.0955 | 0.2157 | 4.0000 | 4.0000 | -5.6089 | -7.4562 | -3.9416 |
| no_ffill | outage-TEMP-12 | full | mlp | 11.4085 | 11.3038 | 0.9268 | 3.0000 | 3.0000 | -0.8872 | -1.1343 | -0.6460 |
| no_ffill | outage-TEMP-12 | full | persistence | 10.5213 | 10.5213 | 0.0000 | 2.0000 | 2.0000 | 0.0000 | 0.0000 | 0.0000 |
| no_ffill | outage-TEMP-12 | full | xgboost | 10.0117 | 9.9693 | 0.4250 | 1.0000 | 1.0000 | 0.5096 | 0.2676 | 0.7076 |
