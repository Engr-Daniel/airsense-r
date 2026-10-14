# P7 Colab workflow

P7 evaluates within-Beijing unseen-station generalization under the frozen
protocol. It does not measure a causal site-shift penalty or inter-city transfer.
P5 and P6 are accepted; their models and result branches remain unchanged.

Open `notebooks/06_p7_site_shift_analysis.ipynb` at its published revision in
a CPU Colab runtime and choose **Runtime → Run all**. The four cells are:

1. Clone and install the embedded source revision; verify its fingerprint.
2. Authorize the existing Drive directory and `AIRSENSE_GITHUB_TOKEN` secret.
3. Run or resume automatically, displaying station/model/seed/epoch progress.
4. Display the completion record and results for subsequent independent review.

No SHA, stage, run name or model directory needs to be typed. Google may still
request Drive/secret authorization in a fresh runtime. Use the same Google
account that holds `MyDrive/AirSense-R/model-checkpoints/storage.json`.

## Recovery

After a browser disconnect, reconnect and rerun cell 3. It attaches to the
existing worker instead of starting a second copy. Stopping its output display
also leaves the worker running. A heartbeat confirms the process is present;
epoch/round messages show actual training progress. FAILED includes the real
exception in the saved log. Do not infer success from a stopped execution timer.

If Colab replaced the runtime, open the same published notebook and run all.
The result branch restores confirmed compact checkpoints; Drive restores native
models and prediction shards. Only unfinished units repeat. If a push failed,
the worker stops with local work retained and retries publication on resume.
Incompatible provenance or missing/corrupt Drive files stops execution for review.
Never delete a lock or run two separate Colab runtimes for the same run.

The worker log is in `.tmp/notebook-jobs/p7-sites-01/worker.log`. It is runtime
local; durable scientific outputs are the pushed result branch and Drive files.
The system cannot guarantee retention of an unfinished epoch or bytes that
have not reached persistent storage before a runtime disappears.

## Scientific sequence and cost

The script automatically performs a bounded training-only smoke/recovery check,
then repeats the full frozen search for every held-out station. It freezes all
12 validation selections, replays development predictions with restored native
models, and only then scores held-out final-test targets. A restarted evaluation
process repeats the replay gate; it never reselects models from test performance.

There are **756 learned-model fits**: 54 tuning fits and nine refits per station,
plus the small engineering smoke check. This may require many Colab sessions.
P6 was inference-only, so its runtime is not a guide to P7 runtime. The search
budget is not silently reduced. Keep enough Drive capacity for retained native
snapshots and prediction CSVs; actual usage depends on model serialization.

## Saved outputs and acceptance

All compact artifacts use the single branch `results/p7-sites-01`. Fold prefixes
identify the held-out station. Exact prediction CSVs are stored under
`model-checkpoints/p7-sites-01/predictions/<station>/`; Git holds SHA-256 and
byte-count references. Native models use separate per-station directories.
Prediction shards preserve decimal labels via round-trip float parsing.

Final outputs include station/seed metrics, equal-station metrics, fold-specific
selection/rank/regret results, paired temporal-bootstrap intervals, a station
comparison figure and a dashboard payload. Runtime copies go to
`figures/p7-runs/p7-sites-01/` and `docs/data/p7-runs/p7-sites-01/`.

The aggregate selection regret averages each station's selected-minus-oracle
MAE. The oracle is descriptive. Policy-minus-fixed-family differences are
reported separately because the validation choice can vary by held-out station.
See [execution decisions](../research/P7_IMPLEMENTATION_DECISIONS.md).

When cell 4 displays **P7 EXECUTION COMPLETE**, save the executed notebook
separately and report completion. That record explicitly leaves scientific
acceptance pending independent checks of Drive files, lineage, metrics and
uncertainty. Do not proceed to P8 solely because the cells succeeded.
