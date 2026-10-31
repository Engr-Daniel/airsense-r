/* AirSense-R Reliability Explorer.
   Presents accepted, checksum-verified evidence exported by scripts/build_explorer_data.py.
   No live data, inference or model switching happens here. */
(function () {
  "use strict";
  const C = window.AirCharts;
  const FROZEN_THRESHOLD = 1.0;
  const MODELS = ["persistence", "xgboost", "mlp", "gru"];
  const MODEL_NAME = { persistence: "Persistence", xgboost: "XGBoost", mlp: "MLP", gru: "GRU" };
  const STATUS = {
    within: { cls: "good", label: "Within threshold", short: "Within" },
    within_ci_crosses: { cls: "warning", label: "Within · CI crosses threshold", short: "Within, CI crosses" },
    above_ci_crosses: { cls: "serious", label: "Above · CI crosses threshold", short: "Above, CI crosses" },
    above: { cls: "critical", label: "Above threshold", short: "Above" },
  };
  const STATUS_COLOR = { good: "var(--status-good)", warning: "var(--status-warning)", serious: "var(--status-serious)", critical: "var(--status-critical)" };
  const REPO = "https://github.com/Engr-Daniel/airsense-r";

  const state = {
    data: null, windows: null, threshold: FROZEN_THRESHOLD, route: "overview",
    sensors: { policy: "primary", group: "random_dropout", id: "random_dropout-30", scope: "full" },
    target: { id: "pm25-outage-12", scope: "affected" },
    stations: { selected: "Shunyi" },
    clean: { station: "Aotizhongxin", window: "winter", seed: "42", step: 0 },
    failure: { source: "clean", dim: "band", measure: "mae" },
  };

  /* ---------- small DOM helpers (text nodes only, never innerHTML for data) ---------- */
  function h(tag, props, ...children) {
    const node = document.createElement(tag);
    for (const [k, v] of Object.entries(props || {})) {
      if (v === undefined || v === null || v === false) continue;
      if (k === "class") node.className = v;
      else if (k.startsWith("on")) node.addEventListener(k.slice(2), v);
      else if (k === "style") node.style.cssText = v;
      else node.setAttribute(k, v === true ? "" : v);
    }
    for (const c of children.flat()) {
      if (c === null || c === undefined || c === false) continue;
      node.appendChild(c instanceof Node ? c : document.createTextNode(String(c)));
    }
    return node;
  }
  const icon = (paths, size) => {
    const s = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    s.setAttribute("width", size || 14); s.setAttribute("height", size || 14); s.setAttribute("viewBox", "0 0 24 24");
    s.setAttribute("fill", "none"); s.setAttribute("stroke", "currentColor"); s.setAttribute("stroke-width", "2.4");
    s.setAttribute("stroke-linecap", "round"); s.setAttribute("stroke-linejoin", "round"); s.setAttribute("aria-hidden", "true");
    for (const d of [].concat(paths)) { const p = document.createElementNS("http://www.w3.org/2000/svg", "path"); p.setAttribute("d", d); s.appendChild(p); }
    return s;
  };
  const ICONS = {
    good: "M5 12.5l4.5 4.5L19 7.5",
    warning: ["M12 7v6", "M12 17h.01"],
    serious: ["M12 5l8 14H4z", "M12 10v4", "M12 17h.01"],
    critical: ["M7 7l10 10", "M17 7L7 17"],
    info: ["M12 11v6", "M12 7h.01"],
  };
  function statusIconBox(cls, size) {
    const box = h("span", { style: `display:inline-grid;place-items:center;width:${size || 18}px;height:${size || 18}px;border-radius:50%;background:${STATUS_COLOR[cls]};color:${cls === "warning" ? "#0b0b0b" : "#fff"};flex:none` });
    box.appendChild(icon(ICONS[cls], (size || 18) - 6));
    return box;
  }
  function statusBadge(key, short) {
    const s = STATUS[key];
    return h("span", { class: `status status-${s.cls}`, title: s.label }, statusIconBox(s.cls, 16), short ? s.short : s.label);
  }
  const f3 = v => C.fmt(v, 3);
  const f2 = v => C.fmt(v, 2);
  const unit = " µg/m³";
  const modelColor = m => `var(--series-${m})`;
  const swatch = m => h("span", { class: "swatch", style: `background:${modelColor(m)}` });
  const modelCell = m => h("span", { class: "model-cell" }, swatch(m), MODEL_NAME[m]);
  const ciText = ci => (ci ? `${f3(ci[0])} – ${f3(ci[1])}` : "not available");

  /* ---------- status logic: identical rule to airsense_r.explorer.regret_status ---------- */
  function statusOf(est, ci, threshold) {
    const t = threshold ?? state.threshold;
    const within = est <= t + 1e-12;
    if (!ci) return within ? "within" : "above";
    if (within) return ci[1] <= t + 1e-12 ? "within" : "within_ci_crosses";
    return ci[0] > t + 1e-12 ? "above" : "above_ci_crosses";
  }
  const isWithin = key => key === "within" || key === "within_ci_crosses";

  function interpretation(est, ci, family) {
    const name = MODEL_NAME[family] || family;
    const t = C.fmt(state.threshold, 1);
    const key = statusOf(est, ci);
    if (est === 0 && (!ci || ci[1] === 0)) return `${name} is the retrospective oracle in this scope (regret 0): retaining the validation-selected family costs nothing here.`;
    return {
      within: `The validation-selected family remains practically competitive: point regret and the full 95% interval stay at or below ${t} µg/m³.`,
      within_ci_crosses: `Point regret is within ${t} µg/m³, but the 95% interval extends above it, so practical competitiveness is not established with confidence.`,
      above_ci_crosses: `The point estimate exceeds ${t} µg/m³, although the 95% interval crosses the threshold.`,
      above: `The original validation-selected family is no longer practically competitive in this scope: point regret and the entire 95% interval exceed ${t} µg/m³.`,
    }[key];
  }

  function alertFor(est, ci, family, title) {
    const key = statusOf(est, ci);
    const cls = STATUS[key].cls;
    return h("div", { class: `alert alert-${cls}`, role: "status" }, statusIconBox(cls, 26),
      h("div", {}, h("strong", {}, title || STATUS[key].label), h("p", {}, interpretation(est, ci, family))));
  }

  function metric(label, value, unitText, note) {
    return h("div", { class: "card metric" }, h("span", { class: "metric-label" }, label),
      h("span", { class: "metric-value num" }, value, unitText ? h("span", { class: "metric-unit" }, unitText) : null),
      note ? h("span", { class: "metric-note" }, note) : null);
  }

  function seg(label, options, current, onChange) {
    return h("div", { class: "field" }, label,
      h("div", { class: "seg", role: "group", "aria-label": label },
        options.map(o => h("button", { type: "button", "aria-pressed": String(o.value === current), disabled: o.disabled, onclick: () => onChange(o.value) }, o.label))));
  }

  function legend(models, extra) {
    return h("div", { class: "legend" }, (extra || []).concat(models.map(m => h("span", {}, swatch(m), MODEL_NAME[m]))));
  }

  function chartBox(draw, ariaLabel) {
    const div = h("div", { class: "chart", role: "figure", "aria-label": ariaLabel || "" });
    pendingDraws.push(() => draw(div));
    return div;
  }
  let pendingDraws = [];

  function table(headers, rows, opts) {
    return h("div", { class: "table-wrap" }, h("table", {},
      h("thead", {}, h("tr", {}, headers.map(x => h("th", { class: x.r ? "r" : null, scope: "col" }, x.label || x)))),
      h("tbody", {}, rows.map(r => h("tr", { class: opts && opts.selected && opts.selected(r) ? "is-selected" : null },
        r.cells.map((c, i) => h("td", { class: headers[i].r ? "r" : null }, c)))))));
  }
  function tableView(headers, rows) {
    return h("details", { class: "table-view" }, h("summary", {}, "View as table"), table(headers, rows));
  }

  function sensitivityNote() {
    if (state.threshold === FROZEN_THRESHOLD) return null;
    return h("div", { class: "alert alert-info", style: "margin-bottom:16px" }, statusIconBox("warning", 22),
      h("div", {}, h("strong", {}, `Sensitivity view: threshold ${C.fmt(state.threshold, 1)} µg/m³`),
        h("p", {}, "The frozen protocol threshold is 1.0 µg/m³. Other thresholds are post-results interpretation aids; they do not change the frozen selection or the confirmatory conclusions.")));
  }

  /* ---------- evidence accessors ---------- */
  const D = () => state.data;
  const sensorReport = (policy, id) => D().sensors.find(s => s.policy === policy && s.id === id);
  const targetScope = (id, scope) => D().target_history.find(t => t.id === id && t.scope === scope);
  const primaryFull = () => D().sensors.filter(s => s.policy === "primary").map(s => ({ s, v: s.scopes.full }));
  const worstTarget = () => D().target_history.reduce((a, b) => (b.selection_regret > a.selection_regret ? b : a));

  /* ======================= VIEWS ======================= */
  function viewOverview() {
    const d = D();
    const c = d.clean;
    const sensors = primaryFull();
    const sensorsWithin = sensors.filter(x => isWithin(statusOf(x.v.selection_regret, x.v.regret_ci))).length;
    const stations = d.site_shift.stations;
    const stationsWithin = stations.filter(s => isWithin(statusOf(s.selection_regret, s.regret_ci))).length;
    const worst = worstTarget();
    const cleanKey = statusOf(c.selection_regret, c.regret_ci);
    const worstKey = statusOf(worst.selection_regret, worst.regret_ci);
    const countBadge = (n, total) => n === total ? statusBadge("within")
      : h("span", { class: "status status-serious" }, statusIconBox("serious", 16), `${total - n} above threshold`);

    const tile = (href, label, value, note, badge) => h("a", { class: "tile", href },
      h("span", { class: "tile-label" }, label), h("span", { class: "tile-value num" }, value), h("span", { class: "tile-note" }, note), h("span", {}, badge));

    const groups = [
      { label: "Clean benchmark", sub: "1 scope", points: [pt("Clean test year", c.selection_regret, c.regret_ci, "#/clean")] },
      { label: "Auxiliary sensors", sub: `${sensors.length} full-period`, points: sensors.map(x => pt(x.s.label, x.v.selection_regret, x.v.regret_ci, `#/sensors?c=${x.s.id}&s=full`)) },
      { label: "Outage windows", sub: "auxiliary, affected", points: d.sensors.filter(s => s.policy === "primary" && s.scopes.affected).map(s => pt(s.label + " · affected windows", s.scopes.affected.selection_regret, s.scopes.affected.regret_ci, `#/sensors?c=${s.id}&s=affected`)) },
      { label: "PM₂.₅ history", sub: `${d.target_history.length} scopes`, points: d.target_history.map(t => pt(`${t.label} · ${t.scope === "affected" ? "affected windows" : "full period"}`, t.selection_regret, t.regret_ci, `#/target?c=${t.id}&s=${t.scope}`)) },
      { label: "Unseen stations", sub: `${stations.length} LOSO folds`, points: stations.map(s => pt(s.station, s.selection_regret, s.regret_ci, `#/stations?st=${s.station}`)) },
    ];

    return [
      sensitivityNote(),
      h("div", { class: "page-head" },
        h("p", { class: "eyebrow" }, "Reliability decision support"),
        h("h1", {}, "Is the validation-selected forecaster still defensible?"),
        h("p", { class: "lede" }, "AirSense-R freezes one 1-hour-ahead PM₂.₅ forecasting family using clean validation data, then asks what that decision costs when conditions change: degraded auxiliary sensors, missing PM₂.₅ history and stations never seen in training.")),
      h("section", { class: "card decision", "aria-label": "Selected forecasting choice" },
        h("div", { class: "decision-main" },
          h("p", { class: "eyebrow" }, "Validation-selected family"),
          h("div", { class: "decision-model" }, MODEL_NAME[c.selected_family]),
          h("div", { style: "display:flex;gap:6px;flex-wrap:wrap;margin:8px 0" },
            h("span", { class: "chip" }, "Frozen before test access"), h("span", { class: "chip" }, "1-h horizon · 24-h lookback"), h("span", { class: "chip" }, `${c.stations} Beijing stations`)),
          h("p", {}, `Clean validation MAE was within 1.0 µg/m³ of the lowest (${MODEL_NAME[c.validation_winner]}), so the frozen simplicity order selected ${MODEL_NAME[c.selected_family]}.`),
          h("p", {}, h("a", { href: "#/clean?flow=1", style: "color:#7dd3c8;font-weight:600" }, "Why was this model selected? →"))),
        h("div", { class: "decision-tiles" },
          tile("#/clean", "Clean benchmark", `${f3(c.selection_regret)}${unit}`, `Regret vs numerical winner ${MODEL_NAME[c.test_winner]} · 95% CI ${ciText(c.regret_ci)}`, statusBadge(cleanKey)),
          tile("#/sensors", "Auxiliary sensor degradation", `${sensorsWithin} / ${sensors.length}`, "Full-period conditions with point regret within threshold (primary imputation)", countBadge(sensorsWithin, sensors.length)),
          tile("#/stations", "Unseen stations", `${stationsWithin} / ${stations.length}`, `Station point estimates within threshold · mean regret ${f3(d.site_shift.mean_selection_regret.estimate)}${unit}`, countBadge(stationsWithin, stations.length)),
          tile(`#/target?c=${worst.id}&s=${worst.scope}`, "Target-history warning", `${f3(worst.selection_regret)}${unit}`, `${worst.label} · ${worst.scope === "affected" ? "outage-affected windows" : "full period"} · 95% CI ${ciText(worst.regret_ci)}`, statusBadge(worstKey)))),
      isWithin(worstKey) ? null : h("div", { style: "margin-top:16px" }, alertFor(worst.selection_regret, worst.regret_ci, worst.selected_family,
        `Reliability boundary: ${worst.label}, ${worst.scope === "affected" ? "outage-affected windows" : "full period"}`)),
      h("section", { class: "card" },
        h("div", { class: "card-head" }, h("div", {}, h("h2", {}, "Selection regret across every evaluated scope"),
          h("p", { class: "sub" }, "Each dot is one accepted scope. Regret = selected-family MAE minus the best family's MAE in that scope. Click a dot to open its evidence."))),
        statusLegend(),
        chartBox(div => C.strip(div, { groups, threshold: state.threshold, label: "Selection regret by evidence group" }), "Strip chart of selection regret across all evaluated scopes"),
        tableView([{ label: "Evidence" }, { label: "Scope" }, { label: "Regret", r: 1 }, { label: "95% CI", r: 1 }, { label: "Status" }],
          groups.flatMap(g => g.points.map(p => ({ cells: [g.label, p.label, f3(p.est), p.lo === null ? "—" : `${f3(p.lo)} – ${f3(p.hi)}`, p.statusText] }))))),
      h("div", { class: "grid g3" },
        h("div", { class: "card prose" }, h("h3", {}, "Selection regret"), h("p", {}, "The extra error accepted by keeping the frozen choice instead of the model that turned out best in hindsight (the retrospective oracle). Regret 0 means the frozen choice was best.")),
        h("div", { class: "card prose" }, h("h3", {}, "Practical threshold"), h("p", {}, "1.0 µg/m³ was frozen before final evaluation. Regret at or below it is treated as a practical near-tie; above it, the choice is no longer practically competitive. Intervals are paired 24-hour block-bootstrap 95% CIs.")),
        h("div", { class: "card prose" }, h("h3", {}, "What this is not"), h("p", {}, "Not live monitoring. No real-time sensors, forecasts, alerts or model switching are shown. All values are offline research evidence from a fixed historical test year. ", h("a", { href: "#/deployment" }, "See the deployment concept.")))),
    ];

    function pt(label, est, ci, href) {
      const key = statusOf(est, ci);
      return { label, est, lo: ci ? ci[0] : null, hi: ci ? ci[1] : null, color: STATUS_COLOR[STATUS[key].cls], statusText: STATUS[key].label, href };
    }
  }

  function statusLegend() {
    return h("div", { class: "legend" }, Object.values(STATUS).map(s => h("span", {}, statusIconBox(s.cls, 14), s.label)));
  }

  function viewClean() {
    const c = D().clean;
    const val = c.validation_mae, test = Object.fromEntries(c.test.map(t => [t.model, t]));
    const maxAll = Math.max(...Object.values(val), ...c.test.map(t => t.mae));
    const byVal = MODELS.slice().sort((a, b) => val[a] - val[b]);
    const byTest = MODELS.slice().sort((a, b) => test[a].mae - test[b].mae);
    const bestVal = val[c.validation_winner];
    const steps = [
      ["Training", "Each learned family is fitted on 2013-03-02 → 2015-02-28 targets only. Preprocessing (imputation medians, scalers, categories) is fitted on training data."],
      ["Hyperparameter tuning", "Three expanding temporal folds inside the training period pick each family's configuration by mean fold MAE: " +
        Object.entries(c.selected_configs).map(([m, cfg]) => `${MODEL_NAME[m]} → ${cfg.id}`).join(", ") + ". Persistence has no parameters."],
      ["Clean validation", "All four candidates are scored on the same clean validation year (2015-03-01 → 2016-02-29), station MAE first, then the unweighted mean over 12 stations and seeds."],
      ["Identify lowest MAE", `${MODEL_NAME[c.validation_winner]} has the lowest aggregate validation MAE: ${f3(bestVal)}${unit}.`],
      ["Check the 1.0 µg/m³ near-tie", "Families within 1.0 µg/m³ of the lowest: " + c.near_ties.map(m => `${MODEL_NAME[m]} (+${f3(c.validation_gap_to_best[m])})`).join(", ") + `. GRU is +${f3(c.validation_gap_to_best.gru)} and is excluded.`],
      ["Apply the simplicity rule", "Among near-ties, the frozen order persistence → XGBoost → MLP → GRU prefers the simplest family."],
      [`${MODEL_NAME[c.selected_family]} selected`, "The decision rests on validation evidence only; the test year has not been opened."],
      ["Freeze the decision", "Selection is recorded and locked before any final-test or stress outcome is inspected."],
      ["Test under future conditions", `Clean test, sensor degradation, PM₂.₅-history stress and unseen stations all evaluate this frozen choice. On the clean test year it costs ${f3(c.selection_regret)}${unit} against ${MODEL_NAME[c.test_winner]}.`],
    ];
    const step = state.clean.step;
    const flowCard = h("section", { class: "card", id: "flow" },
      h("div", { class: "card-head" }, h("div", {}, h("h2", {}, "Why was this model selected?"), h("p", { class: "sub" }, "Step through the frozen selection rule, using the actual validation values."))),
      h("div", { class: "flow" }, steps.slice(0, step + 1).map(([title, body], i) =>
        h("div", { class: "flow-step done" + (i === 6 ? " key" : "") }, h("span", { class: "flow-num" }, String(i + 1)), h("div", { class: "flow-body" }, h("h3", {}, title), h("p", {}, body))))),
      h("div", { class: "flow-controls" },
        h("button", { class: "btn", type: "button", disabled: step === 0, onclick: () => { state.clean.step = Math.max(0, step - 1); render(); } }, "Back"),
        step < steps.length - 1
          ? h("button", { class: "btn btn-primary", type: "button", onclick: () => { state.clean.step = step + 1; render(); } }, `Next: ${steps[step + 1][0]}`)
          : h("button", { class: "btn", type: "button", onclick: () => { state.clean.step = 0; render(); } }, "Restart"),
        step < steps.length - 1 ? h("button", { class: "btn", type: "button", onclick: () => { state.clean.step = steps.length - 1; render(); } }, "Show all") : null));

    const head = [{ label: "Model" }, { label: "Validation MAE", r: 1 }, { label: "Test MAE", r: 1 }, { label: "Test RMSE", r: 1 }, { label: "Test R²", r: 1 }, { label: "Selected − model (95% CI)", r: 1 }];
    const rows = MODELS.map(m => ({ model: m, cells: [modelCell(m), f3(val[m]), f3(test[m].mae), f3(test[m].rmse), C.fmt(test[m].r2, 3),
      m === c.selected_family ? "selected" : `${f3(test[m].selected_minus_model.estimate)} (${f3(test[m].selected_minus_model.ci_low)} – ${f3(test[m].selected_minus_model.ci_high)})`] }));

    return [
      sensitivityNote(),
      h("div", { class: "page-head" }, h("p", { class: "eyebrow" }, "Clean benchmark"),
        h("h1", {}, "The numerical winner is not the selected family"),
        h("p", { class: "lede" }, `On the untouched clean test year (${c.test_period[0].slice(0, 10)} → ${c.test_period[1].slice(0, 10)}), ${MODEL_NAME[c.test_winner]} has the lowest MAE. The protocol nevertheless retained ${MODEL_NAME[c.selected_family]}, selected on validation data. Selection regret measures the cost.`)),
      h("div", { class: "grid g4" },
        metric("Numerical winner (test)", MODEL_NAME[c.test_winner], null, `MAE ${f3(test[c.test_winner].mae)}${unit}`),
        metric("Validation-selected family", MODEL_NAME[c.selected_family], null, `MAE ${f3(test[c.selected_family].mae)}${unit}`),
        metric("Cost of retaining selection", f3(c.selection_regret), "µg/m³", `95% CI ${ciText(c.regret_ci)}`),
        h("div", { class: "card metric" }, h("span", { class: "metric-label" }, "Decision status"), h("span", { style: "margin:6px 0" }, statusBadge(statusOf(c.selection_regret, c.regret_ci))), h("span", { class: "metric-note" }, `Threshold ${C.fmt(state.threshold, 1)} µg/m³`))),
      h("div", { class: "grid g2" },
        h("section", { class: "card" }, h("h2", {}, "Clean validation MAE"), h("p", { class: "sub" }, `Selection evidence. Near-tie band: up to ${f3(bestVal + 1)}${unit} (lowest + 1.0).`),
          chartBox(div => C.hbar(div, { rows: byVal.map(m => ({ label: MODEL_NAME[m], value: val[m], color: modelColor(m), highlight: m === c.selected_family, extra: [{ label: "Gap to lowest", value: "+" + f3(c.validation_gap_to_best[m]) }, { label: "Near-tie", value: c.near_ties.includes(m) ? "yes" : "no" }] })), max: maxAll, unit: "µg/m³", valueLabel: "Validation MAE" }), "Validation MAE by model")),
        h("section", { class: "card" }, h("h2", {}, "Final clean test MAE"), h("p", { class: "sub" }, "Untouched test year; equal weight per station, mean over seeds."),
          chartBox(div => C.hbar(div, { rows: byTest.map(m => ({ label: MODEL_NAME[m], value: test[m].mae, color: modelColor(m), highlight: m === c.selected_family })), max: maxAll, unit: "µg/m³", valueLabel: "Test MAE" }), "Test MAE by model"))),
      h("section", { class: "card" }, h("h2", {}, "Model comparison"), h("p", { class: "sub" }, "Paired differences are selected-family MAE minus comparator MAE; positive values favour the comparator."),
        table(head, rows, { selected: r => r.model === c.selected_family })),
      flowCard,
      predictionsCard(),
    ];
  }

  function predictionsCard() {
    const card = h("section", { class: "card" });
    const meta = D().prediction_windows;
    const draw = () => {
      card.replaceChildren();
      const w = state.windows;
      const win = w ? w[state.clean.window] : null;
      const stations = win ? Object.keys(win.stations).sort() : [];
      card.append(
        h("div", { class: "card-head" }, h("div", {}, h("h2", {}, "Actual vs predicted PM₂.₅"),
          h("p", { class: "sub" }, "Clean test predictions for fixed calendar weeks (chosen by date, not by error). Learned models are shown one training seed at a time — seeds are never averaged, because an averaged forecast was not evaluated. Persistence is deterministic. Display only; the metrics above use every seed and hour."))),
        h("div", { class: "filters", style: "box-shadow:none" },
          h("label", { class: "field" }, "Station",
            h("select", { onchange: e => { state.clean.station = e.target.value; draw(); } },
              (stations.length ? stations : [state.clean.station]).map(s => h("option", { value: s, selected: s === state.clean.station }, s)))),
          seg("Week", meta.windows.map(k => ({ value: k, label: k[0].toUpperCase() + k.slice(1) })), state.clean.window, v => { state.clean.window = v; draw(); }),
          seg("Training seed (learned models)", meta.training_seeds.map(k => ({ value: String(k), label: String(k) })), state.clean.seed, v => { state.clean.seed = v; draw(); })));
      if (!win) { card.append(h("p", { class: "loading" }, "Loading prediction windows…")); return; }
      const st = win.stations[state.clean.station];
      const x = []; const start = new Date(win.start.replace(" ", "T") + "Z");
      for (let i = 0; i < st.actual.length; i++) x.push(new Date(start.getTime() + i * 3600e3).toISOString().slice(0, 16).replace("T", " "));
      card.append(
        h("div", { class: "legend" }, h("span", {}, h("span", { class: "linekey", style: "background:var(--series-actual);height:3px" }), "Observed"), MODELS.map(m => h("span", {}, h("span", { class: "linekey", style: `background:${modelColor(m)}` }), MODEL_NAME[m]))),
        (() => { const div = h("div", { class: "chart" }); requestAnimationFrame(() => C.lines(div, { x, label: `Observed and predicted PM2.5 at ${state.clean.station}`, series: [{ label: "Observed", values: st.actual, color: "var(--series-actual)", width: 2.5 }].concat(MODELS.map(m => ({ label: MODEL_NAME[m] + (m === "persistence" ? "" : ` (seed ${state.clean.seed})`), values: m === "persistence" ? st[m] : st[m][state.clean.seed], color: modelColor(m), width: 1.6, opacity: .9 }))) })); return div; })(),
        h("p", { class: "sub", style: "margin-top:8px" }, "Times are station timestamps (hourly). Gaps mark hours without an observed target. Training seeds can differ markedly for the neural models — compare seeds before reading one curve as the family's behaviour. ", h("a", { href: "data/clean-prediction-windows.json" }, "Download window data (JSON)")));
    };
    if (!state.windows) {
      fetch("data/clean-prediction-windows.json").then(r => r.json()).then(w => { state.windows = w; draw(); }).catch(() => { card.replaceChildren(h("p", { class: "error" }, "Prediction windows could not be loaded.")); });
    }
    draw();
    return card;
  }

  /* ----- shared scope detail (sensor + target-history) ----- */
  function scopeDetail(scope, title, context) {
    const metrics = scope.metrics;
    const sel = scope.selected_family;
    const head = [{ label: "Model" }, { label: "Stress MAE", r: 1 }, { label: "Matched clean MAE", r: 1 }, { label: "RPD", r: 1 }, { label: "Rank clean → stress", r: 1 }, { label: "Selected − model (95% CI)", r: 1 }];
    const rows = metrics.map(m => ({ model: m.model, cells: [modelCell(m.model), f3(m.mae), f3(m.clean_mae), C.fmt(m.rpd_percent, 1) + "%",
      `${m.clean_rank} → ${m.stress_rank}${scope.oracle_families.includes(m.model) ? " (oracle)" : ""}`,
      m.model === sel ? "selected" : m.selected_minus_model ? `${f3(m.selected_minus_model.estimate)} (${f3(m.selected_minus_model.ci_low)} – ${f3(m.selected_minus_model.ci_high)})` : "—"] }));
    return [
      alertFor(scope.selection_regret, scope.regret_ci, sel, title),
      h("div", { class: "grid g4", style: "margin-top:16px" },
        metric(`${MODEL_NAME[sel]} regret`, f3(scope.selection_regret), "µg/m³", `vs oracle ${scope.oracle_families.map(m => MODEL_NAME[m]).join(", ")}`),
        metric("95% CI", scope.regret_ci ? `${f3(scope.regret_ci[0])} – ${f3(scope.regret_ci[1])}` : "n/a", null, "Paired 24-h block bootstrap"),
        metric("Decision threshold", C.fmt(state.threshold, 1), "µg/m³", state.threshold === FROZEN_THRESHOLD ? "Frozen protocol value" : "Sensitivity view"),
        metric("Rank agreement", C.fmt(scope.kendall_tau_b, 2), null, "Kendall τb, clean vs stressed ranking")),
      h("div", { class: "grid g2" },
        h("section", { class: "card" }, h("h2", {}, "MAE: clean → stressed"), h("p", { class: "sub" }, "Hollow = matched clean MAE; filled = MAE under this condition."),
          legend(MODELS),
          chartBox(div => C.dumbbell(div, { rows: metrics.map(m => ({ label: MODEL_NAME[m.model], a: m.clean_mae, b: m.mae, color: modelColor(m.model), highlight: m.model === sel, extra: [{ label: "RPD", value: C.fmt(m.rpd_percent, 1) + "%" }, { label: "Rank", value: `${m.clean_rank} → ${m.stress_rank}` }] })), aLabel: "Clean MAE", bLabel: "Stressed MAE", label: "Clean versus stressed MAE" }), "Clean versus stressed MAE by model")),
        h("section", { class: "card" }, h("h2", {}, "Model detail"), h("p", { class: "sub" }, context),
          table(head, rows, { selected: r => r.model === sel }))),
    ];
  }

  function viewSensors() {
    const s = state.sensors;
    const groups = [["random_dropout", "Random dropout"], ["channel_loss", "Channel loss"], ["noise", "Measurement noise"], ["outage", "Contiguous outage"]];
    const inGroup = D().sensors.filter(r => r.policy === s.policy && r.group === s.group);
    if (!inGroup.some(r => r.id === s.id)) s.id = inGroup[0].id;
    const report = sensorReport(s.policy, s.id);
    if (!report.scopes[s.scope]) s.scope = "full";
    const scope = report.scopes[s.scope];
    const policyLabel = s.policy === "primary" ? "primary imputation" : "no-forward-fill sensitivity policy";
    const all = D().sensors.filter(r => r.policy === s.policy);
    const forestRows = all.flatMap(r => ["full", "affected"].filter(k => r.scopes[k]).map(k => [k, r.scopes[k]]).map(([k, v]) => {
      const key = statusOf(v.selection_regret, v.regret_ci);
      return { id: r.id, scope: k, group: r.group, label: r.label + (k === "affected" ? " · affected" : ""), est: v.selection_regret, lo: v.regret_ci && v.regret_ci[0], hi: v.regret_ci && v.regret_ci[1], color: STATUS_COLOR[STATUS[key].cls], statusText: STATUS[key].label, highlight: r.id === s.id && k === s.scope };
    }));
    const set = patch => { Object.assign(s, patch); syncHash({ c: s.id, s: s.scope, p: s.policy }); render(); };
    return [
      sensitivityNote(),
      h("div", { class: "page-head" }, h("p", { class: "eyebrow" }, "Sensor stress"),
        h("h1", {}, "Auxiliary sensor degradation"),
        h("p", { class: "lede" }, "Frozen models are re-evaluated, without retraining, on test data where non-target sensors (pollutants and meteorology) are corrupted before window construction. PM₂.₅ history is untouched in these experiments.")),
      h("div", { class: "filters", role: "region", "aria-label": "Sensor stress filters" },
        seg("Imputation policy", [{ value: "primary", label: "Primary" }, { value: "no_ffill", label: "No forward fill (sensitivity)" }], s.policy, v => set({ policy: v })),
        seg("Stress type", groups.map(([v, l]) => ({ value: v, label: l })), s.group, v => set({ group: v, id: D().sensors.find(r => r.policy === s.policy && r.group === v).id, scope: "full" })),
        seg(s.group === "channel_loss" || s.group === "outage" ? "Channel / severity" : "Severity", inGroup.map(r => ({ value: r.id, label: r.group === "outage" ? `${r.channel} ${r.severity}` : r.group === "channel_loss" ? r.channel : r.severity })), s.id, v => set({ id: v })),
        seg("Scope", [{ value: "full", label: "Full period" }, { value: "affected", label: "Affected windows", disabled: !report.scopes.affected }], s.scope, v => set({ scope: v }))),
      scopeDetail(scope, `${report.label} · ${s.scope === "affected" ? "outage-affected windows" : "full period"} · ${policyLabel}`,
        `${report.label}; corruption seeds ${report.seeds.join(", ")}. Persistence reads only past PM₂.₅, so its MAE is unchanged by auxiliary-sensor stress (RPD 0%); regret moves only because other models change.`),
      h("section", { class: "card" }, h("h2", {}, `All auxiliary conditions · ${policyLabel}`), h("p", { class: "sub" }, "Selection regret with 95% CI per condition and scope. Click a row to inspect it."),
        statusLegend(),
        chartBox(div => C.forest(div, { rows: forestRows, threshold: state.threshold, groups: true, label: "Selection regret by sensor condition", onSelect: r => set({ id: r.id, scope: r.scope, group: D().sensors.find(x => x.id === r.id).group }) }), "Selection regret by sensor condition"),
        tableView([{ label: "Condition" }, { label: "Regret", r: 1 }, { label: "95% CI", r: 1 }, { label: "Status" }], forestRows.map(r => ({ cells: [r.label, f3(r.est), r.lo === null || r.lo === undefined ? "—" : `${f3(r.lo)} – ${f3(r.hi)}`, r.statusText] })))),
    ];
  }

  function viewTarget() {
    const t = state.target;
    const ids = [...new Set(D().target_history.map(x => x.id))];
    let scope = targetScope(t.id, t.scope);
    if (!scope) { t.scope = "full"; scope = targetScope(t.id, "full"); }
    const hasAffected = !!targetScope(t.id, "affected");
    const set = patch => { Object.assign(t, patch); if (!targetScope(t.id, t.scope)) t.scope = "full"; syncHash({ c: t.id, s: t.scope }); render(); };
    const rows = D().target_history.map(x => {
      const key = statusOf(x.selection_regret, x.regret_ci);
      return { id: x.id, scope: x.scope, label: `${x.label} · ${x.scope === "affected" ? "affected" : "full"}`, est: x.selection_regret, lo: x.regret_ci && x.regret_ci[0], hi: x.regret_ci && x.regret_ci[1], color: STATUS_COLOR[STATUS[key].cls], statusText: STATUS[key].label, highlight: x.id === t.id && x.scope === t.scope };
    });
    return [
      sensitivityNote(),
      h("div", { class: "page-head" }, h("p", { class: "eyebrow" }, "Target-history stress"),
        h("h1", {}, "When PM₂.₅ history itself goes missing"),
        h("p", { class: "lede" }, "Persistence forecasts from the last observed PM₂.₅ value, so losing PM₂.₅ history attacks the selected family directly. Full-period averages can hide this; outage-affected windows show where the decision breaks.")),
      h("div", { class: "alert alert-info", style: "margin-bottom:16px" }, statusIconBox("warning", 22),
        h("div", {}, h("strong", {}, "Post-results extension"), h("p", {}, "Declared on 2026-10-29 after the primary results, with primary imputation only and no refitting. It is reported transparently and does not replace the confirmatory experiments."))),
      h("div", { class: "filters", role: "region", "aria-label": "Target-history filters" },
        seg("Condition", ids.map(id => ({ value: id, label: D().target_history.find(x => x.id === id).label.replace("PM₂.₅ ", "") })), t.id, v => set({ id: v })),
        seg("Scope", [{ value: "full", label: "Full period" }, { value: "affected", label: "Outage-affected windows", disabled: !hasAffected }], t.scope, v => set({ scope: v }))),
      scopeDetail(scope, `${scope.label} · ${scope.scope === "affected" ? "outage-affected windows" : "full period"}`,
        scope.scope === "affected" ? "Only forecast targets whose 24-hour input window overlaps an outage are scored." : "All test targets are scored, including those unaffected by the intervention."),
      h("section", { class: "card" }, h("h2", {}, "All PM₂.₅-history scopes"), h("p", { class: "sub" }, "The 12-hour outage costs little over the full year but exceeds the threshold where it actually happens."),
        statusLegend(),
        chartBox(div => C.forest(div, { rows, threshold: state.threshold, label: "Selection regret by PM2.5-history scope", onSelect: r => set({ id: r.id, scope: r.scope }) }), "Selection regret by PM2.5-history scope"),
        tableView([{ label: "Scope" }, { label: "Regret", r: 1 }, { label: "95% CI", r: 1 }, { label: "Status" }], rows.map(r => ({ cells: [r.label, f3(r.est), `${f3(r.lo)} – ${f3(r.hi)}`, r.statusText] })))),
    ];
  }

  function viewStations() {
    const site = D().site_shift;
    const stations = site.stations;
    if (!stations.some(s => s.station === state.stations.selected)) state.stations.selected = stations[0].station;
    const st = stations.find(s => s.station === state.stations.selected);
    const within = stations.filter(s => isWithin(statusOf(s.selection_regret, s.regret_ci))).length;
    const select = name => { state.stations.selected = name; syncHash({ st: name }); render(); };
    const allSame = stations.every(s => s.selected_family === stations[0].selected_family);
    const forestRows = stations.map(s => {
      const key = statusOf(s.selection_regret, s.regret_ci);
      return { station: s.station, label: s.station, est: s.selection_regret, lo: s.regret_ci[0], hi: s.regret_ci[1], color: STATUS_COLOR[STATUS[key].cls], statusText: STATUS[key].label, highlight: s.station === st.station };
    });
    const sens = D().loso_tolerance_sensitivity;
    return [
      sensitivityNote(),
      h("div", { class: "page-head" }, h("p", { class: "eyebrow" }, "Unseen stations"),
        h("h1", {}, "Leave-one-station-out site shift"),
        h("p", { class: "lede" }, "Each of the 12 Beijing stations is held out in turn. Models are tuned, selected on validation data and frozen without the held-out station, then tested on it. Station identity is never a model input.")),
      h("div", { class: "grid g4" },
        metric("Stations within threshold", `${within} / ${stations.length}`, null, "Point estimates, current threshold"),
        metric("Mean station regret", f3(site.mean_selection_regret.estimate), "µg/m³", `95% CI ${f3(site.mean_selection_regret.ci_low)} – ${f3(site.mean_selection_regret.ci_high)}`),
        metric("Selected family per fold", allSame ? MODEL_NAME[stations[0].selected_family] : "Varies", null, allSame ? "Same choice in all 12 folds" : ""),
        metric("Selected policy MAE", f3(site.selected_policy_mae), "µg/m³", "Mean across held-out stations")),
      h("section", { class: "card" }, h("h2", {}, "Choose a held-out station"), h("p", { class: "sub" }, "Regret of the fold's validation-selected family at that unseen station."),
        h("div", { class: "station-grid" }, stations.map(s => {
          const key = statusOf(s.selection_regret, s.regret_ci);
          return h("button", { class: "station-tile", type: "button", "aria-pressed": String(s.station === st.station), onclick: () => select(s.station) },
            h("span", { class: "station-name" }, s.station), h("span", { class: "station-regret" }, f3(s.selection_regret), h("span", { class: "metric-unit" }, "µg/m³")), statusBadge(key, true));
        }))),
      h("section", { class: "card" },
        h("div", { class: "card-head" }, h("div", {}, h("p", { class: "eyebrow" }, "Held-out station"), h("h2", { style: "font-size:1.4rem" }, st.station))),
        alertFor(st.selection_regret, st.regret_ci, st.selected_family, `${MODEL_NAME[st.selected_family]} regret ${f3(st.selection_regret)}${unit} · 95% CI ${ciText(st.regret_ci)}`),
        h("div", { class: "grid g2", style: "margin-top:16px" },
          h("div", {}, h("h3", {}, "Validation → test MAE at this station"), h("p", { class: "sub" }, "Hollow = fold validation MAE; filled = held-out station test MAE."),
            legend(MODELS),
            chartBox(div => C.dumbbell(div, { rows: MODELS.map(m => ({ label: MODEL_NAME[m], a: st.validation_mae[m], b: st.test_mae[m], color: modelColor(m), highlight: m === st.selected_family })), aLabel: "Validation MAE", bLabel: "Station test MAE", label: "Validation versus held-out station MAE" }), "Validation versus held-out station MAE")),
          h("div", {}, h("h3", {}, "Candidates"),
            table([{ label: "Model" }, { label: "Val. rank", r: 1 }, { label: "Test MAE", r: 1 }, { label: "Test rank", r: 1 }, { label: "Selected − model (95% CI)", r: 1 }],
              MODELS.map(m => ({ model: m, cells: [modelCell(m), String(st.validation_ranks[m]), f3(st.test_mae[m]), String(st.test_ranks[m]),
                m === st.selected_family ? "selected" : `${f3(st.selected_minus_model[m].estimate)} (${f3(st.selected_minus_model[m].ci_low)} – ${f3(st.selected_minus_model[m].ci_high)})`] })),
              { selected: r => r.model === st.selected_family }),
            h("p", { class: "sub", style: "margin-top:8px" }, `Kendall τb between validation and test ranks: ${C.fmt(st.kendall_tau_b, 2)}.`)))),
      h("section", { class: "card" }, h("h2", {}, "All held-out stations"), h("p", { class: "sub" }, "Click a station to inspect it."),
        statusLegend(),
        chartBox(div => C.forest(div, { rows: forestRows, threshold: state.threshold, label: "Station selection regret", onSelect: r => select(r.station) }), "Station selection regret"),
        tableView([{ label: "Station" }, { label: "Regret", r: 1 }, { label: "95% CI", r: 1 }, { label: "Status" }], forestRows.map(r => ({ cells: [r.label, f3(r.est), `${f3(r.lo)} – ${f3(r.hi)}`, r.statusText] })))),
      h("section", { class: "card" }, h("h2", {}, "Counterfactual tolerance sensitivity (post-results)"),
        h("p", { class: "sub" }, "If the near-tie tolerance had been different, would validation selection have changed? Descriptive only; intervals not recomputed."),
        table([{ label: "Tolerance (µg/m³)", r: 1 }, { label: "Stations within", r: 1 }, { label: "Changed selections", r: 1 }, { label: "Mean station regret", r: 1 }],
          sens.map(r => ({ cells: [C.fmt(r.tolerance, 1) + (r.tolerance === FROZEN_THRESHOLD ? " (frozen)" : ""), `${r.stations_within} / ${r.stations}`, String(r.changed_selections), f3(r.mean_station_regret)] })))),
    ];
  }

  function viewFailure() {
    const fa = D().failure_analysis;
    const f = state.failure;
    const key = f.dim === "band" ? "concentration_band" : "season";
    const records = fa[`${f.source === "clean" ? "clean" : "site"}_${f.dim === "band" ? "bands" : "seasons"}`];
    const order = f.dim === "band" ? ["<50", "50 to <100", "100 to <200", ">=200"] : ["MAM", "JJA", "SON", "DJF"];
    const catLabel = f.dim === "band" ? { "<50": "< 50", "50 to <100": "50–100", "100 to <200": "100–200", ">=200": "≥ 200" } : { MAM: "Spring (MAM)", JJA: "Summer (JJA)", SON: "Autumn (SON)", DJF: "Winter (DJF)" };
    const cats = order.filter(c => records.some(r => r[key] === c));
    const value = (m, c) => { const r = records.find(x => x.model === m && x[key] === c); return r ? r[f.measure] : null; };
    const targets = c => records.find(x => x[key] === c).targets;
    const set = patch => { Object.assign(f, patch); render(); };
    const head = [{ label: f.dim === "band" ? "Observed band (µg/m³)" : "Season" }, { label: "Targets", r: 1 }].concat(MODELS.map(m => ({ label: MODEL_NAME[m] + (f.measure === "mae" ? " MAE" : " bias"), r: 1 })));
    const rows = cats.map(c => ({ cells: [catLabel[c], targets(c).toLocaleString("en"), ...MODELS.map(m => f2(value(m, c)))] }));
    return [
      h("div", { class: "page-head" }, h("p", { class: "eyebrow" }, "Failure analysis"),
        h("h1", {}, "Where errors concentrate"),
        h("p", { class: "lede" }, "Error by observed concentration band and by season, for the pooled clean test year and for unseen-station (LOSO) evaluation.")),
      h("div", { class: "alert alert-info", style: "margin-bottom:16px" }, statusIconBox("warning", 22),
        h("div", {}, h("strong", {}, "Exploratory, post-results diagnostics"), h("p", {}, `Bands (${fa.boundaries_ug_m3.join(", ")} µg/m³) and seasons were declared after the aggregate results. They are not health or AQI categories, carry no confidence intervals and are not confirmatory hypotheses.`))),
      h("div", { class: "filters" },
        seg("Evidence", [{ value: "clean", label: "Clean test (pooled)" }, { value: "site", label: "Unseen stations (LOSO)" }], f.source, v => set({ source: v })),
        seg("Group by", [{ value: "band", label: "Concentration band" }, { value: "season", label: "Season" }], f.dim, v => set({ dim: v })),
        seg("Measure", [{ value: "mae", label: "MAE" }, { value: "bias", label: "Bias (pred − obs)" }], f.measure, v => set({ measure: v }))),
      h("section", { class: "card" }, h("h2", {}, `${f.measure === "mae" ? "MAE" : "Mean bias"} by ${f.dim === "band" ? "observed concentration band" : "season"}`),
        h("p", { class: "sub" }, f.measure === "mae" ? "µg/m³; higher is worse." : "µg/m³; negative = under-prediction, positive = over-prediction."),
        legend(MODELS),
        chartBox(div => C.columns(div, { categories: cats.map(c => catLabel[c]), series: MODELS.map(m => ({ label: MODEL_NAME[m], color: modelColor(m), values: cats.map(c => value(m, c)) })), unit: "µg/m³", label: "Error by group" }), "Grouped column chart of error by group"),
        tableView(head, rows)),
      h("section", { class: "card" }, h("h2", {}, "Largest unseen-station errors"),
        h("p", { class: "sub" }, "Top rows by absolute error from the accepted LOSO worst-case table (sanity-checked, not re-selected from every prediction). Several of the largest cases involve abrupt one-hour changes in observed PM₂.₅ (for example, persistence predicting 621 when 3 µg/m³ was observed), which history-based forecasters cannot anticipate."),
        table([{ label: "Station" }, { label: "Target time" }, { label: "Model" }, { label: "Observed", r: 1 }, { label: "Predicted", r: 1 }, { label: "Abs. error", r: 1 }, { label: "Season" }],
          fa.site_worst_cases.map(r => ({ cells: [r.station, r.target_timestamp, modelCell(r.model), C.fmt(r.y_true, 0), C.fmt(r.y_pred, 1), C.fmt(r.absolute_error, 1), r.season] })))),
    ];
  }

  function viewMethod() {
    const c = D().clean, u = D().site_shift.uncertainty;
    const cfg = c.selected_configs;
    const sev = (g) => [...new Set(D().sensors.filter(s => s.group === g && s.policy === "primary").map(s => s.group === "channel_loss" ? s.channel : s.group === "outage" ? `${s.channel} ${s.severity}` : s.severity))].join(", ");
    return [
      h("div", { class: "page-head" }, h("p", { class: "eyebrow" }, "Methodology"),
        h("h1", {}, "How the evidence was produced"),
        h("p", { class: "lede" }, "The protocol was frozen before final experiments. Deviations and post-results additions are documented in the repository.")),
      h("section", { class: "card" }, h("h2", {}, "Data and temporal split"),
        h("p", { class: "sub" }, "UCI Beijing Multi-Site Air Quality data: 12 stations, hourly, March 2013 – February 2017. Splits are by forecast-target timestamp."),
        h("div", { class: "timeline" },
          h("div", { class: "tr" }, h("strong", {}, "Training"), "2013-03-02 → 2015-02-28 · fitting, tuning (3 expanding folds), preprocessing"),
          h("div", { class: "va" }, h("strong", {}, "Clean validation"), "2015-03-01 → 2016-02-29 · model selection"),
          h("div", { class: "te" }, h("strong", {}, "Final test"), "2016-03-01 → 2017-02-28 · untouched until selection frozen")),
        h("p", { class: "sub" }, "Task: 1-hour-ahead PM₂.₅ from a 24-hour lookback of PM₂.₅, co-pollutants (PM10, SO₂, NO₂, CO, O₃), meteorology (TEMP, PRES, DEWP, RAIN, WSPM, wind direction) and calendar terms. Station identity is not an input.")),
      h("div", { class: "grid g2" },
        h("section", { class: "card" }, h("h2", {}, "Candidate families"),
          table([{ label: "Family" }, { label: "Selected configuration" }], [
            { cells: [modelCell("persistence"), "Last observed PM₂.₅; no parameters"] },
            { cells: [modelCell("xgboost"), `${cfg.xgboost.id}: depth ${cfg.xgboost.max_depth}, η ${cfg.xgboost.eta}, ${cfg.xgboost.rounds} rounds`] },
            { cells: [modelCell("mlp"), `${cfg.mlp.id}: hidden [${cfg.mlp.hidden.join(", ")}], Adam ${cfg.mlp.learning_rate}, ${cfg.mlp.epochs} epochs`] },
            { cells: [modelCell("gru"), `${cfg.gru.id}: ${cfg.gru.units} units, head ${cfg.gru.head_units}, Adam ${cfg.gru.learning_rate}, ${cfg.gru.epochs} epochs`] }]),
          h("p", { class: "sub", style: "margin-top:8px" }, "Learned models use seeds 42, 31415 and 27182; MAE is averaged over seeds within station, then over stations. The compact search budget does not support claims about each architecture's best achievable performance.")),
        h("section", { class: "card prose" }, h("h2", {}, "Selection and uncertainty"),
          h("ul", {},
            h("li", {}, "Lowest station-equal clean validation MAE wins; families within 1.0 µg/m³ are resolved by the order persistence → XGBoost → MLP → GRU."),
            h("li", {}, "The test-year best model is a retrospective oracle only; it never changes the frozen choice."),
            h("li", {}, `Uncertainty: paired calendar moving-block bootstrap, ${u.block_hours}-hour blocks, ${u.replicates.toLocaleString("en")} replicates, seed ${u.seed}, ${Math.round(u.confidence * 100)}% intervals, conditional on fitted seeds and observed stations.`),
            h("li", {}, "RPD is the relative percentage change of MAE versus the matched clean scope.")))),
      h("section", { class: "card prose" }, h("h2", {}, "Stress design (test year only, no retraining)"),
        h("ul", {},
          h("li", {}, `Random auxiliary dropout: ${sev("random_dropout")} of non-target observations removed.`),
          h("li", {}, `Whole-channel loss: ${sev("channel_loss")}.`),
          h("li", {}, `Measurement noise: ${sev("noise")} of a training-derived robust scale.`),
          h("li", {}, `Contiguous outages: ${sev("outage")}, one seeded event per calendar month, reported for full period and affected windows.`),
          h("li", {}, "Corruption is applied to the underlying timeline before windowing; all models share identical corruption realizations and scored targets. Five corruption seeds per condition."),
          h("li", {}, "Post-results PM₂.₅-history extension: PM₂.₅ dropout 10/30/50% and 6/12-hour outages, primary imputation only."),
          h("li", {}, "Site shift: leave-one-station-out across all 12 stations with per-fold tuning and selection."))),
      h("section", { class: "card prose" }, h("h2", {}, "Disclosures"),
        h("ul", {},
          h("li", {}, "A clean-test preprocessing incident was corrected on 2026-10-12 with a separately versioned, replay-verified rescoring; frozen validation evidence and the selection were unchanged."),
          h("li", {}, "The PM₂.₅ target-history extension and tolerance-sensitivity tables were added after primary results and are labelled as such."),
          h("li", {}, "Concentration-band, seasonal and worst-case analyses are exploratory."),
          h("li", {}, "Findings are within-Beijing; non-target sensor faults are synthetic interventions."))),
    ];
  }

  function viewDeployment() {
    const stage = (title, body, chip, evidence) => h("div", { class: "stage" + (evidence ? " evidence" : "") }, h("span", { class: "chip" }, chip), h("h3", {}, title), h("p", {}, body));
    const worst = worstTarget();
    const frozen = (est, ci) => isWithin(statusOf(est, ci, FROZEN_THRESHOLD));
    const sensorsAll = D().sensors.filter(s => s.policy === "primary").flatMap(s => Object.values(s.scopes));
    const sensorsWithin = sensorsAll.filter(v => frozen(v.selection_regret, v.regret_ci)).length;
    const stations = D().site_shift.stations;
    const stationsWithin = stations.filter(s => frozen(s.selection_regret, s.regret_ci)).length;
    return [
      h("div", { class: "page-head" }, h("p", { class: "eyebrow" }, "Deployment concept"),
        h("h1", {}, "From research evidence to an operational system"),
        h("p", { class: "lede" }, "How AirSense-R findings could inform a future forecasting service, and what would still need to be built and validated.")),
      h("div", { class: "concept-banner", role: "note" }, statusIconBox("serious", 26),
        h("div", {}, h("strong", {}, "Conceptual architecture — not evaluated as a live production deployment in this study."),
          h("p", { class: "sub", style: "margin:4px 0 0" }, "No live ingestion, real-time forecasting, hardware deployment, alerting or model switching has been implemented or tested. Solid outlines mark components exercised offline in the research; dashed outlines are concept only."))),
      h("section", { class: "card" }, h("h2", {}, "Conceptual pipeline"),
        h("div", { class: "pipeline", style: "margin-top:12px" },
          stage("Sensor station", "Hourly PM₂.₅, co-pollutant and meteorological observations.", "Concept only"),
          stage("Quality & missingness checks", "Detect gaps, outages and implausible values; flag PM₂.₅-history loss.", "Concept only"),
          stage("AirSense-R preprocessing", "Causal imputation and train-fitted transforms, as evaluated offline.", "Evaluated offline", true),
          stage("Selected forecaster", `Frozen ${MODEL_NAME[D().clean.selected_family]} family chosen by the validation rule.`, "Evaluated offline", true),
          stage("Reliability monitor", "Compare live conditions against stress regimes with known regret.", "Concept only"),
          stage("Forecast API / dashboard", "Serve forecasts with reliability context to operators.", "Concept only"))),
      h("div", { class: "grid g2" },
        h("section", { class: "card prose" }, h("h2", {}, "What the evidence would inform"),
          h("ul", {},
            h("li", {}, `Auxiliary-sensor faults: ${sensorsWithin} of ${sensorsAll.length} tested non-target scopes (primary imputation) kept point regret within the frozen 1.0 µg/m³ threshold.`),
            h("li", {}, `PM₂.₅-history outages: in ${worst.label} ${worst.scope === "affected" ? "outage-affected windows" : "scopes"}, regret reached ${f3(worst.selection_regret)} µg/m³ (95% CI ${ciText(worst.regret_ci)}). A monitor would need to detect target-history loss explicitly.`),
            h("li", {}, `New sites within Beijing: ${stationsWithin} of ${stations.length} held-out stations had point regret within the frozen threshold.`))),
        h("section", { class: "card prose" }, h("h2", {}, "Required before any deployment claim"),
          h("ul", {},
            h("li", {}, "Live data ingestion and latency-aware forecasting tested end to end."),
            h("li", {}, "A validated fallback or model-switching policy — none is validated in this study."),
            h("li", {}, "Prospective monitoring on data outside the 2013–2017 Beijing archive."),
            h("li", {}, "Operational alerting thresholds agreed with stakeholders."),
            h("li", {}, "Any Edge or embedded deployment implemented and tested, not assumed.")))),
    ];
  }

  function viewAbout() {
    const p = D().provenance;
    const hash = (label, value) => h("tr", {}, h("td", {}, label), h("td", { class: "hash" }, value));
    return [
      h("div", { class: "page-head" }, h("p", { class: "eyebrow" }, "About the research"),
        h("h1", {}, "AirSense-R"),
        h("p", { class: "lede" }, "Do air-quality forecasters keep their rank under sensor degradation and site shift? AirSense-R evaluates a frozen model-selection decision rather than proposing a new forecasting architecture.")),
      h("div", { class: "grid g3" },
        h("a", { class: "card", href: `${REPO}/blob/main/paper/manuscript.md`, style: "text-decoration:none;color:inherit" }, h("h3", {}, "Paper draft →"), h("p", { class: "sub" }, "Manuscript narrative and supplementary tables generated from accepted evidence.")),
        h("a", { class: "card", href: REPO, style: "text-decoration:none;color:inherit" }, h("h3", {}, "Repository →"), h("p", { class: "sub" }, "Code, frozen protocol, tests, notebooks and acceptance receipts.")),
        h("a", { class: "card", href: `${REPO}/blob/main/research/PROTOCOL.md`, style: "text-decoration:none;color:inherit" }, h("h3", {}, "Frozen protocol →"), h("p", { class: "sub" }, "Hypotheses, split, selection rule, threshold and stress design."))),
      h("section", { class: "card prose" }, h("h2", {}, "Reproduce this explorer's data"),
        h("p", {}, "The explorer is static. Its data is exported from accepted result commits that are verified against acceptance receipts and manifests; clean-test MAE is recomputed from every saved prediction file before export."),
        h("pre", {}, "git fetch origin 'refs/heads/results/*:refs/remotes/origin/results/*'\npip install -e .\npython scripts/build_explorer_data.py"),
        h("p", {}, p.statement)),
      h("section", { class: "card" }, h("h2", {}, "Evidence provenance"),
        h("div", { class: "table-wrap" }, h("table", {}, h("tbody", {},
          hash("Clean benchmark result commit", p.p5.result_commit),
          hash("Clean acceptance receipt SHA-256", p.p5.receipt_sha256),
          hash("Clean prediction files recomputed", String(p.p5.prediction_files_recomputed)),
          hash("Sensor / station analysis result commit", p.p8.result_commit),
          hash("P8 accepted manifest SHA-256", p.p8.manifest_sha256),
          hash("Target-history result commit", p.p9_target_history.result_commit),
          hash("Target-history review commit", p.p9_target_history.review_commit),
          hash("Target-history receipt SHA-256", p.p9_target_history.receipt_sha256),
          hash("Prediction-window file SHA-256", D().prediction_windows.sha256))))),
      h("section", { class: "card prose" }, h("h2", {}, "Limitations"),
        h("ul", {},
          h("li", {}, "Within-Beijing generalization only; no claim about other cities or climates."),
          h("li", {}, "Non-target sensor faults are synthetic interventions on historical data."),
          h("li", {}, "Uncertainty is conditional on fitted seeds and observed stations."),
          h("li", {}, "Subgroup diagnostics and the PM₂.₅-history extension are post-results analyses."),
          h("li", {}, "No live deployment, Edge or embedded system is claimed."))),
    ];
  }

  const VIEWS = { overview: viewOverview, clean: viewClean, sensors: viewSensors, target: viewTarget, stations: viewStations, failure: viewFailure, method: viewMethod, deployment: viewDeployment, about: viewAbout };

  /* ---------- routing ---------- */
  function parseHash() {
    const raw = location.hash.replace(/^#\/?/, "");
    const [route, query] = raw.split("?");
    return { route: VIEWS[route] ? route : "overview", params: new URLSearchParams(query || "") };
  }
  function syncHash(params) {
    const q = new URLSearchParams(params).toString();
    history.replaceState(null, "", `#/${state.route}${q ? "?" + q : ""}`);
  }
  function applyParams(route, params) {
    if (route === "sensors" && params.get("c")) {
      const r = D().sensors.find(s => s.id === params.get("c") && s.policy === (params.get("p") || state.sensors.policy));
      if (r) Object.assign(state.sensors, { id: r.id, group: r.group, policy: r.policy, scope: params.get("s") || "full" });
    }
    if (route === "target" && params.get("c")) Object.assign(state.target, { id: params.get("c"), scope: params.get("s") || "full" });
    if (route === "stations" && params.get("st")) state.stations.selected = params.get("st");
    if (route === "clean" && params.get("flow")) state.clean.step = 8;
  }

  function render(scrollTop) {
    const main = document.getElementById("content");
    pendingDraws = [];
    main.replaceChildren(...VIEWS[state.route]().flat(Infinity).filter(Boolean));
    pendingDraws.forEach(fn => fn());
    document.querySelectorAll("#nav a").forEach(a => { if (a.dataset.route === state.route) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current"); });
    if (scrollTop) {
      window.scrollTo(0, 0);
      const params = parseHash().params;
      if (state.route === "clean" && params.get("flow")) document.getElementById("flow")?.scrollIntoView();
    }
  }

  function onRoute() {
    const { route, params } = parseHash();
    state.route = route;
    applyParams(route, params);
    document.body.classList.remove("nav-open");
    document.getElementById("menu").setAttribute("aria-expanded", "false");
    render(true);
    const titles = { overview: "Overview", clean: "Clean benchmark", sensors: "Sensor stress", target: "Target-history stress", stations: "Unseen stations", failure: "Failure analysis", method: "Methodology", deployment: "Deployment concept", about: "About" };
    document.title = `${titles[route]} · AirSense-R Reliability Explorer`;
  }

  function init() {
    const thr = document.getElementById("threshold");
    for (const t of state.data.sensitivity_tolerances) {
      thr.appendChild(h("option", { value: t, selected: t === FROZEN_THRESHOLD }, `${C.fmt(t, 1)} µg/m³${t === FROZEN_THRESHOLD ? " (frozen)" : " (sensitivity)"}`));
    }
    thr.addEventListener("change", e => { state.threshold = Number(e.target.value); render(); });
    const p = state.data.provenance;
    document.getElementById("snapshot").textContent = `Accepted evidence snapshot · clean ${p.p5.result_commit.slice(0, 7)} · stress ${p.p8.result_commit.slice(0, 7)} · PM₂.₅ ${p.p9_target_history.result_commit.slice(0, 7)} · not live`;
    window.addEventListener("hashchange", onRoute);
    let timer;
    window.addEventListener("resize", () => { clearTimeout(timer); timer = setTimeout(() => render(false), 150); });
    onRoute();
  }

  document.getElementById("theme").addEventListener("click", () => {
    const root = document.documentElement;
    const dark = root.dataset.theme ? root.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
    root.dataset.theme = dark ? "light" : "dark";
    try { localStorage.setItem("airsense-theme", root.dataset.theme); } catch (e) { /* storage unavailable */ }
  });
  document.getElementById("menu").addEventListener("click", e => {
    const open = document.body.classList.toggle("nav-open");
    e.currentTarget.setAttribute("aria-expanded", String(open));
  });

  fetch("data/explorer.json")
    .then(r => { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then(d => { if (d.schema !== "airsense-r-explorer/1") throw new Error("schema"); state.data = d; init(); })
    .catch(() => {
      document.getElementById("content").replaceChildren(h("div", { class: "error" }, h("h2", {}, "Evidence could not be loaded"),
        h("p", {}, "Serve the docs/ folder over HTTP (for example: python -m http.server -d docs) rather than opening the file directly.")));
    });
})();
