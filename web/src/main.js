import "@fontsource-variable/geist";
import "@fontsource-variable/geist-mono";
import "@fontsource-variable/newsreader/opsz.css";
import "@fontsource-variable/newsreader/opsz-italic.css";
import "./style.css";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import {
  DEFAULTS, POLICIES, BASE_PAYOFFS, SUSC, EXPO, MODR,
  validationErrors, logistic, sir, summarise, analyse, deviations, endogenousPayoffs, tippingM, makeGraph, runNetwork,
} from "./model.js";

gsap.registerPlugin(ScrollTrigger);

const $ = (s) => document.querySelector(s);
const reduceMotion = matchMedia("(prefers-reduced-motion: reduce)").matches;
// Canvas colours come from the active theme's CSS variables.
let C = {};
const readColors = () => {
  const s = getComputedStyle(document.documentElement), v = (k) => s.getPropertyValue(k).trim();
  C = { accent: v("--accent"), bg2: v("--bg-2"), cool: v("--cool"), fg: v("--fg-rgb"), acc: v("--accent-rgb") };
};
const easeOutBack = (x) => 1 + 2.7 * (x - 1) ** 3 + 1.7 * (x - 1) ** 2;
const int = (v) => Math.round(v).toLocaleString("en-IN");
const num = (v) => (Number.isInteger(v) ? String(v) : v.toFixed(2)).replace("-", "−");
const compact = (v) => (v >= 1000 ? `${+(v / 1000).toFixed(1)}k` : String(v));
const WORD = { S: "spread", N: "stay quiet", W: "weak moderation", M: "strong moderation" };
const words = (k) => `${WORD[k[0]]} / ${WORD[k[1]]}`;
// n (optional) marks a numeric value that countUp() animates; sfx is appended while counting.
const kpi = (dt, dd, small = "", n = null, sfx = "") =>
  `<div><dt>${dt}</dt><dd${n == null ? "" : ` data-n="${n}" data-sfx="${sfx}"`}>${dd}${small ? `<small>${small}</small>` : ""}</dd></div>`;

function countUp(box) {
  box._tw?.forEach((t) => t.kill());
  const prev = box._v ?? [], now = [];
  box._tw = [...box.querySelectorAll("dd[data-n]")].map((dd, i) => {
    const to = +dd.dataset.n, from = prev[i] ?? 0, node = dd.firstChild;
    now[i] = to;
    if (reduceMotion || from === to) return null;
    const o = { v: from };
    return gsap.to(o, { v: to, duration: 0.7, ease: "power3.out", onUpdate: () => (node.nodeValue = int(o.v) + dd.dataset.sfx) });
  }).filter(Boolean);
  box._v = now;
}

const S = {
  p: { ...DEFAULTS }, model: "logistic", hoverT: null,
  P: structuredClone(BASE_PAYOFFS), profile: "NM",
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
    s += `<path class="line ${l.cls}" ${l.cls === "line--dash" ? "" : 'pathLength="1"'} d="${l.pts.map(([x, y], i) => `${i ? "L" : "M"}${sx(x).toFixed(1)} ${sy(y).toFixed(1)}`).join("")}"/>`;
    if (l.label) ends.push({ y: sy(l.pts.at(-1)[1]), label: l.label, cls: l.lcls ?? "" });
  }
  ends.sort((a, b) => a.y - b.y);
  ends.forEach((e, i) => { if (i && e.y - ends[i - 1].y < 14) e.y = ends[i - 1].y + 14; });
  for (const e of ends) s += `<text class="end ${e.cls}" x="${W - m.r + 8}" y="${e.y + 4}">${e.label}</text>`;
  for (const d of c.dots ?? []) s += `<circle class="pt" cx="${sx(d.x)}" cy="${sy(d.y)}" r="6"/>`;
  svg.innerHTML = s;
  return { inv: (clientX) => { const r = svg.getBoundingClientRect(); return c.x0 + (((clientX - r.left) * W) / r.width - m.l) / (W - m.l - m.r) * (c.x1 - c.x0); } };
}

/* ---------------------------------------------------------------- network drawing */
// fx: prev = previous step's states (null for a still frame), p = 0..1 progress of the step
// transition, t = clock in ms for the idle pulse. Newly reached nodes get a line from their
// source, a pop and a ripple; newly moderated nodes get a ring that closes in.
function drawNet(canvas, g, state, r0 = 3, fx = {}) {
  const dpr = devicePixelRatio || 1, w = canvas.clientWidth, h = canvas.clientHeight;
  if (!w || !h) return;
  if (canvas.width !== Math.round(w * dpr)) { canvas.width = Math.round(w * dpr); canvas.height = Math.round(h * dpr); }
  const { prev = null, p = 1, t = 0 } = fx, ctx = canvas.getContext("2d"), pad = 22;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, w, h);
  const P = g.pos.map(([x, y]) => [pad + x * (w - 2 * pad), pad + y * (h - 2 * pad)]);
  const fresh = (i) => prev && state[i] === EXPO && prev[i] === SUSC;
  const calmed = (i) => prev && state[i] === MODR && prev[i] === EXPO;
  const circle = (x, y, r) => { ctx.beginPath(); ctx.arc(x, y, r, 0, 6.2832); };

  ctx.strokeStyle = `rgba(${C.fg},0.13)`; ctx.lineWidth = 1; ctx.beginPath();
  for (const [i, j] of g.edges) { ctx.moveTo(...P[i]); ctx.lineTo(...P[j]); }
  ctx.stroke();

  ctx.strokeStyle = C.accent; ctx.lineWidth = 1.8; ctx.lineCap = "round"; ctx.beginPath();
  const reach = Math.min(1, p * 2.8);
  for (const [i, j] of g.edges) {
    const a = fresh(j) && prev[i] === EXPO ? i : fresh(i) && prev[j] === EXPO ? j : -1;
    if (a < 0) continue;
    const b = a === i ? j : i;
    ctx.moveTo(...P[a]); ctx.lineTo(P[a][0] + (P[b][0] - P[a][0]) * reach, P[a][1] + (P[b][1] - P[a][1]) * reach);
  }
  ctx.stroke();

  for (let i = 0; i < g.n; i++) {
    const r = r0 + Math.sqrt(g.deg[i]) * r0 * 0.5, [x, y] = P[i], q = Math.max(0, (p - 0.3) / 0.7);
    if (state[i] === SUSC || (fresh(i) && p < 0.3)) {
      circle(x, y, r); ctx.fillStyle = C.bg2; ctx.fill(); ctx.strokeStyle = `rgba(${C.fg},0.5)`; ctx.lineWidth = 1.5; ctx.stroke();
    } else if (state[i] === EXPO) {
      const born = fresh(i), k = born ? easeOutBack(q) : 1 + 0.07 * Math.sin(t / 380 + i);
      if (born && q < 1) { circle(x, y, r * (1 + q * 3.4)); ctx.strokeStyle = `rgba(${C.acc},${0.75 * (1 - q)})`; ctx.lineWidth = 1.5; ctx.stroke(); }
      ctx.shadowColor = C.accent; ctx.shadowBlur = 14;
      circle(x, y, r * k); ctx.fillStyle = C.accent; ctx.fill();
      ctx.shadowBlur = 0;
    } else {
      const close = calmed(i) ? (1 - p) * 10 : 0;
      circle(x, y, r); ctx.fillStyle = C.cool; ctx.fill();
      circle(x, y, r + 3 + close); ctx.strokeStyle = C.cool; ctx.globalAlpha = 0.9 - close * 0.05; ctx.lineWidth = 1.3; ctx.stroke(); ctx.globalAlpha = 1;
    }
  }
}

// Keeps a canvas painting at display rate while it is on screen (or once per kick() under reduced motion).
// frame() returns { g, state, prev, step }; moving forward a step triggers the transition.
function netView(canvas, frame, r0) {
  let last = -1, t0 = 0, fwd = false, raf = 0;
  const paint = (now) => {
    const f = frame();
    if (f.step !== last) { fwd = last >= 0 && f.step > last; last = f.step; t0 = now; }
    const live = fwd && !reduceMotion;
    drawNet(canvas, f.g, f.state, r0, { prev: live ? f.prev : null, p: live ? Math.min(1, (now - t0) / 900) : 1, t: now });
  };
  addEventListener("themechange", () => paint(performance.now()));
  if (reduceMotion) { new ResizeObserver(() => paint(performance.now())).observe(canvas); return { kick: () => paint(performance.now()) }; }
  const run = (now) => { paint(now); raf = requestAnimationFrame(run); };
  new IntersectionObserver(([e]) => { cancelAnimationFrame(raf); if (e.isIntersecting) raf = requestAnimationFrame(run); }).observe(canvas);
  return { kick() {} };
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

const setOf = (a) => `{${a.join(", ")}}`;
const cmp = (a, b) => (a > b ? ">" : a < b ? "<" : "=");
const pair = (k, P) => `(${num(P[k][0])}, ${num(P[k][1])})`;

function renderMatrix(box, explainEl, P, { profile, onPick } = {}) {
  const an = analyse(P);
  const dom = (who, k) => ((who === 1 ? an.sharerDom : an.platformDom) === k ? `<i class="tag tag--dom">Dominant strategy</i>` : "");
  let h = `<div class="matrix__corner"><span><b>Player 2</b> platform →</span><span><b>Player 1</b> sharer ↓</span></div>`;
  for (const p of ["W", "M"]) h += `<div class="matrix__h matrix__h--col"><span class="who">Platform</span><span class="strat"><i>${p}</i>${p === "W" ? "Weak" : "Strong"} moderation</span>${dom(2, p)}</div>`;
  ["S", "N"].forEach((s, ri) => {
    h += `<div class="matrix__h matrix__h--row${ri ? " r2" : ""}"><span class="who">Sharer</span><span class="strat"><i>${s}</i>${s === "S" ? "Spread" : "Stay quiet"}</span>${dom(1, s)}</div>`;
    for (const p of ["W", "M"]) {
      const k = s + p, [us, up] = P[k], eq = an.nash.includes(k), b1 = an.brS[p].includes(s), b2 = an.brP[s].includes(p);
      const who = [b1 && "sharer", b2 && "platform"].filter(Boolean).join(" and ");
      h += `<button type="button" class="cell${ri ? " r2" : ""}${eq ? " is-eq" : ""}${k === profile ? " is-active" : ""}" data-k="${k}" aria-label="${words(k)}: sharer payoff ${num(us)}${b1 ? " (best response)" : ""}, platform payoff ${num(up)}${b2 ? " (best response)" : ""}${eq ? ". Nash equilibrium" : ""}">
        <span class="cell__top">${eq ? `<span class="tag tag--eq">Nash equilibrium</span>` : ""}${an.pareto.includes(k) ? `<span class="tag">Pareto efficient</span>` : ""}</span>
        <span class="cell__pay"><span><span class="u u--1${b1 ? " br" : ""}">${num(us)}</span><span class="lbl">u₁ sharer</span></span><span><span class="u${b2 ? " br" : ""}">${num(up)}</span><span class="lbl">u₂ platform</span></span></span>
        <span class="cell__foot">${who ? `Best response of: <b>${who}</b>` : "Best response of: neither"}</span></button>`;
    }
  });
  box.innerHTML = h;
  const explain = (k) => {
    const moves = deviations(P, k).filter((d) => d.gain > 1e-9);
    explainEl.innerHTML = `<strong>${words(k)}.</strong> ` + (moves.length
      ? moves.map((d) => `The ${d.who.toLowerCase()} can gain ${num(d.gain)} by switching alone to ${WORD[d.to]}, so this is not an equilibrium.`).join(" ")
      : "Neither player gains by deviating alone: each is already playing a best response, so this profile is a Nash equilibrium.");
    box.querySelectorAll(".cell").forEach((c) => c.classList.toggle("is-active", c.dataset.k === k));
  };
  box.querySelectorAll(".cell").forEach((c) => {
    c.addEventListener("click", () => { explain(c.dataset.k); onPick?.(c.dataset.k); });
    c.addEventListener("mouseenter", () => explain(c.dataset.k));
  });
  explain(profile ?? (an.nash[0] ?? "SW"));
  return an;
}

// Step-by-step solution, generated from the same analysis so it follows edited payoffs.
function renderProof(an, P) {
  const br1 = ["W", "M"].map((p) => `u₁(S,${p}) = ${num(P["S" + p][0])} ${cmp(P["S" + p][0], P["N" + p][0])} u₁(N,${p}) = ${num(P["N" + p][0])}  ⇒  BR₁(${p}) = <b>${setOf(an.brS[p])}</b>`);
  const br2 = ["S", "N"].map((s) => `u₂(${s},W) = ${num(P[s + "W"][1])} ${cmp(P[s + "W"][1], P[s + "M"][1])} u₂(${s},M) = ${num(P[s + "M"][1])}  ⇒  BR₂(${s}) = <b>${setOf(an.brP[s])}</b>`);
  const domLine = (name, d, a, b) => `${name}: ${a} ; ${b}  ⇒  ` + (d ? `<b>${WORD[d]} is strictly dominant</b>` : "<b>no strictly dominant strategy</b>");
  const checks = ["SW", "SM", "NW", "NM"].map((k) => {
    const [s, p] = k, ok1 = an.brS[p].includes(s), ok2 = an.brP[s].includes(p);
    return `(${s},${p}): ${s} ∈ BR₁(${p}) ${ok1 ? "✓" : "✗"}   ${p} ∈ BR₂(${s}) ${ok2 ? "✓" : "✗"}  ⇒  ${ok1 && ok2 ? `<b>Nash equilibrium ${pair(k, P)}</b>` : "<em>not an equilibrium</em>"}`;
  });
  const m = an.mixed, nashPareto = an.nash.length && an.nash.every((k) => an.pareto.includes(k));
  const items = [
    ["Best responses", "For each choice of the opponent, find the reply that maximises a player's own payoff: BR(s₋ᵢ) = argmaxₛ uᵢ(s, s₋ᵢ).", [...br1, ...br2]],
    ["Dominant strategies", "A strategy is strictly dominant if it is the unique best response to every choice of the opponent.",
      [domLine("Sharer", an.sharerDom, `BR₁(W) = ${setOf(an.brS.W)}`, `BR₁(M) = ${setOf(an.brS.M)}`), domLine("Platform", an.platformDom, `BR₂(S) = ${setOf(an.brP.S)}`, `BR₂(N) = ${setOf(an.brP.N)}`)]],
    ["Nash equilibrium", "A profile (s*, p*) is a Nash equilibrium when each strategy is a best response to the other: s* ∈ BR₁(p*) and p* ∈ BR₂(s*).",
      [...checks, an.nash.length ? `Result: <b>${an.nash.map((k) => `(${k[0]}, ${k[1]})`).join(" and ")}</b> in pure strategies.` : "Result: <b>no pure-strategy equilibrium</b>."]],
    ["Efficiency and mixing", "An outcome is Pareto efficient if no other outcome makes one player better off without hurting the other. A mixed equilibrium makes each player indifferent between their two strategies.",
      [`Pareto efficient: <b>${an.pareto.map((k) => `(${k[0]},${k[1]})`).join(", ")}</b>`,
        an.nash.length ? `Equilibrium is ${nashPareto ? "<b>Pareto efficient</b>" : "<b>not Pareto efficient</b>"}` : "",
        `Indifference gives p* = P(S) = <b>${m.p == null ? "undefined" : m.p.toFixed(2)}</b>, q* = P(W) = <b>${m.q == null ? "undefined" : m.q.toFixed(2)}</b>  ⇒  ` + (m.exists ? "<b>interior mixed equilibrium exists</b>" : "<b>outside (0, 1): no interior mixed equilibrium</b>")].filter(Boolean)],
  ];
  $("#proof").innerHTML = items.map(([h, d, lines]) => `<li><div><h4>${h}</h4><p>${d}</p></div><div class="eqs">${lines.join("<br>")}</div></li>`).join("");
}

const CONCEPTS = [
  ["Normal-form game", "Γ = ⟨N, (Sᵢ), (uᵢ)⟩", "A game written as a matrix: the players, each player's set of strategies, and a payoff for every combination of choices. Players choose simultaneously.", () => "Two players, two strategies each, four outcomes."],
  ["Payoff (utility)", "uᵢ(s₁, s₂)", "A number that ranks outcomes for one player. Only the order and relative size matter.", (an, P) => `Spreading against a weak platform pays the sharer ${num(P.SW[0])} but costs the platform ${num(-P.SW[1])}.`],
  ["Best response", "BRᵢ(s₋ᵢ) = argmax uᵢ(s, s₋ᵢ)", "The strategy that gives a player the highest payoff against a given choice by the opponent.", (an) => `BR₁(W) = ${setOf(an.brS.W)}, BR₁(M) = ${setOf(an.brS.M)}; BR₂(S) = ${setOf(an.brP.S)}, BR₂(N) = ${setOf(an.brP.N)}.`],
  ["Dominant strategy", "uᵢ(s, s₋ᵢ) > uᵢ(s′, s₋ᵢ) for all s₋ᵢ", "A strategy that pays strictly more than every alternative whatever the opponent does. A rational player never plays a dominated strategy.", (an) => [an.sharerDom && `Sharer: ${WORD[an.sharerDom]}`, an.platformDom && `Platform: ${WORD[an.platformDom]}`].filter(Boolean).join("; ") || "Neither player has one."],
  ["Nash equilibrium", "uᵢ(s*ᵢ, s*₋ᵢ) ≥ uᵢ(sᵢ, s*₋ᵢ) for all sᵢ", "A profile of strategies in which no player can gain by changing strategy while the other keeps theirs. It is a best response to a best response.", (an, P) => an.nash.length ? `${an.nash.map((k) => `${words(k)} ${pair(k, P)}`).join("; ")}.` : "No pure-strategy equilibrium."],
  ["Pareto efficiency", "no s′ with uᵢ(s′) ≥ uᵢ(s), one strict", "An outcome is efficient if no other outcome improves one player without making the other worse off. Equilibria need not be efficient.", (an) => `Efficient: ${an.pareto.map((k) => `(${k[0]},${k[1]})`).join(", ")}.`],
  ["Mixed strategy", "p* = (u₂(N,M) − u₂(N,W)) / Δ", "Choosing among strategies with fixed probabilities. In a mixed equilibrium each player is indifferent between the strategies they randomise over.", (an) => (an.mixed.exists ? `p* = ${an.mixed.p.toFixed(2)}, q* = ${an.mixed.q.toFixed(2)}.` : "Indifference probabilities fall outside (0, 1), so none exists.")],
  ["Deterrence game", "BR₁(M) = N with M dominant", "A game in which a credible, dominant punishment makes the would-be offender comply.", (an) => `Classified as: ${gameKind(an)}.`],
  ["Logistic diffusion", "Iₜ₊₁ = Iₜ + β(1 − m) Iₜ (1 − Iₜ/N)", "Exposure grows in proportion to those already sharing and those not yet reached. Moderation m scales the sharing rate down.", () => `Default β = ${S.p.beta}, m = ${S.p.moderation}: effective rate ${(S.p.beta * (1 - S.p.moderation)).toFixed(2)}.`],
  ["Threshold (tipping) strategy", "m* = r / (r + c)", "The sharer's best response flips from spread to stay quiet once moderation passes m*, where r is the reward for spreading and c the penalty rate.", () => `m* = ${tippingM(S.p.beta).toFixed(2)} at β = ${S.p.beta}.`],
];

function renderConcepts(an, P) {
  $("#concepts-list").innerHTML = CONCEPTS.map(([n, f, d, here]) =>
    `<div class="concept" role="row"><div role="cell"><h3>${n}</h3><p class="formula">${f}</p></div><div role="cell"><p>${d}</p></div><div class="here" role="cell"><small>In this model</small>${here(an, P)}</div></div>`).join("");
}

function renderGame() {
  const an = renderMatrix($("#matrix"), $("#matrix-explain"), S.P, { profile: S.profile, onPick: (k) => (S.profile = k) });
  const P = S.P, eq = an.nash;
  const dom = [an.sharerDom && `Sharer: ${WORD[an.sharerDom]}`, an.platformDom && `Platform: ${WORD[an.platformDom]}`].filter(Boolean);
  const m = an.mixed;
  $("#findings").innerHTML =
    kpi("Type of game", gameKind(an)) +
    kpi("Nash equilibrium", eq.length ? eq.map((k) => `${words(k)}<small>Payoffs ${pair(k, P)}. Each strategy is a best response to the other.</small>`).join("") : "None in pure strategies") +
    kpi("Dominant strategy", dom.length ? dom.join("<br>") : "None", dom.length ? "Strictly better whatever the other player does." : "Each player's best reply depends on the other's choice.") +
    kpi("Mixed equilibrium", m.exists ? `P(S) = ${m.p.toFixed(2)}, P(W) = ${m.q.toFixed(2)}` : "None inside (0, 1)") +
    kpi("Pareto efficient outcomes", an.pareto.map(words).join("<br>"), an.pareto.includes(eq[0]) ? "The equilibrium is among them." : "The equilibrium is not among them.");
  $("#payoff-now").textContent = eq.length ? `Nash: ${eq.map((k) => k.split("").join(" / ")).join(", ")}` : "no pure Nash equilibrium";
  renderProof(an, P);
  renderConcepts(an, P);
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
  const text = `Spreading earns the sharer ${P.SW[0]} against a weak platform but costs ${num(P.SM[0])} against a strong one. The platform loses ${num(P.SW[1])} to a viral story and only pays to stop it when the story is spreading. So the platform moderates strongly, the sharer stays quiet, and the Nash equilibrium gives ${P.NM[0]} to the sharer and ${P.NM[1]} to the platform.`;
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
    kpi("Reached by step " + T, int(a.final), `${Math.round((a.final / N) * 100)}% of ${int(N)}`, a.final) +
    kpi("Peak sharing", int(a.peak), S.model === "sir" ? `at step ${a.peakStep}` : "", a.peak) +
    kpi("Half reached", a.t50 == null ? "never" : `step ${a.t50}`, a.t50 == null ? `within ${T} steps` : "") +
    kpi("Cut vs no moderation", `${cut}%`, "fewer people reached", cut, "%");
  countUp($("#kpis"));
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
      { label: "Stay quiet", lcls: "lab-fg", cls: "line--fg", pts: [[0, 0], [1, 0]] },
    ],
  });
  renderMatrix($("#tip-matrix"), $("#tip-verdict"), P, { profile: an.nash[0] });
  $("#tip-read").innerHTML = `Under strong moderation the sharer's payoff for spreading is zero at <strong>m* = ${mStar.toFixed(2)}</strong>. At m = ${m.toFixed(2)} the Nash equilibrium is <strong>${an.nash.length ? an.nash.map(words).join(" or ") : "mixed"}</strong>, with ${Math.round(f * 100)}% of the population reached.`;
}

function initTipping() {
  $("#tipm").value = S.tipM;
  $("#tipm").addEventListener("input", (e) => { S.tipM = +e.target.value; renderTipping(); });
  renderTipping();
}

function initTheme() {
  const root = document.documentElement;
  const apply = (t) => {
    root.dataset.theme = t;
    $("#theme-name").textContent = t === "night" ? "Paper" : "Night";
    $('meta[name="theme-color"]').content = t === "night" ? "#090c10" : "#f4efe3";
    readColors();
    dispatchEvent(new Event("themechange"));
  };
  apply(root.dataset.theme === "paper" ? "paper" : "night");
  $("#theme").addEventListener("click", () => {
    const t = root.dataset.theme === "night" ? "paper" : "night";
    apply(t);
    try { localStorage.setItem("theme", t); } catch { /* private mode: the choice just doesn't persist */ }
  });
}

/* ---------------------------------------------------------------- hero + motion */
function initHero() {
  const canvas = $("#hero-net"), g = makeGraph("scale-free", 70, 11);
  const h = runNetwork(g, { seeds: 3, spread: 0.55, moderation: 0.12, steps: 14, seed: 5 });
  let i = reduceMotion ? 14 : 0, timer = null;
  const view = netView(canvas, () => ({ g, state: h[i].state, prev: i ? h[i - 1].state : null, step: i }), 3.2);
  const label = () => ($("#hero-step").textContent = `step ${i} · ${h[i].exposed} of ${g.n} reached`);
  const tick = () => { i = i >= 14 ? 0 : i + 1; label(); view.kick(); timer = setTimeout(tick, i === 14 ? 2800 : 950); };
  label(); view.kick();
  if (!reduceMotion) new IntersectionObserver(([e]) => { clearTimeout(timer); if (e.isIntersecting) timer = setTimeout(tick, 900); }).observe(canvas);
}

// Scrolling strip of facts computed from the model, so it never drifts from the numbers below.
function initTicker() {
  const p = DEFAULTS, an = analyse(BASE_PAYOFFS), pct = (m) => Math.round((logistic({ ...p, moderation: m }).at(-1) / p.population) * 100);
  const items = [
    `Nash equilibrium <b>${an.nash.map(words).join(" or ")}</b>`,
    `With no moderation <b>${pct(0)}%</b> are reached in ${p.steps} steps`,
    `At m = 0.85 only <b>${pct(0.85)}%</b>`,
    `Tipping point <b>m* = ${tippingM(p.beta).toFixed(2)}</b> at β = ${p.beta}`,
    `Spreading pays <b>${BASE_PAYOFFS.SW[0]}</b> against a weak platform, <b>${num(BASE_PAYOFFS.SM[0])}</b> against a strong one`,
  ].map((t) => `<span>${t}</span>`).join("");
  $("#ticker").innerHTML = items + items;
}

function initMotion() {
  const here = new IntersectionObserver((es) => es.forEach((e) => {
    if (e.isIntersecting) document.querySelectorAll(".mast__links a").forEach((a) => a.classList.toggle("is-here", a.getAttribute("href") === `#${e.target.id}`));
  }), { rootMargin: "-40% 0px -55% 0px" });
  document.querySelectorAll("main section[id], .hero").forEach((s) => here.observe(s));
  if (reduceMotion) return;

  // Soft orange light that trails the pointer.
  if (matchMedia("(pointer: fine)").matches) {
    const mx = gsap.quickTo("#glow", "x", { duration: 0.9, ease: "power3" }), my = gsap.quickTo("#glow", "y", { duration: 0.9, ease: "power3" });
    gsap.set("#glow", { x: innerWidth * 0.6, y: innerHeight * 0.3 });
    addEventListener("pointermove", (e) => { mx(e.clientX); my(e.clientY); });
  }

  // Charts draw themselves the first time they scroll into view; later redraws stay still.
  const draw = new IntersectionObserver((es) => es.forEach((e) => {
    if (!e.isIntersecting) return;
    draw.unobserve(e.target);
    e.target.querySelectorAll(".line:not(.line--dash)").forEach((p, i) => { p.style.animationDelay = `${i * 0.12}s`; p.classList.add("line--draw"); });
  }), { threshold: 0.35 });
  document.querySelectorAll(".chart svg").forEach((s) => draw.observe(s));

  gsap.to(".hero__fig", { yPercent: -7, ease: "none", scrollTrigger: { trigger: ".hero", start: "top top", end: "bottom top", scrub: true } });
  gsap.from(".findings > div", { opacity: 0, x: 24, duration: 0.8, ease: "power3.out", stagger: 0.09, scrollTrigger: { trigger: ".findings", start: "top 85%", once: true } });
  gsap.from(".index__list li", { opacity: 0, y: 20, duration: 0.8, ease: "power3.out", stagger: 0.1, scrollTrigger: { trigger: ".index__list", start: "top 92%", once: true } });
  gsap.from(".hero__title .line > span", { yPercent: 110, duration: 1.1, ease: "power4.out", stagger: 0.12, delay: 0.1 });
  gsap.from([".hero .kicker", ".hero__sub", ".hero__ctas", ".hero__fig"], { opacity: 0, y: 18, duration: 0.9, ease: "power3.out", stagger: 0.1, delay: 0.45 });
  ScrollTrigger.batch(".reveal", {
    start: "top 88%", once: true,
    onEnter: (els) => gsap.fromTo(els, { opacity: 0, y: 28 }, { opacity: 1, y: 0, duration: 0.9, ease: "power3.out", stagger: 0.1 }),
  });
  // Landing on a #hash puts sections past their trigger before it can fire; show whatever is already in view.
  addEventListener("load", () => setTimeout(() => document.querySelectorAll(".reveal").forEach((el) => {
    if (el.getBoundingClientRect().top < innerHeight * 0.88 && +getComputedStyle(el).opacity === 0) gsap.to(el, { opacity: 1, y: 0, duration: 0.6 });
  }), 500), { once: true });
}

/* ---------------------------------------------------------------- boot */
initTheme(); initHero(); initTicker();
initPayoffFields(); renderGame(); initScrub();
initSpread(); renderSpread();
initTipping();
initMotion();
