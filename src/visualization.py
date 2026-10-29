"""
Interactive Plotly Visualizations for Game Theory and Fake News Propagation.

Styling follows a dark navy/charcoal academic research aesthetic.
"""

from typing import Dict, List, Optional, Tuple
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

from src.propagation import PropagationResult
from src.payoff_model import PayoffMatrix
from src.equilibrium import EquilibriumAnalysisResult

# Academic Dark Theme Palette
THEME = {
    "bg_color": "#0B1120",
    "paper_color": "#0F172A",
    "card_color": "#1E293B",
    "grid_color": "#334155",
    "text_color": "#F8FAFC",
    "subtext_color": "#94A3B8",
    "colors": {
        "No moderation": "#EF4444",        # Red
        "Weak moderation": "#F59E0B",      # Amber
        "Moderate moderation": "#3B82F6",  # Blue
        "Strong moderation": "#10B981",    # Emerald
        "Custom": "#8B5CF6",               # Violet
        "Baseline": "#64748B",             # Slate
    },
    "palette": ["#EF4444", "#F59E0B", "#3B82F6", "#10B981", "#8B5CF6", "#06B6D4", "#EC4899"],
}


def create_propagation_trajectory_chart(
    scenario_results: Dict[str, PropagationResult],
    title: str = "Fake News Exposure Trajectory Over Time",
) -> go.Figure:
    """
    Graph A: Line chart showing exposed population over time across moderation policies.
    """
    fig = go.Figure()

    for name, res in scenario_results.items():
        color = THEME["colors"].get(name, THEME["palette"][len(fig.data) % len(THEME["palette"])])
        fig.add_trace(
            go.Scatter(
                x=res.time_steps,
                y=res.exposure,
                mode="lines+markers",
                name=f"{name} (m={res.moderation_effectiveness:.2f})",
                line=dict(color=color, width=3),
                marker=dict(size=4),
                hovertemplate="<b>%{fullData.name}</b><br>Step: %{x}<br>Exposed: %{y:,.0f} (%{customdata:.1%})<extra></extra>",
                customdata=res.exposure / res.population if res.population > 0 else np.zeros_like(res.exposure),
            )
        )

    # Reference population line
    if scenario_results:
        first_res = next(iter(scenario_results.values()))
        fig.add_hline(
            y=first_res.population,
            line_dash="dot",
            line_color="#64748B",
            annotation_text=f"Total Population N = {first_res.population:,.0f}",
            annotation_position="bottom right",
            annotation_font=dict(color="#94A3B8", size=11),
        )

    fig.update_layout(
        title=dict(text=title, font=dict(color=THEME["text_color"], size=16)),
        paper_bgcolor=THEME["paper_color"],
        plot_bgcolor=THEME["bg_color"],
        font=dict(color=THEME["text_color"], family="Inter, system-ui, sans-serif"),
        xaxis=dict(
            title="Simulation Time Step (t)",
            gridcolor=THEME["grid_color"],
            zerolinecolor=THEME["grid_color"],
            color=THEME["subtext_color"],
        ),
        yaxis=dict(
            title="Exposed Population (I_t)",
            gridcolor=THEME["grid_color"],
            zerolinecolor=THEME["grid_color"],
            color=THEME["subtext_color"],
        ),
        hovermode="x unified",
        legend=dict(
            bgcolor="rgba(15, 23, 42, 0.8)",
            bordercolor=THEME["grid_color"],
            borderwidth=1,
            font=dict(color=THEME["text_color"]),
        ),
        margin=dict(l=60, r=40, t=60, b=60),
    )
    return fig


def create_final_exposure_bar_chart(
    scenario_results: Dict[str, PropagationResult],
    title: str = "Comparison of Final Exposure by Moderation Policy",
) -> go.Figure:
    """
    Graph B: Bar chart comparing final exposure under each moderation scenario.
    """
    scenarios = list(scenario_results.keys())
    final_exposures = [res.final_exposure for res in scenario_results.values()]
    percentages = [
        (res.final_exposure / res.population) * 100 if res.population > 0 else 0
        for res in scenario_results.values()
    ]
    colors = [
        THEME["colors"].get(name, THEME["palette"][i % len(THEME["palette"])])
        for i, name in enumerate(scenarios)
    ]

    fig = go.Figure(
        data=[
            go.Bar(
                x=scenarios,
                y=final_exposures,
                marker=dict(color=colors, line=dict(color="#0F172A", width=1.5)),
                text=[f"{val:,.0f} ({pct:.1f}%)" for val, pct in zip(final_exposures, percentages)],
                textposition="outside",
                textfont=dict(color=THEME["text_color"], size=12),
                hovertemplate="<b>%{x}</b><br>Final Exposure: %{y:,.0f}<extra></extra>",
            )
        ]
    )

    fig.update_layout(
        title=dict(text=title, font=dict(color=THEME["text_color"], size=16)),
        paper_bgcolor=THEME["paper_color"],
        plot_bgcolor=THEME["bg_color"],
        font=dict(color=THEME["text_color"], family="Inter, system-ui, sans-serif"),
        xaxis=dict(
            title="Moderation Scenario",
            gridcolor=THEME["grid_color"],
            color=THEME["subtext_color"],
        ),
        yaxis=dict(
            title="Final Exposed Individuals",
            gridcolor=THEME["grid_color"],
            color=THEME["subtext_color"],
        ),
        margin=dict(l=60, r=40, t=60, b=60),
    )
    return fig


def create_moderation_sweep_chart(
    sweep_df: pd.DataFrame,
    title: str = "Moderation Effectiveness Sensitivity Analysis",
) -> go.Figure:
    """
    Graph C: Plot final exposure and exposure reduction against moderation effectiveness (m).
    """
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=sweep_df["moderation_effectiveness"],
            y=sweep_df["final_exposure"],
            mode="lines",
            name="Final Exposure (Count)",
            line=dict(color="#38BDF8", width=3),
            yaxis="y1",
            hovertemplate="m = %{x:.2f}<br>Final Exposure: %{y:,.0f}<extra></extra>",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=sweep_df["moderation_effectiveness"],
            y=sweep_df["final_reduction_pct"],
            mode="lines",
            name="Exposure Reduction vs m=0 (%)",
            line=dict(color="#10B981", width=3, dash="dash"),
            yaxis="y2",
            hovertemplate="m = %{x:.2f}<br>Reduction: %{y:.1f}%<extra></extra>",
        )
    )

    fig.update_layout(
        title=dict(text=title, font=dict(color=THEME["text_color"], size=16)),
        paper_bgcolor=THEME["paper_color"],
        plot_bgcolor=THEME["bg_color"],
        font=dict(color=THEME["text_color"], family="Inter, system-ui, sans-serif"),
        xaxis=dict(
            title="Moderation Effectiveness (m)",
            gridcolor=THEME["grid_color"],
            color=THEME["subtext_color"],
            range=[0.0, 1.0],
        ),
        yaxis=dict(
            title="Final Exposure Count",
            gridcolor=THEME["grid_color"],
            color="#38BDF8",
        ),
        yaxis2=dict(
            title="Reduction Relative to No Moderation (%)",
            color="#10B981",
            overlaying="y",
            side="right",
            range=[0, 105],
            showgrid=False,
        ),
        legend=dict(
            bgcolor="rgba(15, 23, 42, 0.8)",
            bordercolor=THEME["grid_color"],
            borderwidth=1,
            font=dict(color=THEME["text_color"]),
        ),
        margin=dict(l=60, r=60, t=60, b=60),
    )
    return fig


def create_payoff_matrix_heatmap(
    matrix: PayoffMatrix,
    analysis: EquilibriumAnalysisResult,
) -> go.Figure:
    """
    Graph D: Payoff visualization table/heatmap showing both players' payoffs
    and highlighting Nash equilibrium cells.
    """
    profiles = [
        ("S", "W", matrix.sharer_SW, matrix.platform_SW),
        ("S", "M", matrix.sharer_SM, matrix.platform_SM),
        ("N", "W", matrix.sharer_NW, matrix.platform_NW),
        ("N", "M", matrix.sharer_NM, matrix.platform_NM),
    ]

    eq_profiles = {eq.profile_label for eq in analysis.pure_equilibria}

    # Prepare cell annotations
    annotations = []
    matrix_cells = [
        [f"({matrix.sharer_SW:g}, {matrix.platform_SW:g})", f"({matrix.sharer_SM:g}, {matrix.platform_SM:g})"],
        [f"({matrix.sharer_NW:g}, {matrix.platform_NW:g})", f"({matrix.sharer_NM:g}, {matrix.platform_NM:g})"],
    ]

    # Z values for background shading: highlight equilibrium
    z = [
        [2 if "(S, W)" in eq_profiles else 0, 2 if "(S, M)" in eq_profiles else 0],
        [2 if "(N, W)" in eq_profiles else 0, 2 if "(N, M)" in eq_profiles else 0],
    ]

    fig = go.Figure(
        data=go.Heatmap(
            z=z,
            x=["Weak Moderation (W)", "Strong Moderation (M)"],
            y=["Spread Fake News (S)", "Do Not Spread (N)"],
            colorscale=[
                [0.0, "#1E293B"],   # Dark slate for standard cells
                [0.5, "#1E293B"],
                [1.0, "#065F46"],   # Deep emerald for Nash equilibrium cells
            ],
            showscale=False,
            hoverinfo="none",
        )
    )

    y_labels = ["Spread Fake News (S)", "Do Not Spread (N)"]
    x_labels = ["Weak Moderation (W)", "Strong Moderation (M)"]

    for i, s_label in enumerate(["S", "N"]):
        for j, p_label in enumerate(["W", "M"]):
            u1, u2 = matrix.get_payoff(s_label, p_label)
            is_eq = f"({s_label}, {p_label})" in eq_profiles
            tag = " ★ NASH EQUILIBRIUM" if is_eq else ""
            color = "#34D399" if is_eq else "#F8FAFC"
            weight = "bold" if is_eq else "normal"

            text = f"<b>({u1:g}, {u2:g})</b><br><span style='font-size:11px;color:{color};'>{tag}</span>"
            annotations.append(
                dict(
                    x=x_labels[j],
                    y=y_labels[i],
                    text=text,
                    showarrow=False,
                    font=dict(color=color, size=16),
                )
            )

    fig.update_layout(
        title=dict(
            text="Interactive Payoff Matrix (Sharer Payoff, Platform Payoff)",
            font=dict(color=THEME["text_color"], size=16),
        ),
        paper_bgcolor=THEME["paper_color"],
        plot_bgcolor=THEME["bg_color"],
        font=dict(color=THEME["text_color"], family="Inter, system-ui, sans-serif"),
        xaxis=dict(
            title="Player 2: Social Media Platform Strategy",
            color=THEME["subtext_color"],
            side="bottom",
        ),
        yaxis=dict(
            title="Player 1: Content Sharer Strategy",
            color=THEME["subtext_color"],
            autorange="reversed",
        ),
        annotations=annotations,
        margin=dict(l=60, r=40, t=60, b=60),
    )
    return fig


def create_strategic_best_response_chart(
    matrix: PayoffMatrix,
    analysis: EquilibriumAnalysisResult,
) -> go.Figure:
    """
    Graph E: Strategic reaction correspondence diagram in probability space [0, 1] x [0, 1].

    p = P(Sharer chooses S) on x-axis [0, 1].
    q = P(Platform chooses W) on y-axis [0, 1].

    - Sharer's best response correspondence p*(q) plotted as a function of q.
    - Platform's best response correspondence q*(p) plotted as a function of p.
    - Intersections represent pure or mixed Nash equilibria.
    """
    fig = go.Figure()

    # Indifference points
    mixed = analysis.mixed_equilibrium
    q_star = mixed.q_star
    p_star = mixed.p_star

    # 1. Plot Sharer Best Response p*(q):
    # For a given q = P(Platform plays W):
    # E[u1(S)] = q * u1(S,W) + (1-q) * u1(S,M)
    # E[u1(N)] = q * u1(N,W) + (1-q) * u1(N,M)
    # diff1(q) = E[u1(S)] - E[u1(N)]
    u1_SW, _ = matrix.get_payoff("S", "W")
    u1_SM, _ = matrix.get_payoff("S", "M")
    u1_NW, _ = matrix.get_payoff("N", "W")
    u1_NM, _ = matrix.get_payoff("N", "M")

    q_grid = np.linspace(0.0, 1.0, 300)
    p_br_values = []
    for q_val in q_grid:
        eu_S = q_val * u1_SW + (1.0 - q_val) * u1_SM
        eu_N = q_val * u1_NW + (1.0 - q_val) * u1_NM
        if np.isclose(eu_S, eu_N):
            p_br_values.append(0.5)  # Any p in [0, 1] is best response; show center
        elif eu_S > eu_N:
            p_br_values.append(1.0)  # S is best response -> p=1
        else:
            p_br_values.append(0.0)  # N is best response -> p=0

    fig.add_trace(
        go.Scatter(
            x=p_br_values,
            y=q_grid,
            mode="lines",
            name="Sharer Best Response p*(q)",
            line=dict(color="#38BDF8", width=3),
            hovertemplate="q (P_Platform_W): %{y:.2f}<br>Sharer BR p*: %{x:.2f}<extra></extra>",
        )
    )

    # 2. Plot Platform Best Response q*(p):
    # For a given p = P(Sharer plays S):
    # E[u2(W)] = p * u2(S,W) + (1-p) * u2(N,W)
    # E[u2(M)] = p * u2(S,M) + (1-p) * u2(N,M)
    _, u2_SW = matrix.get_payoff("S", "W")
    _, u2_SM = matrix.get_payoff("S", "M")
    _, u2_NW = matrix.get_payoff("N", "W")
    _, u2_NM = matrix.get_payoff("N", "M")

    p_grid = np.linspace(0.0, 1.0, 300)
    q_br_values = []
    for p_val in p_grid:
        eu_W = p_val * u2_SW + (1.0 - p_val) * u2_NW
        eu_M = p_val * u2_SM + (1.0 - p_val) * u2_NM
        if np.isclose(eu_W, eu_M):
            q_br_values.append(0.5)
        elif eu_W > eu_M:
            q_br_values.append(1.0)  # W is best response -> q=1
        else:
            q_br_values.append(0.0)  # M is best response -> q=0

    fig.add_trace(
        go.Scatter(
            x=p_grid,
            y=q_br_values,
            mode="lines",
            name="Platform Best Response q*(p)",
            line=dict(color="#F59E0B", width=3, dash="dot"),
            hovertemplate="p (P_Sharer_S): %{x:.2f}<br>Platform BR q*: %{y:.2f}<extra></extra>",
        )
    )

    # 3. Mark Pure Strategy Equilibria on the unit square
    for eq in analysis.pure_equilibria:
        p_coord = 1.0 if eq.sharer_strategy == "S" else 0.0
        q_coord = 1.0 if eq.platform_strategy == "W" else 0.0
        fig.add_trace(
            go.Scatter(
                x=[p_coord],
                y=[q_coord],
                mode="markers+text",
                marker=dict(symbol="star", size=16, color="#34D399", line=dict(color="#FFFFFF", width=1.5)),
                name=f"Pure Nash Eq: {eq.profile_label}",
                text=[f" Nash Eq {eq.profile_label}"],
                textposition="top right",
                textfont=dict(color="#34D399", size=12, family="Inter"),
                hovertemplate=f"<b>Pure Nash Equilibrium: {eq.profile_label}</b><br>Payoffs: ({eq.sharer_payoff:g}, {eq.platform_payoff:g})<extra></extra>",
            )
        )

    # 4. Mark Interior Mixed Strategy Equilibrium if present
    if mixed.exists_interior and mixed.p_star is not None and mixed.q_star is not None:
        fig.add_trace(
            go.Scatter(
                x=[mixed.p_star],
                y=[mixed.q_star],
                mode="markers+text",
                marker=dict(symbol="diamond", size=16, color="#A78BFA", line=dict(color="#FFFFFF", width=1.5)),
                name=f"Mixed Nash Eq (p*={mixed.p_star:.2f}, q*={mixed.q_star:.2f})",
                text=[f" Mixed Eq ({mixed.p_star:.2f}, {mixed.q_star:.2f})"],
                textposition="bottom right",
                textfont=dict(color="#A78BFA", size=12, family="Inter"),
                hovertemplate=(
                    f"<b>Interior Mixed Nash Equilibrium</b><br>"
                    f"p* = {mixed.p_star:.4f}<br>q* = {mixed.q_star:.4f}<br>"
                    f"Expected Payoffs: ({mixed.sharer_expected_payoff:.2f}, {mixed.platform_expected_payoff:.2f})<extra></extra>"
                ),
            )
        )

    fig.update_layout(
        title=dict(
            text="Strategic Analysis: Reaction Correspondences in Mixed Strategy Space",
            font=dict(color=THEME["text_color"], size=16),
        ),
        paper_bgcolor=THEME["paper_color"],
        plot_bgcolor=THEME["bg_color"],
        font=dict(color=THEME["text_color"], family="Inter, system-ui, sans-serif"),
        xaxis=dict(
            title="p = Probability(Content Sharer Chooses S [Spread])",
            gridcolor=THEME["grid_color"],
            color=THEME["subtext_color"],
            range=[-0.05, 1.05],
        ),
        yaxis=dict(
            title="q = Probability(Platform Chooses W [Weak Moderation])",
            gridcolor=THEME["grid_color"],
            color=THEME["subtext_color"],
            range=[-0.05, 1.05],
        ),
        legend=dict(
            bgcolor="rgba(15, 23, 42, 0.8)",
            bordercolor=THEME["grid_color"],
            borderwidth=1,
            font=dict(color=THEME["text_color"]),
        ),
        margin=dict(l=60, r=40, t=60, b=60),
    )
    return fig


def create_scenario_comparison_chart(
    scenarios: List[Dict],
    title: str = "Multi-Scenario Trajectory Comparison",
) -> go.Figure:
    """
    Combined chart for custom scenario comparisons.
    """
    fig = go.Figure()

    for idx, sc in enumerate(scenarios):
        color = THEME["palette"][idx % len(THEME["palette"])]
        steps = sc.get("trajectory_steps", [])
        exposure = sc.get("trajectory_exposure", [])
        name = sc.get("name", f"Scenario {idx + 1}")
        m_val = sc.get("moderation", 0.0)

        fig.add_trace(
            go.Scatter(
                x=steps,
                y=exposure,
                mode="lines",
                name=f"{name} (m={m_val:.2f})",
                line=dict(color=color, width=2.5),
                hovertemplate="<b>%{fullData.name}</b><br>Step %{x}: %{y:,.0f}<extra></extra>",
            )
        )

    fig.update_layout(
        title=dict(text=title, font=dict(color=THEME["text_color"], size=16)),
        paper_bgcolor=THEME["paper_color"],
        plot_bgcolor=THEME["bg_color"],
        font=dict(color=THEME["text_color"], family="Inter, system-ui, sans-serif"),
        xaxis=dict(
            title="Simulation Time Step",
            gridcolor=THEME["grid_color"],
            color=THEME["subtext_color"],
        ),
        yaxis=dict(
            title="Exposed Population",
            gridcolor=THEME["grid_color"],
            color=THEME["subtext_color"],
        ),
        legend=dict(
            bgcolor="rgba(15, 23, 42, 0.8)",
            bordercolor=THEME["grid_color"],
            borderwidth=1,
            font=dict(color=THEME["text_color"]),
        ),
        margin=dict(l=60, r=40, t=60, b=60),
    )
    return fig


def create_enhanced_diffusion_chart(
    base_res: PropagationResult,
    policy_res: PropagationResult,
    title: str = "Viral Diffusion Trajectory: Policy vs Baseline",
) -> go.Figure:
    """
    Enhanced Plotly diffusion chart featuring:
    - Shaded area between Baseline and Policy curves ("Misinformation Averted")
    - Annotations for Peak Outbreak and Inflection Point
    - Full SIR curves if model_type == 'sir'
    - Polished academic color palette
    """
    fig = go.Figure()

    # If SIR, plot Susceptible and Debunked for policy
    if policy_res.susceptible is not None and policy_res.debunked is not None:
        fig.add_trace(
            go.Scatter(
                x=policy_res.time_steps,
                y=policy_res.susceptible,
                mode="lines",
                name="Susceptible (S)",
                line=dict(color="#64748B", width=2, dash="dash"),
                hovertemplate="Step %{x}: %{y:,.0f} susceptible<extra></extra>",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=policy_res.time_steps,
                y=policy_res.debunked,
                mode="lines",
                name="Debunked / Recovered (R)",
                line=dict(color="#10B981", width=2.5),
                hovertemplate="Step %{x}: %{y:,.0f} debunked<extra></extra>",
            )
        )

    # Baseline line (Red)
    fig.add_trace(
        go.Scatter(
            x=base_res.time_steps,
            y=base_res.exposure,
            mode="lines",
            name=f"Baseline Unmoderated (m = 0.00)",
            line=dict(color="#EF4444", width=2.5, dash="dot"),
            hovertemplate="Baseline Step %{x}: %{y:,.0f} active<extra></extra>",
        )
    )

    # Policy line (Cyan) with shaded area filling to baseline
    fig.add_trace(
        go.Scatter(
            x=policy_res.time_steps,
            y=policy_res.exposure,
            mode="lines+markers",
            name=f"Active Moderation Policy (m = {policy_res.moderation_effectiveness:.2f})",
            line=dict(color="#38BDF8", width=3.5),
            marker=dict(size=4),
            fill="tonexty",  # Shade area between baseline and policy
            fillcolor="rgba(56, 189, 248, 0.12)",
            hovertemplate="Step %{x}: %{y:,.0f} active (%{customdata:.1%})<extra></extra>",
            customdata=policy_res.exposure / policy_res.population if policy_res.population > 0 else np.zeros_like(policy_res.exposure),
        )
    )

    # Peak annotation on policy curve
    if policy_res.peak_step is not None:
        p_step = policy_res.peak_step
        p_val = policy_res.exposure[p_step]
        fig.add_annotation(
            x=p_step,
            y=p_val,
            text=f"Peak: {p_val:,.0f}",
            showarrow=True,
            arrowhead=2,
            arrowcolor="#38BDF8",
            arrowsize=1,
            arrowwidth=1.5,
            ax=0,
            ay=-35,
            bgcolor="#0F172A",
            bordercolor="#38BDF8",
            borderwidth=1,
            font=dict(color="#38BDF8", size=11),
        )

    # Inflection point annotation
    if policy_res.inflection_step is not None and policy_res.inflection_value is not None:
        i_step = policy_res.inflection_step
        i_val = policy_res.inflection_value
        fig.add_annotation(
            x=i_step,
            y=i_val,
            text=f"Inflection: Step {i_step}",
            showarrow=True,
            arrowhead=2,
            arrowcolor="#F59E0B",
            arrowsize=1,
            arrowwidth=1.5,
            ax=-40,
            ay=25,
            bgcolor="#0F172A",
            bordercolor="#F59E0B",
            borderwidth=1,
            font=dict(color="#F59E0B", size=10),
        )

    # Population reference line
    fig.add_hline(
        y=policy_res.population,
        line_dash="dot",
        line_color="#475569",
        annotation_text=f"Population N = {policy_res.population:,}",
        annotation_position="bottom right",
        annotation_font=dict(color="#94A3B8", size=11),
    )

    fig.update_layout(
        title=dict(text=title, font=dict(color=THEME["text_color"], size=16)),
        paper_bgcolor=THEME["paper_color"],
        plot_bgcolor=THEME["bg_color"],
        font=dict(color=THEME["text_color"], family="Inter, system-ui, sans-serif"),
        xaxis=dict(title="Simulation Time Step (t)", gridcolor=THEME["grid_color"], color=THEME["subtext_color"]),
        yaxis=dict(title="Active Population Count", gridcolor=THEME["grid_color"], color=THEME["subtext_color"]),
        legend=dict(
            bgcolor="rgba(15, 23, 42, 0.8)",
            bordercolor=THEME["grid_color"],
            borderwidth=1,
            font=dict(color=THEME["text_color"]),
        ),
        margin=dict(l=60, r=40, t=60, b=60),
        height=420,
    )
    return fig


def create_network_graph_figure(
    graph,
    pos: Dict[int, Tuple[float, float]],
    node_states: Dict[int, int],
    step: int = 0,
) -> go.Figure:
    """
    Render 2D interactive network scatter with nodes colored by diffusion status:
    - Slate: Susceptible
    - Red: Active Fake News Spreader
    - Sky Blue: Moderated / Quarantined
    """
    edge_x = []
    edge_y = []
    for edge in graph.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        line=dict(width=1, color="rgba(71, 85, 105, 0.45)"),
        hoverinfo="none",
        mode="lines",
    )

    node_x = []
    node_y = []
    node_colors = []
    node_texts = []

    state_colors = {
        0: "#64748B",  # Susceptible
        1: "#EF4444",  # Exposed Spreader
        2: "#38BDF8",  # Moderated / Quarantined
    }
    state_names = {
        0: "Susceptible (Not Exposed)",
        1: "Active Fake News Spreader",
        2: "Moderated / Quarantined",
    }

    for node in graph.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        st_val = node_states.get(node, 0)
        node_colors.append(state_colors.get(st_val, "#64748B"))
        node_texts.append(f"Node #{node}<br>Status: <b>{state_names.get(st_val, 'Unknown')}</b>")

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers",
        hoverinfo="text",
        text=node_texts,
        marker=dict(
            size=14,
            color=node_colors,
            line=dict(width=1.5, color="#0B1120"),
        ),
    )

    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(
        title=dict(
            text=f"Network Peer-to-Peer Transmission Snapshot (Step {step})",
            font=dict(color=THEME["text_color"], size=15),
        ),
        paper_bgcolor=THEME["paper_color"],
        plot_bgcolor=THEME["bg_color"],
        showlegend=False,
        hovermode="closest",
        margin=dict(b=20, l=20, r=20, t=50),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        height=400,
    )
    return fig


def create_tipping_point_figure(
    m_grid: np.ndarray,
    sharer_u_S: np.ndarray,
    sharer_u_N: np.ndarray,
    tipping_m: Optional[float],
    current_m: float,
) -> go.Figure:
    """
    Plot Sharer payoff under Spread vs Compliance across m in [0, 1].
    Highlights the tipping threshold m* where compliance becomes the best response.
    """
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=m_grid,
            y=sharer_u_S,
            mode="lines",
            name="Sharer Payoff from Spreading: u(S, M)",
            line=dict(color="#EF4444", width=3),
            hovertemplate="m: %{x:.2f}<br>u(S): %{y:.2f}<extra></extra>",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=m_grid,
            y=sharer_u_N,
            mode="lines",
            name="Sharer Payoff from Compliance: u(N, M)",
            line=dict(color="#10B981", width=3, dash="dash"),
            hovertemplate="m: %{x:.2f}<br>u(N): %{y:.2f}<extra></extra>",
        )
    )

    # Mark tipping point
    if tipping_m is not None:
        fig.add_vline(
            x=tipping_m,
            line_dash="dot",
            line_color="#F59E0B",
            line_width=2,
            annotation_text=f"Tipping Point m* = {tipping_m:.2f}",
            annotation_position="top left",
            annotation_font=dict(color="#F59E0B", size=12),
        )

    # Mark current slider m
    fig.add_vline(
        x=current_m,
        line_color="#38BDF8",
        line_width=2,
        annotation_text=f"Current Policy m = {current_m:.2f}",
        annotation_position="bottom right",
        annotation_font=dict(color="#38BDF8", size=11),
    )

    fig.update_layout(
        title=dict(
            text="Tipping Point Analysis: Sharer Payoffs vs Moderation Intensity (m)",
            font=dict(color=THEME["text_color"], size=16),
        ),
        paper_bgcolor=THEME["paper_color"],
        plot_bgcolor=THEME["bg_color"],
        font=dict(color=THEME["text_color"], family="Inter, system-ui, sans-serif"),
        xaxis=dict(title="Moderation Intensity (m)", gridcolor=THEME["grid_color"], color=THEME["subtext_color"], range=[0, 1]),
        yaxis=dict(title="Sharer Expected Payoff", gridcolor=THEME["grid_color"], color=THEME["subtext_color"]),
        legend=dict(
            bgcolor="rgba(15, 23, 42, 0.8)",
            bordercolor=THEME["grid_color"],
            borderwidth=1,
            font=dict(color=THEME["text_color"]),
        ),
        margin=dict(l=60, r=40, t=60, b=60),
        height=380,
    )
    return fig


def create_sensitivity_heatmap_figure(
    beta_vals: np.ndarray,
    m_vals: np.ndarray,
    z_exposure_pct: np.ndarray,
    current_beta: float,
    current_m: float,
) -> go.Figure:
    """
    2D Contour Heatmap of Final Exposure across beta x m space.
    """
    fig = go.Figure(
        data=go.Contour(
            z=z_exposure_pct,
            x=m_vals,
            y=beta_vals,
            colorscale="Viridis",
            colorbar=dict(
                title=dict(text="Final Exposure %", font=dict(color="#F8FAFC")),
                tickfont=dict(color="#94A3B8"),
            ),
            contours=dict(showlabels=True, labelfont=dict(color="#FFFFFF", size=10)),
            hovertemplate="Moderation m: %{x:.2f}<br>Beta: %{y:.2f}<br>Final Exposure: %{z:.1f}%<extra></extra>",
        )
    )

    # Highlight current operating point
    fig.add_trace(
        go.Scatter(
            x=[current_m],
            y=[current_beta],
            mode="markers+text",
            marker=dict(symbol="star", size=16, color="#EF4444", line=dict(color="#FFFFFF", width=2)),
            name="Current Operating Point",
            text=[" Current Policy"],
            textposition="top right",
            textfont=dict(color="#EF4444", size=12),
            hovertemplate=f"Current Policy: m = {current_m:.2f}, beta = {current_beta:.2f}<extra></extra>",
        )
    )

    fig.update_layout(
        title=dict(
            text="Sensitivity Landscape: Final Exposure over Sharing Propensity (β) × Moderation (m)",
            font=dict(color=THEME["text_color"], size=16),
        ),
        paper_bgcolor=THEME["paper_color"],
        plot_bgcolor=THEME["bg_color"],
        font=dict(color=THEME["text_color"], family="Inter, system-ui, sans-serif"),
        xaxis=dict(title="Platform Moderation Intensity (m)", gridcolor=THEME["grid_color"], color=THEME["subtext_color"]),
        yaxis=dict(title="Sharing Propensity (β)", gridcolor=THEME["grid_color"], color=THEME["subtext_color"]),
        margin=dict(l=60, r=40, t=60, b=60),
        height=400,
    )
    return fig


def create_replicator_dynamics_figure(
    generations: np.ndarray,
    spreader_fraction: np.ndarray,
    compliant_fraction: np.ndarray,
    ess_type: str,
) -> go.Figure:
    """
    Plot evolutionary replicator dynamics trajectory across generations.
    """
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=generations,
            y=spreader_fraction,
            mode="lines",
            name="Spreader Fraction: x(t)",
            line=dict(color="#EF4444", width=3),
            hovertemplate="Generation %{x}: %{y:.1%} spreaders<extra></extra>",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=generations,
            y=compliant_fraction,
            mode="lines",
            name="Compliant Fraction: 1 - x(t)",
            line=dict(color="#10B981", width=3, dash="dash"),
            hovertemplate="Generation %{x}: %{y:.1%} compliant<extra></extra>",
        )
    )

    fig.update_layout(
        title=dict(
            text=f"Evolutionary Replicator Dynamics: {ess_type}",
            font=dict(color=THEME["text_color"], size=16),
        ),
        paper_bgcolor=THEME["paper_color"],
        plot_bgcolor=THEME["bg_color"],
        font=dict(color=THEME["text_color"], family="Inter, system-ui, sans-serif"),
        xaxis=dict(title="Generations / Iterations", gridcolor=THEME["grid_color"], color=THEME["subtext_color"]),
        yaxis=dict(title="Population Share [0, 1]", gridcolor=THEME["grid_color"], color=THEME["subtext_color"], range=[-0.02, 1.02]),
        legend=dict(
            bgcolor="rgba(15, 23, 42, 0.8)",
            bordercolor=THEME["grid_color"],
            borderwidth=1,
            font=dict(color=THEME["text_color"]),
        ),
        margin=dict(l=60, r=40, t=60, b=60),
        height=380,
    )
    return fig

