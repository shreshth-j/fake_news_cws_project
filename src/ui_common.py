"""
Shared UI components, styling, and session state management across pages.
Simulation-First Architecture with experiment persistence and step-by-step state.
"""

import streamlit as st
from typing import Dict, List, Optional, Any
from src.payoff_model import PayoffMatrix
from src.propagation import SimulationParameters, simulate_moderation_scenarios, run_propagation_simulation
from src.equilibrium import analyze_game, EquilibriumAnalysisResult


CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }

    /* Metric card styling */
    .metric-card {
        background: #0F172A;
        border: 1px solid #1E293B;
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    .metric-title {
        color: #94A3B8;
        font-size: 0.80rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 3px;
    }
    .metric-value {
        color: #F8FAFC;
        font-size: 1.55rem;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
        letter-spacing: -0.02em;
    }
    .metric-delta {
        font-size: 0.82rem;
        font-weight: 500;
        margin-top: 3px;
    }
    .delta-positive { color: #34D399; }
    .delta-negative { color: #F87171; }
    .delta-neutral { color: #94A3B8; }

    /* Compact simulation banner */
    .sim-banner {
        background: linear-gradient(90deg, #1E293B 0%, #0F172A 100%);
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 12px 18px;
        margin-bottom: 16px;
        color: #E2E8F0;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    /* Academic callout box */
    .academic-callout {
        background: #0F172A;
        border-left: 4px solid #38BDF8;
        border-radius: 0 8px 8px 0;
        padding: 12px 16px;
        margin: 12px 0;
        color: #E2E8F0;
        font-size: 0.90rem;
        line-height: 1.5;
    }

    .badge-nash {
        background-color: rgba(16, 185, 129, 0.18);
        color: #34D399;
        border: 1px solid #10B981;
        border-radius: 4px;
        padding: 3px 8px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        display: inline-block;
    }

    .badge-suboptimal {
        background-color: rgba(239, 68, 68, 0.18);
        color: #F87171;
        border: 1px solid #EF4444;
        border-radius: 4px;
        padding: 3px 8px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        display: inline-block;
    }

    /* Clean Streamlit elements */
    div[data-testid="stMetricValue"] {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 1.65rem !important;
    }

    .stButton>button {
        font-weight: 500;
        border-radius: 6px;
        transition: all 0.15s ease-in-out;
    }
</style>
"""


def init_session_state() -> None:
    """Initialize shared parameters and experiment state in st.session_state."""
    if "initialized" not in st.session_state:
        st.session_state.initialized = True

        # Model simulation parameters
        st.session_state.population = 10000
        st.session_state.initial_exposed = 100.0
        st.session_state.beta = 0.35
        st.session_state.moderation_effectiveness = 0.25
        st.session_state.time_steps = 30

        # Scenario moderation values
        st.session_state.m_none = 0.00
        st.session_state.m_weak = 0.25
        st.session_state.m_moderate = 0.55
        st.session_state.m_strong = 0.85

        # Payoff matrix
        st.session_state.payoff_matrix = PayoffMatrix.default()

        # Strategic Game selection
        st.session_state.selected_sharer = "S"
        st.session_state.selected_platform = "M"

        # Step-by-step simulation state
        st.session_state.step_sim_current_step = 0
        st.session_state.step_sim_history = [100.0]

        # Saved experiments catalog for comparison page
        p_base = SimulationParameters(population=10000, initial_exposed=100.0, beta=0.35, moderation_effectiveness=0.0, time_steps=30)
        r_base = run_propagation_simulation(p_base)

        p_mod = SimulationParameters(population=10000, initial_exposed=100.0, beta=0.35, moderation_effectiveness=0.45, time_steps=30)
        r_mod = run_propagation_simulation(p_mod)

        p_strong = SimulationParameters(population=10000, initial_exposed=100.0, beta=0.35, moderation_effectiveness=0.85, time_steps=30)
        r_strong = run_propagation_simulation(p_strong)

        st.session_state.saved_experiments = [
            {
                "id": "exp_preset_1",
                "name": "Benchmark: No Moderation (m = 0.00)",
                "model_type": "Deterministic Equation",
                "population": 10000,
                "initial_exposed": 100.0,
                "beta": 0.35,
                "moderation": 0.00,
                "time_steps": 30,
                "final_exposure": r_base.final_exposure,
                "peak_exposure": r_base.peak_exposure,
                "final_exposure_pct": (r_base.final_exposure / 10000) * 100,
                "reduction_pct": 0.0,
                "trajectory_steps": list(r_base.time_steps),
                "trajectory_exposure": list(r_base.exposure),
                "timestamp": "Default Benchmark",
                "notes": "Unmitigated viral exposure baseline.",
            },
            {
                "id": "exp_preset_2",
                "name": "Balanced Policy (m = 0.45)",
                "model_type": "Deterministic Equation",
                "population": 10000,
                "initial_exposed": 100.0,
                "beta": 0.35,
                "moderation": 0.45,
                "time_steps": 30,
                "final_exposure": r_mod.final_exposure,
                "peak_exposure": r_mod.peak_exposure,
                "final_exposure_pct": (r_mod.final_exposure / 10000) * 100,
                "reduction_pct": ((r_base.final_exposure - r_mod.final_exposure) / r_base.final_exposure) * 100,
                "trajectory_steps": list(r_mod.time_steps),
                "trajectory_exposure": list(r_mod.exposure),
                "timestamp": "Default Benchmark",
                "notes": "Moderate platform intervention.",
            },
            {
                "id": "exp_preset_3",
                "name": "Strict Enforcement (m = 0.85)",
                "model_type": "Deterministic Equation",
                "population": 10000,
                "initial_exposed": 100.0,
                "beta": 0.35,
                "moderation": 0.85,
                "time_steps": 30,
                "final_exposure": r_strong.final_exposure,
                "peak_exposure": r_strong.peak_exposure,
                "final_exposure_pct": (r_strong.final_exposure / 10000) * 100,
                "reduction_pct": ((r_base.final_exposure - r_strong.final_exposure) / r_base.final_exposure) * 100,
                "trajectory_steps": list(r_strong.time_steps),
                "trajectory_exposure": list(r_strong.exposure),
                "timestamp": "Default Benchmark",
                "notes": "Aggressive proactive content quarantine.",
            },
        ]


def apply_theme() -> None:
    """Inject styling into current page."""
    init_session_state()
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def get_current_simulation_params(moderation_effectiveness: Optional[float] = None) -> SimulationParameters:
    """Create SimulationParameters from current session state."""
    init_session_state()
    m = st.session_state.moderation_effectiveness if moderation_effectiveness is None else moderation_effectiveness
    return SimulationParameters(
        population=int(st.session_state.population),
        initial_exposed=float(st.session_state.initial_exposed),
        beta=float(st.session_state.beta),
        moderation_effectiveness=float(m),
        time_steps=int(st.session_state.time_steps),
    )


def get_current_payoff_matrix() -> PayoffMatrix:
    init_session_state()
    return st.session_state.payoff_matrix


def set_current_payoff_matrix(matrix: PayoffMatrix) -> None:
    matrix.validate()
    st.session_state.payoff_matrix = matrix


def get_current_equilibrium_analysis() -> EquilibriumAnalysisResult:
    matrix = get_current_payoff_matrix()
    return analyze_game(matrix)


def render_sidebar_info() -> None:
    """Render consistent sidebar with simulation-first focus."""
    init_session_state()
    st.sidebar.markdown("### Interactive Simulation Lab")
    st.sidebar.caption("Current Active Parameters")

    st.sidebar.markdown(f"**Population (N):** `{st.session_state.population:,}`")
    st.sidebar.markdown(f"**Initial (I₀):** `{st.session_state.initial_exposed:,.0f}`")
    st.sidebar.markdown(f"**Transmission (β):** `{st.session_state.beta:.2f}`")
    st.sidebar.markdown(f"**Moderation (m):** `{st.session_state.moderation_effectiveness:.2f}`")
    st.sidebar.markdown(f"**Duration (T):** `{st.session_state.time_steps} steps`")

    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Saved Experiments:** `{len(st.session_state.saved_experiments)}`")

    analysis = get_current_equilibrium_analysis()
    if analysis.has_pure_equilibrium:
        eq_labels = ", ".join(eq.profile_label for eq in analysis.pure_equilibria)
        st.sidebar.markdown(f"**Game Equilibrium:** `{eq_labels}`")
    else:
        st.sidebar.markdown("**Game Equilibrium:** `Mixed Strategy`")

    st.sidebar.markdown("---")
    st.sidebar.caption("Simulation-First Game Theory Dashboard\nNavigate using the pages above.")
