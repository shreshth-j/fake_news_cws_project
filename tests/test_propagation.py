"""
Unit tests for the discrete-time propagation simulation.
"""

import pytest
import numpy as np
from src.propagation import (
    SimulationParameters,
    run_propagation_simulation,
    simulate_moderation_scenarios,
    sweep_moderation_effectiveness,
)
from src.metrics import safe_percentage_reduction


def test_propagation_single_step_calculation():
    """Verify exact formula calculation for a single time step."""
    params = SimulationParameters(
        population=1000,
        initial_exposed=100.0,
        beta=0.4,
        moderation_effectiveness=0.25,
        time_steps=1,
    )
    result = run_propagation_simulation(params)
    # Expected:
    # delta = 0.4 * (1 - 0.25) * 100 * (1 - 100/1000)
    # delta = 0.3 * 100 * 0.9 = 27.0
    # I_1 = 100.0 + 27.0 = 127.0
    assert len(result.exposure) == 2
    assert np.isclose(result.exposure[0], 100.0)
    assert np.isclose(result.exposure[1], 127.0)
    assert np.isclose(result.final_exposure, 127.0)


def test_exposure_never_exceeds_population():
    """Ensure exposure is strictly bounded by population N even under extreme growth."""
    params = SimulationParameters(
        population=500,
        initial_exposed=10.0,
        beta=2.5,  # High transmission
        moderation_effectiveness=0.0,
        time_steps=50,
    )
    result = run_propagation_simulation(params)
    assert np.all(result.exposure <= 500.0)
    assert np.all(result.exposure >= 0.0)
    assert np.isclose(result.final_exposure, 500.0)


def test_invalid_simulation_parameters():
    """Check that validation raises ValueError for out-of-bound or invalid inputs."""
    # Population <= 0
    with pytest.raises(ValueError):
        SimulationParameters(population=0).validate()
    with pytest.raises(ValueError):
        SimulationParameters(population=-100).validate()

    # Initial exposed < 0 or > population
    with pytest.raises(ValueError):
        SimulationParameters(population=100, initial_exposed=-5).validate()
    with pytest.raises(ValueError):
        SimulationParameters(population=100, initial_exposed=150).validate()

    # Beta < 0
    with pytest.raises(ValueError):
        SimulationParameters(beta=-0.1).validate()

    # Moderation out of [0, 1]
    with pytest.raises(ValueError):
        SimulationParameters(moderation_effectiveness=-0.05).validate()
    with pytest.raises(ValueError):
        SimulationParameters(moderation_effectiveness=1.05).validate()

    # Time steps < 0
    with pytest.raises(ValueError):
        SimulationParameters(time_steps=-1).validate()


def test_zero_initial_exposure():
    """When I_0 = 0, no propagation should occur; exposure remains 0."""
    params = SimulationParameters(
        population=1000,
        initial_exposed=0.0,
        beta=0.5,
        moderation_effectiveness=0.0,
        time_steps=20,
    )
    result = run_propagation_simulation(params)
    assert np.all(result.exposure == 0.0)
    assert result.final_exposure == 0.0
    assert result.peak_exposure == 0.0


def test_zero_moderation_effectiveness():
    """When m = 0, diffusion proceeds at maximum unmoderated rate."""
    p_unmoderated = SimulationParameters(
        population=1000,
        initial_exposed=50.0,
        beta=0.3,
        moderation_effectiveness=0.0,
        time_steps=10,
    )
    p_moderated = SimulationParameters(
        population=1000,
        initial_exposed=50.0,
        beta=0.3,
        moderation_effectiveness=0.5,
        time_steps=10,
    )
    res_un = run_propagation_simulation(p_unmoderated)
    res_mod = run_propagation_simulation(p_moderated)

    assert res_un.final_exposure > res_mod.final_exposure
    assert res_un.exposure[-1] > res_un.exposure[0]


def test_full_moderation_effectiveness():
    """When m = 1, (1 - m) = 0, so no new infections occur: I_t = I_0 for all t."""
    params = SimulationParameters(
        population=1000,
        initial_exposed=75.0,
        beta=0.6,
        moderation_effectiveness=1.0,
        time_steps=25,
    )
    result = run_propagation_simulation(params)
    assert np.all(np.isclose(result.exposure, 75.0))
    assert np.isclose(result.final_exposure, 75.0)
    assert np.isclose(result.peak_exposure, 75.0)


def test_safe_handling_percentage_with_zero_baselines():
    """Test safe handling of zero baselines in reduction calculations."""
    # Baseline = 0, Current = 0 -> 0.0% reduction
    assert safe_percentage_reduction(0.0, 0.0) == 0.0
    # Baseline = 0, Current = 10 -> None (cannot compute meaningful reduction from 0)
    assert safe_percentage_reduction(0.0, 10.0) is None
    # Baseline = 100, Current = 40 -> 60.0% reduction
    assert np.isclose(safe_percentage_reduction(100.0, 40.0), 60.0)

    # Result compute_reduction with zero baseline
    p_zero = SimulationParameters(population=100, initial_exposed=0.0, time_steps=5)
    res_zero = run_propagation_simulation(p_zero)
    red = res_zero.compute_reduction(res_zero)
    assert red["final_reduction_pct"] == 0.0
    assert red["peak_reduction_pct"] == 0.0


def test_simulate_moderation_scenarios():
    """Test standard 4 scenarios execution and monotonicity."""
    base_params = SimulationParameters(
        population=5000,
        initial_exposed=100.0,
        beta=0.35,
        time_steps=20,
    )
    scenarios = simulate_moderation_scenarios(base_params)

    assert "No moderation" in scenarios
    assert "Weak moderation" in scenarios
    assert "Moderate moderation" in scenarios
    assert "Strong moderation" in scenarios

    # Stronger moderation must result in lower or equal final exposure
    assert scenarios["No moderation"].final_exposure >= scenarios["Weak moderation"].final_exposure
    assert scenarios["Weak moderation"].final_exposure >= scenarios["Moderate moderation"].final_exposure
    assert scenarios["Moderate moderation"].final_exposure >= scenarios["Strong moderation"].final_exposure


def test_sweep_moderation_effectiveness():
    """Verify moderation sweep generates monotonically decreasing final exposure."""
    base_params = SimulationParameters(
        population=2000,
        initial_exposed=50.0,
        beta=0.4,
        time_steps=15,
    )
    sweep_df = sweep_moderation_effectiveness(base_params, steps=11)
    assert len(sweep_df) == 11
    # Check that final exposure decreases or stays constant as m increases
    exposures = sweep_df["final_exposure"].values
    assert np.all(np.diff(exposures) <= 1e-5)


def test_sir_propagation_with_debunking():
    """Verify SIR model produces peak outbreak, inflection point, and debunked recovery."""
    params = SimulationParameters(
        population=5000,
        initial_exposed=100.0,
        beta=0.45,
        moderation_effectiveness=0.20,
        time_steps=40,
        debunking_rate=0.08,
        model_type="sir",
    )
    res = run_propagation_simulation(params)
    assert res.susceptible is not None
    assert res.debunked is not None
    assert res.peak_exposure > 0.0
    assert res.peak_step is not None
    # S + I + R should conserve total population
    total_pop = res.susceptible + res.exposure + res.debunked
    assert np.allclose(total_pop, 5000.0, atol=1e-3)

