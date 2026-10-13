# Review saved P6 results

Use `05b_p6_saved_result_verification.ipynb` in a CPU Colab runtime and choose
**Runtime → Run all**. It contains four code cells. The published notebook embeds
its matching verifier revision, result snapshot, run name and storage directory.
No SHA or stage entry is needed. Colab may ask for Drive authorization and access
to the existing `AIRSENSE_GITHUB_TOKEN` secret.

This is a review of saved arrays, not another experiment. It does not train,
perform model inference, download raw observations, or modify the original P6
branch or Drive predictions. It uses a small pinned review environment without
TensorFlow/XGBoost. The original generating revision remains part of the lineage.

The review checks the exact final result snapshot
`464574140e7abb79094935313d6f3eb44fce3a93`, verifies that accepted preflight records
are unchanged, checks all Drive bundle bytes against Git references, recomputes
every station/model/seed metric, and independently calculates paired uncertainty.
It reports comparisons on full and outage-affected target sets.

The independent bootstrap constructs frequency weights for each sampled calendar
hour and multiplies those weights by saved errors. It does not call the original
P6 bootstrap or use its error-prefix implementation. The scientific block length,
sampling seed, replicates, pairing, station/seed aggregation and oracle definition
remain unchanged. Numerical verification uses `atol=1e-8`, `rtol=1e-10` for
different floating-point summation orders; these are comparison tolerances, not
changes to forecast replay tolerances or scientific significance thresholds.

## Progress and reconnection

Cell 3 prints file counts, the current condition, and remotely confirmed review
checkpoints. While a calculation is quiet, it reports that the worker is active
every 30 seconds. This is a liveness message, not a claim that another unit has
finished. Its complete log and status are kept under the review checkout's `.tmp`.

- Browser disconnect: reconnect and rerun cell 3. It attaches to the existing
  worker in that runtime rather than launching another copy.
- New runtime: run all four cells. The same review branch is restored; all Drive
  files are verified again, and confirmed condition reviews are reused.
- Stop button: stops the display. The worker continues in that runtime; rerunning
  cell 3 reconnects. A failed worker produces a visible FAILED state and log.
- Runtime loss: remotely confirmed condition reviews survive. The in-flight
  review may repeat. Drive read/mount failures must be resolved before resuming.

One runtime only: local OS locks cannot coordinate two independent Colab machines.
Never delete a writer lock. A lock file left behind by a dead process is reusable;
the OS, not the file's existence, decides whether another worker holds it.

Review outputs are published incrementally on
`results/p6-sensors-01-review-01`. Original predictions stay in
`MyDrive/AirSense-R/model-checkpoints/p6-artifacts/p6-sensors-01`.
The final cell verifies and displays the completed review record. Save its executed
notebook for inspection before declaring P6 scientifically accepted.

## Scope of the interface update

Notebook 05 remains the historical advanced experiment template. Notebook 05b is
the simplified next step for the existing completed run. The reconnectable job
controller is reusable for future experiment notebooks; P7's interface has not
yet been built. This avoids relaunching a completed P6 experiment just to change
its interface. Live Colab verification remains pending until the user runs 05b.
