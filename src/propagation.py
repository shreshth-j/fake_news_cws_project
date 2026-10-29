"""
Discrete-time Fake News Exposure Propagation Model.

Mathematical Formulation:
    I_{t+1} = I_t + beta * (1 - m) * I_t * (1 - I_t / N)

Where:
    N     : Total simulated population (N > 0).
    I_t   : Number of people exposed at time step t.
    beta  : Baseline transmission or sharing rate (beta >= 0).
    m     : Moderation effectiveness (0 <= m <= 1).
    T     : Number of simulation time steps (T >= 0).
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd


@dataclass
class SimulationParameters:
    """Parameters for the discrete-time fake news propagation model."""
    population: int = 10000
    initial_exposed: float = 100.0
    beta: float = 0.35
    moderation_effectiveness: float = 0.25
    time_steps: int = 30
    debunking_rate: float = 0.05
    model_type: str = "logistic"  # "logistic" or "sir"

    def validate(self) -> None:
        """Validate parameter ranges and types."""
        if not isinstance(self.population, (int, np.integer)) or self.population <= 0:
            raise ValueError(f"Population N must be a positive integer, got {self.population}")
        if self.initial_exposed < 0:
            raise ValueError(f"Initial exposed population I_0 cannot be negative, got {self.initial_exposed}")
        if self.initial_exposed > self.population:
            raise ValueError(f"Initial exposed population ({self.initial_exposed}) cannot exceed population ({self.population})")
        if self.beta < 0:
            raise ValueError(f"Baseline transmission rate beta must be non-negative, got {self.beta}")
        if not (0.0 <= self.moderation_effectiveness <= 1.0):
            raise ValueError(f"Moderation effectiveness m must be bounded in [0, 1], got {self.moderation_effectiveness}")
        if not isinstance(self.time_steps, (int, np.integer)) or self.time_steps < 0:
            raise ValueError(f"Time steps T must be a non-negative integer, got {self.time_steps}")
        if not (0.0 <= self.debunking_rate <= 1.0):
            raise ValueError(f"Debunking rate must be in [0, 1], got {self.debunking_rate}")
        if self.model_type not in ("logistic", "sir"):
            raise ValueError(f"Unknown model_type '{self.model_type}'. Expected 'logistic' or 'sir'.")


@dataclass
class PropagationResult:
    """Container for simulation trajectory and computed metrics."""
    time_steps: np.ndarray
    exposure: np.ndarray
    population: int
    final_exposure: float
    peak_exposure: float
    moderation_effectiveness: float
    beta: float
    initial_exposed: float
    susceptible: Optional[np.ndarray] = None
    debunked: Optional[np.ndarray] = None
    inflection_step: Optional[int] = None
    inflection_value: Optional[float] = None
    peak_step: Optional[int] = None

    def get_time_to_threshold(self, fraction: float) -> Optional[int]:
        """
        Return the first time step where exposure reaches or exceeds fraction * population.
        Returns None if threshold is never reached within the simulation horizon.
        """
        threshold = fraction * self.population
        indices = np.where(self.exposure >= threshold)[0]
        if len(indices) > 0:
            return int(self.time_steps[indices[0]])
        return None

    def compute_reduction(self, baseline: "PropagationResult") -> Dict[str, Optional[float]]:
        """
        Compute percentage reduction in final and peak exposure relative to a baseline.
        Returns None for percentages if baseline value is zero.
        """
        if baseline.final_exposure > 0:
            final_reduction = ((baseline.final_exposure - self.final_exposure) / baseline.final_exposure) * 100.0
        else:
            final_reduction = 0.0 if self.final_exposure == 0 else None

        if baseline.peak_exposure > 0:
            peak_reduction = ((baseline.peak_exposure - self.peak_exposure) / baseline.peak_exposure) * 100.0
        else:
            peak_reduction = 0.0 if self.peak_exposure == 0 else None

        return {
            "final_reduction_pct": final_reduction,
            "peak_reduction_pct": peak_reduction,
        }

    def to_dataframe(self) -> pd.DataFrame:
        """Convert trajectory into a pandas DataFrame."""
        df_dict = {
            "step": self.time_steps,
            "exposure": self.exposure,
            "exposure_fraction": self.exposure / self.population if self.population > 0 else 0.0,
        }
        if self.susceptible is not None:
            df_dict["susceptible"] = self.susceptible
        if self.debunked is not None:
            df_dict["debunked"] = self.debunked
        return pd.DataFrame(df_dict)


def run_propagation_simulation(params: SimulationParameters) -> PropagationResult:
    """
    Run the deterministic discrete-time exposure propagation model.

    Models:
    - Logistic:
        I_{t+1} = I_t + beta * (1 - m) * I_t * (1 - I_t / N)
    - SIR (Susceptible - Infected/Sharing - Recovered/Debunked):
        S_{t+1} = S_t - beta * (1 - m) * S_t * I_t / N
        I_{t+1} = I_t + beta * (1 - m) * S_t * I_t / N - gamma * I_t
        R_{t+1} = R_t + gamma * I_t
    """
    params.validate()

    N = float(params.population)
    T = int(params.time_steps)
    beta = float(params.beta)
    m = float(params.moderation_effectiveness)
    gamma = float(params.debunking_rate)
    is_sir = params.model_type == "sir"

    time_steps = np.arange(T + 1, dtype=np.int64)

    if not is_sir:
        trajectory = np.zeros(T + 1, dtype=np.float64)
        trajectory[0] = float(params.initial_exposed)

        for t in range(T):
            current_I = trajectory[t]
            delta = beta * (1.0 - m) * current_I * (1.0 - (current_I / N))
            next_I = current_I + delta
            if not np.isfinite(next_I):
                next_I = N if delta > 0 else 0.0
            next_I = min(N, max(0.0, next_I))
            trajectory[t + 1] = next_I

        susceptible = None
        debunked = None
    else:
        # SIR model
        S_arr = np.zeros(T + 1, dtype=np.float64)
        I_arr = np.zeros(T + 1, dtype=np.float64)
        R_arr = np.zeros(T + 1, dtype=np.float64)

        I_arr[0] = min(N, float(params.initial_exposed))
        S_arr[0] = max(0.0, N - I_arr[0])
        R_arr[0] = 0.0

        for t in range(T):
            S_t = S_arr[t]
            I_t = I_arr[t]
            R_t = R_arr[t]

            new_infections = beta * (1.0 - m) * (S_t * I_t / N) if N > 0 else 0.0
            new_infections = min(S_t, max(0.0, new_infections))

            new_debunked = gamma * I_t
            new_debunked = min(I_t, max(0.0, new_debunked))

            S_next = max(0.0, S_t - new_infections)
            I_next = max(0.0, I_t + new_infections - new_debunked)
            R_next = min(N, R_t + new_debunked)

            S_arr[t + 1] = S_next
            I_arr[t + 1] = I_next
            R_arr[t + 1] = R_next

        trajectory = I_arr
        susceptible = S_arr
        debunked = R_arr

    final_exposure = float(trajectory[-1])
    peak_exposure = float(np.max(trajectory))
    peak_step = int(np.argmax(trajectory))

    # Compute inflection point (step with max positive first difference dI/dt)
    diffs = np.diff(trajectory)
    if len(diffs) > 0 and np.max(diffs) > 0:
        inflection_step = int(np.argmax(diffs))
        inflection_value = float(trajectory[inflection_step])
    else:
        inflection_step = None
        inflection_value = None

    return PropagationResult(
        time_steps=time_steps,
        exposure=trajectory,
        population=params.population,
        final_exposure=final_exposure,
        peak_exposure=peak_exposure,
        moderation_effectiveness=m,
        beta=beta,
        initial_exposed=params.initial_exposed,
        susceptible=susceptible,
        debunked=debunked,
        inflection_step=inflection_step,
        inflection_value=inflection_value,
        peak_step=peak_step,
    )


def simulate_moderation_scenarios(
    base_params: SimulationParameters,
    scenario_moderations: Optional[Dict[str, float]] = None,
) -> Dict[str, PropagationResult]:
    """
    Simulate standard or custom moderation scenarios.

    Default scenarios:
        - No moderation: m = 0.00
        - Weak moderation: m = 0.25
        - Moderate moderation: m = 0.55
        - Strong moderation: m = 0.85
    """
    if scenario_moderations is None:
        scenario_moderations = {
            "No moderation": 0.00,
            "Weak moderation": 0.25,
            "Moderate moderation": 0.55,
            "Strong moderation": 0.85,
        }

    results: Dict[str, PropagationResult] = {}
    for name, m_val in scenario_moderations.items():
        scenario_params = SimulationParameters(
            population=base_params.population,
            initial_exposed=base_params.initial_exposed,
            beta=base_params.beta,
            moderation_effectiveness=m_val,
            time_steps=base_params.time_steps,
        )
        results[name] = run_propagation_simulation(scenario_params)

    return results


def sweep_moderation_effectiveness(
    base_params: SimulationParameters,
    steps: int = 50,
) -> pd.DataFrame:
    """
    Compute final exposure and reduction across an effectiveness grid from 0 to 1.
    """
    m_values = np.linspace(0.0, 1.0, steps)
    # Baseline with m = 0
    baseline_params = SimulationParameters(
        population=base_params.population,
        initial_exposed=base_params.initial_exposed,
        beta=base_params.beta,
        moderation_effectiveness=0.0,
        time_steps=base_params.time_steps,
    )
    baseline_res = run_propagation_simulation(baseline_params)

    records = []
    for m in m_values:
        p = SimulationParameters(
            population=base_params.population,
            initial_exposed=base_params.initial_exposed,
            beta=base_params.beta,
            moderation_effectiveness=float(m),
            time_steps=base_params.time_steps,
        )
        res = run_propagation_simulation(p)
        red = res.compute_reduction(baseline_res)
        records.append({
            "moderation_effectiveness": float(m),
            "final_exposure": res.final_exposure,
            "final_exposure_pct": (res.final_exposure / res.population) * 100.0,
            "peak_exposure": res.peak_exposure,
            "final_reduction_pct": red["final_reduction_pct"] if red["final_reduction_pct"] is not None else 0.0,
            "peak_reduction_pct": red["peak_reduction_pct"] if red["peak_reduction_pct"] is not None else 0.0,
        })

    return pd.DataFrame(records)
