// Reads a JSON array of parameter sets on stdin, prints the JS model's results.
// Used by tests/test_js_parity.py to compare with the Python source of truth.
import { logistic, sir, endogenousPayoffs, analyse, tippingM } from "../src/model.js";

let input = "";
process.stdin.on("data", (c) => (input += c));
process.stdin.on("end", () => {
  const out = JSON.parse(input).map((p) => {
    const lg = logistic(p);
    const payoffs = endogenousPayoffs(p.beta, p.moderation, lg.at(-1) / p.population);
    const an = analyse(payoffs);
    return {
      logistic: lg, sir: sir(p), payoffs,
      nash: an.nash, mixed: an.mixed.exists, pareto: an.pareto,
      dominant: [an.sharerDom, an.platformDom], tipping: tippingM(p.beta),
    };
  });
  process.stdout.write(JSON.stringify(out));
});
