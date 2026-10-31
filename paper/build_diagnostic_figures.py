"""Render additional manuscript figures from accepted evidence, without inference."""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from airsense_r.evaluation.p6_verify import Snapshot

ROOT = Path(__file__).resolve().parents[1]
MODELS = ["persistence", "xgboost", "mlp", "gru"]
LABELS = ["Persistence", "XGBoost", "MLP", "GRU"]
COLORS = ["#222222", "#0072B2", "#D55E00", "#009E73"]


def condition_label(name: str) -> str:
    """Use readable intervention names instead of internal run identifiers."""
    parts = name.split("-")
    if parts[0] == "random_dropout":
        return f"Random dropout {parts[1]}%"
    if parts[0] == "noise":
        return f"Noise {int(parts[1])}%"
    channel = {"TEMP": "temperature", "NO2": "NO₂", "CO": "CO"}[parts[1]]
    return f"Loss of {channel}" if parts[0] == "whole" else f"{channel} outage {parts[2]} h"


def build(directory: Path, preview: Path | None = None) -> None:
    """Validate acceptance and record every plotted value and generated checksum."""
    acceptance_path = ROOT / "results/p8/final_acceptance.json"
    acceptance = json.loads(acceptance_path.read_bytes())
    snapshot = Snapshot(directory)
    if sha256(snapshot.raw_manifest).hexdigest() != acceptance["manifest_sha256"]:
        raise ValueError("P8 input is not the accepted snapshot")
    target_path = ROOT / "results/p9-target-history/final_acceptance.json"
    target = json.loads(target_path.read_bytes())
    if target["status"] != "P9_target_history_accepted":
        raise ValueError("Target-history evidence is not accepted")
    clean_path = ROOT / "results/p5/corrected_acceptance.json"
    clean = json.loads(clean_path.read_bytes())
    if not clean["accepted"]:
        raise ValueError("Clean evidence is not accepted")
    out = ROOT / "paper/overleaf/figures"
    out.mkdir(parents=True, exist_ok=True)
    if preview:
        preview.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 10, "pdf.fonttype": 42, "axes.spines.top": False,
                         "axes.spines.right": False})
    evidence = {"p8_result_commit": acceptance["result_commit"],
        "p8_manifest_sha256": sha256(snapshot.raw_manifest).hexdigest(),
        "target_history_result_commit": target["result_commit"],
        "target_history_review_commit": target["review_commit"],
        "input_receipts": {p.relative_to(ROOT).as_posix(): sha256(p.read_bytes()).hexdigest()
                           for p in [acceptance_path, target_path, clean_path]},
        "builder_sha256": sha256(Path(__file__).read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
        "figures": {}, "scope": "Presentation of accepted summaries; no fitting or new inference."}

    def save(fig, name: str, data: dict) -> None:
        fig.savefig(out / f"{name}.pdf", bbox_inches="tight",
                    metadata={"Creator": "AirSense-R", "CreationDate": None, "ModDate": None})
        if preview:
            fig.savefig(preview / f"{name}.png", dpi=160, bbox_inches="tight")
        plt.close(fig)
        evidence["figures"][name] = {"pdf_sha256": sha256((out / f"{name}.pdf").read_bytes()).hexdigest(),
                                    "plotted_data": data}

    reports = snapshot.json("sensor-accepted-uncertainty.json")["reports"]
    primary = [r for r in reports if r["policy"] == "primary"]
    assert len(primary) == 15
    order = [r["condition"]["id"] for r in primary]
    ranks = np.array([[next(m["stress_rank"] for m in r["scopes"]["full"]["metrics"]
                           if m["model"] == model) for model in MODELS] for r in primary])
    fig, axes = plt.subplots(1, 2, figsize=(11, 6.4), gridspec_kw={"width_ratios": [1, 1.2]},
                             constrained_layout=True)
    ax = axes[0]
    ax.imshow(ranks, vmin=1, vmax=4, cmap="Blues_r", aspect="auto")
    for (i, j), value in np.ndenumerate(ranks):
        ax.text(j, i, f"{value:g}", ha="center", va="center", color="white" if value < 2 else "black")
    ax.set(xticks=np.arange(4), xticklabels=LABELS, yticks=np.arange(15),
           yticklabels=[condition_label(n) for n in order], title="(a) Numerical rank — primary imputation")
    ax.tick_params(axis="x", labelrotation=20)
    intervals = []
    for policy, offset, color, label in [("primary", -.13, COLORS[1], "Primary"),
                                        ("no_ffill", .13, COLORS[2], "No forward fill")]:
        rows = []
        for name in order:
            r = next(x for x in reports if x["policy"] == policy and x["condition"]["id"] == name)
            u = r["scopes"]["full"]["uncertainty"]
            assert u["available"]
            q = u["selection_regret"]
            rows.append([q["estimate"], q["ci_low"], q["ci_high"]])
        a = np.array(rows)
        axes[1].errorbar(a[:, 0], np.arange(15) + offset,
                        xerr=np.array([a[:, 0]-a[:, 1], a[:, 2]-a[:, 0]]),
                        fmt="o", markersize=4, color=color, label=label, capsize=2)
        intervals.append({"policy": policy, "values_estimate_low_high": rows})
    axes[1].axvline(1, color="#666666", ls="--", label="Practical threshold")
    axes[1].set(ylim=(14.5, -.5), yticks=np.arange(15), yticklabels=[], xlim=(-.04, 1.08),
                xlabel="Persistence selection regret (µg/m³)", title="(b) Decision cost — 95% pointwise intervals")
    axes[1].legend(loc="upper right", fontsize=9)
    save(fig, "rank_and_regret", {"conditions": order, "models": MODELS,
         "primary_ranks": ranks.tolist(), "regret": intervals,
         "note": "All 15 primary conditions; full period only. Rank 1 is lowest MAE; rank is not equivalence."})

    fig, axes = plt.subplots(1, 3, figsize=(11.8, 3.8), constrained_layout=True, sharey=True)
    panel_data = []
    for ax, scope, kind, title in zip(axes, ["full", "full", "affected"],
            ["dropout", "outage", "outage"],
            ["(a) Random dropout — full period", "(b) Outage — full period", "(c) Outage — affected histories"]):
        levels = [0, 10, 30, 50] if kind == "dropout" else [6, 12]
        matrix = []
        for model, label, color in zip(MODELS, LABELS, COLORS):
            values = []
            for level in levels:
                metrics = clean["metrics"] if level == 0 else next(r["metrics"] for r in target["summaries"]
                    if r["condition"] == f"pm25-{kind}-{level}" and r["scope"] == scope)
                values.append(next(m["mae"] for m in metrics if m["model"] == model))
            matrix.append(values)
            ax.plot(levels, values, "o-", color=color, label=label, linewidth=1.7, markersize=4)
        ax.set(title=title, xticks=levels, xlabel="PM2.5 dropout (%)" if kind == "dropout" else "PM2.5 outage (hours)", ylim=(0, 29))
        ax.grid(axis="y", alpha=.2)
        panel_data.append({"kind": kind, "scope": scope, "levels": levels, "models": MODELS, "mae": matrix})
    axes[0].set_ylabel("MAE (µg/m³)")
    axes[0].legend(fontsize=8, loc="upper left", ncol=2)
    save(fig, "target_history_accuracy", {"panels": panel_data,
        "note": "Post-results extension; primary imputation. Point estimates only; lines connect tested levels, not fitted response curves. Affected masks differ between outage conditions."})

    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2), constrained_layout=True)
    data = []
    for ax, key, order, title in [(axes[0], "concentration_band", ["<50", "50 to <100", "100 to <200", ">=200"],
                                  "(a) Observed target PM2.5 (µg/m³)"),
                                 (axes[1], "season", ["DJF", "MAM", "JJA", "SON"], "(b) Calendar season")]:
        frame = pd.read_csv(directory / f"p7-site-shift-{key}.csv", float_precision="round_trip")
        counts = [int(frame.loc[frame[key] == v, "targets"].iloc[0]) for v in order]
        for model, label, color in zip(MODELS, LABELS, COLORS):
            values = frame[frame.model == model].set_index(key).loc[order, "mae"].to_numpy()
            ax.plot(np.arange(4), values, "o-", color=color, label=label)
        ax.set(xticks=np.arange(4), xticklabels=[f"{v}\nn={n:,}" for v, n in zip(order, counts)],
               ylim=(0, 30), title=title, ylabel="LOSO MAE (µg/m³)")
        ax.grid(axis="y", alpha=.2)
        data.append({"group": key, "records": frame.to_dict(orient="records")})
    axes[1].legend(fontsize=9, ncol=2, loc="upper left")
    save(fig, "descriptive_error_regimes", {"groups": data,
        "note": "Post-results descriptive diagnostics; equal-station summaries, no subgroup confidence intervals. Counts are distinct station-target observations, not independent replications or per-model totals. Bands are not AQI categories."})
    (ROOT / "paper/diagnostic_figure_evidence.json").write_text(json.dumps(evidence, indent=2)+"\n", encoding="utf-8")
    print("Rendered three evidence-linked figures; accepted artifacts unchanged.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--p8-directory", type=Path, required=True)
    parser.add_argument("--preview-directory", type=Path)
    args = parser.parse_args()
    build(args.p8_directory.resolve(), args.preview_directory)
