"""
Page 1: Moderation Experiments
Comparative policy lab featuring simultaneous policy evaluations,
early vs. late intervention dynamics, and one-click experiment presets.
"""

import streamlit as st
import pandas as pd
import numpy as np

from src.ui_common import (
    apply_theme,
    init_session_state,
    get_current_simulation_params,
    render_sidebar_info,
)
from src.propagation import (
    SimulationParameters,
    simulate_moderation_scenarios,
    sweep_moderation_effectiveness,
    run_propagation_simulation,
)
from src.experiment_runner import (
    run_delayed_moderation_simulation,
    sweep_sharing_rate,
    create_delayed_intervention_chart,
    create_sharing_rate_sweep_chart,
    package_experiment_record,
)
from src.metrics import generate_scenario_comparison_table
from src.visualization import (
    create_propagation_trajectory_chart,
    create_final_exposure_bar_chart,
    create_moderation_sweep_chart,
)

st.set_page_config(
    page_title="Moderation Experiments | Fake News Model",
    page_icon="⚖️",
    layout="wide",
)

apply_theme()
init_session_state()
render_sidebar_info()

st.title("⚖️ Moderation Experiments Laboratory")
st.markdown(
    "Test, compare, and benchmark diverse platform content governance policies. "
    "Evaluate policy effectiveness, early versus delayed interventions, and transmission pressure thresholds."
)

st.markdown("---")

# One-Click Experiment Presets
st.subheader("1. Instant Experiment Presets")
st.caption("Load canonical scenarios instantly to observe key dynamical principles.")

preset_col1, preset_col2, preset_col3, preset_col4 = st.columns(4)

with preset_col1:
    if st.button("🔥 A: Viral Misinformation", use_container_width=True):
        st.session_state.beta = 0.55
        st.session_state.moderation_effectiveness = 0.15
        st.session_state.m_weak = 0.15
        st.success("Loaded Preset A: High transmission (β=0.55), Weak moderation (m=0.15).")
        st.rerun()

with preset_col2:
    if st.button("🛡️ B: Effective Intervention", use_container_width=True):
        st.session_state.beta = 0.55
        st.session_state.moderation_effectiveness = 0.75
        st.session_state.m_strong = 0.85
        st.success("Loaded Preset B: High transmission (β=0.55) suppressed by Strong moderation (m=0.75).")
        st.rerun()

with preset_col3:
    if st.button("⚡ C: High Sharing Pressure", use_container_width=True):
        st.session_state.beta = 0.85
        st.session_state.moderation_effectiveness = 0.40
        st.success("Loaded Preset C: Intense viral pressure (β=0.85), Moderate moderation (m=0.40).")
        st.rerun()

with preset_col4:
    if st.button("⏱️ D: Early vs Late Intervention", use_container_width=True):
        st.session_state.beta = 0.45
        st.session_state.moderation_effectiveness = 0.70
        st.success("Loaded Preset D: Prepared for Early vs Delayed Intervention analysis below.")
        st.rerun()

st.markdown("---")

# Section 2: Multi-Policy Simultaneous Comparison
st.subheader("2. Multi-Policy Benchmark")
st.caption("Simultaneously compare 4 platform moderation policies against the unmoderated baseline.")

# Configurable policy sliders
pol_c1, pol_c2, pol_c3, pol_c4 = st.columns(4)
with pol_c1:
    m_none = st.slider("No Moderation (m)", 0.00, 0.10, float(st.session_state.m_none), 0.01)
with pol_c2:
    m_weak = st.slider("Weak Moderation (m)", 0.05, 0.40, float(st.session_state.m_weak), 0.01)
with pol_c3:
    m_mod = st.slider("Moderate Moderation (m)", 0.35, 0.70, float(st.session_state.m_moderate), 0.01)
with pol_c4:
    m_str = st.slider("Strong Moderation (m)", 0.65, 1.00, float(st.session_state.m_strong), 0.01)

base_params = get_current_simulation_params()
scenarios_dict = {
    "No moderation": m_none,
    "Weak moderation": m_weak,
    "Moderate moderation": m_mod,
    "Strong moderation": m_str,
}
scenario_results = simulate_moderation_scenarios(base_params, scenarios_dict)
baseline_res = scenario_results["No moderation"]

# Trajectory and Bar Charts side-by-side
col_chart_l, col_chart_r = st.columns([3, 2])
with col_chart_l:
    fig_traj = create_propagation_trajectory_chart(scenario_results, title="Policy Exposure Trajectories")
    st.plotly_chart(fig_traj, use_container_width=True)

with col_chart_r:
    fig_bar = create_final_exposure_bar_chart(scenario_results, title="Final Exposure by Policy")
    st.plotly_chart(fig_bar, use_container_width=True)

# Comparison Table & Best Policy
summary_df = generate_scenario_comparison_table(scenario_results, baseline_key="No moderation")
st.dataframe(summary_df, use_container_width=True, hide_index=True)

# Best Policy Callout
best_policy = min(scenario_results.items(), key=lambda x: x[1].final_exposure)
best_red = best_policy[1].compute_reduction(baseline_res)["final_reduction_pct"]
st.info(
    f"🏆 **Best Performing Policy:** `{best_policy[0]}` achieved lowest final exposure of "
    f"**{best_policy[1].final_exposure:,.0f}** individuals (**{best_red:.1f}% reduction** vs No Moderation)."
)

st.markdown("---")

# Section 3: Early vs Delayed Intervention Experiment
st.subheader("3. Early Intervention vs. Delayed Reaction")
st.markdown(
    "Explore how timing affects policy efficacy. Does waiting to verify misinformation compromise platform control?"
)

delay_c1, delay_c2 = st.columns([1, 3])
with delay_c1:
    delay_step = st.slider(
        "Intervention Delay (Steps)",
        min_value=1,
        max_value=max(2, base_params.time_steps - 2),
        value=min(8, base_params.time_steps - 2),
        help="Number of steps the misinformation is allowed to spread before moderation activates.",
    )
    intervention_strength = st.slider(
        "Intervention Intensity (m)",
        min_value=0.10,
        max_value=1.00,
        value=0.75,
        step=0.05,
    )

with delay_c2:
    # 1. Early intervention from t=0
    early_p = SimulationParameters(
        population=base_params.population,
        initial_exposed=base_params.initial_exposed,
        beta=base_params.beta,
        moderation_effectiveness=intervention_strength,
        time_steps=base_params.time_steps,
    )
    early_res = run_propagation_simulation(early_p)

    # 2. Delayed intervention
    delayed_res = run_delayed_moderation_simulation(base_params, delay_step=delay_step, m_intervention=intervention_strength)

    # Plot
    fig_delay = create_delayed_intervention_chart(early_res, delayed_res, baseline_res, delay_step=delay_step)
    st.plotly_chart(fig_delay, use_container_width=True)

# Delay Metrics
d_kpi1, d_kpi2, d_kpi3 = st.columns(3)
with d_kpi1:
    st.metric("Early Intervention Final", f"{early_res.final_exposure:,.0f}", "Immediate action at t = 0")
with d_kpi2:
    penalty = delayed_res.final_exposure - early_res.final_exposure
    st.metric(
        f"Delayed Intervention (t={delay_step})",
        f"{delayed_res.final_exposure:,.0f}",
        f"+{penalty:,.0f} additional exposed due to delay",
        delta_color="inverse",
    )
with d_kpi3:
    penalty_pct = (penalty / early_res.final_exposure) * 100 if early_res.final_exposure > 0 else 0
    st.metric("Delay Vulnerability Penalty", f"+{penalty_pct:.1f}% exposure", "Cost of delayed enforcement")

st.markdown("---")

# Section 4: Dual Sensitivity Sweeps
st.subheader("4. Parameter Sensitivity Sweeps")
tab_sweep_m, tab_sweep_b = st.tabs(["Moderation Effectiveness Sweep (m ∈ [0, 1])", "Transmission Rate Sweep (β ∈ [0.05, 1.20])"])

with tab_sweep_m:
    st.caption("Continuously sweep platform moderation effectiveness to identify the inflection point of diminishing returns.")
    sweep_m_df = sweep_moderation_effectiveness(base_params, steps=40)
    fig_sweep_m = create_moderation_sweep_chart(sweep_m_df)
    st.plotly_chart(fig_sweep_m, use_container_width=True)

with tab_sweep_b:
    st.caption("Sweep peer-to-peer transmission propensity β while holding current moderation policy fixed.")
    sweep_b_df = sweep_sharing_rate(
        population=base_params.population,
        initial_exposed=base_params.initial_exposed,
        moderation_effectiveness=base_params.moderation_effectiveness,
        time_steps=base_params.time_steps,
        steps=30,
    )
    fig_sweep_b = create_sharing_rate_sweep_chart(sweep_b_df)
    st.plotly_chart(fig_sweep_b, use_container_width=True)
