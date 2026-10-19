/* Launch readiness dashboard. Renders window.CERT_REPORT (the engine's report.json)
   with hand-written SVG. No dependencies. */
(function () {
  "use strict";

  var R = window.CERT_REPORT;
  var NS = "http://www.w3.org/2000/svg";
  var COLORS = { go: "#3a8a5f", conditional: "#c58a1d", "no-go": "#a8342a", "n/a": "#e7dfcf" };
  var DECISION_LABEL = { go: "Go", conditional: "Conditional", "no-go": "No-go", "n/a": "Not in scope" };
  var REC_LABEL = { go: "GO", conditional: "CONDITIONAL", partial: "PARTIAL", "no-go": "NO-GO" };
  var GATE_LABEL = { passed: "Pass", known_issues: "Pass", conditional: "Waiver", failed: "Fail", "n/a": "n/a" };
  var ICON = {
    check: '<svg viewBox="0 0 12 12" aria-hidden="true"><path d="M2.5 6.4l2.3 2.3 4.7-5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    warn: '<svg viewBox="0 0 12 12" aria-hidden="true"><path d="M6 2.5v4.2" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/><circle cx="6" cy="9.2" r="1" fill="currentColor"/></svg>',
    cross: '<svg viewBox="0 0 12 12" aria-hidden="true"><path d="M3 3l6 6M9 3l-6 6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>',
    half: '<svg viewBox="0 0 12 12" aria-hidden="true"><circle cx="6" cy="6" r="4.2" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M6 1.8a4.2 4.2 0 0 1 0 8.4z" fill="currentColor"/></svg>',
    dot: '<svg viewBox="0 0 12 12" aria-hidden="true"><circle cx="6" cy="6" r="2" fill="currentColor"/></svg>'
  };
  var REC_ICON = { go: "check", conditional: "warn", partial: "half", "no-go": "cross" };
  var GATE_ICON = { passed: "check", known_issues: "check", conditional: "warn", failed: "cross", "n/a": "dot" };

  function $(id) { return document.getElementById(id); }
  function el(tag, attrs, html) {
    var n = document.createElement(tag);
    if (attrs) Object.keys(attrs).forEach(function (k) { n.setAttribute(k, attrs[k]); });
    if (html != null) n.innerHTML = html;
    return n;
  }
  function svg(tag, attrs) {
    var n = document.createElementNS(NS, tag);
    if (attrs) Object.keys(attrs).forEach(function (k) { n.setAttribute(k, attrs[k]); });
    return n;
  }
  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function fmtDate(iso) {
    var d = new Date(iso + "T00:00:00");
    return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  }

  var partnersById = {};
  R.partners.forEach(function (p) { partnersById[p.id] = p; });
  var modelsById = {};
  R.models.forEach(function (m) { modelsById[m.id] = m; });
  var cellIndex = {};
  R.matrix.forEach(function (c) { cellIndex[c.partner + "|" + c.model] = c; });

  /* Header and KPIs */
  function renderHeader() {
    var s = R.summary;
    $("lede").textContent =
      R.plan + ", as of " + fmtDate(R.as_of) + ". " + s.partners + " partner apps evaluated across " +
      s.models + " TV models in three model years: " + s.targeted_cells + " in-scope app and model pairs.";
    var ready = s.recommendations.go + s.recommendations.conditional + s.recommendations.partial;
    var tiles = [
      { label: "Pairs certified", value: s.certified_pct + "<small>%</small>", sub: (s.go + s.conditional) + " of " + s.targeted_cells + " go or conditional", accent: true },
      { label: "Partners shipping", value: ready + "<small>/ " + s.partners + "</small>", sub: s.recommendations.go + " go, " + s.recommendations.conditional + " conditional, " + s.recommendations.partial + " partial" },
      { label: "Blocking issues", value: String(s.blocking_issues), sub: "Top issue holds " + (R.blocking_issues[0] ? R.blocking_issues[0].reach_models : 0) + " models" },
      { label: "Active waivers", value: String(s.active_waivers), sub: R.waivers.length ? "Next expiry in " + R.waivers[0].days_left + " days" : "None in effect" }
    ];
    var box = $("kpis");
    tiles.forEach(function (t) {
      box.appendChild(el("div", { class: "kpi" + (t.accent ? " accent" : "") },
        '<div class="label">' + t.label + '</div><div class="value">' + t.value + '</div><div class="sub">' + esc(t.sub) + "</div>"));
    });
  }

  /* Readiness stacked bar */
  function renderStack() {
    var s = R.summary;
    var parts = [
      { k: "go", n: s.go, label: "Go" },
      { k: "conditional", n: s.conditional, label: "Conditional" },
      { k: "no-go", n: s.no_go, label: "No-go" }
    ];
    var W = 1000, H = 28, gap = 3, total = s.targeted_cells;
    var root = svg("svg", { viewBox: "0 0 " + W + " " + H, preserveAspectRatio: "none", role: "img",
      "aria-label": parts.map(function (p) { return p.label + " " + p.n; }).join(", ") });
    var x = 0;
    var visible = parts.filter(function (p) { return p.n > 0; });
    var usable = W - gap * (visible.length - 1);
    visible.forEach(function (p, i) {
      var w = (p.n / total) * usable;
      var r = svg("rect", { x: x, y: 0, width: Math.max(w, 1), height: H, rx: 4, fill: COLORS[p.k] });
      bindTip(r, function () {
        return "<b>" + p.label + "</b>: " + p.n + " pairs (" + Math.round((100 * p.n) / total) + "%)";
      });
      root.appendChild(r);
      x += w + (i < visible.length - 1 ? gap : 0);
    });
    $("stack").appendChild(root);
    $("pairs-note").textContent = total + " in-scope pairs; out-of-scope models are excluded, not failed.";
    var legendEl = $("stack-legend");
    var sw = { go: "go", conditional: "cond", "no-go": "nogo" };
    parts.forEach(function (p) {
      legendEl.appendChild(el("li", null, '<span class="sw ' + sw[p.k] + '"></span>' + p.label + " <b>" + p.n + "</b>"));
    });
  }

  /* Partner cards */
  function renderPartners() {
    var box = $("partners");
    R.partners.forEach(function (p) {
      var card = el("article", { class: "card partner" });
      var cov = p.coverage_pct;
      var W = 200, H = 10;
      var goW = p.targeted ? (p.go / p.targeted) * W : 0;
      var cW = p.targeted ? (p.conditional / p.targeted) * W : 0;
      var bar =
        '<svg viewBox="0 0 ' + W + " " + H + '" preserveAspectRatio="none" aria-hidden="true">' +
        '<rect x="0" y="0" width="' + W + '" height="' + H + '" rx="4" fill="#efe8da"/>' +
        (goW ? '<rect x="0" y="0" width="' + goW + '" height="' + H + '" rx="4" fill="' + COLORS.go + '"/>' : "") +
        (cW ? '<rect x="' + (goW + (goW ? 2 : 0)) + '" y="0" width="' + Math.max(cW - 2, 1) + '" height="' + H + '" rx="4" fill="' + COLORS.conditional + '"/>' : "") +
        "</svg>";
      card.innerHTML =
        '<div class="partner-top"><div><div class="name">' + esc(p.name) + '</div><div class="meta">' +
        esc(p.category) + " / v" + esc(p.version) + "</div></div>" +
        '<span class="badge ' + p.recommendation + '">' + ICON[REC_ICON[p.recommendation]] + REC_LABEL[p.recommendation] + "</span></div>" +
        '<div class="cov">' + bar + "<span><b>" + (p.go + p.conditional) + "</b> / " + p.targeted + " models</span></div>" +
        '<p class="why">' + esc(p.rationale.join("; ")) + "</p>";
      card.setAttribute("aria-label", p.name + ": " + REC_LABEL[p.recommendation] + ", " + cov + "% coverage");
      box.appendChild(card);
    });
  }

  /* Heatmap: partner rows x model columns, grouped by model year */
  function renderHeatmap() {
    var legendEl = $("matrix-legend");
    [["go", "go", "Go"], ["cond", "conditional", "Conditional (waiver)"], ["nogo", "no-go", "No-go"], ["na", "n/a", "Not in scope"]]
      .forEach(function (x) { legendEl.appendChild(el("li", null, '<span class="sw ' + x[0] + '"></span>' + x[2])); });

    var cell = 18, gap = 2, groupGap = 14, labelW = 148, top = 40;
    var years = [];
    R.models.forEach(function (m) { if (years.indexOf(m.model_year) < 0) years.push(m.model_year); });
    var cols = [];
    var x = labelW;
    var groups = [];
    years.forEach(function (y) {
      var ms = R.models.filter(function (m) { return m.model_year === y; });
      var start = x;
      ms.forEach(function (m) { cols.push({ m: m, x: x }); x += cell + gap; });
      groups.push({ y: y, x0: start, x1: x - gap, n: ms.length });
      x += groupGap - gap;
    });
    var W = x - groupGap + gap + 4;
    var H = top + R.partners.length * (cell + 6) + 4;
    var root = svg("svg", { class: "heatmap", width: W, height: H, viewBox: "0 0 " + W + " " + H, role: "grid",
      "aria-label": "Certification decisions by partner app and TV model" });

    groups.forEach(function (g) {
      var t = svg("text", { x: g.x0, y: 14, class: "yr" });
      t.textContent = g.y + " models";
      root.appendChild(t);
      var c = svg("text", { x: g.x1, y: 14, class: "tier", "text-anchor": "end" });
      c.textContent = g.n;
      root.appendChild(c);
      root.appendChild(svg("line", { x1: g.x0, x2: g.x1, y1: 20, y2: 20, stroke: "#d6ccb6", "stroke-width": 1 }));
    });
    cols.forEach(function (col) {
      var t = svg("text", { x: col.x + cell / 2, y: top - 6, class: "tier", "text-anchor": "middle" });
      t.textContent = col.m.tier.charAt(0).toUpperCase();
      root.appendChild(t);
    });

    var glyph = { conditional: "!", "no-go": "×" };
    R.partners.forEach(function (p, r) {
      var y = top + r * (cell + 6);
      var row = svg("g", { class: "row", role: "row" });
      var name = svg("text", { x: 0, y: y + cell / 2 + 4, class: "pname" });
      name.textContent = p.name;
      row.appendChild(name);
      cols.forEach(function (col) {
        var c = cellIndex[p.id + "|" + col.m.id];
        var g = svg("g", { class: "cell", tabindex: "-1", role: "gridcell",
          "aria-label": p.name + " on " + col.m.id + ": " + DECISION_LABEL[c.decision] });
        var rect = svg("rect", { class: "c", x: col.x, y: y, width: cell, height: cell, rx: 4, fill: COLORS[c.decision] });
        g.appendChild(rect);
        if (glyph[c.decision]) {
          var t = svg("text", { x: col.x + cell / 2, y: y + cell / 2 + 4, class: "glyph", "text-anchor": "middle" });
          t.textContent = glyph[c.decision];
          g.appendChild(t);
        }
        g.addEventListener("click", function () { select(g, c); });
        g.addEventListener("keydown", function (e) {
          if (e.key === "Enter" || e.key === " ") { e.preventDefault(); select(g, c); }
        });
        bindTip(g, function () { return tipFor(c); });
        row.appendChild(g);
      });
      root.appendChild(row);
    });
    $("heatmap-scroll").appendChild(root);
    var first = root.querySelector(".cell");
    if (first) first.setAttribute("tabindex", "0");
    enableGridKeys(root, cols.length);
  }

  function enableGridKeys(root, ncols) {
    var cells = Array.prototype.slice.call(root.querySelectorAll(".cell"));
    cells.forEach(function (c, i) {
      c.addEventListener("keydown", function (e) {
        var j = i;
        if (e.key === "ArrowRight") j = i + 1;
        else if (e.key === "ArrowLeft") j = i - 1;
        else if (e.key === "ArrowDown") j = i + ncols;
        else if (e.key === "ArrowUp") j = i - ncols;
        else return;
        e.preventDefault();
        if (j < 0 || j >= cells.length) return;
        c.setAttribute("tabindex", "-1");
        cells[j].setAttribute("tabindex", "0");
        cells[j].focus();
        cells[j].dispatchEvent(new Event("click"));
      });
    });
  }

  function tipFor(c) {
    var m = modelsById[c.model];
    var p = partnersById[c.partner];
    var html = "<b>" + esc(p.name) + "</b> on <b>" + esc(m.id) + "</b><br>" + DECISION_LABEL[c.decision] +
      " / " + esc(m.tier) + " tier, SDK " + esc(m.sdk);
    if (c.reasons.length) html += '<div class="r">' + esc(c.reasons[0]) + (c.reasons.length > 1 ? " (+" + (c.reasons.length - 1) + " more)" : "") + "</div>";
    else if (c.known_issues.length) html += '<div class="r">Known issue: ' + esc(c.known_issues[0]) + "</div>";
    return html;
  }

  var selected = null;
  function select(g, c) {
    if (selected) selected.classList.remove("sel");
    selected = g;
    g.classList.add("sel");
    var m = modelsById[c.model];
    var p = partnersById[c.partner];
    var badgeClass = c.decision === "n/a" ? "partial" : c.decision;
    var items = c.reasons.map(function (r) { return "<li>" + esc(r) + "</li>"; })
      .concat(c.known_issues.map(function (r) { return "<li>Known issue: " + esc(r) + "</li>"; }));
    if (!items.length) items = ["<li>All applicable tests passed with evidence on file.</li>"];
    $("detail").innerHTML =
      "<h4>" + esc(p.name) + " on " + esc(m.id) + ' <span class="badge ' + badgeClass + '">' +
      DECISION_LABEL[c.decision].toUpperCase() + "</span></h4>" +
      '<div class="model-meta">' + esc(m.series) + " " + m.model_year + " / " + esc(m.tier) + " / SoC " + esc(m.soc) +
      " / firmware " + esc(m.firmware) + " / SDK " + esc(m.sdk) + "</div><ul>" + items.join("") + "</ul>";
  }

  /* Gate status table */
  function renderGates() {
    var t = $("gates");
    var head = "<thead><tr><th>Partner</th>" + R.gates.map(function (g) {
      return '<th scope="col"' + (g.global ? ' class="glob"' : "") + ">" + g.id + (g.global ? " *" : "") +
        "<span>" + esc(g.name) + "</span></th>";
    }).join("") + "</tr></thead>";
    var body = "<tbody>" + R.partners.map(function (p) {
      return '<tr><th scope="row">' + esc(p.name) + "</th>" + p.gates.map(function (g) {
        var cls = g.status === "n/a" ? "na" : g.status;
        var label = GATE_LABEL[g.status];
        if (g.status === "failed") label += " " + g.models_failed;
        if (g.status === "conditional") label += " " + g.models_conditional;
        var title = g.status === "known_issues" ? "Passed with known minor issues" :
          g.status === "failed" ? g.models_failed + " models blocked at this gate" :
          g.status === "conditional" ? g.models_conditional + " models under waiver" : label;
        return '<td><span class="pill ' + cls + '" title="' + esc(title) + '">' + ICON[GATE_ICON[g.status]] + label + "</span></td>";
      }).join("") + "</tr>";
    }).join("") + "</tbody>";
    t.innerHTML = head + body;
  }

  /* Blocking issues ranked by reach */
  function renderIssues() {
    var list = $("issues");
    var max = R.summary.models;
    if (!R.blocking_issues.length) {
      list.appendChild(el("li", null, '<p class="hint">No blocking issues.</p>'));
      return;
    }
    R.blocking_issues.forEach(function (b) {
      var W = 300, H = 14;
      var w = Math.max((b.reach_models / max) * W, 4);
      var color = b.severity === "blocker" ? COLORS["no-go"] : "#7b8aa0";
      var partners = b.partners.map(function (id) { return partnersById[id] ? partnersById[id].name : id; }).join(", ");
      var li = el("li", { class: "issue" });
      li.innerHTML =
        '<span class="rank">' + b.rank + "</span>" +
        '<span class="title">' + esc(b.title) + "</span>" +
        '<span class="meta"><code>' + esc(b.key) + "</code> / " + esc(b.gate) + " / " + esc(b.severity) + " / " + esc(partners) + "</span>" +
        '<div class="bar-row"><svg viewBox="0 0 ' + W + " " + H + '" preserveAspectRatio="none" aria-hidden="true">' +
        '<rect x="0" y="0" width="' + W + '" height="' + H + '" rx="4" fill="#efe8da"/>' +
        '<rect x="0" y="0" width="' + w + '" height="' + H + '" rx="4" fill="' + color + '"/></svg>' +
        '<span class="n">' + b.reach_models + " models</span></div>";
      list.appendChild(li);
    });
  }

  function renderWaivers() {
    var box = $("waivers");
    if (!R.waivers.length) { box.innerHTML = '<p class="hint">No waivers in effect.</p>'; return; }
    R.waivers.forEach(function (w) {
      var p = partnersById[w.partner];
      box.appendChild(el("div", { class: "waiver" },
        '<div><div class="t">' + esc(p ? p.name : w.partner) + " / " + esc(w.test) + " on " + w.models + " models</div>" +
        '<div class="m">' + esc(w.mitigation) + "</div>" +
        '<div class="m">Approved by ' + esc(w.approved_by) + ", expires " + fmtDate(w.expires) + "</div></div>" +
        '<div class="days"><b>' + w.days_left + "</b><span>days left</span></div>"));
    });
  }

  /* Tooltip */
  var tip = $("tip");
  function bindTip(node, html) {
    node.addEventListener("pointerenter", function (e) {
      if (e.pointerType === "touch") return;
      tip.innerHTML = html();
      tip.hidden = false;
      place(e);
    });
    node.addEventListener("pointermove", function (e) { if (!tip.hidden) place(e); });
    node.addEventListener("pointerleave", function () { tip.hidden = true; });
  }
  function place(e) {
    var pad = 14, w = tip.offsetWidth, h = tip.offsetHeight;
    var x = e.clientX + pad, y = e.clientY + pad;
    if (x + w > window.innerWidth - 8) x = e.clientX - w - pad;
    if (y + h > window.innerHeight - 8) y = e.clientY - h - pad;
    tip.style.left = Math.max(8, x) + "px";
    tip.style.top = Math.max(8, y) + "px";
  }

  renderHeader();
  renderStack();
  renderPartners();
  renderHeatmap();
  renderGates();
  renderIssues();
  renderWaivers();

  /* Open on the most instructive cell: the top blocker's first affected model. */
  var top = R.blocking_issues[0];
  if (top) {
    var hit = R.matrix.filter(function (c) {
      return c.decision === "no-go" && top.partners.indexOf(c.partner) >= 0;
    })[0];
    if (hit) {
      var node = document.querySelector('.heatmap .cell[aria-label^="' + partnersById[hit.partner].name + " on " + hit.model + ':"]');
      if (node) select(node, hit);
    }
  }
})();
