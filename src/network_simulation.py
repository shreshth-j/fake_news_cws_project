"""
Network-Based Fake News Propagation Model.

Simulates peer-to-peer transmission of misinformation over explicit network topologies:
1. Preferential Attachment (Scale-free Barabási–Albert graph)
2. Random Graph (Erdős–Rényi graph)

Node States:
    0: SUSCEPTIBLE (Not exposed)
    1: EXPOSED (Active fake news sharer)
    2: MODERATED (Detected and blocked/quarantined)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
import networkx as nx
import numpy as np
import plotly.graph_objects as go

# Node state constants
STATE_SUSCEPTIBLE = 0
STATE_EXPOSED = 1
STATE_MODERATED = 2

STATE_NAMES = {
    STATE_SUSCEPTIBLE: "Susceptible (Not Exposed)",
    STATE_EXPOSED: "Exposed (Active Sharer)",
    STATE_MODERATED: "Moderated (Blocked / Quarantined)",
}

STATE_COLORS = {
    STATE_SUSCEPTIBLE: "#64748B",  # Slate gray
    STATE_EXPOSED: "#EF4444",      # Vibrant coral red
    STATE_MODERATED: "#38BDF8",    # Sky blue
}


def generate_synthetic_network(
    network_type: str = "preferential_attachment",
    n_nodes: int = 60,
    seed: Optional[int] = 42,
) -> Tuple[nx.Graph, Dict[int, Tuple[float, float]]]:
    """
    Generate a NetworkX graph and precompute 2D spring layout positions.
    """
    if network_type == "preferential_attachment":
        m_edges = min(2, max(1, n_nodes - 1))
        G = nx.barabasi_albert_graph(n=n_nodes, m=m_edges, seed=seed)
    elif network_type == "random":
        p = min(1.0, max(0.04, 3.2 / max(n_nodes, 1)))
        G = nx.erdos_renyi_graph(n=n_nodes, p=p, seed=seed)
    else:
        raise ValueError(f"Unknown network_type '{network_type}'. Expected 'preferential_attachment' or 'random'.")

    # Compute spring layout
    pos = nx.spring_layout(G, seed=seed if seed is not None else 42, k=0.35, iterations=50)
    return G, pos


@dataclass
class NetworkStepRecord:
    """Snapshot of network propagation state at a specific simulation step."""
    step: int
    node_states: Dict[int, int]
    cumulative_exposed: int
    newly_exposed: int
    active_sharers: int
    moderated_count: int
    susceptible_count: int


@dataclass
class NetworkSimulationResult:
    """Complete network propagation history."""
    graph: nx.Graph
    pos: Dict[int, Tuple[float, float]]
    steps: List[NetworkStepRecord]
    network_type: str
    total_nodes: int
    transmission_rate: float
    moderation_effectiveness: float
    seed: Optional[int]


def run_full_network_simulation(
    graph: nx.Graph,
    pos: Dict[int, Tuple[float, float]],
    network_type: str = "preferential_attachment",
    n_initial_exposed: int = 3,
    transmission_rate: float = 0.40,
    moderation_effectiveness: float = 0.30,
    max_steps: int = 15,
    seed: Optional[int] = 42,
) -> NetworkSimulationResult:
    """
    Run complete network diffusion simulation from step 0 to max_steps.
    """
    rng = np.random.default_rng(seed)
    n_nodes = graph.number_of_nodes()

    # Step 0: Initialize states
    node_states: Dict[int, int] = {i: STATE_SUSCEPTIBLE for i in range(n_nodes)}

    # Pick initial seeds (highest degree or random)
    nodes_by_degree = sorted(graph.degree, key=lambda x: x[1], reverse=True)
    n_seeds = min(n_initial_exposed, n_nodes)
    seed_nodes = [node for node, _ in nodes_by_degree[:n_seeds]] if n_seeds > 0 else []

    for s_node in seed_nodes:
        node_states[s_node] = STATE_EXPOSED

    history: List[NetworkStepRecord] = []
    initial_exposed_count = len(seed_nodes)

    record_0 = NetworkStepRecord(
        step=0,
        node_states=dict(node_states),
        cumulative_exposed=initial_exposed_count,
        newly_exposed=initial_exposed_count,
        active_sharers=initial_exposed_count,
        moderated_count=0,
        susceptible_count=n_nodes - initial_exposed_count,
    )
    history.append(record_0)

    # Effective transmission probability across an edge
    p_trans = float(np.clip(transmission_rate * (1.0 - moderation_effectiveness), 0.0, 1.0))
    p_mod = float(np.clip(moderation_effectiveness, 0.0, 1.0))

    for step in range(1, max_steps + 1):
        prev_states = history[-1].node_states
        new_states = dict(prev_states)
        newly_exposed_nodes: Set[int] = set()

        # Find active sharers
        active_sharers = [n for n, st in prev_states.items() if st == STATE_EXPOSED]

        # 1. Active sharers attempt to infect susceptible neighbors
        for sharer in active_sharers:
            for neighbor in graph.neighbors(sharer):
                if prev_states[neighbor] == STATE_SUSCEPTIBLE and neighbor not in newly_exposed_nodes:
                    if rng.random() < p_trans:
                        newly_exposed_nodes.add(neighbor)

        for n_exp in newly_exposed_nodes:
            new_states[n_exp] = STATE_EXPOSED

        # 2. Platform moderation detection on active sharers
        for sharer in active_sharers:
            if rng.random() < p_mod:
                new_states[sharer] = STATE_MODERATED

        # Calculate step metrics
        exposed_total = sum(1 for st in new_states.values() if st in (STATE_EXPOSED, STATE_MODERATED))
        active_count = sum(1 for st in new_states.values() if st == STATE_EXPOSED)
        mod_count = sum(1 for st in new_states.values() if st == STATE_MODERATED)
        susc_count = sum(1 for st in new_states.values() if st == STATE_SUSCEPTIBLE)

        step_record = NetworkStepRecord(
            step=step,
            node_states=new_states,
            cumulative_exposed=exposed_total,
            newly_exposed=len(newly_exposed_nodes),
            active_sharers=active_count,
            moderated_count=mod_count,
            susceptible_count=susc_count,
        )
        history.append(step_record)

    return NetworkSimulationResult(
        graph=graph,
        pos=pos,
        steps=history,
        network_type=network_type,
        total_nodes=n_nodes,
        transmission_rate=transmission_rate,
        moderation_effectiveness=moderation_effectiveness,
        seed=seed,
    )


def create_network_plotly_figure(
    graph: nx.Graph,
    pos: Dict[int, Tuple[float, float]],
    node_states: Dict[int, int],
    step_num: int = 0,
    title: Optional[str] = None,
) -> go.Figure:
    """
    Render an interactive Plotly 2D network diagram showing nodes, edges, and state color codes.
    """
    # 1. Extract edge coordinates
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
        line=dict(width=1.0, color="#334155"),
        hoverinfo="none",
        mode="lines",
        showlegend=False,
    )

    # 2. Extract node coordinates and attributes by state
    fig = go.Figure()
    fig.add_trace(edge_trace)

    for state_val, state_label in STATE_NAMES.items():
        state_nodes = [node for node, st in node_states.items() if st == state_val]
        if not state_nodes:
            continue

        node_x = [pos[node][0] for node in state_nodes]
        node_y = [pos[node][1] for node in state_nodes]
        degrees = [graph.degree[node] for node in state_nodes]
        hover_texts = [
            f"<b>Node {node}</b><br>State: {state_label}<br>Connections (Degree): {deg}"
            for node, deg in zip(state_nodes, degrees)
        ]

        marker_size = 14 if state_val == STATE_EXPOSED else (12 if state_val == STATE_MODERATED else 10)

        fig.add_trace(
            go.Scatter(
                x=node_x,
                y=node_y,
                mode="markers",
                name=f"{state_label} ({len(state_nodes)})",
                marker=dict(
                    color=STATE_COLORS[state_val],
                    size=marker_size,
                    line=dict(color="#0F172A", width=1.5),
                ),
                text=hover_texts,
                hoverinfo="text",
            )
        )

    chart_title = title or f"Network Misinformation State at Time Step t = {step_num}"

    fig.update_layout(
        title=dict(text=chart_title, font=dict(color="#F8FAFC", size=15)),
        paper_bgcolor="#0F172A",
        plot_bgcolor="#0B1120",
        font=dict(color="#F8FAFC", family="Inter, system-ui, sans-serif"),
        showlegend=True,
        legend=dict(
            bgcolor="rgba(15, 23, 42, 0.85)",
            bordercolor="#334155",
            borderwidth=1,
            font=dict(color="#F8FAFC", size=11),
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        margin=dict(l=20, r=20, t=50, b=20),
        height=520,
    )
    return fig


def create_network_spread_curves_chart(
    sim_result: NetworkSimulationResult,
    title: str = "Network Propagation Curves Over Time",
) -> go.Figure:
    """
    Plot cumulative exposure and newly exposed counts across simulation steps.
    """
    steps = [rec.step for rec in sim_result.steps]
    cumulative = [rec.cumulative_exposed for rec in sim_result.steps]
    active = [rec.active_sharers for rec in sim_result.steps]
    moderated = [rec.moderated_count for rec in sim_result.steps]
    newly = [rec.newly_exposed for rec in sim_result.steps]

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=steps,
            y=cumulative,
            mode="lines+markers",
            name="Cumulative Exposed",
            line=dict(color="#EF4444", width=3),
            marker=dict(size=6),
            hovertemplate="Step %{x}: %{y} total exposed<extra></extra>",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=steps,
            y=active,
            mode="lines+markers",
            name="Active Sharers (Infectious)",
            line=dict(color="#F59E0B", width=2, dash="dash"),
            marker=dict(size=5),
            hovertemplate="Step %{x}: %{y} active sharers<extra></extra>",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=steps,
            y=moderated,
            mode="lines+markers",
            name="Moderated / Quarantined",
            line=dict(color="#38BDF8", width=2),
            marker=dict(size=5),
            hovertemplate="Step %{x}: %{y} moderated<extra></extra>",
        )
    )

    fig.add_trace(
        go.Bar(
            x=steps,
            y=newly,
            name="Newly Exposed / Step",
            marker=dict(color="rgba(239, 68, 68, 0.4)"),
            hovertemplate="Step %{x}: %{y} newly exposed<extra></extra>",
            yaxis="y2",
        )
    )

    fig.update_layout(
        title=dict(text=title, font=dict(color="#F8FAFC", size=15)),
        paper_bgcolor="#0F172A",
        plot_bgcolor="#0B1120",
        font=dict(color="#F8FAFC", family="Inter, system-ui, sans-serif"),
        xaxis=dict(
            title="Time Step (t)",
            gridcolor="#334155",
            color="#94A3B8",
            dtick=1,
        ),
        yaxis=dict(
            title="Total Nodes",
            gridcolor="#334155",
            color="#F8FAFC",
            range=[0, sim_result.total_nodes * 1.05],
        ),
        yaxis2=dict(
            title="New Nodes / Step",
            color="#F87171",
            overlaying="y",
            side="right",
            showgrid=False,
            range=[0, max(max(newly) * 1.5, 5)],
        ),
        legend=dict(
            bgcolor="rgba(15, 23, 42, 0.8)",
            bordercolor="#334155",
            borderwidth=1,
            font=dict(color="#F8FAFC"),
        ),
        margin=dict(l=50, r=50, t=50, b=50),
        height=380,
    )
    return fig
