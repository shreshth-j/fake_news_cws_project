"""
Unit tests for the Experiment Runner and Delayed Intervention simulation.
"""

import pytest
import numpy as np

from src.propagation import SimulationParameters, run_propagation_simulation
from src.experiment_runner import (
    run_delayed_moderation_simulation,
    sweep_sharing_rate,
    package_experiment_record,
)


def test_delayed_moderation_intermediate_impact():
    """
    Delayed moderation should result in final exposure strictly between
    immediate early moderation and no moderation.
    """
    base_params = SimulationParameters(
        population=5000,
        initial_exposed=50.0,
        beta=0.45,
        moderation_effectiveness=0.80,
        time_steps=20,
    )
    # 1. Early intervention from t=0
    early_res = run_propagation_simulation(base_params)

    # 2. Delayed intervention starting at t=8
    delayed_res = run_delayed_moderation_simulation(base_params, delay_step=8, m_intervention=0.80)

    # 3. No moderation (m=0)
    no_mod_params = SimulationParameters(
        population=5000,
        initial_exposed=50.0,
        beta=0.45,
        moderation_effectiveness=0.0,
        time_steps=20,
    )
    no_mod_res = run_propagation_simulation(no_mod_params)

    assert delayed_res.final_exposure >= early_res.final_exposure
    assert delayed_res.final_exposure <= no_mod_res.final_exposure
    assert delayed_res.exposure[8] > early_res.exposure[8]


def test_sharing_rate_sweep_monotonicity():
    """Verify that increasing transmission rate beta increases or preserves final exposure."""
    df = sweep_sharing_rate(population=2000, initial_exposed=50.0, moderation_effectiveness=0.3, time_steps=15, steps=10)
    assert len(df) == 10
    assert np.all(np.diff(df["final_exposure"].values) >= -1e-5)


def test_package_experiment_record_structure():
    """Verify packaging of an experiment record."""
    rec = package_experiment_record(
        name="Test Experiment",
        model_type="Deterministic",
        population=1000,
        initial_exposed=10.0,
        beta=0.3,
        moderation=0.5,
        time_steps=10,
        final_exposure=250.0,
        peak_exposure=250.0,
        trajectory_steps=[0, 1, 2],
        trajectory_exposure=[10.0, 50.0, 250.0],
        reduction_pct=50.0,
    )
    assert rec["name"] == "Test Experiment"
    assert rec["final_exposure"] == 250.0
    assert rec["final_exposure_pct"] == 25.0
    assert "timestamp" in rec
    assert rec["reduction_pct"] == 50.0
