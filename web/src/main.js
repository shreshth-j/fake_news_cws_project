import "@fontsource-variable/geist";
import "@fontsource-variable/geist-mono";
import "@fontsource-variable/newsreader/opsz.css";
import "@fontsource-variable/newsreader/opsz-italic.css";
import "./style.css";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import {
  DEFAULTS, POLICIES, BASE_PAYOFFS, SUSC, EXPO,
  validationErrors, logistic, sir, summarise, analyse, deviations, endogenousPayoffs, tippingM, makeGraph, runNetwork,
} from "./model.js";

gsap.registerPlugin(ScrollTrigger);

const $ = (s) => document.querySelector(s);
const reduceMotion = matchMedia("(prefers-reduced-motion: reduce)").matches;
const INK = "#17140f", RED = "#c2381f", PAPER = "#ece6d6";
const int = (v) => Math.round(v).toLocaleString("en-IN");
const num = (v) => (Number.isInteger(v) ? String(v) : v.toFixed(2)).replace("-", "−");
const compact = (v) => (v >= 1000 ? `${+(v / 1000).toFixed(1)}k` : String(v));
const WORD = { S: "spread", N: "stay quiet", W: "weak moderation", M: "strong moderation" };
const words = (k) => `${WORD[k[0]]} / ${WORD[k[1]]}`;
const kpi = (dt, dd, small = "") => `<div><dt>${dt}</dt><dd>${dd}${small ? `<small>${small}</small>` : ""}</dd></div>`;

const S = {
  p: { ...DEFAULTS }, model: "logistic", hoverT: null,
  P: structuredClone(BASE_PAYOFFS), profile: "NM",
  net: { kind: "scale-free", spread: 0.5, mod: 0.2, seeds: 3, seedNo: 7, step: 0, timer: null },
  tipM: 0.3,
};

/* ---------------------------------------------------------------- chart */
// One small line-chart drawer for all three SVG charts.
function lineChart(svg, c) {
  const vb = svg.viewBox.baseVal, W = vb.width, H = vb.height;
  const m = { l: 52, r: c.right ?? 24, t: 12, b: 32 };
  const sx = (v) => m.l + ((v - c.x0) / (c.x1 - c.x0)) * (W - m.l - m.r);
  const sy = (v) => H - m.b - ((v - c.y0) / (c.y1 - c.y0)) * (H - m.t - m.b);
  let s = "";
  for (const v of c.yTicks) s += `<line class="grid" x1="${m.l}" x2="${W - m.r}" y1="${sy(v)}" y2="${sy(v)}"/><text x="${m.l - 8}" y="${sy(v) + 4}" text-anchor="end">${c.yFmt(v)}</text>`;
  for (const v of c.xTicks) s += `<text x="${sx(v)}" y="${H - 10}" text-anchor="middle">${c.xFmt?.(v) ?? v}</text>`;
  s += `<line class="ax" x1="${m.l}" x2="${W - m.r}" y1="${sy(c.y0)}" y2="${sy(c.y0)}"/>`;
  if (c.y0 < 0) s += `<line class="ax" x1="${m.l}" x2="${W - m.r}" y1="${sy(0)}" y2="${sy(0)}"/>`;
  for (const v of c.vlines ?? []) s += `<line class="vl" x1="${sx(v.x)}" x2="${sx(v.x)}" y1="${m.t}" y2="${sy(c.y0)}"/>${v.label ? `<text class="vl-t" x="${sx(v.x) + 6}" y="${m.t + 12}">${v.label}</text>` : ""}`;
  const ends = [];
  for (const l of c.series) {
    s += `<path class="line ${l.cls}" d="${l.pts.map(([x, y], i) => `${i ? "L" : "M"}${sx(x).toFixed(1)} ${sy(y).toFixed(1)}`).join("")}"/>`;
    if (l.label) ends.push({ y: sy(l.pts.at(-1)[1]), label: l.label, cls: l.lcls ?? "" });
  }
  ends.sort((a, b) => a.y - b.y);
  ends.forEach((e, i) => { if (i && e.y - ends[i - 1].y < 14) e.y = ends[i - 1].y + 14; });
  for (const e of ends) s += `<text class="${e.cls}" x="${W - m.r + 8}" y="${e.y + 4}">${e.label}</text>`;
  for (const d of c.dots ?? []) s += `<circle class="pt" cx="${sx(d.x)}" cy="${sy(d.y)}" r="6"/>`;
  svg.innerHTML = s;
  return { inv: (clientX) => { const r = svg.getBoundingClientRect(); return c.x0 + (((clientX - r.left) * W) / r.width - m.l) / (W - m.l - m.r) * (c.x1 - c.x0); } };
}

/* ---------------------------------------------------------------- network drawing */
function drawNet(canvas, g, state, r0 = 3) {
  const dpr = devicePixelRatio || 1, w = canvas.clientWidth, h = canvas.clientHeight;
  if (canvas.width !== Math.round(w * dpr)) { canvas.width = Math.round(w * dpr); canvas.height = Math.round(h * dpr); }
  const ctx = canvas.getContext("2d"), pad = 22;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, w, h);
  const P = g.pos.map(([x, y]) => [pad + x * (w - 2 * pad), pad + y * (h - 2 * pad)]);
  ctx.strokeStyle = "rgba(23,20,15,0.2)"; ctx.lineWidth = 1; ctx.beginPath();
  for (const [i, j] of g.edges) { ctx.moveTo(...P[i]); ctx.lineTo(...P[j]); }
  ctx.stroke();
  for (let i = 0; i < g.n; i++) {
    const r = r0 + Math.sqrt(g.deg[i]) * r0 * 0.5, [x, y] = P[i];
    ctx.beginPath(); ctx.arc(x, y, r, 0, 6.2832);
    if (state[i] === EXPO) { ctx.fillStyle = RED; ctx.fill(); }
    else if (state[i] === SUSC) { ctx.fillStyle = PAPER; ctx.fill(); ctx.strokeStyle = "rgba(23,20,15,0.55)"; ctx.lineWidth = 1.5; ctx.stroke(); }
    else {
      ctx.fillStyle = INK; ctx.fill();
      ctx.beginPath(); ctx.arc(x, y, r + 3, 0, 6.2832); ctx.strokeStyle = INK; ctx.lineWidth = 1.2; ctx.stroke();
    }
  }
}

/* ---------------------------------------------------------------- 01 game */
function gameKind(an) {
  const P = an.P;
  if (an.sharerDom === "S" && an.platformDom === "W" && P.NM[0] > P.SW[0] && P.NM[1] > P.SW[1]) return "Prisoner's dilemma";
  if (an.platformDom === "M" && an.brS.M.length === 1 && an.brS.M[0] === "N") return "Deterrence game";
  if (an.nash.length >= 2) return "Coordination game";
  if (!an.nash.length) return "Inspection game";
  return "One stable outcome";
}

function renderMatrix(box, explainEl, P, { profile, onPick } = {}) {
  const an = analyse(P);
  let h = `<div class="matrix__h"></div>` +
    ["W", "M"].map((p) => `<div class="matrix__h matrix__h--col"><b>${p === "W" ? "Weak" : "Strong"}</b>platform moderation</div>`).join("");
  ["S", "N"].forEach((s, ri) => {
    h += `<div class="matrix__h matrix__h--row"><b>${s === "S" ? "Spread" : "Stay quiet"}</b>sharer</div>`;
    for (const p of ["W", "M"]) {
      const k = s + p, [us, up] = P[k], eq = an.nash.includes(k);
      h += `<button type="button" class="cell${ri ? " r2" : ""}${eq ? " is-eq" : ""}${k === profile ? " is-active" : ""}" data-k="${k}" aria-label="${words(k)}: sharer ${num(us)}, platform ${num(up)}${eq ? ", stable" : ""}">
        <span class="cell__pay"><span class="pa${an.brS[p].includes(s) ? " br" : ""}">${num(us)}</span><br><span class="pb${an.brP[s].includes(p) ? " br" : ""}">${num(up)}</span></span>
        <span class="cell__tags">${eq ? `<span class="tag tag--eq">Stable</span>` : ""}${an.pareto.includes(k) ? `<span class="tag">Efficient</span>` : ""}</span></button>`;
    }
  });
  box.innerHTML = h;
  const explain = (k) => {
    const moves = deviations(P, k).filter((d) => d.gain > 1e-9);
    explainEl.innerHTML = `<strong>${words(k)}.</strong> ` + (moves.length
      ? moves.map((d) => `The ${d.who.toLowerCase()} would switch to ${WORD[d.to]} and gain ${num(d.gain)}.`).join(" ")
      : "Neither side gains by switching alone, so this is where the game settles.");
    box.querySelectorAll(".cell").forEach((c) => c.classList.toggle("is-active", c.dataset.k === k));
  };
  box.querySelectorAll(".cell").forEach((c) => {
    c.addEventListener("click", () => { explain(c.dataset.k); onPick?.(c.dataset.k); });
    c.addEventListener("mouseenter", () => explain(c.dataset.k));
  });
  explain(profile ?? (an.nash[0] ?? "SW"));
  return an;
}

function renderGame() {
  const an = renderMatrix($("#matrix"), $("#matrix-explain"), S.P, { profile: S.profile, onPick: (k) => (S.profile = k) });
  const P = S.P, eq = an.nash;
  const dom = [an.sharerDom && `Sharer: ${WORD[an.sharerDom]}`, an.platformDom && `Platform: ${WORD[an.platformDom]}`].filter(Boolean);
  const mixed = an.mixed.exists
    ? `Sharer spreads ${Math.round(an.mixed.p * 100)}% of the time, platform is weak ${Math.round(an.mixed.q * 100)}%`
    : "None inside (0, 1)";
  $("#findings").innerHTML =
    kpi("Type of game", gameKind(an)) +
    kpi("Stable outcome", eq.length ? eq.map((k) => `${words(k)}<small>payoffs (${num(P[k][0])}, ${num(P[k][1])}). Neither side gains by moving alone.</small>`).join("") : "No stable pair in pure strategies") +
    kpi("Dominant strategy", dom.length ? dom.join("<br>") : "None", dom.length ? "Best whatever the other side does." : "") +
    kpi("Mixed equilibrium", mixed) +
    kpi("Best for both", an.pareto.map(words).join("<br>"), an.pareto.includes(eq[0]) ? "" : "The stable outcome is not on this list.");
  $("#payoff-now").textContent = eq.length ? `stable: ${eq.map((k) => k.split("").join(" / ")).join(", ")}` : "no stable pair";
}

function initPayoffFields() {
  const keys = [["SW", "Spread · weak"], ["SM", "Spread · strong"], ["NW", "Quiet · weak"], ["NM", "Quiet · strong"]];
  $("#payoff-fields").innerHTML = keys.flatMap(([k, l]) => [0, 1].map((i) =>
    `<label class="num"><span>${i ? "Platform" : "Sharer"} · ${l}</span><input type="number" step="any" data-k="${k}" data-i="${i}" value="${S.P[k][i]}" /></label>`)).join("");
  const fields = [...document.querySelectorAll("#payoff-fields input")];
  const sync = () => fields.forEach((f) => (f.value = S.P[f.dataset.k][f.dataset.i]));
  fields.forEach((f) => f.addEventListener("input", () => {
    const bad = fields.filter((x) => x.value.trim() === "" || !Number.isFinite(+x.value));
    fields.forEach((x) => x.setAttribute("aria-invalid", String(bad.includes(x))));
    $("#payoff-error").textContent = bad.length ? "Every payoff needs to be a number." : "";
    if (bad.length) return;
    fields.forEach((x) => (S.P[x.dataset.k][x.dataset.i] = +x.value));
    renderGame();
  }));
  $("#payoff-reset").addEventListener("click", () => {
    S.P = structuredClone(BASE_PAYOFFS); sync();
    fields.forEach((x) => x.setAttribute("aria-invalid", "false")); $("#payoff-error").textContent = "";
    renderGame();
  });
}

function initScrub() {
  const P = BASE_PAYOFFS;
  const text = `Spreading earns the sharer ${P.SW[0]} against a weak platform but costs ${num(P.SM[0])} against a strong one. The platform loses ${num(P.SW[1])} to a viral story and only pays to stop it when the story is spreading. So the platform moderates strongly, the sharer stays quiet, and the stable outcome is ${P.NM[0]} for the sharer and ${P.NM[1]} for the platform.`;
  const el = $("#scrub");
  el.innerHTML = text.split(" ").map((w) => `<span class="w${/\d/.test(w) ? " hl" : ""}">${w}</span>`).join(" ");
  const ws = el.querySelectorAll(".w");
  if (reduceMotion) return gsap.set(ws, { opacity: 1 });
  gsap.to(ws, { opacity: 1, stagger: 0.12, ease: "none", scrollTrigger: { trigger: el, start: "top 80%", end: "bottom 50%", scrub: true } });
}

/* ---------------------------------------------------------------- 02 spread */
const run = (p) => (S.model === "sir" ? sir(p) : logistic(p));

function renderSpread() {
  const p = S.p, errs = validationErrors(p);
  $("#spread-error").textContent = errs.join(" ");
  if (errs.length) return;
  for (const k of Object.keys(DEFAULTS)) { const o = $(`#o-${k}`); if (o) o.textContent = k === "population" ? int(p[k]) : k === "moderation" ? p[k].toFixed(2) : p[k]; }
  const T = p.steps, N = p.population;
  const mine = run(p), base = run({ ...p, moderation: 0 });
  const series = POLICIES.map(([name, m]) => ({ label: name, cls: "line--policy", pts: run({ ...p, moderation: m }).map((v, t) => [t, v]) }));
  series.push({ label: "You", lcls: "lab-you", cls: "line--you", pts: mine.map((v, t) => [t, v]) });
  const tick = Math.ceil(T / 5 / 5) * 5;
  const chart = lineChart($("#spread-chart"), {
    x0: 0, x1: T, y0: 0, y1: N, right: 120, series,
    xTicks: Array.from({ length: Math.floor(T / tick) + 1 }, (_, i) => i * tick),
    yTicks: [0, N / 4, N / 2, (3 * N) / 4, N].map(Math.round), yFmt: compact,
    vlines: S.hoverT == null ? [] : [{ x: S.hoverT }],
  });
  const a = summarise(mine, N), b = summarise(base, N);
  const cut = b.final > 0 ? Math.round(((b.final - a.final) / b.final) * 100) : 0;
  $("#kpis").innerHTML =
    kpi("Reached by step " + T, int(a.final), `${Math.round((a.final / N) * 100)}% of ${int(N)}`) +
    kpi("Peak sharing", int(a.peak), S.model === "sir" ? `at step ${a.peakStep}` : "") +
    kpi("Half reached", a.t50 == null ? "never" : `step ${a.t50}`, a.t50 == null ? `within ${T} steps` : "") +
    kpi("Cut vs no moderation", `${cut}%`, "fewer people reached");
  const t = S.hoverT;
  $("#spread-read").textContent = t == null ? "Hover or tap the chart to read a step." :
    `step ${t}  ·  you ${int(mine[t])}  ·  ` + POLICIES.map(([n, m]) => `${n.toLowerCase()} ${int(run({ ...p, moderation: m })[t])}`).join("  ·  ");
  $("#spread-chart").onpointermove = (e) => {
    const v = Math.max(0, Math.min(T, Math.round(chart.inv(e.clientX))));
    if (v !== S.hoverT) { S.hoverT = v; renderSpread(); }
  };
  $("#spread-chart").onpointerleave = () => { S.hoverT = null; renderSpread(); };
}

function initSpread() {
  for (const k of Object.keys(DEFAULTS)) {
    const el = $(`#${k}`);
    if (!el) continue;
    el.value = S.p[k];
    el.addEventListener("input", () => { S.p[k] = +el.value; renderSpread(); renderTipping(); });
  }
  $("#model-seg").addEventListener("click", (e) => {
    const b = e.target.closest("button"); if (!b) return;
    S.model = b.dataset.v;
    $("#model-seg").querySelectorAll("button").forEach((x) => x.setAttribute("aria-checked", String(x === b)));
    $("#debunk-field").hidden = S.model !== "sir";
    renderSpread(); renderTipping();
  });
  $("#spread-reset").addEventListener("click", () => {
    S.p = { ...DEFAULTS };
    for (const k of Object.keys(DEFAULTS)) if ($(`#${k}`)) $(`#${k}`).value = S.p[k];
    renderSpread(); renderTipping();
  });
}

/* ---------------------------------------------------------------- 03 network */
let graph, hist;
function simulateNet() {
  const n = S.net;
  graph = makeGraph(n.kind, 60, n.seedNo);
  hist = runNetwork(graph, { seeds: n.seeds, spread: n.spread, moderation: n.mod, steps: 15, seed: n.seedNo + 100 });
}

function renderNet() {
  const n = S.net, h = hist[n.step];
  $("#o-spread").textContent = n.spread.toFixed(2); $("#o-netmod").textContent = n.mod.toFixed(2);
  $("#o-seeds").textContent = n.seeds; $("#o-step").textContent = `${n.step} of 15`;
  drawNet($("#net-canvas"), graph, h.state, 3.4);
  $("#net-kpis").innerHTML =
    kpi("Reached", `${h.exposed}`, `of ${graph.n} accounts`) + kpi("Sharing now", `${h.active}`, `+${h.fresh} this step`) + kpi("Moderated", `${h.moderated}`, "quarantined");
  lineChart($("#net-chart"), {
    x0: 0, x1: 15, y0: 0, y1: graph.n, right: 96, xTicks: [0, 5, 10, 15], yTicks: [0, 20, 40, 60], yFmt: String,
    vlines: [{ x: n.step }],
    series: [
      { label: "Reached", lcls: "lab-ink", cls: "line--ink", pts: hist.map((r, t) => [t, r.exposed]) },
      { label: "Sharing", lcls: "lab-you", cls: "line--you", pts: hist.map((r, t) => [t, r.active]) },
      { label: "Moderated", cls: "line--dash", pts: hist.map((r, t) => [t, r.moderated]) },
    ],
  });
  $("#step").value = n.step;
}

function initNet() {
  const n = S.net;
  const rebuild = (fresh) => { if (fresh) simulateNet(); else hist = runNetwork(graph, { seeds: n.seeds, spread: n.spread, moderation: n.mod, steps: 15, seed: n.seedNo + 100 }); renderNet(); };
  const stop = () => { clearInterval(n.timer); n.timer = null; $("#net-play").textContent = "Play"; $("#net-play").setAttribute("aria-pressed", "false"); };
  for (const [id, key] of [["spread", "spread"], ["netmod", "mod"], ["seeds", "seeds"]]) {
    $(`#${id}`).value = n[key];
    $(`#${id}`).addEventListener("input", (e) => { n[key] = +e.target.value; rebuild(false); });
  }
  $("#step").addEventListener("input", (e) => { stop(); n.step = +e.target.value; renderNet(); });
  $("#net-seg").addEventListener("click", (e) => {
    const b = e.target.closest("button"); if (!b) return;
    n.kind = b.dataset.v; n.step = 0; stop();
    $("#net-seg").querySelectorAll("button").forEach((x) => x.setAttribute("aria-checked", String(x === b)));
    rebuild(true);
  });
  $("#net-new").addEventListener("click", () => { n.seedNo = (n.seedNo * 7 + 3) % 1000; n.step = 0; stop(); rebuild(true); });
  $("#net-play").addEventListener("click", () => {
    if (n.timer) return stop();
    if (n.step >= 15) n.step = 0;
    $("#net-play").textContent = "Pause"; $("#net-play").setAttribute("aria-pressed", "true");
    n.timer = setInterval(() => { n.step += 1; renderNet(); if (n.step >= 15) stop(); }, 650);
    n.step += 1; renderNet();
  });
  simulateNet(); renderNet();
  new ResizeObserver(() => renderNet()).observe($("#net-canvas"));
}

/* ---------------------------------------------------------------- 04 tipping */
function renderTipping() {
  const { p } = S, m = S.tipM, viral = 5 * (p.beta / 0.35), mStar = tippingM(p.beta);
  const f = (run({ ...p, moderation: m }).at(-1)) / p.population;
  const P = endogenousPayoffs(p.beta, m, f), an = analyse(P);
  $("#o-tipm").textContent = m.toFixed(2);
  const xs = Array.from({ length: 101 }, (_, i) => i / 100);
  lineChart($("#tip-chart"), {
    x0: 0, x1: 1, y0: -5, y1: Math.ceil(viral + 0.5), right: 110,
    xTicks: [0, 0.25, 0.5, 0.75, 1], xFmt: (v) => v.toFixed(2), yTicks: [-4, 0, 4, 8].filter((v) => v <= viral + 0.5), yFmt: num,
    vlines: [{ x: mStar, label: `m* = ${mStar.toFixed(2)}` }],
    dots: [{ x: m, y: viral * (1 - m) - 4 * m }],
    series: [
      { label: "Spread", lcls: "lab-you", cls: "line--you", pts: xs.map((x) => [x, viral * (1 - x) - 4 * x]) },
      { label: "Stay quiet", lcls: "lab-ink", cls: "line--ink", pts: [[0, 0], [1, 0]] },
    ],
  });
  renderMatrix($("#tip-matrix"), $("#tip-verdict"), P, { profile: an.nash[0] });
  $("#tip-read").innerHTML = `Under strong moderation the sharer's payoff for spreading is zero at <strong>m* = ${mStar.toFixed(2)}</strong>. At m = ${m.toFixed(2)} the stable outcome is <strong>${an.nash.length ? an.nash.map(words).join(" or ") : "mixed"}</strong>, with ${Math.round(f * 100)}% of the population reached.`;
}

function initTipping() {
  $("#tipm").value = S.tipM;
  $("#tipm").addEventListener("input", (e) => { S.tipM = +e.target.value; renderTipping(); });
  renderTipping();
}

/* ---------------------------------------------------------------- hero + motion */
function initHero() {
  const canvas = $("#hero-net"), g = makeGraph("scale-free", 70, 11);
  const h = runNetwork(g, { seeds: 3, spread: 0.55, moderation: 0.12, steps: 14, seed: 5 });
  let i = reduceMotion ? 14 : 0, timer = null;
  const draw = () => {
    drawNet(canvas, g, h[i].state, 3.2);
    $("#hero-step").textContent = `step ${i} · ${h[i].exposed} of ${g.n} reached`;
  };
  const tick = () => { i = i >= 14 ? 0 : i + 1; draw(); timer = setTimeout(tick, i === 14 ? 2600 : 700); };
  draw();
  new ResizeObserver(draw).observe(canvas);
  if (!reduceMotion) new IntersectionObserver(([e]) => { clearTimeout(timer); if (e.isIntersecting) timer = setTimeout(tick, 700); }).observe(canvas);
}

function initMotion() {
  const here = new IntersectionObserver((es) => es.forEach((e) => {
    if (e.isIntersecting) document.querySelectorAll(".mast__links a").forEach((a) => a.classList.toggle("is-here", a.getAttribute("href") === `#${e.target.id}`));
  }), { rootMargin: "-40% 0px -55% 0px" });
  document.querySelectorAll("main section[id]").forEach((s) => here.observe(s));
  if (reduceMotion) return;
  gsap.from(".hero__title .line > span", { yPercent: 110, duration: 1.1, ease: "power4.out", stagger: 0.12, delay: 0.1 });
  gsap.from([".hero .kicker", ".hero__sub", ".hero__ctas", ".hero__fig"], { opacity: 0, y: 18, duration: 0.9, ease: "power3.out", stagger: 0.1, delay: 0.45 });
  ScrollTrigger.batch(".reveal", {
    start: "top 88%", once: true,
    onEnter: (els) => gsap.fromTo(els, { opacity: 0, y: 28 }, { opacity: 1, y: 0, duration: 0.9, ease: "power3.out", stagger: 0.1 }),
  });
}

/* ---------------------------------------------------------------- boot */
initHero();
initPayoffFields(); renderGame(); initScrub();
initSpread(); renderSpread();
initNet();
initTipping();
initMotion();
