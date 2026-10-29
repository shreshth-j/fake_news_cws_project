"""
Unit tests for the Nash equilibrium solver.
"""

import pytest
import numpy as np
from src.payoff_model import PayoffMatrix
from src.equilibrium import (
    compute_best_responses,
    compute_pure_equilibria,
    compute_mixed_equilibrium,
    analyze_game,
    analyze_unilateral_deviation,
)


def test_initial_example_matrix_equilibrium():
    """
    CRITICAL COURSE REQUIREMENT:
    For the initial illustrative matrix:
      (S, W) = (5, -4)
      (S, M) = (-2, 3)
      (N, W) = (1, 0)
      (N, M) = (0, 2)
    Verify that the pure-strategy Nash equilibrium is (N, M), with payoffs (0, 2).
    """
    matrix = PayoffMatrix.default()
    analysis = analyze_game(matrix)

    # 1. Verify Best Responses
    br = analysis.best_responses
    assert br.sharer_br_to_W == ["S"]    # 5 > 1
    assert br.sharer_br_to_M == ["N"]    # 0 > -2
    assert br.platform_br_to_S == ["M"]  # 3 > -4
    assert br.platform_br_to_N == ["M"]  # 2 > 0

    # 2. Verify Pure Nash Equilibrium
    assert analysis.has_pure_equilibrium is True
    assert len(analysis.pure_equilibria) == 1

    eq = analysis.pure_equilibria[0]
    assert eq.sharer_strategy == "N"
    assert eq.platform_strategy == "M"
    assert eq.sharer_payoff == 0.0
    assert eq.platform_payoff == 2.0
    assert eq.profile_label == "(N, M)"

    # 3. Verify Mixed Equilibrium
    # Since Platform strictly dominates with M (M is BR against both S and N),
    # there is no strictly interior mixed equilibrium.
    assert analysis.mixed_equilibrium.exists_interior is False


def test_game_with_multiple_pure_equilibria():
    """Test a coordination-style game with multiple pure equilibria and an interior mixed equilibrium."""
    # Coordination / Stag Hunt type
    # (S, W) = (4, 4)
    # (S, M) = (0, 0)
    # (N, W) = (0, 0)
    # (N, M) = (2, 2)
    matrix = PayoffMatrix(
        sharer_SW=4.0, platform_SW=4.0,
        sharer_SM=0.0, platform_SM=0.0,
        sharer_NW=0.0, platform_NW=0.0,
        sharer_NM=2.0, platform_NM=2.0,
    )
    analysis = analyze_game(matrix)

    # Pure equilibria: (S, W) and (N, M)
    assert analysis.has_pure_equilibrium is True
    assert len(analysis.pure_equilibria) == 2
    profiles = {eq.profile_label for eq in analysis.pure_equilibria}
    assert profiles == {"(S, W)", "(N, M)"}

    # Mixed equilibrium:
    # 4p = 2(1-p) => 6p = 2 => p* = 1/3
    # 4q = 2(1-q) => 6q = 2 => q* = 1/3
    mixed = analysis.mixed_equilibrium
    assert mixed.exists_interior is True
    assert np.isclose(mixed.p_star, 1.0 / 3.0)
    assert np.isclose(mixed.q_star, 1.0 / 3.0)
    # Expected payoff at mixed eq = (1/3)*4 + (2/3)*0 = 4/3
    assert np.isclose(mixed.sharer_expected_payoff, 4.0 / 3.0)
    assert np.isclose(mixed.platform_expected_payoff, 4.0 / 3.0)


def test_matching_pennies_no_pure_equilibrium():
    """Test a matching-pennies / zero-sum cycling game with no pure equilibrium."""
    # (S, W) = (1, -1)
    # (S, M) = (-1, 1)
    # (N, W) = (-1, 1)
    # (N, M) = (1, -1)
    matrix = PayoffMatrix(
        sharer_SW=1.0, platform_SW=-1.0,
        sharer_SM=-1.0, platform_SM=1.0,
        sharer_NW=-1.0, platform_NW=1.0,
        sharer_NM=1.0, platform_NM=-1.0,
    )
    analysis = analyze_game(matrix)

    # Pure equilibria: NONE
    assert analysis.has_pure_equilibrium is False
    assert len(analysis.pure_equilibria) == 0

    # Strictly interior mixed equilibrium:
    # p* = 0.5, q* = 0.5
    mixed = analysis.mixed_equilibrium
    assert mixed.exists_interior is True
    assert np.isclose(mixed.p_star, 0.5)
    assert np.isclose(mixed.q_star, 0.5)
    assert np.isclose(mixed.sharer_expected_payoff, 0.0)
    assert np.isclose(mixed.platform_expected_payoff, 0.0)


def test_payoff_ties_and_degenerate_cases():
    """Test handling of ties when strategies give identical payoffs."""
    # All payoffs identical (2, 2)
    matrix = PayoffMatrix(
        sharer_SW=2.0, platform_SW=2.0,
        sharer_SM=2.0, platform_SM=2.0,
        sharer_NW=2.0, platform_NW=2.0,
        sharer_NM=2.0, platform_NM=2.0,
    )
    analysis = analyze_game(matrix)

    # When all payoffs are equal, both strategies are best responses for both players
    br = analysis.best_responses
    assert set(br.sharer_br_to_W) == {"S", "N"}
    assert set(br.sharer_br_to_M) == {"S", "N"}
    assert set(br.platform_br_to_S) == {"W", "M"}
    assert set(br.platform_br_to_N) == {"W", "M"}

    # All 4 profiles are pure Nash equilibria
    assert len(analysis.pure_equilibria) == 4

    # Degenerate mixed denominator
    assert analysis.mixed_equilibrium.exists_interior is False


def test_unilateral_deviation_analysis():
    """Verify unilateral deviation analysis detects profitable deviations."""
    matrix = PayoffMatrix.default()

    # (S, W) is NOT a Nash equilibrium: Platform has incentive to deviate to M
    dev_SW = analyze_unilateral_deviation(matrix, "S", "W")
    assert dev_SW.is_nash_equilibrium is False
    assert dev_SW.sharer_can_improve is False
    assert dev_SW.platform_can_improve is True
    assert dev_SW.platform_best_deviation == "M"
    assert dev_SW.platform_gain == 7.0  # from -4 to 3 is +7

    # (N, M) IS a Nash equilibrium: Neither player has incentive to deviate
    dev_NM = analyze_unilateral_deviation(matrix, "N", "M")
    assert dev_NM.is_nash_equilibrium is True
    assert dev_NM.sharer_can_improve is False
    assert dev_NM.platform_can_improve is False


def test_dominant_strategies_and_pareto():
    """Verify dominant strategy and Pareto efficiency calculations on the default matrix."""
    from src.equilibrium import compute_dominant_strategies, compute_pareto_efficiency, compute_best_responses

    matrix = PayoffMatrix.default()
    br = compute_best_responses(matrix)
    dom = compute_dominant_strategies(matrix, br)

    # For default matrix: Platform has dominant strategy 'M' (3 > -4 and 2 > 0)
    assert dom.platform_dominant == "M"
    # Sharer has NO dominant strategy (against W prefers S, against M prefers N)
    assert dom.sharer_dominant is None
    # Game is solvable by iterated dominance
    assert dom.has_dominant_solvable_equilibrium is True

    # Pareto efficiency
    pareto = compute_pareto_efficiency(matrix)
    # Profiles: (S,W)=(5,-4), (S,M)=(-2,3), (N,W)=(1,0), (N,M)=(0,2)
    # (S, W) gives 5 to sharer (highest sharer payoff, so pareto optimal)
    # (S, M) gives 3 to platform (highest platform payoff, so pareto optimal)
    # (N, M) gives (0, 2): is not dominated by any profile where both are higher
    assert ("S", "W") in pareto
    assert ("S", "M") in pareto


def test_endogenous_payoffs_and_taxonomy():
    """Verify endogenous payoff generation and game taxonomy classification."""
    from src.payoff_model import compute_endogenous_payoffs, classify_game_taxonomy

    # Low moderation (slack platform) -> Spreading is highly rewarding, platform harmed
    m_slack = compute_endogenous_payoffs(beta=0.70, moderation=0.05, final_exposure_fraction=0.85)
    tax_slack = classify_game_taxonomy(m_slack)
    assert m_slack.sharer_SW > m_slack.sharer_NW

    # High moderation -> Deterrence game where platform forces compliance
    m_deter = compute_endogenous_payoffs(beta=0.35, moderation=0.80, final_exposure_fraction=0.15)
    tax_deter = classify_game_taxonomy(m_deter)
    assert tax_deter.game_type == "Deterrence Game"


def test_replicator_dynamics_and_tipping():
    """Verify evolutionary replicator dynamics and tipping point computation."""
    from src.equilibrium import simulate_replicator_dynamics, compute_tipping_points

    matrix = PayoffMatrix.default()
    # High platform moderation probability should drive spreaders towards 0
    res = simulate_replicator_dynamics(matrix, initial_spreader_frac=0.50, platform_prob_M=0.90, generations=30)
    assert res.final_spreader_share < 0.20

    # Tipping point analysis
    tp = compute_tipping_points(beta=0.35, final_exposure_pct=0.70)
    assert tp.tipping_m_sharer is not None
    assert 0.0 < tp.tipping_m_sharer < 1.0


