"""
Page 2: Network Spread
Peer-to-peer misinformation diffusion over synthetic social network topologies.
"""

import streamlit as st
import pandas as pd
import numpy as np

from src.ui_common import apply_theme, init_session_state, render_sidebar_info
from src.network_simulation import (
    generate_synthetic_network,
    run_full_network_simulation,
    create_network_plotly_figure,
    create_network_spread_curves_chart,
    STATE_SUSCEPTIBLE,
    STATE_EXPOSED,
    STATE_MODERATED,
)

st.set_page_config(
    page_title="Network Spread | Fake News Model",
    page_icon="🕸️",
    layout="wide",
)

apply_theme()
init_session_state()
render_sidebar_info()

st.title("🕸️ Network Spread Laboratory")
st.caption(
    "Visualize microscopic misinformation diffusion through explicit network structures. "
    "Observe hub super-spreaders, cluster virality, and platform quarantine dynamics."
)

st.markdown(
    """
    <div class="academic-callout">
        <b>Network Topology vs. Population Equation:</b>
        <br>
        Unlike the deterministic mean-field equation, this simulation models localized peer-to-peer 
        transmission across an explicit graph $G = (V, E)$. An exposed node attempts to infect 
        susceptible neighbors with probability $P_{\\text{transmit}} = \\beta (1 - m)$. 
        Concurrently, platform moderation inspects active sharers with probability $m$, 
        moving detected nodes into a quarantined (moderated) state.
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("---")

# Network Setup Controls
st.subheader("1. Network Topology & Transmission Configuration")

col_net1, col_net2, col_net3, col_net4 = st.columns(4)

with col_net1:
    net_type = st.selectbox(
        "Network Structure:",
        options=["preferential_attachment", "random"],
        format_func=lambda x: "Barabási–Albert (Scale-Free)" if x == "preferential_attachment" else "Erdős–Rényi (Random Graph)",
        index=0,
        help="Scale-Free networks feature hub super-spreaders (power law). Random graphs feature Poisson degree distributions.",
    )

with col_net2:
    n_nodes = st.slider(
        "Network Size (Nodes |V|):",
        min_value=25,
        max_value=120,
        value=60,
        step=5,
        help="Number of simulated users in the social graph.",
    )

with col_net3:
    n_seeds = st.slider(
        "Initial Seeds (Exposed):",
        min_value=1,
        max_value=10,
        value=3,
        step=1,
        help="Initial accounts sharing the fake news item at t = 0.",
    )

with col_net4:
    net_seed = st.number_input(
        "Random Seed (Reproducibility):",
        min_value=1,
        max_value=9999,
        value=42,
        step=1,
    )

col_dyn1, col_dyn2, col_dyn3 = st.columns(3)

with col_dyn1:
    net_trans_rate = st.slider("Edge Sharing Rate (β):", 0.05, 1.00, 0.45, 0.05)
with col_dyn2:
    net_mod_rate = st.slider("Moderation Detection (m):", 0.00, 1.00, 0.35, 0.05)
with col_dyn3:
    net_steps = st.slider("Simulation Rounds (T):", 5, 25, 12, 1)

# Session state caching for generated network to ensure responsive UI
net_cache_key = f"{net_type}_{n_nodes}_{net_seed}"
if "cached_network_key" not in st.session_state or st.session_state.cached_network_key != net_cache_key:
    G, pos = generate_synthetic_network(network_type=net_type, n_nodes=n_nodes, seed=int(net_seed))
    st.session_state.cached_network = G
    st.session_state.cached_pos = pos
    st.session_state.cached_network_key = net_cache_key

G = st.session_state.cached_network
pos = st.session_state.cached_pos

# Run simulation
sim_result = run_full_network_simulation(
    graph=G,
    pos=pos,
    network_type=net_type,
    n_initial_exposed=int(n_seeds),
    transmission_rate=float(net_trans_rate),
    moderation_effectiveness=float(net_mod_rate),
    max_steps=int(net_steps),
    seed=int(net_seed),
)

st.markdown("---")

# Section 2: Interactive Step Viewer & Network Graph
st.subheader("2. Interactive Network Graph & Time Stepper")

step_slider_col, reset_col = st.columns([4, 1])

with step_slider_col:
    selected_step = st.slider(
        "Explore Network State Across Time Steps:",
        min_value=0,
        max_value=net_steps,
        value=min(4, net_steps),
        step=1,
        help="Slide to inspect the state of every node at any simulation epoch.",
    )

with reset_col:
    st.write("")
    if st.button("🎲 Re-Seed Network", use_container_width=True):
        st.session_state.cached_network_key = ""
        st.rerun()

current_record = sim_result.steps[selected_step]

# Live Network State Metrics
m_col1, m_col2, m_col3, m_col4 = st.columns(4)

with m_col1:
    st.metric(
        "Total Exposed",
        f"{current_record.cumulative_exposed} / {n_nodes}",
        f"{(current_record.cumulative_exposed / n_nodes) * 100:.1f}% exposure",
    )

with m_col2:
    st.metric(
        "Active Sharers (Infectious)",
        f"{current_record.active_sharers}",
        "Nodes currently transmitting",
        delta_color="inverse",
    )

with m_col3:
    st.metric(
        "Moderated / Quarantined",
        f"{current_record.moderated_count}",
        "Blocked by platform",
        delta_color="normal",
    )

with m_col4:
    st.metric(
        "Newly Exposed This Round",
        f"{current_record.newly_exposed}",
        f"At step t = {selected_step}",
    )

# Render Network Figure
fig_net = create_network_plotly_figure(
    graph=G,
    pos=pos,
    node_states=current_record.node_states,
    step_num=selected_step,
    title=f"Network Misinformation State at Time Step t = {selected_step} ({net_type.title()})",
)
st.plotly_chart(fig_net, use_container_width=True)

st.markdown("---")

# Section 3: Network Diffusion Time-Series Curves
st.subheader("3. Network Diffusion Kinetics")
fig_curves = create_network_spread_curves_chart(sim_result)
st.plotly_chart(fig_curves, use_container_width=True)
