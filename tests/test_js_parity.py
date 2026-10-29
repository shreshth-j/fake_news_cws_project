"""The website's JS model (web/src/model.js) must agree with the Python source of truth."""
import itertools
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from src.equilibrium import analyze_game, compute_dominant_strategies, compute_pareto_efficiency, compute_tipping_points
from src.payoff_model import compute_endogenous_payoffs
from src.propagation import SimulationParameters, run_propagation_simulation

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")

GRID = [
    dict(population=10000, initialExposed=100, beta=b, moderation=m, steps=30, debunk=0.05)
    for b, m in itertools.product([0.1, 0.35, 0.6, 0.9], [0.0, 0.25, 0.55, 0.85, 1.0])
]


def test_js_model_matches_python():
    out = subprocess.run(["node", str(ROOT / "web" / "scripts" / "parity.mjs")],
                         input=json.dumps(GRID), capture_output=True, text=True, check=True)
    results = json.loads(out.stdout)
    assert len(results) == len(GRID)
    for g, js in zip(GRID, results):
        kw = dict(population=g["population"], initial_exposed=g["initialExposed"], beta=g["beta"],
                  moderation_effectiveness=g["moderation"], time_steps=g["steps"], debunking_rate=g["debunk"])
        lg = run_propagation_simulation(SimulationParameters(**kw))
        sr = run_propagation_simulation(SimulationParameters(model_type="sir", **kw))
        assert js["logistic"] == pytest.approx(list(lg.exposure)), g
        assert js["sir"] == pytest.approx(list(sr.exposure)), g

        mx = compute_endogenous_payoffs(g["beta"], g["moderation"], lg.final_exposure / g["population"])
        py = {"SW": (mx.sharer_SW, mx.platform_SW), "SM": (mx.sharer_SM, mx.platform_SM),
              "NW": (mx.sharer_NW, mx.platform_NW), "NM": (mx.sharer_NM, mx.platform_NM)}
        for k, v in py.items():
            assert js["payoffs"][k] == pytest.approx(v), (g, k)

        an = analyze_game(mx)
        assert js["nash"] == [e.sharer_strategy + e.platform_strategy for e in an.pure_equilibria], g
        assert js["mixed"] == an.mixed_equilibrium.exists_interior, g
        assert js["pareto"] == ["".join(p) for p in compute_pareto_efficiency(mx)], g
        dom = compute_dominant_strategies(mx, an.best_responses)
        assert js["dominant"] == [dom.sharer_dominant, dom.platform_dominant], g
        assert js["tipping"] == pytest.approx(compute_tipping_points(beta=g["beta"]).tipping_m_sharer), g
