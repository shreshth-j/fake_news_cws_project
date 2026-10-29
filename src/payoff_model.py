"""
Game-Theoretic Payoff Matrix Model for Content Sharers and Platforms.

Players:
    1. Content Sharer (Strategies: S = Spread, N = Do Not Spread)
    2. Social Media Platform (Strategies: W = Weak Moderation, M = Strong Moderation)

Profiles:
    (S, W): Sharer benefits from viral spread, Platform suffers misinformation harm.
    (S, M): Sharer penalized by active moderation sanctions, Platform successfully limits harm.
    (N, W): Baseline quiet state, low moderation cost.
    (N, M): Platform incurs strong moderation costs despite low misinformation activity.
"""

from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np


@dataclass
class PayoffMatrix:
    """Configurable 2x2 Payoff Matrix for Content Sharer vs Platform."""
    sharer_SW: float = 5.0
    platform_SW: float = -4.0

    sharer_SM: float = -2.0
    platform_SM: float = 3.0

    sharer_NW: float = 1.0
    platform_NW: float = 0.0

    sharer_NM: float = 0.0
    platform_NM: float = 2.0

    def validate(self) -> None:
        """Validate that all payoffs are finite real numbers."""
        for field_name, value in asdict(self).items():
            if not isinstance(value, (int, float, np.floating, np.integer)) or not np.isfinite(value):
                raise ValueError(f"Payoff {field_name} must be a finite number, got {value}")

    def get_payoff(self, sharer_strategy: str, platform_strategy: str) -> Tuple[float, float]:
        """Return (sharer_payoff, platform_payoff) for a given strategy profile."""
        s = sharer_strategy.upper()
        p = platform_strategy.upper()

        if s == "S" and p == "W":
            return float(self.sharer_SW), float(self.platform_SW)
        elif s == "S" and p == "M":
            return float(self.sharer_SM), float(self.platform_SM)
        elif s == "N" and p == "W":
            return float(self.sharer_NW), float(self.platform_NW)
        elif s == "N" and p == "M":
            return float(self.sharer_NM), float(self.platform_NM)
        else:
            raise ValueError(f"Invalid strategy profile: ({sharer_strategy}, {platform_strategy}). Expected (S|N, W|M)")

    def to_dataframe(self) -> pd.DataFrame:
        """Return formatted dataframe representation of the matrix."""
        return pd.DataFrame(
            [
                {
                    "Sharer Strategy": "S (Spread)",
                    "Platform W (Weak)": f"({self.sharer_SW:g}, {self.platform_SW:g})",
                    "Platform M (Strong)": f"({self.sharer_SM:g}, {self.platform_SM:g})",
                },
                {
                    "Sharer Strategy": "N (Do Not Spread)",
                    "Platform W (Weak)": f"({self.sharer_NW:g}, {self.platform_NW:g})",
                    "Platform M (Strong)": f"({self.sharer_NM:g}, {self.platform_NM:g})",
                },
            ]
        ).set_index("Sharer Strategy")

    def to_dict(self) -> Dict[str, float]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> "PayoffMatrix":
        matrix = cls(
            sharer_SW=float(data.get("sharer_SW", 5.0)),
            platform_SW=float(data.get("platform_SW", -4.0)),
            sharer_SM=float(data.get("sharer_SM", -2.0)),
            platform_SM=float(data.get("platform_SM", 3.0)),
            sharer_NW=float(data.get("sharer_NW", 1.0)),
            platform_NW=float(data.get("platform_NW", 0.0)),
            sharer_NM=float(data.get("sharer_NM", 0.0)),
            platform_NM=float(data.get("platform_NM", 2.0)),
        )
        matrix.validate()
        return matrix

    @classmethod
    def default(cls) -> "PayoffMatrix":
        """Return the canonical course example payoff matrix."""
        return cls()

    def get_profile_interpretation(self, s: str, p: str) -> str:
        """Provide detailed academic explanation of a strategy profile."""
        s, p = s.upper(), p.upper()
        if s == "S" and p == "W":
            return (
                "**Viral Misinformation Exploitation:** The sharer exploits weak platform moderation, "
                f"capturing maximum utility ({self.sharer_SW:g}) from virality/engagement. "
                f"Conversely, the platform suffers high reputational and societal penalty ({self.platform_SW:g})."
            )
        elif s == "S" and p == "M":
            return (
                "**Moderated Misinformation (Deterrence in action):** The sharer attempts to distribute fake news, "
                f"but faces aggressive enforcement, incurring net negative utility ({self.sharer_SM:g}). "
                f"The platform achieves positive utility ({self.platform_SM:g}) by protecting ecosystem integrity."
            )
        elif s == "N" and p == "W":
            return (
                "**Quiet Organic Baseline (Laissez-Faire):** Content sharers do not propagate fake news, "
                f"achieving organic utility ({self.sharer_NW:g}). The platform minimizes operating costs "
                f"under weak moderation, yielding a neutral baseline payoff ({self.platform_NW:g})."
            )
        elif s == "N" and p == "M":
            return (
                "**Over-Moderated Compliant State:** Sharers do not spread fake news, experiencing "
                f"neutral utility ({self.sharer_NM:g}). The platform maintains aggressive moderation, "
                f"retaining positive governance utility ({self.platform_NM:g}) despite enforcement overhead."
            )
        return "Unknown profile."


def compute_endogenous_payoffs(
    beta: float,
    moderation: float,
    final_exposure_fraction: float,
    moderation_cost_coeff: float = 1.5,
    penalty_coeff: float = 4.0,
    viral_reward_coeff: float = 5.0,
    reputational_damage_coeff: float = 4.0,
) -> PayoffMatrix:
    """
    Compute micro-founded endogenous payoffs connecting simulation outcomes to strategic incentives:
    - Sharer virality reward scales with transmission propensity beta.
    - Platform damage scales with final exposure from the viral diffusion.
    - Sharer penalty and platform cost scale with moderation intensity m.
    """
    # 1. Unmoderated spreading (S, W)
    viral_reward = float(np.round(viral_reward_coeff * (beta / 0.35), 2))
    rep_damage = float(np.round(-reputational_damage_coeff * max(0.15, final_exposure_fraction), 2))

    # 2. Moderated spreading (S, M)
    # Virality is partially suppressed by (1 - m), and user incurs penalty scaling with m
    sharer_penalized = float(np.round(viral_reward * (1.0 - moderation) - penalty_coeff * moderation, 2))
    # Platform protects reputation (safety benefit) minus direct moderation operating cost
    safety_benefit = 3.0 * (1.0 - final_exposure_fraction * 0.5)
    platform_moderated = float(np.round(safety_benefit - moderation_cost_coeff * moderation, 2))

    # 3. Organic non-spreading under weak moderation (N, W)
    sharer_NW = 1.0
    platform_NW = 0.0

    # 4. Compliant state under strong moderation (N, M)
    sharer_NM = 0.0
    platform_NM = float(np.round(2.0 - moderation_cost_coeff * moderation, 2))

    matrix = PayoffMatrix(
        sharer_SW=viral_reward,
        platform_SW=rep_damage,
        sharer_SM=sharer_penalized,
        platform_SM=platform_moderated,
        sharer_NW=sharer_NW,
        platform_NW=platform_NW,
        sharer_NM=sharer_NM,
        platform_NM=platform_NM,
    )
    matrix.validate()
    return matrix


@dataclass
class GameTaxonomyResult:
    """Classification of the 2x2 game structure into standard game-theoretic paradigms."""
    game_type: str
    description: str
    equilibrium_summary: str
    icon: str


def classify_game_taxonomy(matrix: PayoffMatrix) -> GameTaxonomyResult:
    """
    Classify the 2x2 game into standard strategic paradigms:
    - Deterrence Game
    - Prisoner's Dilemma
    - Coordination / Stag Hunt
    - Hawk-Dove / Chicken
    - Inspection Game / Cycling
    - Zero-Sum / Constant-Sum
    """
    u1_SW, u2_SW = matrix.sharer_SW, matrix.platform_SW
    u1_SM, u2_SM = matrix.sharer_SM, matrix.platform_SM
    u1_NW, u2_NW = matrix.sharer_NW, matrix.platform_NW
    u1_NM, u2_NM = matrix.sharer_NM, matrix.platform_NM

    # Check dominant strategies
    s_dom = None
    if u1_SW > u1_NW and u1_SM > u1_NM:
        s_dom = "S"
    elif u1_NW > u1_SW and u1_NM > u1_SM:
        s_dom = "N"

    p_dom = None
    if u2_SW > u2_SM and u2_NW > u2_NM:
        p_dom = "W"
    elif u2_SM > u2_SW and u2_NM > u2_NW:
        p_dom = "M"

    # Best responses
    s_br_W = "S" if u1_SW > u1_NW else ("N" if u1_NW > u1_SW else "Tie")
    s_br_M = "S" if u1_SM > u1_NM else ("N" if u1_NM > u1_SM else "Tie")
    p_br_S = "W" if u2_SW > u2_SM else ("M" if u2_SM > u2_SW else "Tie")
    p_br_N = "W" if u2_NW > u2_NM else ("M" if u2_NM > u2_NW else "Tie")

    # Prisoner's Dilemma check: both players have dominant strategies leading to Pareto suboptimal outcome
    if s_dom == "S" and p_dom == "W" and (u1_NM > u1_SW and u2_NM > u2_SW):
        return GameTaxonomyResult(
            game_type="Prisoner's Dilemma",
            description="Both players have dominant defect strategies (Spread, Weak) resulting in an inefficient outcome compared to mutual compliance.",
            equilibrium_summary="Strict dominant equilibrium at (S, W), Pareto dominated by (N, M).",
            icon="⛓️",
        )

    # Deterrence Game: Platform dominant M forces Sharer to comply with N
    if p_dom == "M" and s_br_M == "N":
        return GameTaxonomyResult(
            game_type="Deterrence Game",
            description="The Platform's strictly dominant strategy to heavily moderate (M) reliably deters Sharers from spreading fake news, forcing compliance (N).",
            equilibrium_summary="Dominance-solvable equilibrium at (N, M). Social welfare is maximized.",
            icon="🛡️",
        )

    # Coordination / Stag Hunt: Multiple pure equilibria along diagonal
    pure_eqs = []
    if s_br_W == "S" and p_br_S == "W":
        pure_eqs.append("(S, W)")
    if s_br_M == "S" and p_br_S == "M":
        pure_eqs.append("(S, M)")
    if s_br_W == "N" and p_br_N == "W":
        pure_eqs.append("(N, W)")
    if s_br_M == "N" and p_br_N == "M":
        pure_eqs.append("(N, M)")

    if len(pure_eqs) >= 2:
        return GameTaxonomyResult(
            game_type="Coordination / Multi-Equilibria Game",
            description=f"Multiple pure Nash equilibria exist: {', '.join(pure_eqs)}. Players' optimal choices depend on reciprocal trust and expectations.",
            equilibrium_summary=f"Coexisting stable states: {', '.join(pure_eqs)}.",
            icon="🤝",
        )

    # Inspection Game / Matching Pennies (no pure equilibrium)
    if len(pure_eqs) == 0:
        return GameTaxonomyResult(
            game_type="Inspection Game (Cycling / No Pure NE)",
            description="Sharer wants to spread when platform is slack; Platform wants to moderate when sharer spreads. Incentives cycle continuously.",
            equilibrium_summary="Dynamic cycling resolved exclusively through an interior Mixed Strategy Nash Equilibrium.",
            icon="🔄",
        )

    # Anti-coordination / Chicken
    if "(S, W)" in pure_eqs and "(N, M)" not in pure_eqs:
        return GameTaxonomyResult(
            game_type="Asymmetric Conflict / Hawk-Dove",
            description="Asymmetric payoffs create high-stakes tension between viral aggression and platform moderation costs.",
            equilibrium_summary=f"Equilibrium stabilized at {', '.join(pure_eqs)}.",
            icon="⚔️",
        )

    return GameTaxonomyResult(
        game_type="Strategic Normal-Form Game",
        description="Standard 2x2 asymmetric matrix with unique strategic equilibrium.",
        equilibrium_summary=f"Equilibrium at {', '.join(pure_eqs) if pure_eqs else 'Mixed Equilibrium'}.",
        icon="⚖️",
    )


@dataclass
class Extended3x2PayoffMatrix:
    """
    Extended 3-Strategy Platform game:
    Sharer strategies: S (Spread), N (Do Not Spread)
    Platform strategies: W (Weak), Med (Medium / Fact-Checking Labels), M (Strong / Deplatforming)
    """
    sharer_SW: float = 5.0
    platform_SW: float = -4.0

    sharer_SMed: float = 2.0
    platform_SMed: float = 1.0

    sharer_SM: float = -2.0
    platform_SM: float = 3.0

    sharer_NW: float = 1.0
    platform_NW: float = 0.0

    sharer_NMed: float = 0.8
    platform_NMed: float = 1.5

    sharer_NM: float = 0.0
    platform_NM: float = 2.0

    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame([
            {
                "Sharer Strategy": "S (Spread)",
                "Weak (W)": f"({self.sharer_SW:g}, {self.platform_SW:g})",
                "Medium (Med) [Labeling]": f"({self.sharer_SMed:g}, {self.platform_SMed:g})",
                "Strong (M) [Banning]": f"({self.sharer_SM:g}, {self.platform_SM:g})",
            },
            {
                "Sharer Strategy": "N (Do Not Spread)",
                "Weak (W)": f"({self.sharer_NW:g}, {self.platform_NW:g})",
                "Medium (Med) [Labeling]": f"({self.sharer_NMed:g}, {self.platform_NMed:g})",
                "Strong (M) [Banning]": f"({self.sharer_NM:g}, {self.platform_NM:g})",
            },
        ]).set_index("Sharer Strategy")

