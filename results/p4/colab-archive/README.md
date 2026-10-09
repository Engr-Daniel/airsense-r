# Completed P4 Colab run archive

Six completed run branches were consolidated on 2026-10-09 before branch deletion.
[index.json](index.json) records each original branch tip, every file checksum,
and the archive location. All 56 registered artifacts were checked against their
original manifest sizes and SHA-256 values. Manifests retain original code,
configuration, dataset, and environment provenance.

Each run directory contains the original manifest and artifacts, plus the original
checkpoint branch marker. This archive preserves final snapshots, not all
intermediate Git commits. Executed notebooks are separately available in notebooks/.

The completed branches are no longer live resume destinations. Use a new run ID
for future runs. Automatic notebook synchronization will still create new
results/<run-id> branches; retain active branches until runs finish and their
outputs have been archived and verified. Simply rerunning a deleted branch's ID
does not automatically restore this archive.

No raw datasets or model binaries are included.
