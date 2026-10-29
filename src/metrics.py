"""
Metrics and Reporting Utilities for Simulation and Game Analysis.
"""

from typing import Dict, List, Optional
import pandas as pd
import numpy as np

from src.propagation import PropagationResult


def safe_percentage_reduction(baseline: float, current: float) -> Optional[float]:
    """
    Safely calculate percentage reduction: (baseline - current) / baseline * 100.
    Returns None if baseline <= 0 and current > 0.
    Returns 0.0 if both baseline and current are 0.
    """
    if baseline > 0:
        return ((baseline - current) / baseline) * 100.0
    elif np.isclose(baseline, 0.0) and np.isclose(current, 0.0):
        return 0.0
    return None


def generate_scenario_comparison_table(
    scenario_results: Dict[str, PropagationResult],
    baseline_key: str = "No moderation",
) -> pd.DataFrame:
    """
    Generate a formatted summary comparison table for moderation scenarios.
    """
    baseline = scenario_results.get(baseline_key)
    rows = []

    for name, res in scenario_results.items():
        time_to_25 = res.get_time_to_threshold(0.25)
        time_to_50 = res.get_time_to_threshold(0.50)
        time_to_75 = res.get_time_to_threshold(0.75)

        if baseline is not None:
            red = res.compute_reduction(baseline)
            final_red = red["final_reduction_pct"]
            peak_red = red["peak_reduction_pct"]
        else:
            final_red = 0.0
            peak_red = 0.0

        rows.append({
            "Scenario": name,
            "Moderation (m)": f"{res.moderation_effectiveness:.2f}",
            "Final Exposure": f"{res.final_exposure:,.0f}",
            "Final Exposure (%)": f"{(res.final_exposure / res.population) * 100:.1f}%",
            "Peak Exposure": f"{res.peak_exposure:,.0f}",
            "Time to 25% (t)": str(time_to_25) if time_to_25 is not None else "Not reached",
            "Time to 50% (t)": str(time_to_50) if time_to_50 is not None else "Not reached",
            "Time to 75% (t)": str(time_to_75) if time_to_75 is not None else "Not reached",
            "Final Reduction vs Base": f"{final_red:.1f}%" if final_red is not None else "N/A",
            "Peak Reduction vs Base": f"{peak_red:.1f}%" if peak_red is not None else "N/A",
        })

    return pd.DataFrame(rows)


def build_scenario_comparison_export(
    scenario_records: List[Dict],
) -> pd.DataFrame:
    """
    Build a comprehensive exportable DataFrame from a list of user-defined scenario dictionaries.
    """
    return pd.DataFrame(scenario_records)
