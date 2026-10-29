"""
Page 3: Game Strategy & Payoffs
Compact, visual Game Theory module connecting strategic payoffs directly to viral diffusion consequences.
"""

import streamlit as st
import pandas as pd
import numpy as np

from src.ui_common import (
    apply_theme,
    init_session_state,
    get_current_payoff_matrix,
    set_current_payoff_matrix,
    get_current_equilibrium_analysis,
    get_current_simulation_params,
    render_sidebar_info,
)
from src.payoff_model import PayoffMatrix
from src.propagation import SimulationParameters, run_propagation_simulation
from src.equilibrium import analyze_unilateral_deviation
from src.visualization import (
    create_payoff_matrix_heatmap,
    create_propagation_trajectory_chart,
    create_strategic_best_response_chart,
)

st.set_page_config(
    page_title="Game Strategy & Payoffs | Fake News Model",
    page_icon="🎯",
    layout="wide",
)

apply_theme()
init_session_state()
render_sidebar_info()

st.title("🎯 Game Strategy & Payoffs")
st.caption(
    "Strategic foundation of the platform governance conflict. "
    "Examine strategic incentives, Nash equilibria, and observe how equilibrium choices govern exposure outcomes."
)

st.markdown("---")

matrix = get_current_payoff_matrix()
analysis = get_current_equilibrium_analysis()
base_params = get_current_simulation_params()

# Top Section: Strategic Profile & Simulation Linkage
st.subheader("1. Connect Strategy Profile to Simulation Outcome")
st.caption("Select a profile to observe player payoffs, deviation incentives, and resulting diffusion trajectory.")

col_strat_l, col_strat_r = st.columns([1, 2])

with col_strat_l:
    profile_choice = st.radio(
        "Select Active Strategy Profile (Sharer, Platform):",
        options=["(S, W)", "(S, M)", "(N, W)", "(N, M)"],
        index=1,
        help="(S, W): Viral Spread, Weak Moderation. (S, M): Active Moderation. (N, W): Compliant Laissez-Faire. (N, M): Over-Governance.",
    )

    s_code = "S" if "(S," in profile_choice else "N"
    p_code = "W" if ", W)" in profile_choice else "M"

    dev = analyze_unilateral_deviation(matrix, s_code, p_code)
    u_s, u_p = dev.current_payoffs

    st.markdown("---")
    st.markdown(f"**Strategy Profile:** `{profile_choice}`")
    st.markdown(f"**Payoff Pair:** `Sharer: {u_s:g}` | `Platform: {u_p:g}`")

    if dev.is_nash_equilibrium:
        st.markdown('<div class="badge-nash">Stable Nash Equilibrium</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="badge-suboptimal">Strategically Unstable Profile</div>', unsafe_allow_html=True)

    st.caption(dev.explanation)

with col_strat_r:
    # Map profile to simulation parameters
    coupled_beta = base_params.beta if s_code == "S" else 0.0
    coupled_m = float(st.session_state.m_weak) if p_code == "W" else float(st.session_state.m_strong)

    profile_sim_p = SimulationParameters(
        population=base_params.population,
        initial_exposed=base_params.initial_exposed if s_code == "S" else 0.0,
        beta=coupled_beta,
        moderation_effectiveness=coupled_m,
        time_steps=base_params.time_steps,
    )
    profile_sim_res = run_propagation_simulation(profile_sim_p)

    # Reference baseline
    base_unmod = run_propagation_simulation(
        SimulationParameters(
            population=base_params.population,
            initial_exposed=base_params.initial_exposed,
            beta=base_params.beta,
            moderation_effectiveness=0.0,
            time_steps=base_params.time_steps,
        )
    )

    fig_link = create_propagation_trajectory_chart(
        {
            f"Selected Profile {profile_choice}": profile_sim_res,
            "Unmoderated Baseline (m=0)": base_unmod,
        },
        title=f"Diffusion Trajectory from Strategy Profile {profile_choice}",
    )
    st.plotly_chart(fig_link, use_container_width=True)

# Interpretation Callout
st.markdown(
    f"""
    <div class="academic-callout">
        <b>Strategic & Epidemiological Interpretation:</b> Under profile <code>{profile_choice}</code>, 
        misinformation spreads to <b>{profile_sim_res.final_exposure:,.0f}</b> individuals 
        (<b>{(profile_sim_res.final_exposure / profile_sim_res.population) * 100:.1f}%</b> of population). 
        <i>Key Insight:</i> A Nash equilibrium denotes strategic stability where neither player unilaterally departs, 
        which does <b>not</b> guarantee zero fake news exposure. Real platform governance balances enforcement costs against harm.
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("---")

# Section 2: Compact Interactive Payoff Matrix
st.subheader("2. Compact Payoff Matrix & Equilibrium Visualizer")

mat_col_l, mat_col_r = st.columns([1, 1])

with mat_col_l:
    st.markdown("#### Payoff Configuration")
    c1, c2 = st.columns(2)
    with c1:
        s_SW = st.number_input("Sharer (S, W):", value=float(matrix.sharer_SW), step=0.5)
        p_SW = st.number_input("Platform (S, W):", value=float(matrix.platform_SW), step=0.5)
        s_NW = st.number_input("Sharer (N, W):", value=float(matrix.sharer_NW), step=0.5)
        p_NW = st.number_input("Platform (N, W):", value=float(matrix.platform_NW), step=0.5)
    with c2:
        s_SM = st.number_input("Sharer (S, M):", value=float(matrix.sharer_SM), step=0.5)
        p_SM = st.number_input("Platform (S, M):", value=float(matrix.platform_SM), step=0.5)
        s_NM = st.number_input("Sharer (N, M):", value=float(matrix.sharer_NM), step=0.5)
        p_NM = st.number_input("Platform (N, M):", value=float(matrix.platform_NM), step=0.5)

    if st.button("Reset Payoffs to Course Default", use_container_width=True):
        set_current_payoff_matrix(PayoffMatrix.default())
        st.rerun()

    # Apply changes
    new_mat = PayoffMatrix(
        sharer_SW=s_SW, platform_SW=p_SW,
        sharer_SM=s_SM, platform_SM=p_SM,
        sharer_NW=s_NW, platform_NW=p_NW,
        sharer_NM=s_NM, platform_NM=p_NM,
    )
    new_mat.validate()
    set_current_payoff_matrix(new_mat)

with mat_col_r:
    st.markdown("#### Matrix Heatmap & Nash Highlighting")
    fig_mat = create_payoff_matrix_heatmap(new_mat, analysis)
    st.plotly_chart(fig_mat, use_container_width=True)

st.markdown("---")

# Section 3: Reaction Correspondences & Mixed Strategy
st.subheader("3. Best Response Correspondences in Probability Space")
st.caption("Visualizes best-response functions in mixed strategy unit square [0, 1] x [0, 1]. Star indicates Pure Nash Eq; Diamond indicates Mixed Eq.")

fig_br = create_strategic_best_response_chart(new_mat, analysis)
st.plotly_chart(fig_br, use_container_width=True)

# Mathematical Details in Expanders (Keeping main page clean)
with st.expander("📐 Mathematical Formulations & Mixed Strategy Derivations", expanded=False):
    st.markdown(
        """
        **Best Response Correspondences:**
        - Player 1 (Sharer): $BR_1(s_2) = \\arg\\max_{s_1} u_1(s_1, s_2)$
        - Player 2 (Platform): $BR_2(s_1) = \\arg\\max_{s_2} u_2(s_1, s_2)$
        
        **Mixed Strategy Indifference Equations:**
        Let $p = \\mathbb{P}(\\text{Sharer plays } S)$ and $q = \\mathbb{P}(\\text{Platform plays } W)$:
        - Platform indifference solves $p^*$:
          $$p^* = \\frac{u_2(N, M) - u_2(N, W)}{(u_2(S, W) - u_2(S, M)) - (u_2(N, W) - u_2(N, M))}$$
        - Sharer indifference solves $q^*$:
          $$q^* = \\frac{u_1(N, M) - u_1(S, M)}{(u_1(S, W) - u_1(S, M)) - (u_1(N, W) - u_1(N, M))}$$
        """
    )
    if analysis.mixed_equilibrium.exists_interior:
        st.success(f"Interior Mixed Nash Eq found at p* = {analysis.mixed_equilibrium.p_star:.3f}, q* = {analysis.mixed_equilibrium.q_star:.3f}.")
    else:
        st.info(analysis.mixed_equilibrium.explanation)
