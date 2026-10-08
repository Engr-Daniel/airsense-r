# P2 External Cross-Checks

These values are **secondary consistency checks**, not substitutes for AirSense-R's runtime audit of the authoritative UCI bytes.

## Official UCI metadata

UCI dataset 501 states that the dataset contains 420,768 hourly observations from 12 nationally controlled Beijing air-quality stations from 2013-03-01 through 2017-02-28. It includes six pollutants, meteorological variables, and missing values encoded as `NA`.

Source: <https://archive.ics.uci.edu/dataset/501/beijing+multi+site+air+quality+data>

## Published station-variable missingness check

A 2025 Scientific Reports paper reports the following missing-value counts for ten of the UCI station files:

| Station | PM2.5 | PM10 | SO2 | NO2 | CO | O3 | TEMP | PRES | DEWP | RAIN | wd | WSPM |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Aotizhongxin | 925 | 718 | 935 | 1023 | 1776 | 1719 | 20 | 20 | 20 | 20 | 81 | 14 |
| Changping | 774 | 582 | 628 | 667 | 1521 | 604 | 53 | 50 | 53 | 51 | 140 | 43 |
| Dongsi | 750 | 553 | 663 | 1601 | 3197 | 664 | 20 | 20 | 20 | 20 | 78 | 14 |
| Guanyuan | 616 | 429 | 474 | 659 | 1753 | 1173 | 20 | 20 | 20 | 20 | 81 | 14 |
| Huairou | 953 | 777 | 980 | 1639 | 1422 | 1151 | 51 | 53 | 53 | 55 | 302 | 49 |
| Nongzhanguan | 628 | 440 | 446 | 692 | 1206 | 506 | 20 | 20 | 20 | 20 | 78 | 14 |
| Shunyi | 913 | 548 | 1296 | 1365 | 2178 | 1489 | 51 | 51 | 54 | 51 | 483 | 44 |
| Tiantan | 677 | 597 | 1118 | 744 | 1126 | 843 | 20 | 20 | 20 | 20 | 78 | 14 |
| Wanliu | 382 | 284 | 575 | 1070 | 1812 | 2107 | 20 | 20 | 20 | 20 | 123 | 14 |
| Wanshouxigong | 696 | 484 | 669 | 754 | 1297 | 1078 | 19 | 19 | 19 | 19 | 79 | 13 |

Source: *Deep learning framework for hourly air pollutants forecasting using encoding cyclical features across multiple monitoring sites in Beijing*, Scientific Reports (2025): <https://pmc.ncbi.nlm.nih.gov/articles/PMC12216515/>

A separate Gucheng study reports PM2.5=646, PM10=381, SO2=507, NO2=668, CO=1401, O3=729, TEMP=51, PRES=50, DEWP=51, RAIN=43 and WSPM=42 missing values (wind direction excluded from that study's table).

Source: <https://e-journal.unair.ac.id/JISEBI/article/download/47538/26585>

## Why these are not copied into the primary audit output

Published papers may use preprocessing, file subsets, or transformed copies. AirSense-R therefore does not treat secondary counts as canonical. The runtime command:

```bash
python scripts/run_data_audit.py
```

must compute the final counts directly from the current authoritative UCI archive, including Dingling and every other station.

Any discrepancy between runtime UCI results and the published checks must be documented rather than silently reconciled.
