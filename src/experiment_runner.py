"""
Experiment Runner and Preset Configurations.

Manages one-click experimental scenarios, delayed intervention models,
sharing rate sweeps, and saved experiment records.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from src.propagation import (
    SimulationParameters,
    PropagationResult,
    run_propagation_simulation,
)
from src.network_simulation import (
    generate_synthetic_network,
    run_full_network_simulation,
    NetworkSimulationResult,
)


def run_delayed_moderation_simulation(
    params: SimulationParameters,
    delay_step: int = 8,
    m_intervention: float = 0.75,
) -> PropagationResult:
    """
    Simulate delayed moderation:
    - For t < delay_step: moderation effectiveness m = 0.0 (unmitigated spread).
    - For t >= delay_step: platform activates moderation with m = m_intervention.
    """
    params.validate()
    N = float(params.population)
    T = int(params.time_steps)
    beta = float(params.beta)

    trajectory = np.zeros(T + 1, dtype=np.float64)
    trajectory[0] = float(params.initial_exposed)

    for t in range(T):
        current_I = trajectory[t]
        current_m = 0.0 if t < delay_step else float(m_intervention)
        delta = beta * (1.0 - current_m) * current_I * (1.0 - (current_I / N))
        next_I = current_I + delta

        if not np.isfinite(next_I):
            next_I = N if delta > 0 else 0.0
        next_I = min(N, max(0.0, next_I))
        trajectory[t + 1] = next_I

    time_steps = np.arange(T + 1, dtype=np.int64)
    final_exposure = float(trajectory[-1])
    peak_exposure = float(np.max(trajectory))

    return PropagationResult(
        time_steps=time_steps,
        exposure=trajectory,
        population=params.population,
        final_exposure=final_exposure,
        peak_exposure=peak_exposure,
        moderation_effectiveness=m_intervention,
        beta=beta,
        initial_exposed=params.initial_exposed,
    )


def sweep_sharing_rate(
    population: int = 10000,
    initial_exposed: float = 100.0,
    moderation_effectiveness: float = 0.35,
    time_steps: int = 30,
    steps: int = 25,
) -> pd.DataFrame:
    """
    Sweep transmission rate beta across [0.05, 1.20] for a fixed moderation policy.
    """
    beta_values = np.linspace(0.05, 1.20, steps)
    records = []

    for b in beta_values:
        p = SimulationParameters(
            population=population,
            initial_exposed=initial_exposed,
            beta=float(b),
            moderation_effectiveness=moderation_effectiveness,
            time_steps=time_steps,
        )
        res = run_propagation_simulation(p)
        records.append({
            "beta": float(b),
            "final_exposure": res.final_exposure,
            "final_exposure_pct": (res.final_exposure / population) * 100.0,
            "peak_exposure": res.peak_exposure,
        })

    return pd.DataFrame(records)


def create_delayed_intervention_chart(
    early_res: PropagationResult,
    late_res: PropagationResult,
    unmoderated_res: PropagationResult,
    delay_step: int,
) -> go.Figure:
    """
    Compare early vs late intervention against the unmoderated baseline.
    """
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=unmoderated_res.time_steps,
            y=unmoderated_res.exposure,
            mode="lines",
            name="No Moderation Baseline (m = 0)",
            line=dict(color="#EF4444", width=2.5, dash="dot"),
            hovertemplate="Step %{x}: %{y:,.0f} exposed<extra></extra>",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=late_res.time_steps,
            y=late_res.exposure,
            mode="lines+markers",
            name=f"Late Intervention (Delayed to t = {delay_step})",
            line=dict(color="#F59E0B", width=3),
            marker=dict(size=4),
            hovertemplate="Step %{x}: %{y:,.0f} exposed<extra></extra>",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=early_res.time_steps,
            y=early_res.exposure,
            mode="lines+markers",
            name="Early Intervention (Active from t = 0)",
            line=dict(color="#10B981", width=3),
            marker=dict(size=4),
            hovertemplate="Step %{x}: %{y:,.0f} exposed<extra></extra>",
        )
    )

    # Vertical line indicating intervention delay
    fig.add_vline(
        x=delay_step,
        line_width=1.5,
        line_dash="dash",
        line_color="#94A3B8",
        annotation_text=f"Intervention Starts (t = {delay_step})",
        annotation_position="top left",
        annotation_font=dict(color="#94A3B8", size=11),
    )

    fig.update_layout(
        title=dict(
            text=f"Early vs. Late Intervention Impact (Intervention at t = {delay_step})",
            font=dict(color="#F8FAFC", size=15),
        ),
        paper_bgcolor="#0F172A",
        plot_bgcolor="#0B1120",
        font=dict(color="#F8FAFC", family="Inter, system-ui, sans-serif"),
        xaxis=dict(title="Simulation Time Step (t)", gridcolor="#334155", color="#94A3B8"),
        yaxis=dict(title="Exposed Population (I_t)", gridcolor="#334155", color="#94A3B8"),
        legend=dict(
            bgcolor="rgba(15, 23, 42, 0.8)",
            bordercolor="#334155",
            borderwidth=1,
            font=dict(color="#F8FAFC"),
        ),
        margin=dict(l=50, r=40, t=50, b=50),
        height=420,
    )
    return fig


def create_sharing_rate_sweep_chart(sweep_df: pd.DataFrame) -> go.Figure:
    """
    Plot final exposure as a function of the sharing rate beta.
    """
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=sweep_df["beta"],
            y=sweep_df["final_exposure"],
            mode="lines+markers",
            name="Final Exposure",
            line=dict(color="#A78BFA", width=3),
            marker=dict(size=5),
            hovertemplate="Beta: %{x:.2f}<br>Final Exposure: %{y:,.0f}<extra></extra>",
        )
    )

    fig.update_layout(
        title=dict(
            text="Sharing Pressure Sensitivity (Final Exposure vs Transmission Rate β)",
            font=dict(color="#F8FAFC", size=15),
        ),
        paper_bgcolor="#0F172A",
        plot_bgcolor="#0B1120",
        font=dict(color="#F8FAFC", family="Inter, system-ui, sans-serif"),
        xaxis=dict(title="Baseline Transmission Rate (β)", gridcolor="#334155", color="#94A3B8"),
        yaxis=dict(title="Final Exposed Individuals", gridcolor="#334155", color="#94A3B8"),
        margin=dict(l=50, r=40, t=50, b=50),
        height=380,
    )
    return fig


def package_experiment_record(
    name: str,
    model_type: str,
    population: int,
    initial_exposed: float,
    beta: float,
    moderation: float,
    time_steps: int,
    final_exposure: float,
    peak_exposure: float,
    trajectory_steps: List[int],
    trajectory_exposure: List[float],
    reduction_pct: Optional[float] = None,
    notes: str = "",
) -> Dict[str, Any]:
    """
    Format and bundle an experiment into a clean serializable record for saved experiment history.
    """
    return {
        "id": f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
        "name": name,
        "model_type": model_type,
        "population": int(population),
        "initial_exposed": float(initial_exposed),
        "beta": float(beta),
        "moderation": float(moderation),
        "time_steps": int(time_steps),
        "final_exposure": float(final_exposure),
        "peak_exposure": float(peak_exposure),
        "final_exposure_pct": (float(final_exposure) / float(population)) * 100.0 if population > 0 else 0.0,
        "reduction_pct": reduction_pct if reduction_pct is not None else 0.0,
        "trajectory_steps": trajectory_steps,
        "trajectory_exposure": trajectory_exposure,
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "notes": notes,
    }
