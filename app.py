"""
Fake News Propagation & Game Theory Dashboard
College Game Theory & Information Security Project.
Interactive Threat Modeling: Peer-to-Peer Contagion vs. Strategic Platform Deterrence.
"""

from typing import Dict, Tuple
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.equilibrium import (
    analyze_game,
    compute_dominant_strategies,
    compute_pareto_efficiency,
)
from src.payoff_model import PayoffMatrix, classify_game_taxonomy
from src.propagation import SimulationParameters, run_propagation_simulation

# ----------------- PAGE CONFIG -----------------
st.set_page_config(
    page_title="Fake News Propagation & Game Theory Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------- SESSION STATE & COURSE DEFAULTS -----------------
# ----------------- SESSION STATE & COURSE DEFAULTS -----------------
COURSE_DEFAULTS = {
    "payoff_s_SW": 5.0,
    "payoff_p_SW": -4.0,
    "payoff_s_SM": -2.0,
    "payoff_p_SM": 3.0,
    "payoff_s_NW": 1.0,
    "payoff_p_NW": 0.0,
    "payoff_s_NM": 0.0,
    "payoff_p_NM": 2.0,
    "pop_slider": 10000,
    "seed_slider": 100,
    "beta_slider": 0.35,
    "mod_slider": 0.50,
    "steps_slider": 30,
    "highlight_mode": "All Elements",
}

for key, val in COURSE_DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = val

# Auto-heal any stale zeroed state from previous test runs
if st.session_state.get("payoff_s_SW") == 0.0 and st.session_state.get("payoff_p_SW") == 0.0:
    for k in ["payoff_s_SW", "payoff_p_SW", "payoff_s_SM", "payoff_p_SM",
              "payoff_s_NW", "payoff_p_NW", "payoff_s_NM", "payoff_p_NM"]:
        st.session_state[k] = COURSE_DEFAULTS[k]


# ----------------- SYSTEM AUTO CUSTOM CSS: DUAL-MODE (DARK / LIGHT) -----------------
SYSTEM_AUTO_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600;700&family=Space+Grotesk:wght@500;600;700;800&display=swap');

    /* Design System CSS Variables - Default: Dark Threat Intelligence */
    :root {
        --bg-app: #0A0F1E;
        --bg-sidebar: #0F172A;
        --bg-card: rgba(15, 23, 42, 0.75);
        --bg-card-hover: rgba(15, 23, 42, 0.90);
        --border-card: rgba(255, 255, 255, 0.12);
        --border-card-hover: rgba(0, 240, 255, 0.45);
        --text-primary: #FFFFFF;
        --text-secondary: #F1F5F9;
        --text-muted: #E2E8F0;
        --shadow-card: 0 8px 30px rgba(0, 0, 0, 0.45);
        --hero-grad: linear-gradient(135deg, #00F0FF 0%, #38BDF8 35%, #818CF8 70%, #C084FC 100%);
        --tabs-bg: rgba(15, 23, 42, 0.85);
        --tabs-border: rgba(255, 255, 255, 0.12);
        --tab-active-bg: rgba(0, 240, 255, 0.18);
        --tab-active-color: #00F0FF;
        --chip-slate-bg: rgba(241, 245, 249, 0.14);
        --chip-slate-text: #FFFFFF;
        --chip-slate-border: rgba(241, 245, 249, 0.35);
        --nash-cell-bg: rgba(16, 185, 129, 0.12);
        --tuple-color: #00F0FF;
    }

    .stApp {
        background-color: #0A0F1E !important;
        color: #F8FAFC !important;
    }

    section[data-testid="stSidebar"] {
        background-color: #0F172A !important;
        border-right: 1px solid rgba(255, 255, 255, 0.12) !important;
    }

    /* High-Contrast Whitish Sidebar Typography (Dark Mode) */
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] h4,
    section[data-testid="stSidebar"] h5,
    section[data-testid="stSidebar"] h6 {
        color: #FFFFFF !important;
        font-weight: 700 !important;
        letter-spacing: -0.01em !important;
    }
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] div {
        color: #F1F5F9 !important;
    }
    section[data-testid="stSidebar"] hr {
        border-color: rgba(255, 255, 255, 0.15) !important;
    }
    .stSlider label, .stSelectbox label, .stNumberInput label, .stRadio label {
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }
    .stSlider div[data-testid="stTickBarMin"],
    .stSlider div[data-testid="stTickBarMax"] {
        color: #E2E8F0 !important;
        font-weight: 500 !important;
    }
    div[data-testid="stTooltipIcon"] svg,
    section[data-testid="stSidebar"] svg {
        fill: #00F0FF !important;
        color: #00F0FF !important;
    }

    /* Sleek Dark Selector / Dropdown Boxes (Dark Mode) */
    div[data-baseweb="select"] {
        background-color: transparent !important;
    }
    div[data-baseweb="select"] > div {
        background-color: #1E293B !important;
        border: 1px solid rgba(0, 240, 255, 0.35) !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.3) !important;
    }
    div[data-baseweb="select"] * {
        background-color: transparent !important;
        color: #FFFFFF !important;
        font-weight: 500 !important;
    }
    div[data-baseweb="select"] svg {
        fill: #00F0FF !important;
        color: #00F0FF !important;
    }
    div[data-baseweb="select"]:hover > div,
    div[data-baseweb="select"]:focus-within > div {
        border-color: #00F0FF !important;
        box-shadow: 0 0 16px rgba(0, 240, 255, 0.35) !important;
    }

    /* Dropdown Popover Menu Items (Dark Mode) */
    div[data-baseweb="popover"],
    div[data-baseweb="popover"] > div,
    ul[data-baseweb="menu"] {
        background-color: #1E293B !important;
        border: 1px solid rgba(0, 240, 255, 0.4) !important;
        border-radius: 8px !important;
        box-shadow: 0 12px 28px rgba(0, 0, 0, 0.55) !important;
    }
    li[data-baseweb="menu-item"] {
        background-color: #1E293B !important;
        color: #FFFFFF !important;
        padding: 9px 14px !important;
        font-size: 0.88rem !important;
        transition: background 0.15s ease !important;
    }
    li[data-baseweb="menu-item"] * {
        color: #FFFFFF !important;
    }
    li[data-baseweb="menu-item"]:hover,
    li[data-baseweb="menu-item"][aria-selected="true"] {
        background-color: rgba(0, 240, 255, 0.22) !important;
        color: #00F0FF !important;
    }
    li[data-baseweb="menu-item"]:hover * {
        color: #00F0FF !important;
    }

    /* Number Inputs in Dark Mode */
    div[data-baseweb="input"] {
        background-color: #1E293B !important;
        border: 1px solid rgba(255, 255, 255, 0.22) !important;
        border-radius: 8px !important;
    }
    div[data-baseweb="input"] input {
        background-color: #1E293B !important;
        color: #FFFFFF !important;
    }
    div[data-baseweb="input"]:focus-within {
        border-color: #00F0FF !important;
        box-shadow: 0 0 12px rgba(0, 240, 255, 0.3) !important;
    }

    /* Dark Mode Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%) !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(0, 240, 255, 0.45) !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 0.55rem 1.1rem !important;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.35) !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button * {
        color: #FFFFFF !important;
    }
    .stButton > button:hover {
        border-color: #00F0FF !important;
        color: #00F0FF !important;
        box-shadow: 0 0 20px rgba(0, 240, 255, 0.45) !important;
        transform: translateY(-1px) !important;
    }
    .stButton > button:hover * {
        color: #00F0FF !important;
    }

    .kpi-value {
        color: #FFFFFF !important;
    }

    .matrix-cell, .kpi-card, .glass-panel {
        background: rgba(15, 23, 42, 0.75) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.35) !important;
    }

    /* System Light Mode Adaptation - Triggers automatically according to OS / browser preference */
    @media (prefers-color-scheme: light) {
        :root {
            --bg-app: #F8FAFC;
            --bg-sidebar: #F1F5F9;
            --bg-card: rgba(255, 255, 255, 0.90);
            --bg-card-hover: rgba(255, 255, 255, 1.0);
            --border-card: rgba(0, 0, 0, 0.08);
            --border-card-hover: rgba(2, 132, 199, 0.45);
            --text-primary: #0F172A;
            --text-secondary: #475569;
            --text-muted: #64748B;
            --shadow-card: 0 6px 20px rgba(0, 0, 0, 0.06);
            --hero-grad: linear-gradient(135deg, #0284C7 0%, #2563EB 50%, #7C3AED 100%);
            --tabs-bg: rgba(241, 245, 249, 0.85);
            --tabs-border: rgba(0, 0, 0, 0.08);
            --tab-active-bg: rgba(2, 132, 199, 0.12);
            --tab-active-color: #0284C7;
            --chip-slate-bg: rgba(100, 116, 139, 0.10);
            --chip-slate-text: #334155;
            --chip-slate-border: rgba(100, 116, 139, 0.20);
            --nash-cell-bg: rgba(16, 185, 129, 0.10);
            --tuple-color: #0284C7;
        }

        .stApp {
            background-color: #F8FAFC !important;
            color: #0F172A !important;
        }

        section[data-testid="stSidebar"] {
            background-color: #F1F5F9 !important;
            border-right: 1px solid rgba(0, 0, 0, 0.08) !important;
        }

        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] h4,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] div {
            color: #0F172A !important;
        }

        /* Light Mode Selectors and Buttons */
        div[data-baseweb="select"] > div {
            background-color: #FFFFFF !important;
            border: 1px solid rgba(0, 0, 0, 0.15) !important;
        }
        div[data-baseweb="select"] * {
            color: #0F172A !important;
        }
        div[data-baseweb="select"] svg {
            fill: #0284C7 !important;
        }
        ul[data-baseweb="menu"], [data-baseweb="popover"], div[data-baseweb="popover"] > div {
            background-color: #FFFFFF !important;
            border: 1px solid rgba(0, 0, 0, 0.12) !important;
            color: #0F172A !important;
        }
        li[data-baseweb="menu-item"] {
            background-color: #FFFFFF !important;
            color: #0F172A !important;
        }
        li[data-baseweb="menu-item"]:hover {
            background-color: rgba(2, 132, 199, 0.10) !important;
            color: #0284C7 !important;
        }
        div[data-baseweb="input"] {
            background-color: #FFFFFF !important;
            border: 1px solid rgba(0, 0, 0, 0.15) !important;
        }
        div[data-baseweb="input"] input {
            background-color: #FFFFFF !important;
            color: #0F172A !important;
        }
        .stButton > button {
            background: #FFFFFF !important;
            color: #0F172A !important;
            border: 1px solid rgba(0, 0, 0, 0.15) !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05) !important;
        }
        .stButton > button:hover {
            border-color: #0284C7 !important;
            color: #0284C7 !important;
            box-shadow: 0 4px 12px rgba(2, 132, 199, 0.15) !important;
        }

        .kpi-value {
            color: #0F172A !important;
        }

        .matrix-cell, .kpi-card, .glass-panel {
            background: rgba(255, 255, 255, 0.92) !important;
            border: 1px solid rgba(0, 0, 0, 0.08) !important;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.05) !important;
        }

        .matrix-cell:hover, .kpi-card:hover {
            border-color: rgba(2, 132, 199, 0.4) !important;
            box-shadow: 0 8px 24px rgba(2, 132, 199, 0.12) !important;
        }

        .stTabs [data-baseweb="tab-list"] {
            background-color: rgba(241, 245, 249, 0.9) !important;
            border: 1px solid rgba(0, 0, 0, 0.08) !important;
        }

        .stTabs [data-baseweb="tab"] {
            color: #64748B !important;
        }

        .stTabs [aria-selected="true"] {
            background-color: rgba(2, 132, 199, 0.12) !important;
            color: #0284C7 !important;
            border: 1px solid rgba(2, 132, 199, 0.3) !important;
        }
    }

    /* Global Typography */
    html, body, [class*="css"] {
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }

    /* Clean Streamlit Default Chrome while keeping the sidebar expand arrow fully accessible */
    #MainMenu, [data-testid="stToolbarActions"], footer {
        visibility: hidden !important;
        display: none !important;
    }

    /* Keep header and toolbar transparent so the sidebar reopen arrow is fully visible and clickable */
    header[data-testid="stHeader"] {
        background: transparent !important;
        z-index: 999990 !important;
        height: 2.8rem !important;
    }
    [data-testid="stToolbar"] {
        background: transparent !important;
    }
    /* Hide the right-side section in toolbar (deploy button, 3 dots menu) */
    header [data-testid="stToolbar"] > div > div:last-child {
        visibility: hidden !important;
        display: none !important;
    }

    /* Ensure the sidebar expand arrow (Streamlit 1.30+) is ALWAYS visible, interactive, and styled */
    [data-testid="stExpandSidebarButton"] {
        visibility: visible !important;
        display: inline-flex !important;
        z-index: 999999 !important;
    }
    [data-testid="stExpandSidebarButton"] button {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-card) !important;
        color: var(--text-primary) !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
        backdrop-filter: blur(10px) !important;
        -webkit-backdrop-filter: blur(10px) !important;
    }
    [data-testid="stExpandSidebarButton"] button:hover {
        border-color: #00F0FF !important;
        color: #00F0FF !important;
    }

    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 3.5rem;
        max-width: 1400px;
    }

    /* Hero Header */
    .hero-title {
        background: var(--hero-grad);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2.35rem;
        font-weight: 800;
        margin: 0 0 6px 0;
        letter-spacing: -0.03em;
        line-height: 1.15;
    }
    .hero-subtitle {
        font-size: 1.0rem;
        color: var(--text-secondary);
        font-weight: 400;
        margin-bottom: 12px;
        line-height: 1.5;
    }

    /* Animated Live Badge */
    .live-badge {
        display: inline-flex;
        align-items: center;
        gap: 7px;
        padding: 4px 11px;
        background: rgba(16, 185, 129, 0.12);
        border: 1px solid rgba(16, 185, 129, 0.35);
        border-radius: 9999px;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        color: #10B981;
        text-transform: uppercase;
        margin-bottom: 12px;
    }
    .pulse-dot {
        width: 8px;
        height: 8px;
        background: #10B981;
        border-radius: 50%;
        box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
        animation: pulseDot 2s infinite cubic-bezier(0.4, 0, 0.6, 1);
    }
    @keyframes pulseDot {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
        70% { transform: scale(1.1); box-shadow: 0 0 0 7px rgba(16, 185, 129, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }

    /* Glassmorphism Metric Cards */
    .kpi-container {
        display: flex;
        gap: 16px;
        margin-bottom: 18px;
    }
    .kpi-card {
        background: var(--bg-card);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        border: 1px solid var(--border-card);
        border-radius: 14px;
        padding: 16px 18px;
        flex: 1;
        box-shadow: var(--shadow-card);
        transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        min-height: 125px;
    }
    .kpi-card:hover {
        transform: translateY(-4px);
        border-color: var(--border-card-hover);
        box-shadow: 0 12px 35px rgba(0, 240, 255, 0.12);
    }
    .kpi-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 8px;
    }
    .kpi-title {
        font-size: 0.80rem;
        font-weight: 600;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .kpi-icon {
        font-size: 1.15rem;
    }
    .kpi-value {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.85rem;
        font-weight: 700;
        color: var(--text-primary);
        margin: 2px 0 6px 0;
        letter-spacing: -0.02em;
    }
    .kpi-chip {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 3px 8px;
        border-radius: 6px;
        width: fit-content;
    }
    .chip-cyan { background: rgba(0, 240, 255, 0.12); color: #00F0FF; border: 1px solid rgba(0, 240, 255, 0.25); }
    .chip-emerald { background: rgba(16, 185, 129, 0.12); color: #10B981; border: 1px solid rgba(16, 185, 129, 0.25); }
    .chip-coral { background: rgba(244, 63, 94, 0.12); color: #F43F5E; border: 1px solid rgba(244, 63, 94, 0.25); }
    .chip-slate { background: var(--chip-slate-bg); color: var(--chip-slate-text); border: 1px solid var(--chip-slate-border); }

    /* Glass Panels for Payoff Matrix & Explainer */
    .glass-panel {
        background: var(--bg-card);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        border: 1px solid var(--border-card);
        border-radius: 14px;
        padding: 18px 20px;
        margin-bottom: 16px;
        box-shadow: var(--shadow-card);
    }

    /* Payoff Matrix Cell Styles - Both columns have equal bright contrast */
    .matrix-cell {
        background: var(--bg-card);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        border: 1px solid var(--border-card);
        border-radius: 12px;
        padding: 16px 18px;
        min-height: 220px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        transition: all 0.25s ease;
        position: relative;
        opacity: 1.0 !important;
    }
    .matrix-cell:hover {
        transform: translateY(-3px);
        border-color: rgba(56, 189, 248, 0.4);
        box-shadow: 0 10px 28px rgba(0, 0, 0, 0.4);
    }

    /* Nash Equilibrium Glowing Cell */
    .nash-cell-glow {
        border: 2px solid #10B981 !important;
        background: var(--nash-cell-bg) !important;
        box-shadow: 0 0 20px rgba(16, 185, 129, 0.25), inset 0 0 12px rgba(16, 185, 129, 0.12) !important;
        animation: glowPulse 2.5s infinite ease-in-out;
    }
    @keyframes glowPulse {
        0%, 100% { box-shadow: 0 0 15px rgba(16, 185, 129, 0.25), inset 0 0 10px rgba(16, 185, 129, 0.08); }
        50% { box-shadow: 0 0 28px rgba(16, 185, 129, 0.50), inset 0 0 16px rgba(16, 185, 129, 0.20); }
    }

    /* Badges */
    .badge-nash {
        background: #10B981;
        color: #0A0F1E;
        font-weight: 800;
        font-size: 0.72rem;
        padding: 3px 8px;
        border-radius: 5px;
        letter-spacing: 0.03em;
        display: inline-block;
        margin-right: 5px;
    }
    .badge-sharer-br {
        background: rgba(0, 240, 255, 0.15);
        color: #00F0FF;
        border: 1px solid #00F0FF;
        font-weight: 700;
        font-size: 0.70rem;
        padding: 2px 7px;
        border-radius: 5px;
        display: inline-block;
        margin-right: 4px;
    }
    .badge-platform-br {
        background: rgba(245, 158, 11, 0.15);
        color: #F59E0B;
        border: 1px solid #F59E0B;
        font-weight: 700;
        font-size: 0.70rem;
        padding: 2px 7px;
        border-radius: 5px;
        display: inline-block;
        margin-right: 4px;
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: var(--tabs-bg);
        padding: 6px;
        border-radius: 12px;
        border: 1px solid var(--tabs-border);
    }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 20px;
        border-radius: 8px;
        color: #E2E8F0 !important;
        font-weight: 600;
        font-size: 0.90rem;
        transition: all 0.2s ease;
    }
    .stTabs [data-baseweb="tab"] * {
        color: inherit !important;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #00F0FF !important;
        background-color: rgba(0, 240, 255, 0.08) !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: var(--tab-active-bg) !important;
        color: #00F0FF !important;
        border: 1px solid rgba(0, 240, 255, 0.4) !important;
    }
    .stTabs [aria-selected="true"] * {
        color: #00F0FF !important;
    }

    /* Expander styling in dark mode */
    div[data-testid="stExpander"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-card) !important;
        border-radius: 12px !important;
    }
    div[data-testid="stExpander"] details summary {
        color: #FFFFFF !important;
    }
    div[data-testid="stExpander"] details summary span,
    div[data-testid="stExpander"] details summary p {
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }
    div[data-testid="stExpander"] details summary svg {
        fill: #00F0FF !important;
        color: #00F0FF !important;
    }

    /* Radio button labels in dark mode */
    div[data-testid="stRadio"] label,
    div[data-testid="stRadio"] label p,
    div[data-testid="stRadio"] label span {
        color: #F1F5F9 !important;
        font-weight: 500 !important;
    }
</style>
"""

st.markdown(SYSTEM_AUTO_CSS, unsafe_allow_html=True)


# ----------------- PRESET HANDLER -----------------
SCENARIO_PRESETS = {
    "Default Course Baseline": {
        "pop": 10000, "seed": 100, "beta": 0.35, "mod": 0.50, "steps": 30,
        "payoffs": {"payoff_s_SW": 5.0, "payoff_p_SW": -4.0, "payoff_s_SM": -2.0, "payoff_p_SM": 3.0,
                    "payoff_s_NW": 1.0, "payoff_p_NW": 0.0, "payoff_s_NM": 0.0, "payoff_p_NM": 2.0},
    },
    "Highly Viral Outbreak (Low Moderation)": {
        "pop": 15000, "seed": 250, "beta": 0.65, "mod": 0.15, "steps": 35,
        "payoffs": {"payoff_s_SW": 7.0, "payoff_p_SW": -6.0, "payoff_s_SM": -1.0, "payoff_p_SM": 2.0,
                    "payoff_s_NW": 1.0, "payoff_p_NW": 0.0, "payoff_s_NM": 0.0, "payoff_p_NM": 1.5},
    },
    "Strict Platform Deterrence": {
        "pop": 10000, "seed": 50, "beta": 0.25, "mod": 0.85, "steps": 30,
        "payoffs": {"payoff_s_SW": 4.0, "payoff_p_SW": -3.0, "payoff_s_SM": -3.0, "payoff_p_SM": 4.0,
                    "payoff_s_NW": 1.0, "payoff_p_NW": 0.0, "payoff_s_NM": 0.0, "payoff_p_NM": 2.5},
    },
    "Zero Moderation (Laissez-Faire)": {
        "pop": 10000, "seed": 100, "beta": 0.40, "mod": 0.00, "steps": 30,
        "payoffs": {"payoff_s_SW": 5.0, "payoff_p_SW": -4.0, "payoff_s_SM": -2.0, "payoff_p_SM": 3.0,
                    "payoff_s_NW": 1.0, "payoff_p_NW": 0.0, "payoff_s_NM": 0.0, "payoff_p_NM": 2.0},
    },
}


def on_preset_change():
    chosen = st.session_state.get("scenario_selector")
    preset_data = SCENARIO_PRESETS.get(chosen)
    if preset_data:
        st.session_state.pop_slider = preset_data["pop"]
        st.session_state.seed_slider = preset_data["seed"]
        st.session_state.beta_slider = preset_data["beta"]
        st.session_state.mod_slider = preset_data["mod"]
        st.session_state.steps_slider = preset_data["steps"]
        for pk, pv in preset_data["payoffs"].items():
            st.session_state[pk] = pv
        st.toast(f"⚡ Loaded scenario: {chosen}")


def on_payoff_change():
    st.toast("⚡ Payoff Matrix & Equilibria Recomputed!")


def reset_payoffs_callback():
    for k in ["payoff_s_SW", "payoff_p_SW", "payoff_s_SM", "payoff_p_SM",
              "payoff_s_NW", "payoff_p_NW", "payoff_s_NM", "payoff_p_NM"]:
        st.session_state[k] = COURSE_DEFAULTS[k]
    st.toast("🔄 Reset payoff values to course defaults!")


def reset_all_callback():
    for k, v in COURSE_DEFAULTS.items():
        st.session_state[k] = v
    st.toast("🔄 Reset all simulation controls and payoffs to defaults!")


# ----------------- SIDEBAR (GROUPED SECTIONS WITH ICONS) -----------------
with st.sidebar:
    st.markdown("### ⚙️ Simulation Controls")

    st.selectbox(
        "⚡ Scenario Presets",
        options=list(SCENARIO_PRESETS.keys()),
        key="scenario_selector",
        on_change=on_preset_change,
        help="Quickly populate sliders and payoffs with representative threat scenarios.",
    )

    st.markdown("---")
    st.markdown("#### 👥 1. Population & Seeding")
    population = st.slider(
        "Total Population (N)",
        min_value=1000,
        max_value=50000,
        step=1000,
        key="pop_slider",
        help="Total network size of interacting individuals.",
    )
    initial_exposed = st.slider(
        "Initial Seeds (I₀)",
        min_value=10,
        max_value=500,
        step=10,
        key="seed_slider",
        help="Initial patient-zero seed cohort propagating the false narrative.",
    )

    st.markdown("#### 📡 2. Transmission & Moderation")
    beta = st.slider(
        "Sharing Propensity (β)",
        min_value=0.05,
        max_value=1.00,
        step=0.01,
        key="beta_slider",
        help="Probability of peer transmission per interaction.",
    )
    moderation = st.slider(
        "Platform Moderation (m)",
        min_value=0.00,
        max_value=1.00,
        step=0.05,
        key="mod_slider",
        help="Institutional filter intensity (0.0 = Slack / Laissez-Faire, 1.0 = Total Suppression).",
    )
    time_steps = st.slider(
        "Simulation Steps (T)",
        min_value=10,
        max_value=60,
        step=5,
        key="steps_slider",
        help="Discrete observation horizon.",
    )

    st.markdown("---")
    st.button("🔄 Reset All to Defaults", on_click=reset_all_callback, use_container_width=True)

    st.markdown(
        """
        <div style="font-size: 0.80rem; color: var(--text-secondary); line-height: 1.5; padding: 6px 0;">
            <div style="font-weight: 700; color: var(--text-primary); margin-bottom: 4px;">🎓 Game Theory Project by:</div>
            <div>• <b>Shreshth Juneja</b> (2427030246)</div>
            <div>• <b>Devaanshee Agarwal</b> (2427030504)</div>
            <div style="margin-top: 6px; font-size: 0.72rem; color: var(--text-muted);">Model: 2×2 Strategic Deterrence + Logistic Contagion</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ----------------- COMPUTATION LOGIC (WITH CACHING) -----------------
@st.cache_data
def compute_simulation(population: int, initial_exposed: float, beta: float, moderation: float, time_steps: int):
    """Run baseline unmoderated and policy moderated logistic diffusion simulations."""
    p_base = SimulationParameters(
        population=population,
        initial_exposed=initial_exposed,
        beta=beta,
        moderation_effectiveness=0.0,
        time_steps=time_steps,
    )
    res_base = run_propagation_simulation(p_base)

    p_policy = SimulationParameters(
        population=population,
        initial_exposed=initial_exposed,
        beta=beta,
        moderation_effectiveness=moderation,
        time_steps=time_steps,
    )
    res_policy = run_propagation_simulation(p_policy)

    red_pct = ((res_base.final_exposure - res_policy.final_exposure) / res_base.final_exposure * 100.0) if res_base.final_exposure > 0 else 0.0
    return res_base, res_policy, red_pct


def compute_game(payoffs: Dict[str, float]):
    """Instantiate and analyze the 2x2 normal form game."""
    matrix = PayoffMatrix(
        sharer_SW=float(payoffs["payoff_s_SW"]),
        platform_SW=float(payoffs["payoff_p_SW"]),
        sharer_SM=float(payoffs["payoff_s_SM"]),
        platform_SM=float(payoffs["payoff_p_SM"]),
        sharer_NW=float(payoffs["payoff_s_NW"]),
        platform_NW=float(payoffs["payoff_p_NW"]),
        sharer_NM=float(payoffs["payoff_s_NM"]),
        platform_NM=float(payoffs["payoff_p_NM"]),
    )
    matrix.validate()
    analysis = analyze_game(matrix)
    dom_strat = compute_dominant_strategies(matrix, analysis.best_responses)
    pareto_profiles = compute_pareto_efficiency(matrix)
    taxonomy = classify_game_taxonomy(matrix)
    return matrix, analysis, dom_strat, pareto_profiles, taxonomy


# Execute calculations
base_res, policy_res, reduction_pct = compute_simulation(
    population=population,
    initial_exposed=float(initial_exposed),
    beta=beta,
    moderation=moderation,
    time_steps=time_steps,
)

current_payoffs = {
    "payoff_s_SW": st.session_state.payoff_s_SW,
    "payoff_p_SW": st.session_state.payoff_p_SW,
    "payoff_s_SM": st.session_state.payoff_s_SM,
    "payoff_p_SM": st.session_state.payoff_p_SM,
    "payoff_s_NW": st.session_state.payoff_s_NW,
    "payoff_p_NW": st.session_state.payoff_p_NW,
    "payoff_s_NM": st.session_state.payoff_s_NM,
    "payoff_p_NM": st.session_state.payoff_p_NM,
}
matrix, analysis, dom_strat, pareto_profiles, taxonomy = compute_game(current_payoffs)

if analysis.has_pure_equilibrium:
    eq_label = ", ".join(eq.profile_label for eq in analysis.pure_equilibria)
    pe = analysis.pure_equilibria[0]
    eq_chip = f"({pe.sharer_payoff:g}, {pe.platform_payoff:g}) Payoffs"
else:
    eq_label = "Mixed Strategy Eq"
    if analysis.mixed_equilibrium.exists_interior:
        eq_chip = f"p*={analysis.mixed_equilibrium.p_star:.2f}, q*={analysis.mixed_equilibrium.q_star:.2f}"
    else:
        eq_chip = "Cycling Dynamics"


# ----------------- HERO HEADER -----------------
st.markdown(
    """
    <div style="margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; margin-bottom: 8px;">
            <div class="live-badge" style="margin-bottom: 0;">
                <div class="pulse-dot"></div>
                Live Simulation & Strategic Engine
            </div>
            <div style="display: inline-flex; align-items: center; gap: 8px; flex-wrap: wrap; font-size: 0.84rem;">
                <span style="font-weight: 700; color: var(--text-primary);">🎓 Game Theory Project by:</span>
                <span class="kpi-chip chip-cyan" style="font-size: 0.78rem; font-weight: 600;">Shreshth Juneja (2427030246)</span>
                <span class="kpi-chip chip-cyan" style="font-size: 0.78rem; font-weight: 600;">Devaanshee Agarwal (2427030504)</span>
            </div>
        </div>
        <h1 class="hero-title">Fake News Propagation & Game Theory Dashboard</h1>
        <div class="hero-subtitle">
            Strategic Threat Modeling: Institutional Platform Moderation vs. Viral Misinformation Contagion Dynamics.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ----------------- TOP KPI CARDS ROW (CUSTOM GLASS HTML) -----------------
def render_kpis():
    pct_final = (policy_res.final_exposure / population) * 100.0 if population > 0 else 0.0
    saved_users = base_res.final_exposure - policy_res.final_exposure

    html = f"""
    <div class="kpi-container">
        <div class="kpi-card">
            <div class="kpi-header">
                <span class="kpi-title">Final Exposure</span>
                <span class="kpi-icon">👥</span>
            </div>
            <div class="kpi-value">{policy_res.final_exposure:,.0f}</div>
            <div class="kpi-chip chip-cyan">{pct_final:.1f}% of population</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-header">
                <span class="kpi-title">Peak Exposure</span>
                <span class="kpi-icon">📈</span>
            </div>
            <div class="kpi-value">{policy_res.peak_exposure:,.0f}</div>
            <div class="kpi-chip chip-slate">Baseline was {base_res.peak_exposure:,.0f}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-header">
                <span class="kpi-title">Exposure Reduction</span>
                <span class="kpi-icon">🛡️</span>
            </div>
            <div class="kpi-value">{reduction_pct:.1f}%</div>
            <div class="kpi-chip chip-emerald">Saved {saved_users:,.0f} users</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-header">
                <span class="kpi-title">Nash Equilibrium</span>
                <span class="kpi-icon">🏆</span>
            </div>
            <div class="kpi-value">{eq_label}</div>
            <div class="kpi-chip chip-emerald">{eq_chip}</div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


render_kpis()


# ----------------- TABS LAYOUT -----------------
tab_prop, tab_matrix, tab_theory = st.tabs([
    "📈 Propagation",
    "⚖️ Payoff Matrix",
    "🧠 Equilibrium Analysis",
])


# ================= TAB 1: PROPAGATION (ANIMATED PLOTLY CHART) =================
with tab_prop:
    st.subheader("Viral Propagation Over Time (Logistic Contagion Curve)")

    def render_chart():
        t_arr = base_res.time_steps
        y_base = base_res.exposure
        y_policy = policy_res.exposure

        fig = go.Figure()

        # Shaded Area between curves: "Users Saved"
        fig.add_trace(
            go.Scatter(
                x=t_arr,
                y=y_base,
                mode="lines",
                name="Baseline Unmoderated (m = 0.00)",
                line=dict(color="#F43F5E", width=2.5, dash="dot"),
                hovertemplate="<b>Baseline (m=0)</b><br>Step %{x}: %{y:,.0f} exposed (%{customdata:.1%})<extra></extra>",
                customdata=y_base / population if population > 0 else np.zeros_like(y_base),
            )
        )

        fig.add_trace(
            go.Scatter(
                x=t_arr,
                y=y_policy,
                mode="lines+markers",
                name=f"Moderated Policy (m = {moderation:.2f})",
                line=dict(color="#00F0FF", width=3.5),
                marker=dict(size=4, color="#00F0FF"),
                fill="tonexty",
                fillcolor="rgba(16, 185, 129, 0.16)",
                hovertemplate="<b>Active Policy (m=" + f"{moderation:.2f}" + ")</b><br>Step %{x}: %{y:,.0f} exposed (%{customdata:.1%})<extra></extra>",
                customdata=y_policy / population if population > 0 else np.zeros_like(y_policy),
            )
        )

        # Population reference ceiling line
        fig.add_hline(
            y=population,
            line_dash="dot",
            line_color="rgba(255, 255, 255, 0.25)",
            line_width=1.5,
            annotation_text=f"Total Network N = {population:,}",
            annotation_position="bottom right",
            annotation_font=dict(color="#CBD5E1", size=11, family="Inter"),
        )

        annot_bg = "rgba(15, 23, 42, 0.85)"
        peak_color = "#00F0FF"

        # Inflection point on policy curve
        diffs = np.diff(y_policy)
        if len(diffs) > 0 and np.max(diffs) > 0:
            infl_step = int(np.argmax(diffs))
            infl_val = y_policy[infl_step]
            fig.add_annotation(
                x=infl_step,
                y=infl_val,
                text=f"Inflection (d²I/dt²=0): Step {infl_step}",
                showarrow=True,
                arrowhead=2,
                arrowcolor="#F59E0B",
                arrowsize=1.2,
                arrowwidth=1.5,
                ax=-50,
                ay=30,
                bgcolor=annot_bg,
                bordercolor="#F59E0B",
                borderwidth=1,
                font=dict(color="#F59E0B", size=10, family="Inter"),
            )

        # Peak on policy curve
        peak_step = int(np.argmax(y_policy))
        peak_val = y_policy[peak_step]
        fig.add_annotation(
            x=peak_step,
            y=peak_val,
            text=f"Peak: {peak_val:,.0f}",
            showarrow=True,
            arrowhead=2,
            arrowcolor=peak_color,
            arrowsize=1.2,
            arrowwidth=1.5,
            ax=0,
            ay=-35,
            bgcolor=annot_bg,
            bordercolor=peak_color,
            borderwidth=1,
            font=dict(color=peak_color, size=11, family="Inter"),
        )

        # Animation frames for scrubbing through t
        frames = [
            go.Frame(
                data=[
                    go.Scatter(x=t_arr[:k+1], y=y_base[:k+1]),
                    go.Scatter(x=t_arr[:k+1], y=y_policy[:k+1]),
                ],
                name=f"frame_{k}",
            )
            for k in range(1, len(t_arr))
        ]
        fig.frames = frames

        # Play / Pause & Time Step Slider Menu
        fig.update_layout(
            updatemenus=[
                dict(
                    type="buttons",
                    direction="left",
                    x=0.0,
                    y=1.18,
                    xanchor="left",
                    yanchor="top",
                    pad=dict(r=10, t=10),
                    showactive=False,
                    buttons=[
                        dict(
                            label="▶ Play Outbreak",
                            method="animate",
                            args=[
                                None,
                                dict(
                                    frame=dict(duration=80, redraw=False),
                                    fromcurrent=True,
                                    transition=dict(duration=0),
                                ),
                            ],
                        ),
                        dict(
                            label="⏸ Pause",
                            method="animate",
                            args=[
                                [None],
                                dict(
                                    frame=dict(duration=0, redraw=False),
                                    mode="immediate",
                                    transition=dict(duration=0),
                                ),
                            ],
                        ),
                    ],
                )
            ],
            sliders=[
                dict(
                    active=len(t_arr) - 1,
                    y=-0.18,
                    x=0.05,
                    len=0.92,
                    pad=dict(b=10, t=20),
                    currentvalue=dict(
                        font=dict(size=12, color=peak_color),
                        prefix="Simulation Step: ",
                        visible=True,
                        xanchor="right",
                    ),
                    steps=[
                        dict(
                            method="animate",
                            args=[
                                [f"frame_{k}"],
                                dict(
                                    mode="immediate",
                                    frame=dict(duration=0, redraw=False),
                                    transition=dict(duration=0),
                                ),
                            ],
                            label=str(k),
                        )
                        for k in range(1, len(t_arr))
                    ],
                )
            ],
        )

        fig.update_layout(
            title=dict(
                text=f"Viral Transmission Contagion: Policy (m = {moderation:.2f}) vs Baseline (m = 0.00)",
                font=dict(size=15, family="Space Grotesk"),
            ),
            paper_bgcolor="rgba(0, 0, 0, 0)",
            plot_bgcolor="rgba(0, 0, 0, 0)",
            font=dict(family="Inter, system-ui, sans-serif"),
            xaxis=dict(
                title="Simulation Time Step (t)",
                gridcolor="rgba(255, 255, 255, 0.10)",
                color="#E2E8F0",
                range=[0, time_steps],
            ),
            yaxis=dict(
                title="Exposed Individuals (I_t)",
                gridcolor="rgba(255, 255, 255, 0.10)",
                color="#E2E8F0",
                range=[0, population * 1.05],
            ),
            legend=dict(
                bgcolor="rgba(15, 23, 42, 0.75)",
                bordercolor="rgba(255, 255, 255, 0.15)",
                font=dict(color="#F1F5F9", size=11),
                borderwidth=1,
                x=0.02,
                y=0.98,
            ),
            margin=dict(l=60, r=40, t=75, b=60),
            height=460,
        )
        return fig

    fig_chart = render_chart()
    st.plotly_chart(fig_chart, use_container_width=True)

    st.markdown(
        f"""
        <div class="glass-panel" style="margin-top: 10px; display: flex; justify-content: space-around; text-align: center;">
            <div>
                <span style="font-size:0.8rem;color:var(--text-secondary);">Baseline Outbreak (m=0.00)</span>
                <div style="font-size:1.3rem;font-weight:700;color:#F43F5E;">{base_res.final_exposure:,.0f} exposed</div>
            </div>
            <div style="border-left: 1px solid var(--border-card); padding-left: 20px;">
                <span style="font-size:0.8rem;color:var(--text-secondary);">Moderated Exposure (m={moderation:.2f})</span>
                <div style="font-size:1.3rem;font-weight:700;color:#00F0FF;">{policy_res.final_exposure:,.0f} exposed</div>
            </div>
            <div style="border-left: 1px solid var(--border-card); padding-left: 20px;">
                <span style="font-size:0.8rem;color:var(--text-secondary);">Green Shaded Area</span>
                <div style="font-size:1.3rem;font-weight:700;color:#10B981;">{base_res.final_exposure - policy_res.final_exposure:,.0f} Infections Prevented</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ================= TAB 2: PAYOFF MATRIX (2X2 GLASS GRID) =================
with tab_matrix:
    st.subheader("Strategic Normal-Form Payoff Matrix")

    # Payoff Editor Expander (placed above the matrix as requested)
    with st.expander("✏️ Customize Payoff Numbers", expanded=False):
        st.markdown(
            "Adjust any of the 8 payoff values to immediately recompute Best Responses, Dominance, and Nash Equilibria."
        )
        ed1, ed2, ed3, ed4 = st.columns(4)
        with ed1:
            st.markdown("**Profile (S, W) [Viral]**")
            st.number_input("Sharer (S, W):", value=5.0, key="payoff_s_SW", step=1.0, on_change=on_payoff_change)
            st.number_input("Platform (S, W):", value=-4.0, key="payoff_p_SW", step=1.0, on_change=on_payoff_change)
        with ed2:
            st.markdown("**Profile (S, M) [Deterred]**")
            st.number_input("Sharer (S, M):", value=-2.0, key="payoff_s_SM", step=1.0, on_change=on_payoff_change)
            st.number_input("Platform (S, M):", value=3.0, key="payoff_p_SM", step=1.0, on_change=on_payoff_change)
        with ed3:
            st.markdown("**Profile (N, W) [Laissez-Faire]**")
            st.number_input("Sharer (N, W):", value=1.0, key="payoff_s_NW", step=1.0, on_change=on_payoff_change)
            st.number_input("Platform (N, W):", value=0.0, key="payoff_p_NW", step=1.0, on_change=on_payoff_change)
        with ed4:
            st.markdown("**Profile (N, M) [Compliant]**")
            st.number_input("Sharer (N, M):", value=0.0, key="payoff_s_NM", step=1.0, on_change=on_payoff_change)
            st.number_input("Platform (N, M):", value=2.0, key="payoff_p_NM", step=1.0, on_change=on_payoff_change)

        st.button("🔄 Reset Payoffs to Course Values", on_click=reset_payoffs_callback)

    # Highlight Mode Selection Controls
    h_c1, h_c2 = st.columns([3, 1])
    with h_c1:
        highlight_mode = st.radio(
            "Highlight Filter Mode:",
            options=["All Elements", "Best Responses Only", "Strict Dominance Only", "Nash Equilibrium Only"],
            horizontal=True,
            key="highlight_mode",
            help="Toggle what visual badges and indicators are displayed on the matrix.",
        )
    with h_c2:
        st.markdown(
            f"""
            <div style="text-align:right;padding-top:14px;">
                <span class="kpi-chip chip-cyan">{taxonomy.icon} {taxonomy.game_type}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Best Responses and Nash Logic
    s_br_W = "S" in analysis.best_responses.sharer_br_to_W
    s_br_M = "S" in analysis.best_responses.sharer_br_to_M
    n_br_W = "N" in analysis.best_responses.sharer_br_to_W
    n_br_M = "N" in analysis.best_responses.sharer_br_to_M

    p_br_S = "W" in analysis.best_responses.platform_br_to_S
    p_br_N = "W" in analysis.best_responses.platform_br_to_N
    m_br_S = "M" in analysis.best_responses.platform_br_to_S
    m_br_N = "M" in analysis.best_responses.platform_br_to_N

    is_nash_SW = s_br_W and p_br_S
    is_nash_SM = s_br_M and m_br_S
    is_nash_NW = n_br_W and p_br_N
    is_nash_NM = n_br_M and m_br_N

    # Dominance Badges (Both columns maintain equal bright contrast)
    p_dom = dom_strat.platform_dominant
    col_W_dim = ""
    col_M_dim = ""

    badge_W = " ⭐ STRICTLY DOMINANT" if p_dom == "W" else (" (Strictly Dominated)" if p_dom == "M" else "")
    badge_M = " ⭐ STRICTLY DOMINANT" if p_dom == "M" else (" (Strictly Dominated)" if p_dom == "W" else "")

    # Platform Column Headers
    sp_col, col_h_W, col_h_M = st.columns([1, 4, 4])
    with sp_col:
        st.write("")
    with col_h_W:
        st.markdown(
            f"""
            <div class="glass-panel" style="text-align:center;padding:12px;margin-bottom:8px;">
                <span style="font-weight:700;color:var(--text-primary);font-size:0.95rem;">Platform: Weak Moderation (W)</span><br>
                <span style="font-size:0.75rem;color:var(--text-secondary);">Low Operating Cost / Slack Filters {badge_W}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_h_M:
        border_m = "border: 1px solid #00F0FF;" if p_dom == "M" else ""
        st.markdown(
            f"""
            <div class="glass-panel" style="text-align:center;padding:12px;margin-bottom:8px;{border_m}">
                <span style="font-weight:700;color:#00F0FF;font-size:0.95rem;">Platform: Strong Moderation (M) {badge_M}</span><br>
                <span style="font-size:0.75rem;color:#10B981;font-weight:600;">Active Enforcement (Sanctions & Downranking)</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    def render_cell(
        label: str,
        s_val: float,
        p_val: float,
        is_nash: bool,
        s_br: bool,
        p_br: bool,
        logic: str,
        dim_class: str = "",
    ):
        show_nash = is_nash and (highlight_mode in ["All Elements", "Nash Equilibrium Only"])
        show_s_br = s_br and (highlight_mode in ["All Elements", "Best Responses Only"])
        show_p_br = p_br and (highlight_mode in ["All Elements", "Best Responses Only"])

        glow_class = "nash-cell-glow" if show_nash else ""
        top_border = ""
        if show_nash:
            top_border = "border-top: 3px solid #10B981 !important;"
        elif show_s_br and not show_p_br:
            top_border = "border-top: 3px solid #00F0FF !important;"
        elif show_p_br and not show_s_br:
            top_border = "border-top: 3px solid #F59E0B !important;"
        elif show_s_br and show_p_br:
            top_border = "border-top: 3px solid #10B981 !important;"

        badges_html = []
        if show_nash:
            badges_html.append('<span class="badge-nash">🏆 NASH EQUILIBRIUM</span>')
        if show_s_br:
            badges_html.append('<span class="badge-sharer-br">🎯 Sharer Best Response</span>')
        if show_p_br:
            badges_html.append('<span class="badge-platform-br">🛡️ Platform Best Response</span>')

        badge_block = "".join(badges_html) if badges_html else '<span style="font-size:0.73rem;color:var(--text-muted);">No Strategic Extremum</span>'

        st.markdown(
            f"""
            <div class="matrix-cell {glow_class} {dim_class}" style="{top_border}">
                <div>
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                        <span style="font-weight:700;color:var(--text-primary);font-size:0.95rem;">{label}</span>
                        <span class="kpi-chip chip-slate" style="font-size:0.72rem;">Surplus: <b>{s_val + p_val:+g}</b></span>
                    </div>
                    <div style="font-family:'JetBrains Mono', monospace;font-size:1.75rem;font-weight:700;color:var(--tuple-color);margin:8px 0;">
                        ({s_val:g}, {p_val:g})
                        <span style="font-size:0.75rem;color:var(--text-secondary);font-family:'Inter',sans-serif;font-weight:400;margin-left:6px;">(Sharer, Platform)</span>
                    </div>
                    <div style="margin-bottom:12px;">{badge_block}</div>
                </div>
                <div style="font-size:0.80rem;color:var(--text-secondary);line-height:1.45;border-top:1px solid var(--border-card);padding-top:10px;">
                    {logic}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Row 1: Sharer S (Spread)
    r1_lbl, cell_SW_col, cell_SM_col = st.columns([1, 4, 4])
    with r1_lbl:
        st.markdown(
            """
            <div style="height:100%;display:flex;flex-direction:column;justify-content:center;padding:8px;">
                <div style="font-weight:700;color:#F43F5E;font-size:1.0rem;">Sharer: Spread (S)</div>
                <span style="font-size:0.75rem;color:var(--text-secondary);">Viral Misinformation Seeding</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with cell_SW_col:
        render_cell(
            label="Profile (S, W) — Viral Exploitation",
            s_val=matrix.sharer_SW,
            p_val=matrix.platform_SW,
            is_nash=is_nash_SW,
            s_br=s_br_W,
            p_br=p_br_S,
            logic="Weak moderation allows fake news to spread unhindered. Sharer reaps maximum engagement (+5), while platform brand suffers severe advertiser damage (-4).",
            dim_class=col_W_dim,
        )
    with cell_SM_col:
        render_cell(
            label="Profile (S, M) — Active Deterrence",
            s_val=matrix.sharer_SM,
            p_val=matrix.platform_SM,
            is_nash=is_nash_SM,
            s_br=s_br_M,
            p_br=m_br_S,
            logic="Platform filters and sanctions active misinformation (+3). Penalties and shadowbans eliminate virality gains, leaving the sharer with a net loss (-2).",
            dim_class=col_M_dim,
        )

    # Row 2: Sharer N (Do Not Spread)
    r2_lbl, cell_NW_col, cell_NM_col = st.columns([1, 4, 4])
    with r2_lbl:
        st.markdown(
            """
            <div style="height:100%;display:flex;flex-direction:column;justify-content:center;padding:8px;">
                <div style="font-weight:700;color:#10B981;font-size:1.0rem;">Sharer: Do Not Spread (N)</div>
                <span style="font-size:0.75rem;color:var(--text-secondary);">Organic Honest Sharing</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with cell_NW_col:
        render_cell(
            label="Profile (N, W) — Laissez-Faire Baseline",
            s_val=matrix.sharer_NW,
            p_val=matrix.platform_NW,
            is_nash=is_nash_NW,
            s_br=n_br_W,
            p_br=p_br_N,
            logic="Users post organic truthful content (+1). Platform maintains low operating overhead with neutral baseline utility (0).",
            dim_class=col_W_dim,
        )
    with cell_NM_col:
        render_cell(
            label="Profile (N, M) — Enforced Compliance",
            s_val=matrix.sharer_NM,
            p_val=matrix.platform_NM,
            is_nash=is_nash_NM,
            s_br=n_br_M,
            p_br=m_br_N,
            logic="Sharer complies with platform rules (0). Platform preserves a clean, trustworthy community (+2), minus steady automated filter infrastructure costs.",
            dim_class=col_M_dim,
        )


# ================= TAB 3: EQUILIBRIUM ANALYSIS =================
with tab_theory:
    st.subheader("Game-Theoretic Equilibrium & Dominance Proofs")

    # Step-by-Step Interactive Stepper
    with st.expander("🔍 Step-by-Step Interactive Proof: How to Find the Nash Equilibrium", expanded=True):
        step_choice = st.select_slider(
            "Select Interactive Analytical Step:",
            options=[
                "Step 1: Sharer Best Responses",
                "Step 2: Platform Best Responses",
                "Step 3: Identify Mutual Nash Equilibrium",
                "Step 4: Strictly Dominant Strategies (IESDS)",
            ],
            value="Step 1: Sharer Best Responses",
        )

        if step_choice == "Step 1: Sharer Best Responses":
            st.markdown(
                f"""
                <div class="glass-panel" style="border-left: 4px solid #00F0FF;">
                    <b style="color:#00F0FF;">Step 1: Compute Content Sharer's Best Responses</b><br>
                    Conditional on each action the Platform could take, what maximizes Sharer utility?
                    <ul>
                        <li><b>If Platform plays Weak Moderation (W):</b> Sharer compares Spread <i>u(S,W) = {matrix.sharer_SW:g}</i> vs. Do Not Spread <i>u(N,W) = {matrix.sharer_NW:g}</i>. Since {matrix.sharer_SW:g} &gt; {matrix.sharer_NW:g}, <b>Best Response is Spread (S)</b>.</li>
                        <li><b>If Platform plays Strong Moderation (M):</b> Sharer compares Spread <i>u(S,M) = {matrix.sharer_SM:g}</i> vs. Do Not Spread <i>u(N,M) = {matrix.sharer_NM:g}</i>. Since {matrix.sharer_NM:g} &gt; {matrix.sharer_SM:g}, <b>Best Response is Do Not Spread (N)</b>.</li>
                    </ul>
                    <i>Conclusion: Sharer's best response depends strictly on platform policy (no unconditional dominant move).</i>
                </div>
                """,
                unsafe_allow_html=True,
            )
        elif step_choice == "Step 2: Platform Best Responses":
            st.markdown(
                f"""
                <div class="glass-panel" style="border-left: 4px solid #F59E0B;">
                    <b style="color:#F59E0B;">Step 2: Compute Platform's Best Responses</b><br>
                    Conditional on each action the Content Sharer could take, what maximizes Platform utility?
                    <ul>
                        <li><b>If Sharer chooses Spread (S):</b> Platform compares Weak <i>u(S,W) = {matrix.platform_SW:g}</i> vs. Strong <i>u(S,M) = {matrix.platform_SM:g}</i>. Since {matrix.platform_SM:g} &gt; {matrix.platform_SW:g}, <b>Best Response is Strong Moderation (M)</b>.</li>
                        <li><b>If Sharer chooses Do Not Spread (N):</b> Platform compares Weak <i>u(N,W) = {matrix.platform_NW:g}</i> vs. Strong <i>u(N,M) = {matrix.platform_NM:g}</i>. Since {matrix.platform_NM:g} &gt; {matrix.platform_NW:g}, <b>Best Response is Strong Moderation (M)</b>.</li>
                    </ul>
                    <i>Notice: Strong Moderation (M) is strictly superior regardless of the sharer's action!</i>
                </div>
                """,
                unsafe_allow_html=True,
            )
        elif step_choice == "Step 3: Identify Mutual Nash Equilibrium":
            st.markdown(
                f"""
                <div class="glass-panel" style="border-left: 4px solid #10B981;">
                    <b style="color:#10B981;">Step 3: Mark Mutual Best Response Intersections</b><br>
                    A strategy profile <i>(s*, p*)</i> is a Nash Equilibrium if and only if both players are simultaneously playing mutual best responses:
                    <ul>
                        <li><b>(S, W):</b> Only Sharer is playing BR (Platform would deviate to M). ❌ Not Nash.</li>
                        <li><b>(S, M):</b> Only Platform is playing BR (Sharer would deviate to N). ❌ Not Nash.</li>
                        <li><b>(N, W):</b> Neither player is playing BR. ❌ Not Nash.</li>
                        <li><b>(N, M):</b> Both Sharer (N is BR to M) and Platform (M is BR to N) are at mutual best responses! <b>🏆 UNIQUE NASH EQUILIBRIUM</b>.</li>
                    </ul>
                    Neither player can unilaterally improve their payoff by deviating.
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div class="glass-panel" style="border-left: 4px solid #818CF8;">
                    <b style="color:#818CF8;">Step 4: Iterated Elimination of Strictly Dominated Strategies (IESDS)</b><br>
                    A strategy is Strictly Dominated if another action yields strictly higher payoff in every scenario:
                    <ul>
                        <li><b>Platform:</b> Strong Moderation (M) strictly dominates Weak Moderation (W), since <i>{matrix.platform_SM:g} &gt; {matrix.platform_SW:g}</i> and <i>{matrix.platform_NM:g} &gt; {matrix.platform_NW:g}</i>. We eliminate column W completely.</li>
                        <li><b>Reduced Game:</b> Sharer anticipates that a rational platform will never play W. In the remaining column M, Sharer compares <i>u(S,M) = {matrix.sharer_SM:g}</i> vs. <i>u(N,M) = {matrix.sharer_NM:g}</i>.</li>
                        <li>Sharer chooses N, confirming the single dominance-solvable equilibrium at <b>{eq_label}</b>.</li>
                    </ul>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # The Three Core Course Theoretical Explanations (Strictly Preserved)
    th1, th2, th3 = st.columns(3)
    with th1:
        st.markdown(
            f"""
            <div class="glass-panel" style="height:100%;">
                <div style="font-size:0.80rem;font-weight:700;color:var(--text-secondary);text-transform:uppercase;margin-bottom:6px;">1. Nash Equilibrium Stability</div>
                <div style="font-size:1.15rem;font-weight:700;color:#10B981;margin-bottom:8px;">Profile {eq_label} ({eq_chip})</div>
                <div style="font-size:0.82rem;color:var(--text-secondary);line-height:1.5;">
                    Both players are at mutual Best Responses. Neither the Content Sharer (earning {matrix.sharer_NM:g}) nor the Platform (earning {matrix.platform_NM:g}) can increase their utility by unilaterally deviating. The profile is mathematically self-enforcing.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with th2:
        st.markdown(
            f"""
            <div class="glass-panel" style="height:100%;">
                <div style="font-size:0.80rem;font-weight:700;color:var(--text-secondary);text-transform:uppercase;margin-bottom:6px;">2. Dominant Strategy Resolution</div>
                <div style="font-size:1.15rem;font-weight:700;color:#00F0FF;margin-bottom:8px;">Platform Strictly Dominates with M</div>
                <div style="font-size:0.82rem;color:var(--text-secondary);line-height:1.5;">
                    {dom_strat.solution_summary}
                    <br><br>
                    Because <b>3 &gt; -4</b> (under misinformation) and <b>2 &gt; 0</b> (under truthful organic sharing), strong enforcement is the Platform's unconditional optimal strategy.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with th3:
        st.markdown(
            f"""
            <div class="glass-panel" style="height:100%;">
                <div style="font-size:0.80rem;font-weight:700;color:var(--text-secondary);text-transform:uppercase;margin-bottom:6px;">3. Bridge to Propagation Curve</div>
                <div style="font-size:1.15rem;font-weight:700;color:#F59E0B;margin-bottom:8px;">Deterrence Suppresses Viral Outbreaks</div>
                <div style="font-size:0.82rem;color:var(--text-secondary);line-height:1.5;">
                    Slacking to <b>W</b> allows sharers to capture viral exploitation utility (+5), sparking the exponential red contagion curve above. Credibly committing to <b>M</b> imposes deterrence (-2), forcing compliance (N) and locking in the blue curve!
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
