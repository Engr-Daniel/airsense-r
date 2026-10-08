# Data policy — remote only

AirSense-R does **not** require a permanent local copy of the raw Beijing dataset.

The authoritative source is the UCI Machine Learning Repository:

- Dataset: Beijing Multi-Site Air Quality (ID 501)
- DOI: `10.24432/C5RK5G`
- Page: <https://archive.ics.uci.edu/dataset/501/beijing+multi+site+air+quality+data>
- Runtime archive: <https://archive.ics.uci.edu/static/public/501/beijing+multi+site+air+quality+data.zip>

`python scripts/run_data_audit.py` streams the archive into a temporary directory,
computes an acquisition SHA-256, recursively extracts it, audits the station files, and
then deletes all raw bytes automatically. Only small audit reports are retained in
`audit/`.

The `data/raw/` and `data/processed/` directories remain empty placeholders for users
who later choose an alternative workflow. They are not required for the default study.
