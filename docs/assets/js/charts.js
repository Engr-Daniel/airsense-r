/* Small dependency-free SVG chart helpers for the AirSense-R explorer.
   All labels are inserted with textContent; no innerHTML from data. */
(function () {
  "use strict";
  const NS = "http://www.w3.org/2000/svg";

  function svgEl(tag, attrs, parent) {
    const node = document.createElementNS(NS, tag);
    for (const [k, v] of Object.entries(attrs || {})) {
      if (v === undefined || v === null) continue;
      // CSS custom properties resolve reliably as style, not as presentation attributes.
      if ((k === "fill" || k === "stroke") && String(v).startsWith("var(")) node.style.setProperty(k, v);
      else node.setAttribute(k, v);
    }
    if (parent) parent.appendChild(node);
    return node;
  }
  function text(parent, x, y, value, attrs) {
    const t = svgEl("text", Object.assign({ x, y }, attrs || {}), parent);
    t.textContent = value;
    return t;
  }
  function niceMax(v) {
    if (v <= 0) return 1;
    const p = Math.pow(10, Math.floor(Math.log10(v)));
    const n = v / p;
    return (n <= 1 ? 1 : n <= 2 ? 2 : n <= 2.5 ? 2.5 : n <= 5 ? 5 : 10) * p;
  }
  // Upper axis bound rounded to a nice tick step rather than a nice magnitude (avoids 25 -> 50).
  function axisMax(v, count) {
    if (v <= 0) return 1;
    const step = niceMax(v / (count || 5));
    return Math.ceil(v / step - 1e-9) * step;
  }
  function ticks(min, max, count) {
    const step = niceMax((max - min) / (count || 5));
    const out = [];
    for (let v = Math.ceil(min / step) * step; v <= max + 1e-9; v += step) out.push(+v.toFixed(10));
    return out;
  }
  function fmt(v, d) { return v === null || v === undefined || Number.isNaN(v) ? "—" : Number(v).toFixed(d === undefined ? 2 : d); }

  /* ---------- tooltip ---------- */
  const tip = () => document.getElementById("tooltip");
  function showTip(evt, title, rows) {
    const t = tip();
    t.replaceChildren();
    if (title) { const h = document.createElement("div"); h.className = "tt-title"; h.textContent = title; t.appendChild(h); }
    for (const r of rows) {
      const row = document.createElement("div"); row.className = "tt-row";
      const l = document.createElement("span");
      if (r.color) { const k = document.createElement("i"); k.className = "linekey"; k.style.background = r.color; l.appendChild(k); }
      l.appendChild(document.createTextNode(r.label));
      const v = document.createElement("strong"); v.textContent = r.value;
      row.append(l, v); t.appendChild(row);
    }
    t.classList.add("on");
    moveTip(evt);
  }
  function moveTip(evt) {
    const t = tip();
    let x, y;
    if (evt && evt.clientX !== undefined && evt.type !== "focus") { x = evt.clientX; y = evt.clientY; }
    else { const r = evt.target.getBoundingClientRect(); x = r.left + r.width / 2; y = r.top; }
    const w = t.offsetWidth, h = t.offsetHeight;
    let left = x + 14, top = y - h - 10;
    if (left + w > window.innerWidth - 8) left = x - w - 14;
    if (top < 8) top = y + 16;
    t.style.left = left + "px"; t.style.top = top + "px";
  }
  function hideTip() { tip().classList.remove("on"); }
  function bindTip(node, title, rows) {
    node.setAttribute("tabindex", "0");
    node.setAttribute("aria-label", [title].concat(rows.map(r => r.label + " " + r.value)).join(", "));
    node.addEventListener("pointerenter", e => showTip(e, title, rows));
    node.addEventListener("pointermove", moveTip);
    node.addEventListener("pointerleave", hideTip);
    node.addEventListener("focus", e => showTip(e, title, rows));
    node.addEventListener("blur", hideTip);
  }

  function frame(container, height, label) {
    container.replaceChildren();
    const width = Math.max(container.clientWidth || 600, 280);
    const svg = svgEl("svg", { viewBox: `0 0 ${width} ${height}`, role: "img", "aria-label": label || "" }, container);
    return { svg, width, height };
  }

  function thresholdLine(g, x, top, bottom, label) {
    svgEl("line", { x1: x, x2: x, y1: top, y2: bottom, class: "thr" }, g);
    if (label) text(g, x + 4, top + 10, label, { class: "thr-label" });
  }

  /* ---------- horizontal bars ---------- */
  function hbar(container, o) {
    const rowH = 38, top = 8, labelW = Math.min(150, (container.clientWidth || 600) * 0.32);
    const h = top + o.rows.length * rowH + 26;
    const { svg, width } = frame(container, h, o.label);
    const right = width - 58, left = labelW;
    const max = axisMax((o.max || Math.max(...o.rows.map(r => r.value))) * 1.05, 4);
    const x = v => left + (v / max) * (right - left);
    const grid = svgEl("g", { class: "grid" }, svg);
    for (const t of ticks(0, max, 4)) {
      svgEl("line", { x1: x(t), x2: x(t), y1: top, y2: h - 22 }, grid);
      text(svg, x(t), h - 6, fmt(t, t % 1 ? 1 : 0), { "text-anchor": "middle", class: "num" });
    }
    o.rows.forEach((r, i) => {
      const y = top + i * rowH, barH = 20, by = y + (rowH - barH) / 2;
      text(svg, left - 10, y + rowH / 2 + 4, r.label, { "text-anchor": "end", class: "lbl", "font-weight": r.highlight ? 700 : 400 });
      const w = Math.max(x(r.value) - left, 2);
      // 4px rounded data end, square at the baseline.
      const path = `M${left},${by} h${w - 4} a4,4 0 0 1 4,4 v${barH - 8} a4,4 0 0 1 -4,4 h${-(w - 4)} z`;
      svgEl("path", { d: path, fill: r.color }, svg);
      text(svg, x(r.value) + 6, by + barH / 2 + 4, fmt(r.value, o.decimals ?? 3), { class: "val num" });
      const hit = svgEl("rect", { x: 0, y, width, height: rowH, class: "hit" }, svg);
      bindTip(hit, r.label, [{ label: o.valueLabel || "Value", value: fmt(r.value, o.decimals ?? 3) + (o.unit ? " " + o.unit : ""), color: r.color }].concat(r.extra || []));
    });
    svgEl("line", { x1: left, x2: left, y1: top, y2: h - 22, class: "base" }, svg);
  }

  /* ---------- dot + interval (forest) ---------- */
  function forest(container, o) {
    const rowH = o.rowH || 30, top = 22, labelW = o.labelW || Math.min(190, (container.clientWidth || 600) * 0.34);
    const h = top + o.rows.length * rowH + 28;
    const { svg, width } = frame(container, h, o.label);
    const left = labelW, right = width - 20;
    const maxV = Math.max(o.threshold * 1.15, ...o.rows.map(r => Math.max(r.hi ?? r.est, r.est)));
    const max = o.max || axisMax(maxV);
    const min = o.min ?? 0;
    const x = v => left + ((v - min) / (max - min)) * (right - left);
    const grid = svgEl("g", { class: "grid" }, svg);
    for (const t of ticks(min, max, 5)) {
      svgEl("line", { x1: x(t), x2: x(t), y1: top - 4, y2: h - 24 }, grid);
      text(svg, x(t), h - 8, fmt(t, 1), { "text-anchor": "middle", class: "num" });
    }
    thresholdLine(svg, x(o.threshold), top - 18, h - 24, `${fmt(o.threshold, 1)} µg/m³ threshold`);
    let lastGroup = null;
    o.rows.forEach((r, i) => {
      const y = top + i * rowH + rowH / 2;
      if (o.groups && r.group !== lastGroup && i > 0) svgEl("line", { x1: 0, x2: width, y1: y - rowH / 2, y2: y - rowH / 2, class: "base", opacity: .5 }, svg);
      lastGroup = r.group;
      text(svg, left - 10, y + 4, r.label, { "text-anchor": "end", class: "lbl", "font-weight": r.highlight ? 700 : 400 });
      if (r.lo !== null && r.lo !== undefined) {
        svgEl("line", { x1: x(r.lo), x2: x(r.hi), y1: y, y2: y, stroke: "var(--text-secondary)", "stroke-width": 2, "stroke-linecap": "round" }, svg);
      }
      svgEl("circle", { cx: x(r.est), cy: y, r: 5.5, fill: r.color, stroke: "var(--surface-1)", "stroke-width": 2 }, svg);
      const hit = svgEl("rect", { x: 0, y: y - rowH / 2, width, height: rowH, class: "hit" }, svg);
      if (o.onSelect) hit.addEventListener("click", () => o.onSelect(r));
      bindTip(hit, r.label, [
        { label: "Selection regret", value: fmt(r.est, 3) + " µg/m³", color: r.color },
        { label: "95% CI", value: r.lo === null || r.lo === undefined ? "not available" : `${fmt(r.lo, 3)} – ${fmt(r.hi, 3)}` },
        { label: "Status", value: r.statusText || "" },
      ]);
    });
  }

  /* ---------- strip: many scopes per evidence row ---------- */
  function strip(container, o) {
    const rowH = 46, top = 26, labelW = Math.min(200, (container.clientWidth || 600) * 0.3);
    const h = top + o.groups.length * rowH + 28;
    const { svg, width } = frame(container, h, o.label);
    const left = labelW, right = width - 24;
    const max = axisMax(Math.max(o.threshold * 1.2, ...o.groups.flatMap(g => g.points.map(p => p.est))) * 1.05);
    const x = v => left + (v / max) * (right - left);
    const grid = svgEl("g", { class: "grid" }, svg);
    for (const t of ticks(0, max, 5)) {
      svgEl("line", { x1: x(t), x2: x(t), y1: top - 4, y2: h - 24 }, grid);
      text(svg, x(t), h - 8, fmt(t, 1), { "text-anchor": "middle", class: "num" });
    }
    thresholdLine(svg, x(o.threshold), top - 22, h - 24, `${fmt(o.threshold, 1)} µg/m³ threshold`);
    o.groups.forEach((g, i) => {
      const y = top + i * rowH + rowH / 2;
      svgEl("line", { x1: left, x2: right, y1: y, y2: y, stroke: "var(--grid)" }, svg);
      text(svg, left - 12, y - 2, g.label, { "text-anchor": "end", class: "lbl", "font-weight": 600 });
      text(svg, left - 12, y + 13, g.sub, { "text-anchor": "end" });
      // Deterministic vertical jitter so coincident points stay visible.
      g.points.forEach((p, j) => {
        const jy = y + ((j % 5) - 2) * 4;
        const c = svgEl("circle", { cx: x(p.est), cy: jy, r: 5, fill: p.color, stroke: "var(--surface-1)", "stroke-width": 2 }, svg);
        const hit = svgEl("circle", { cx: x(p.est), cy: jy, r: 11, class: "hit" }, svg);
        hit.addEventListener("pointerenter", () => c.setAttribute("r", 7));
        hit.addEventListener("pointerleave", () => c.setAttribute("r", 5));
        if (p.href) hit.addEventListener("click", () => { location.hash = p.href; });
        bindTip(hit, p.label, [
          { label: "Selection regret", value: fmt(p.est, 3) + " µg/m³", color: p.color },
          { label: "95% CI", value: p.lo === null || p.lo === undefined ? "not available" : `${fmt(p.lo, 3)} – ${fmt(p.hi, 3)}` },
          { label: "Status", value: p.statusText },
        ]);
      });
    });
  }

  /* ---------- dumbbell: reference -> stressed ---------- */
  function dumbbell(container, o) {
    const rowH = 38, top = 10, labelW = Math.min(150, (container.clientWidth || 600) * 0.3);
    const h = top + o.rows.length * rowH + 28;
    const { svg, width } = frame(container, h, o.label);
    const left = labelW, right = width - 70;
    const all = o.rows.flatMap(r => [r.a, r.b]);
    const lo = Math.min(...all) * 0.9, hi = Math.max(...all) * 1.05;
    const step = niceMax((hi - lo) / 5);
    const min = Math.max(0, Math.floor(lo / step) * step);
    const max = Math.ceil(hi / step) * step;
    const x = v => left + ((v - min) / (max - min)) * (right - left);
    const grid = svgEl("g", { class: "grid" }, svg);
    for (const t of ticks(min, max, 5)) {
      svgEl("line", { x1: x(t), x2: x(t), y1: top, y2: h - 24 }, grid);
      text(svg, x(t), h - 8, fmt(t, step < 1 ? 1 : 0), { "text-anchor": "middle", class: "num" });
    }
    o.rows.forEach((r, i) => {
      const y = top + i * rowH + rowH / 2;
      text(svg, left - 10, y + 4, r.label, { "text-anchor": "end", class: "lbl", "font-weight": r.highlight ? 700 : 400 });
      svgEl("line", { x1: x(r.a), x2: x(r.b), y1: y, y2: y, stroke: r.color, "stroke-width": 2, opacity: .55 }, svg);
      svgEl("circle", { cx: x(r.a), cy: y, r: 5, fill: "var(--surface-1)", stroke: r.color, "stroke-width": 2 }, svg);
      svgEl("circle", { cx: x(r.b), cy: y, r: 6, fill: r.color, stroke: "var(--surface-1)", "stroke-width": 2 }, svg);
      text(svg, Math.max(x(r.a), x(r.b)) + 12, y + 4, fmt(r.b, 2), { class: "val num" });
      const hit = svgEl("rect", { x: 0, y: y - rowH / 2, width, height: rowH, class: "hit" }, svg);
      bindTip(hit, r.label, [
        { label: o.aLabel, value: fmt(r.a, 3) + " µg/m³" },
        { label: o.bLabel, value: fmt(r.b, 3) + " µg/m³", color: r.color },
      ].concat(r.extra || []));
    });
  }

  /* ---------- grouped columns ---------- */
  function columns(container, o) {
    const h = o.height || 280, top = 14, bottom = 40, left = 46;
    const { svg, width } = frame(container, h, o.label);
    const right = width - 10;
    const vals = o.series.flatMap(s => s.values);
    const minV = Math.min(0, ...vals), maxV = Math.max(0, ...vals);
    const max = axisMax(maxV * 1.08), min = minV < 0 ? -axisMax(-minV * 1.08) : 0;
    const y = v => top + (1 - (v - min) / (max - min)) * (h - top - bottom);
    const grid = svgEl("g", { class: "grid" }, svg);
    for (const t of ticks(min, max, 5)) {
      svgEl("line", { x1: left, x2: right, y1: y(t), y2: y(t) }, grid);
      text(svg, left - 8, y(t) + 4, fmt(t, Math.abs(t) < 10 && t % 1 ? 1 : 0), { "text-anchor": "end", class: "num" });
    }
    const band = (right - left) / o.categories.length;
    const barW = Math.min(22, (band * 0.8 - 2 * (o.series.length - 1)) / o.series.length);
    const groupW = barW * o.series.length + 2 * (o.series.length - 1);
    o.categories.forEach((cat, ci) => {
      const gx = left + ci * band + (band - groupW) / 2;
      text(svg, left + ci * band + band / 2, h - bottom + 18, cat, { "text-anchor": "middle", class: "lbl" });
      o.series.forEach((s, si) => {
        const v = s.values[ci];
        const bx = gx + si * (barW + 2), y0 = y(0), y1 = y(v);
        const hgt = Math.abs(y1 - y0);
        const r = Math.min(4, hgt);
        const d = v >= 0
          ? `M${bx},${y0} v${-(hgt - r)} a${r},${r} 0 0 1 ${r},${-r} h${barW - 2 * r} a${r},${r} 0 0 1 ${r},${r} v${hgt - r} z`
          : `M${bx},${y0} v${hgt - r} a${r},${r} 0 0 0 ${r},${r} h${barW - 2 * r} a${r},${r} 0 0 0 ${r},${-r} v${-(hgt - r)} z`;
        svgEl("path", { d, fill: s.color }, svg);
        const hit = svgEl("rect", { x: bx - 1, y: Math.min(y0, y1) - 6, width: barW + 2, height: hgt + 12, class: "hit" }, svg);
        bindTip(hit, cat, [{ label: s.label, value: fmt(v, o.decimals ?? 2) + (o.unit ? " " + o.unit : ""), color: s.color }]);
      });
    });
    svgEl("line", { x1: left, x2: right, y1: y(0), y2: y(0), class: "base" }, svg);
    if (o.yLabel) text(svg, 4, 10, o.yLabel, {});
  }

  /* ---------- time-series lines with crosshair ---------- */
  function lines(container, o) {
    const h = o.height || 300, top = 14, bottom = 34, left = 46;
    const { svg, width } = frame(container, h, o.label);
    const right = width - 12;
    const n = o.x.length;
    const vals = o.series.flatMap(s => s.values.filter(v => v !== null));
    const max = axisMax(Math.max(...vals) * 1.05);
    const x = i => left + (i / (n - 1)) * (right - left);
    const y = v => top + (1 - v / max) * (h - top - bottom);
    const grid = svgEl("g", { class: "grid" }, svg);
    for (const t of ticks(0, max, 5)) {
      svgEl("line", { x1: left, x2: right, y1: y(t), y2: y(t) }, grid);
      text(svg, left - 8, y(t) + 4, fmt(t, 0), { "text-anchor": "end", class: "num" });
    }
    for (let i = 0; i < n; i += 24) {
      text(svg, x(i), h - 12, o.x[i].slice(5, 10), { "text-anchor": "start" });
      svgEl("line", { x1: x(i), x2: x(i), y1: h - bottom, y2: h - bottom + 4, class: "base" }, svg);
    }
    svgEl("line", { x1: left, x2: right, y1: y(0), y2: y(0), class: "base" }, svg);
    for (const s of o.series) {
      let d = "", pen = false;
      s.values.forEach((v, i) => {
        if (v === null) { pen = false; return; }
        d += (pen ? "L" : "M") + x(i).toFixed(1) + "," + y(v).toFixed(1);
        pen = true;
      });
      svgEl("path", { d, fill: "none", stroke: s.color, "stroke-width": s.width || 2, "stroke-linejoin": "round", "stroke-linecap": "round", opacity: s.opacity || 1 }, svg);
    }
    const cross = svgEl("line", { x1: 0, x2: 0, y1: top, y2: h - bottom, stroke: "var(--text-muted)", "stroke-width": 1, visibility: "hidden" }, svg);
    const overlay = svgEl("rect", { x: left, y: top, width: right - left, height: h - top - bottom, class: "hit", tabindex: 0, "aria-label": "Hover or use arrow keys to read values" }, svg);
    let focusIndex = 0;
    const readout = (evt, i) => {
      i = Math.max(0, Math.min(n - 1, i));
      cross.setAttribute("x1", x(i)); cross.setAttribute("x2", x(i)); cross.setAttribute("visibility", "visible");
      showTip(evt, o.x[i], o.series.map(s => ({ label: s.label, value: s.values[i] === null ? "missing" : fmt(s.values[i], 1), color: s.color })));
    };
    overlay.addEventListener("pointermove", e => {
      const box = svg.getBoundingClientRect();
      const px = (e.clientX - box.left) * (width / box.width);
      focusIndex = Math.round(((px - left) / (right - left)) * (n - 1));
      readout(e, focusIndex);
    });
    overlay.addEventListener("pointerleave", () => { cross.setAttribute("visibility", "hidden"); hideTip(); });
    overlay.addEventListener("keydown", e => {
      if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
      e.preventDefault();
      focusIndex = Math.max(0, Math.min(n - 1, focusIndex + (e.key === "ArrowRight" ? 1 : -1)));
      readout({ target: overlay, type: "focus" }, focusIndex);
    });
    overlay.addEventListener("blur", () => { cross.setAttribute("visibility", "hidden"); hideTip(); });
  }

  window.AirCharts = { hbar, forest, strip, dumbbell, columns, lines, fmt, bindTip };
})();
