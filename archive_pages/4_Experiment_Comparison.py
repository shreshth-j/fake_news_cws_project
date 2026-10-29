"""
Page 4: Experiment Comparison
Multi-experiment comparison laboratory allowing users to overlay saved runs,
evaluate metrics, delete experiments, and export research telemetry to CSV.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from src.ui_common import apply_theme, init_session_state, render_sidebar_info
from src.experiment_runner import package_experiment_record
from src.propagation import SimulationParameters, run_propagation_simulation

st.set_page_config(
    page_title="Experiment Comparison | Fake News Model",
    page_icon="📁",
    layout="wide",
)

apply_theme()
init_session_state()
render_sidebar_info()

st.title("📁 Experiment Comparison Laboratory")
st.caption(
    "Compare and contrast saved experimental runs side-by-side. "
    "Overlay diffusion trajectories, benchmark peak exposure thresholds, and export data."
)

st.info(
    "💡 **Session Note:** Saved experiments persist in browser session state during this session. "
    "To preserve experiments permanently, use the CSV Export buttons below."
)

st.markdown("---")

# Saved Experiments Catalog
saved_runs = st.session_state.saved_experiments

if not saved_runs:
    st.warning("No saved experiments found in session history. Return to the Simulation Lab to run and save experiments.")
    st.stop()

# Selection & Actions Row
st.subheader("1. Select Experiments to Overlay & Compare")

exp_names = [exp["name"] for exp in saved_runs]

sel_col1, sel_col2, sel_col3 = st.columns([3, 1, 1])

with sel_col1:
    selected_names = st.multiselect(
        "Choose experiments to overlay on the comparison chart:",
        options=exp_names,
        default=exp_names[:min(4, len(exp_names))],
    )

with sel_col2:
    st.write("")
    if st.button("➕ Add Quick Benchmark", use_container_width=True):
        p_quick = SimulationParameters(population=10000, initial_exposed=100.0, beta=0.60, moderation_effectiveness=0.60, time_steps=30)
        r_quick = run_propagation_simulation(p_quick)
        rec_quick = package_experiment_record(
            name=f"Custom Run #{len(saved_runs)+1} (m=0.60, β=0.60)",
            model_type="Deterministic Equation",
            population=10000,
            initial_exposed=100.0,
            beta=0.60,
            moderation=0.60,
            time_steps=30,
            final_exposure=r_quick.final_exposure,
            peak_exposure=r_quick.peak_exposure,
            trajectory_steps=list(r_quick.time_steps),
            trajectory_exposure=list(r_quick.exposure),
            reduction_pct=None,
            notes="Added from comparison laboratory.",
        )
        st.session_state.saved_experiments.append(rec_quick)
        st.rerun()

with sel_col3:
    st.write("")
    if st.button("🗑️ Reset to Benchmarks", use_container_width=True):
        st.session_state.initialized = False
        init_session_state()
        st.rerun()

# Filter active selected runs
active_runs = [exp for exp in saved_runs if exp["name"] in selected_names]

# Section 2: Overlaid Trajectory Chart
st.subheader("2. Multi-Trajectory Overlay")

if active_runs:
    fig_comp = go.Figure()
    palette = ["#38BDF8", "#EF4444", "#10B981", "#F59E0B", "#8B5CF6", "#EC4899", "#06B6D4"]

    for idx, exp in enumerate(active_runs):
        color = palette[idx % len(palette)]
        steps = exp.get("trajectory_steps", [])
        exposure = exp.get("trajectory_exposure", [])
        name = exp.get("name", f"Experiment {idx+1}")
        m_val = exp.get("moderation", 0.0)

        fig_comp.add_trace(
            go.Scatter(
                x=steps,
                y=exposure,
                mode="lines+markers",
                name=f"{name} (m={m_val:.2f})",
                line=dict(color=color, width=2.5),
                marker=dict(size=4),
                hovertemplate="<b>%{fullData.name}</b><br>Step %{x}: %{y:,.0f} exposed<extra></extra>",
            )
        )

    fig_comp.update_layout(
        title=dict(text="Comparative Exposure Curves (Overlaid Runs)", font=dict(color="#F8FAFC", size=15)),
        paper_bgcolor="#0F172A",
        plot_bgcolor="#0B1120",
        font=dict(color="#F8FAFC", family="Inter, system-ui, sans-serif"),
        xaxis=dict(title="Simulation Time Step", gridcolor="#334155", color="#94A3B8"),
        yaxis=dict(title="Exposed Population", gridcolor="#334155", color="#94A3B8"),
        legend=dict(bgcolor="rgba(15, 23, 42, 0.8)", bordercolor="#334155", borderwidth=1),
        margin=dict(l=50, r=40, t=50, b=50),
        height=420,
    )
    st.plotly_chart(fig_comp, use_container_width=True)
else:
    st.info("Select at least one experiment above to display the comparison graph.")

st.markdown("---")

# Section 3: Detailed Comparison Table
st.subheader("3. Experiment Parameters & Outcomes Summary")

table_rows = []
for exp in saved_runs:
    is_active = "✅" if exp["name"] in selected_names else "⬜"
    table_rows.append({
        "Selected": is_active,
        "Name": exp["name"],
        "Model Type": exp["model_type"],
        "Population (N)": f"{exp['population']:,}",
        "Sharing Rate (β)": f"{exp['beta']:.2f}",
        "Moderation (m)": f"{exp['moderation']:.2f}",
        "Final Exposure": f"{exp['final_exposure']:,.0f}",
        "Exposure (%)": f"{exp['final_exposure_pct']:.1f}%",
        "Peak Exposure": f"{exp['peak_exposure']:,.0f}",
        "Reduction vs Base": f"{exp['reduction_pct']:.1f}%" if exp.get("reduction_pct") is not None else "N/A",
        "Saved At": exp.get("timestamp", "-"),
    })

summary_table_df = pd.DataFrame(table_rows)
st.dataframe(summary_table_df, use_container_width=True, hide_index=True)

# Delete Run Controls
with st.expander("🗑️ Delete a Saved Run"):
    del_target = st.selectbox("Select run to delete:", options=[exp["name"] for exp in saved_runs])
    if st.button("Confirm Delete"):
        st.session_state.saved_experiments = [exp for exp in saved_runs if exp["name"] != del_target]
        st.success(f"Deleted '{del_target}'.")
        st.rerun()

st.markdown("---")

# Section 4: CSV Data Exports
st.subheader("4. Research Data Export")

export_clean_df = pd.DataFrame(saved_runs).drop(columns=["trajectory_steps", "trajectory_exposure"], errors="ignore")

exp_col1, exp_col2 = st.columns(2)

with exp_col1:
    st.download_button(
        label="📥 Download Experiment Summary (CSV)",
        data=export_clean_df.to_csv(index=False).encode("utf-8"),
        file_name="fake_news_experiment_summary.csv",
        mime="text/csv",
        use_container_width=True,
    )

with exp_col2:
    # Build merged trajectory matrix for export
    max_len = max((len(exp.get("trajectory_steps", [])) for exp in saved_runs), default=0)
    if max_len > 0:
        merged_dict = {"step": list(range(max_len))}
        for exp in saved_runs:
            t_exp = list(exp.get("trajectory_exposure", []))
            if len(t_exp) < max_len:
                pad = t_exp[-1] if t_exp else 0.0
                t_exp = t_exp + [pad] * (max_len - len(t_exp))
            merged_dict[exp["name"]] = t_exp
        merged_trajectories_df = pd.DataFrame(merged_dict)
        st.download_button(
            label="📥 Download All Trajectories (CSV)",
            data=merged_trajectories_df.to_csv(index=False).encode("utf-8"),
            file_name="fake_news_trajectories_matrix.csv",
            mime="text/csv",
            use_container_width=True,
        )
