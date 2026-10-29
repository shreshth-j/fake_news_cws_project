"""
Nash Equilibrium Solver for 2x2 Strategic Games.

Computes:
1. Best response correspondences for both players.
2. Pure-strategy Nash equilibria with tie handling.
3. Mixed-strategy Nash equilibrium probabilities (p*, q*) and expected utilities.
4. Unilateral deviation analysis for any selected strategy profile.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
import numpy as np

from src.payoff_model import PayoffMatrix


@dataclass
class BestResponseResult:
    """Best responses of both players."""
    sharer_br_to_W: List[str]  # Best responses of Sharer when Platform plays W
    sharer_br_to_M: List[str]  # Best responses of Sharer when Platform plays M
    platform_br_to_S: List[str]  # Best responses of Platform when Sharer plays S
    platform_br_to_N: List[str]  # Best responses of Platform when Sharer plays N

    sharer_reasoning: Dict[str, str]
    platform_reasoning: Dict[str, str]


@dataclass
class PureEquilibrium:
    """A pure-strategy Nash equilibrium profile and payoffs."""
    sharer_strategy: str
    platform_strategy: str
    sharer_payoff: float
    platform_payoff: float
    profile_label: str  # e.g., "(N, M)"
    justification: str


@dataclass
class MixedEquilibrium:
    """Mixed-strategy equilibrium analysis."""
    exists_interior: bool
    p_star: Optional[float]  # P(Sharer plays S)
    q_star: Optional[float]  # P(Platform plays W)
    sharer_expected_payoff: Optional[float]
    platform_expected_payoff: Optional[float]
    explanation: str
    delta_sharer: float  # Denominator for q*
    delta_platform: float  # Denominator for p*


@dataclass
class DeviationAnalysis:
    """Analysis of unilateral deviation incentives from a specific profile."""
    profile: Tuple[str, str]
    is_nash_equilibrium: bool
    current_payoffs: Tuple[float, float]
    sharer_can_improve: bool
    sharer_best_deviation: Optional[str]
    sharer_gain: float
    platform_can_improve: bool
    platform_best_deviation: Optional[str]
    platform_gain: float
    explanation: str


@dataclass
class EquilibriumAnalysisResult:
    """Full analysis result combining best responses, pure equilibria, and mixed equilibria."""
    matrix: PayoffMatrix
    best_responses: BestResponseResult
    pure_equilibria: List[PureEquilibrium]
    has_pure_equilibrium: bool
    mixed_equilibrium: MixedEquilibrium


def compute_best_responses(matrix: PayoffMatrix) -> BestResponseResult:
    """
    Compute best responses for each player under all opponent pure strategies.
    Properly handles ties (if payoffs are equal, both strategies are best responses).
    """
    matrix.validate()

    # --- Sharer Best Responses ---
    # Against W:
    u_SW, _ = matrix.get_payoff("S", "W")
    u_NW, _ = matrix.get_payoff("N", "W")
    if np.isclose(u_SW, u_NW):
        br_sharer_W = ["S", "N"]
        sharer_reason_W = f"Indifferent between S and N against Weak moderation: u(S, W) = u(N, W) = {u_SW:g}."
    elif u_SW > u_NW:
        br_sharer_W = ["S"]
        sharer_reason_W = f"S is strictly preferred against Weak moderation: u(S, W) = {u_SW:g} > u(N, W) = {u_NW:g}."
    else:
        br_sharer_W = ["N"]
        sharer_reason_W = f"N is strictly preferred against Weak moderation: u(N, W) = {u_NW:g} > u(S, W) = {u_SW:g}."

    # Against M:
    u_SM, _ = matrix.get_payoff("S", "M")
    u_NM, _ = matrix.get_payoff("N", "M")
    if np.isclose(u_SM, u_NM):
        br_sharer_M = ["S", "N"]
        sharer_reason_M = f"Indifferent between S and N against Strong moderation: u(S, M) = u(N, M) = {u_SM:g}."
    elif u_SM > u_NM:
        br_sharer_M = ["S"]
        sharer_reason_M = f"S is strictly preferred against Strong moderation: u(S, M) = {u_SM:g} > u(N, M) = {u_NM:g}."
    else:
        br_sharer_M = ["N"]
        sharer_reason_M = f"N is strictly preferred against Strong moderation: u(N, M) = {u_NM:g} > u(S, M) = {u_SM:g}."

    # --- Platform Best Responses ---
    # Against S:
    _, u_SW_plat = matrix.get_payoff("S", "W")
    _, u_SM_plat = matrix.get_payoff("S", "M")
    if np.isclose(u_SW_plat, u_SM_plat):
        br_platform_S = ["W", "M"]
        plat_reason_S = f"Indifferent between W and M against S: u(S, W) = u(S, M) = {u_SW_plat:g}."
    elif u_SM_plat > u_SW_plat:
        br_platform_S = ["M"]
        plat_reason_S = f"M is strictly preferred against S: u(S, M) = {u_SM_plat:g} > u(S, W) = {u_SW_plat:g}."
    else:
        br_platform_S = ["W"]
        plat_reason_S = f"W is strictly preferred against S: u(S, W) = {u_SW_plat:g} > u(S, M) = {u_SM_plat:g}."

    # Against N:
    _, u_NW_plat = matrix.get_payoff("N", "W")
    _, u_NM_plat = matrix.get_payoff("N", "M")
    if np.isclose(u_NW_plat, u_NM_plat):
        br_platform_N = ["W", "M"]
        plat_reason_N = f"Indifferent between W and M against N: u(N, W) = u(N, M) = {u_NW_plat:g}."
    elif u_NM_plat > u_NW_plat:
        br_platform_N = ["M"]
        plat_reason_N = f"M is strictly preferred against N: u(N, M) = {u_NM_plat:g} > u(N, W) = {u_NW_plat:g}."
    else:
        br_platform_N = ["W"]
        plat_reason_N = f"W is strictly preferred against N: u(N, W) = {u_NW_plat:g} > u(N, M) = {u_NM_plat:g}."

    return BestResponseResult(
        sharer_br_to_W=br_sharer_W,
        sharer_br_to_M=br_sharer_M,
        platform_br_to_S=br_platform_S,
        platform_br_to_N=br_platform_N,
        sharer_reasoning={"W": sharer_reason_W, "M": sharer_reason_M},
        platform_reasoning={"S": plat_reason_S, "N": plat_reason_N},
    )


def compute_pure_equilibria(matrix: PayoffMatrix, br: BestResponseResult) -> List[PureEquilibrium]:
    """
    Check all four pure strategy profiles: (S, W), (S, M), (N, W), (N, M).
    A profile (s, p) is a Nash equilibrium iff s in BR_sharer(p) and p in BR_platform(s).
    """
    profiles = [("S", "W"), ("S", "M"), ("N", "W"), ("N", "M")]
    equilibria = []

    for s, p in profiles:
        sharer_br = br.sharer_br_to_W if p == "W" else br.sharer_br_to_M
        platform_br = br.platform_br_to_S if s == "S" else br.platform_br_to_N

        if s in sharer_br and p in platform_br:
            u_s, u_p = matrix.get_payoff(s, p)
            other_s = "N" if s == "S" else "S"
            other_p = "M" if p == "W" else "W"
            dev_s_payoff, _ = matrix.get_payoff(other_s, p)
            _, dev_p_payoff = matrix.get_payoff(s, other_p)

            justification = (
                f"Profile ({s}, {p}) is a Nash Equilibrium: "
                f"Sharer earns {u_s:g} (deviating to {other_s} yields {dev_s_payoff:g} <= {u_s:g}); "
                f"Platform earns {u_p:g} (deviating to {other_p} yields {dev_p_payoff:g} <= {u_p:g}). "
                "Neither player can unilaterally improve their payoff."
            )

            equilibria.append(
                PureEquilibrium(
                    sharer_strategy=s,
                    platform_strategy=p,
                    sharer_payoff=u_s,
                    platform_payoff=u_p,
                    profile_label=f"({s}, {p})",
                    justification=justification,
                )
            )

    return equilibria


def compute_mixed_equilibrium(matrix: PayoffMatrix) -> MixedEquilibrium:
    """
    Compute mixed-strategy equilibrium probabilities:
    Let p = Prob(Sharer plays S), 1-p = Prob(Sharer plays N).
    Let q = Prob(Platform plays W), 1-q = Prob(Platform plays M).

    Indifference conditions:
    1. Platform indifferent between W and M:
       p * u2(S, W) + (1-p) * u2(N, W) = p * u2(S, M) + (1-p) * u2(N, M)
       p * [(u2(S, W) - u2(S, M)) - (u2(N, W) - u2(N, M))] = u2(N, M) - u2(N, W)
       delta_p = (u2(S, W) - u2(S, M)) - (u2(N, W) - u2(N, M))
       p* = (u2(N, M) - u2(N, W)) / delta_p

    2. Sharer indifferent between S and N:
       q * u1(S, W) + (1-q) * u1(S, M) = q * u1(N, W) + (1-q) * u1(N, M)
       q * [(u1(S, W) - u1(S, M)) - (u1(N, W) - u1(N, M))] = u1(N, M) - u1(S, M)
       delta_q = (u1(S, W) - u1(S, M)) - (u1(N, W) - u1(N, M))
       q* = (u1(N, M) - u1(S, M)) / delta_q
    """
    u1_SW, u2_SW = matrix.get_payoff("S", "W")
    u1_SM, u2_SM = matrix.get_payoff("S", "M")
    u1_NW, u2_NW = matrix.get_payoff("N", "W")
    u1_NM, u2_NM = matrix.get_payoff("N", "M")

    # Platform indifference solves p*
    numerator_p = u2_NM - u2_NW
    delta_p = (u2_SW - u2_SM) - (u2_NW - u2_NM)

    # Sharer indifference solves q*
    numerator_q = u1_NM - u1_SM
    delta_q = (u1_SW - u1_SM) - (u1_NW - u1_NM)

    if np.isclose(delta_p, 0.0) or np.isclose(delta_q, 0.0):
        return MixedEquilibrium(
            exists_interior=False,
            p_star=None,
            q_star=None,
            sharer_expected_payoff=None,
            platform_expected_payoff=None,
            explanation=(
                "No strictly interior mixed-strategy equilibrium exists because the indifference equations "
                "degenerate (zero denominator in indifference conditions). One or both players have constant "
                "payoff differences across strategies."
            ),
            delta_sharer=delta_q,
            delta_platform=delta_p,
        )

    p_star = numerator_p / delta_p
    q_star = numerator_q / delta_q

    # Check if strictly interior: 0 < p* < 1 and 0 < q* < 1
    tol = 1e-7
    is_interior = (tol < p_star < 1.0 - tol) and (tol < q_star < 1.0 - tol)

    if is_interior:
        # Expected payoffs under mixed equilibrium
        sharer_eu = q_star * u1_SW + (1.0 - q_star) * u1_SM
        platform_eu = p_star * u2_SW + (1.0 - p_star) * u2_NW

        explanation = (
            f"A strictly interior mixed-strategy Nash equilibrium exists at "
            f"p* = P(S) = {p_star:.4f} and q* = P(W) = {q_star:.4f}. "
            f"At this profile, the Content Sharer mixes between S ({p_star:.2%}) and N ({(1-p_star):.2%}) "
            f"to make the Platform indifferent between W and M. Simultaneously, the Platform mixes between "
            f"W ({q_star:.2%}) and M ({(1-q_star):.2%}) to make the Sharer indifferent between S and N. "
            f"Expected payoffs: Sharer E[U1] = {sharer_eu:.4f}, Platform E[U2] = {platform_eu:.4f}."
        )

        return MixedEquilibrium(
            exists_interior=True,
            p_star=float(p_star),
            q_star=float(q_star),
            sharer_expected_payoff=float(sharer_eu),
            platform_expected_payoff=float(platform_eu),
            explanation=explanation,
            delta_sharer=delta_q,
            delta_platform=delta_p,
        )
    else:
        explanation = (
            f"No strictly interior mixed-strategy Nash equilibrium exists. "
            f"The indifference equations yield mathematical points p* = {p_star:.4f} and q* = {q_star:.4f}, "
            "which fall outside the valid interior probability interval (0, 1). "
            "This implies one or both players have a dominant pure strategy or pure-equilibrium attractor."
        )
        return MixedEquilibrium(
            exists_interior=False,
            p_star=float(p_star) if np.isfinite(p_star) else None,
            q_star=float(q_star) if np.isfinite(q_star) else None,
            sharer_expected_payoff=None,
            platform_expected_payoff=None,
            explanation=explanation,
            delta_sharer=delta_q,
            delta_platform=delta_p,
        )


def analyze_game(matrix: PayoffMatrix) -> EquilibriumAnalysisResult:
    """Run full game-theoretic equilibrium analysis."""
    br = compute_best_responses(matrix)
    pure_eq = compute_pure_equilibria(matrix, br)
    mixed_eq = compute_mixed_equilibrium(matrix)

    return EquilibriumAnalysisResult(
        matrix=matrix,
        best_responses=br,
        pure_equilibria=pure_eq,
        has_pure_equilibrium=len(pure_eq) > 0,
        mixed_equilibrium=mixed_eq,
    )


def analyze_unilateral_deviation(
    matrix: PayoffMatrix,
    selected_sharer: str,
    selected_platform: str,
) -> DeviationAnalysis:
    """
    Examine whether either player has an incentive to unilaterally deviate
    from (selected_sharer, selected_platform).
    """
    s = selected_sharer.upper()
    p = selected_platform.upper()

    cur_u1, cur_u2 = matrix.get_payoff(s, p)
    alt_s = "N" if s == "S" else "S"
    alt_p = "M" if p == "W" else "W"

    dev_u1, _ = matrix.get_payoff(alt_s, p)
    _, dev_u2 = matrix.get_payoff(s, alt_p)

    sharer_gain = dev_u1 - cur_u1
    sharer_can_improve = sharer_gain > 1e-7

    platform_gain = dev_u2 - cur_u2
    platform_can_improve = platform_gain > 1e-7

    is_nash = (not sharer_can_improve) and (not platform_can_improve)

    explanations = []
    if is_nash:
        explanations.append(
            f"The selected strategy profile ({s}, {p}) is a Nash Equilibrium! "
            f"Sharer payoff is {cur_u1:g} (deviating to {alt_s} would yield {dev_u1:g}, gain: {sharer_gain:+g}). "
            f"Platform payoff is {cur_u2:g} (deviating to {alt_p} would yield {dev_u2:g}, gain: {platform_gain:+g}). "
            "Neither player can strictly improve their payoff by deviating unilaterally."
        )
    else:
        explanations.append(f"The selected strategy profile ({s}, {p}) is NOT a Nash Equilibrium:")
        if sharer_can_improve:
            explanations.append(
                f"- Content Sharer has a profitable deviation to '{alt_s}', increasing payoff from {cur_u1:g} to {dev_u1:g} (+{sharer_gain:g})."
            )
        else:
            explanations.append(
                f"- Content Sharer has no incentive to deviate (current {cur_u1:g} >= alternative {dev_u1:g})."
            )

        if platform_can_improve:
            explanations.append(
                f"- Platform has a profitable deviation to '{alt_p}', increasing payoff from {cur_u2:g} to {dev_u2:g} (+{platform_gain:g})."
            )
        else:
            explanations.append(
                f"- Platform has no incentive to deviate (current {cur_u2:g} >= alternative {dev_u2:g})."
            )

    return DeviationAnalysis(
        profile=(s, p),
        is_nash_equilibrium=is_nash,
        current_payoffs=(cur_u1, cur_u2),
        sharer_can_improve=sharer_can_improve,
        sharer_best_deviation=alt_s if sharer_can_improve else None,
        sharer_gain=max(0.0, sharer_gain),
        platform_can_improve=platform_can_improve,
        platform_best_deviation=alt_p if platform_can_improve else None,
        platform_gain=max(0.0, platform_gain),
        explanation="\n".join(explanations),
    )


@dataclass
class DominantStrategyResult:
    """Summary of dominant and dominated strategies for both players."""
    sharer_dominant: Optional[str]
    platform_dominant: Optional[str]
    sharer_explanation: str
    platform_explanation: str
    has_dominant_solvable_equilibrium: bool
    solution_summary: str


def compute_dominant_strategies(matrix: PayoffMatrix, br: BestResponseResult) -> DominantStrategyResult:
    """
    Determine whether either player has a strictly or weakly dominant strategy.
    A strategy is strictly dominant if it yields a strictly higher payoff than all alternatives,
    regardless of opponent actions.
    """
    matrix.validate()

    # 1. Sharer Dominance Check
    u_SW, _ = matrix.get_payoff("S", "W")
    u_NW, _ = matrix.get_payoff("N", "W")
    u_SM, _ = matrix.get_payoff("S", "M")
    u_NM, _ = matrix.get_payoff("N", "M")

    s_beats_n_against_W = u_SW > u_NW
    s_beats_n_against_M = u_SM > u_NM
    n_beats_s_against_W = u_NW > u_SW
    n_beats_s_against_M = u_NM > u_SM

    if s_beats_n_against_W and s_beats_n_against_M:
        sharer_dom = "S"
        sharer_exp = f"Strategy S (Spread) is strictly dominant: yields higher payoff against both Weak ({u_SW:g} > {u_NW:g}) and Strong ({u_SM:g} > {u_NM:g}) moderation."
    elif n_beats_s_against_W and n_beats_s_against_M:
        sharer_dom = "N"
        sharer_exp = f"Strategy N (Do Not Spread) is strictly dominant: yields higher payoff against both Weak ({u_NW:g} > {u_SW:g}) and Strong ({u_NM:g} > {u_SM:g}) moderation."
    else:
        sharer_dom = None
        sharer_exp = f"No dominant strategy: against Weak moderation S is preferred ({u_SW:g} > {u_NW:g}), but against Strong moderation N is preferred ({u_NM:g} > {u_SM:g}). Sharer's best response depends strictly on the platform's action."

    # 2. Platform Dominance Check
    _, u_SW_p = matrix.get_payoff("S", "W")
    _, u_SM_p = matrix.get_payoff("S", "M")
    _, u_NW_p = matrix.get_payoff("N", "W")
    _, u_NM_p = matrix.get_payoff("N", "M")

    m_beats_w_against_S = u_SM_p > u_SW_p
    m_beats_w_against_N = u_NM_p > u_NW_p
    w_beats_m_against_S = u_SW_p > u_SM_p
    w_beats_m_against_N = u_NW_p > u_NM_p

    if m_beats_w_against_S and m_beats_w_against_N:
        platform_dom = "M"
        platform_exp = f"Strategy M (Strong Moderation) is strictly dominant: Platform earns higher utility under M whether Sharers spread ({u_SM_p:g} > {u_SW_p:g}) or do not spread ({u_NM_p:g} > {u_NW_p:g})."
    elif w_beats_m_against_S and w_beats_m_against_N:
        platform_dom = "W"
        platform_exp = f"Strategy W (Weak Moderation) is strictly dominant: Platform earns higher utility under W whether Sharers spread ({u_SW_p:g} > {u_SM_p:g}) or do not spread ({u_NW_p:g} > {u_NM_p:g})."
    else:
        platform_dom = None
        platform_exp = "No dominant strategy: Platform's optimal policy depends on the volume of misinformation."

    # IESDS / Dominant Strategy Solvability
    solvable = False
    solution_summary = ""
    if sharer_dom and platform_dom:
        solvable = True
        solution_summary = f"Dominant Strategy Equilibrium: Both players have dominant strategies ({sharer_dom}, {platform_dom})."
    elif platform_dom and not sharer_dom:
        solvable = True
        best_resp_to_plat_dom = br.sharer_br_to_M if platform_dom == "M" else br.sharer_br_to_W
        solution_summary = (
            f"Iterated Dominance Solvable: Platform will always play its dominant strategy '{platform_dom}'. "
            f"Anticipating this, Sharer plays best response '{best_resp_to_plat_dom[0]}', confirming equilibrium ({best_resp_to_plat_dom[0]}, {platform_dom})."
        )
    elif sharer_dom and not platform_dom:
        solvable = True
        best_resp_to_sharer_dom = br.platform_br_to_S if sharer_dom == "S" else br.platform_br_to_N
        solution_summary = (
            f"Iterated Dominance Solvable: Sharer will always play its dominant strategy '{sharer_dom}'. "
            f"Anticipating this, Platform plays '{best_resp_to_sharer_dom[0]}', confirming equilibrium ({sharer_dom}, {best_resp_to_sharer_dom[0]})."
        )
    else:
        solution_summary = "Neither player has a dominant strategy; equilibrium requires simultaneous best-response coordination."

    return DominantStrategyResult(
        sharer_dominant=sharer_dom,
        platform_dominant=platform_dom,
        sharer_explanation=sharer_exp,
        platform_explanation=platform_exp,
        has_dominant_solvable_equilibrium=solvable,
        solution_summary=solution_summary,
    )


def compute_pareto_efficiency(matrix: PayoffMatrix) -> List[Tuple[str, str]]:
    """
    Identify all Pareto-optimal strategy profiles.
    A profile is Pareto optimal if no other profile makes at least one player strictly better off
    without making the other player worse off.
    """
    profiles = [("S", "W"), ("S", "M"), ("N", "W"), ("N", "M")]
    payoffs = {p: matrix.get_payoff(p[0], p[1]) for p in profiles}

    pareto_optimal = []
    for p1 in profiles:
        u1_1, u2_1 = payoffs[p1]
        is_dominated = False
        for p2 in profiles:
            if p2 == p1:
                continue
            u1_2, u2_2 = payoffs[p2]
            # p2 dominates p1 if both >= and at least one >
            if (u1_2 >= u1_1 and u2_2 >= u2_1) and (u1_2 > u1_1 or u2_2 > u2_1):
                is_dominated = True
                break
        if not is_dominated:
            pareto_optimal.append(p1)

    return pareto_optimal


@dataclass
class ReplicatorDynamicsResult:
    """Evolutionary game theory replicator trajectory for the sharer population."""
    generations: np.ndarray
    spreader_fraction: np.ndarray
    compliant_fraction: np.ndarray
    u_spread: np.ndarray
    u_compliant: np.ndarray
    stable_equilibrium_type: str
    final_spreader_share: float


def simulate_replicator_dynamics(
    matrix: PayoffMatrix,
    initial_spreader_frac: float = 0.50,
    platform_prob_M: float = 0.50,
    generations: int = 60,
    learning_rate: float = 0.08,
) -> ReplicatorDynamicsResult:
    """
    Simulate evolutionary replicator dynamics for the sharer population.

    Let x_t = fraction of population playing S (Spread), 1 - x_t playing N (Do Not Spread).
    Platform plays M with probability y = platform_prob_M (or moderation intensity).

    Payoffs:
        U_S = (1 - y) * u(S, W) + y * u(S, M)
        U_N = (1 - y) * u(N, W) + y * u(N, M)
        U_avg = x * U_S + (1 - x) * U_N

    Replicator differential equation:
        dx/dt = x * (U_S - U_avg) = x * (1 - x) * (U_S - U_N)
    """
    x_hist = np.zeros(generations + 1, dtype=np.float64)
    x_hist[0] = np.clip(initial_spreader_frac, 0.001, 0.999)

    u1_SW, _ = matrix.get_payoff("S", "W")
    u1_SM, _ = matrix.get_payoff("S", "M")
    u1_NW, _ = matrix.get_payoff("N", "W")
    u1_NM, _ = matrix.get_payoff("N", "M")

    y = float(np.clip(platform_prob_M, 0.0, 1.0))
    u_S = (1.0 - y) * u1_SW + y * u1_SM
    u_N = (1.0 - y) * u1_NW + y * u1_NM
    fitness_diff = u_S - u_N

    for t in range(generations):
        x = x_hist[t]
        dx = learning_rate * x * (1.0 - x) * fitness_diff
        x_next = np.clip(x + dx, 0.0, 1.0)
        x_hist[t + 1] = x_next

    gen_axis = np.arange(generations + 1)
    final_x = float(x_hist[-1])

    if np.isclose(final_x, 0.0, atol=0.05):
        eq_type = "Full Extinction of Spreaders (Clean Platform ESS)"
    elif np.isclose(final_x, 1.0, atol=0.05):
        eq_type = "All-Spreader Dominance (Viral Outbreak ESS)"
    else:
        eq_type = f"Polymorphic Mixed Coexistence (x* = {final_x:.2f})"

    return ReplicatorDynamicsResult(
        generations=gen_axis,
        spreader_fraction=x_hist,
        compliant_fraction=1.0 - x_hist,
        u_spread=np.full_like(gen_axis, u_S, dtype=np.float64),
        u_compliant=np.full_like(gen_axis, u_N, dtype=np.float64),
        stable_equilibrium_type=eq_type,
        final_spreader_share=final_x,
    )


@dataclass
class TippingPointResult:
    """Tipping point analysis showing critical moderation thresholds."""
    m_grid: np.ndarray
    sharer_u_S: np.ndarray
    sharer_u_N: np.ndarray
    platform_u_W: np.ndarray
    platform_u_M: np.ndarray
    tipping_m_sharer: Optional[float]
    tipping_m_platform: Optional[float]
    explanation: str


def compute_tipping_points(
    beta: float = 0.35,
    final_exposure_pct: float = 0.70,
    moderation_cost_coeff: float = 1.5,
    penalty_coeff: float = 4.0,
    viral_reward_coeff: float = 5.0,
    steps: int = 100,
) -> TippingPointResult:
    """
    Compute payoff trajectories across m in [0, 1] and determine the exact tipping threshold
    where Sharer switches from Spread (S) to Compliance (N).
    """
    m_grid = np.linspace(0.0, 1.0, steps)
    r_viral = viral_reward_coeff * (beta / 0.35)

    # u_S(S, M) = r_viral * (1 - m) - penalty * m
    # u_S(N, M) = 0
    # Threshold m* where u_S(S, M) = 0: r_viral * (1 - m*) = penalty * m* => m* = r_viral / (r_viral + penalty)
    if r_viral + penalty_coeff > 0:
        tipping_m_sharer = float(np.clip(r_viral / (r_viral + penalty_coeff), 0.0, 1.0))
    else:
        tipping_m_sharer = 0.50

    sharer_u_S = np.array([r_viral * (1.0 - m) - penalty_coeff * m for m in m_grid])
    sharer_u_N = np.zeros_like(m_grid)

    platform_u_W = np.full_like(m_grid, -4.0 * max(0.2, final_exposure_pct))
    platform_u_M = np.array([3.0 * (1.0 - 0.5 * final_exposure_pct) - moderation_cost_coeff * m for m in m_grid])

    # Platform tipping threshold where u_M = u_W
    plat_diff = platform_u_M - platform_u_W
    cross_idx = np.where(np.diff(np.sign(plat_diff)))[0]
    tipping_m_plat = float(m_grid[cross_idx[0]]) if len(cross_idx) > 0 else None

    exp = (
        f"Critical Deterrence Threshold occurs at m* = {tipping_m_sharer:.2f}. "
        f"For moderation intensity m >= {tipping_m_sharer:.2f}, Sharer's penalty outweighs virality, "
        f"tipping the game into full rule compliance (N)."
    )

    return TippingPointResult(
        m_grid=m_grid,
        sharer_u_S=sharer_u_S,
        sharer_u_N=sharer_u_N,
        platform_u_W=platform_u_W,
        platform_u_M=platform_u_M,
        tipping_m_sharer=tipping_m_sharer,
        tipping_m_platform=tipping_m_plat,
        explanation=exp,
    )


