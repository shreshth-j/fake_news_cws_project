"""
Page 5: Methodology & Model Assumptions
Concise, structured documentation of mathematical models, game-theoretic foundations, and limitations.
"""

import streamlit as st
from src.ui_common import apply_theme, init_session_state, render_sidebar_info

st.set_page_config(
    page_title="Methodology | Fake News Model",
    page_icon="📖",
    layout="wide",
)

apply_theme()
init_session_state()
render_sidebar_info()

st.title("📖 Model Assumptions & Methodology")
st.caption(
    "A concise mathematical specification of the two-player game-theoretic framework, "
    "the discrete-time propagation equation, and the network diffusion dynamics."
)

st.markdown(
    """
    <div class="academic-callout">
        <b>Academic Scope & Disclaimer:</b>
        This application implements a stylized mathematical model combining strategic decision analysis 
        with macroscopic and network diffusion kinetics. It is designed for interactive university education 
        and demonstration of policy trade-offs, not empirical forecasting on proprietary networks.
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("---")

tab_game, tab_diff, tab_assump = st.tabs([
    "♟️ 1. Game-Theoretic Framework",
    "📈 2. Propagation Models (Equation & Network)",
    "⚖️ 3. Assumptions & Limitations",
])

with tab_game:
    st.subheader("1. Strategic Game Formulation")
    st.markdown(
        """
        The conflict between misinformation spreaders and platform governors is framed as a 2-player strategic game:
        - **Player 1 (Content Sharer):** Action set $S_1 = \\{S, N\\}$ ($S$: Spread Fake News, $N$: Do Not Spread).
        - **Player 2 (Social Media Platform):** Action set $S_2 = \\{W, M\\}$ ($W$: Weak Moderation, $M$: Strong Moderation).
        """
    )

    st.markdown("#### Initial Illustrative Payoff Structure")
    st.markdown(
        """
        | Profile $(s_1, s_2)$ | Sharer Payoff $u_1$ | Platform Payoff $u_2$ | Strategic Interpretation |
        | :---: | :---: | :---: | :--- |
        | **$(S, W)$** | $+5$ | $-4$ | Viral virality exploitation; platform reputation damaged. |
        | **$(S, M)$** | $-2$ | $+3$ | Active deterrence: account sanctions exceed virality gain. |
        | **$(N, W)$** | $+1$ | $0$ | Compliant organic baseline; minimal platform overhead. |
        | **$(N, M)$** | $0$ | $+2$ | Strict governance overhead despite compliant users. |
        """
    )

    st.markdown("#### Best Responses & Nash Equilibrium")
    st.latex(r"BR_1(W) = \{S\}, \quad BR_1(M) = \{N\}")
    st.latex(r"BR_2(S) = \{M\}, \quad BR_2(N) = \{M\}")
    st.markdown(
        "Checking mutual best responses reveals the unique pure-strategy Nash equilibrium at **$(N, M)$** "
        "with payoffs **$(0, 2)$**."
    )

with tab_diff:
    st.subheader("2. Diffusion Kinetics")

    st.markdown("#### Model A: Macroscopic Population Equation")
    st.latex(
        r"I_{t+1} = \min\left(N, \max\left(0, I_t + \beta (1 - m) I_t \left(1 - \frac{I_t}{N}\right)\right)\right)"
    )
    st.markdown(
        """
        - $N$: Total network population.
        - $I_t$: Active exposed population at step $t$.
        - $\\beta$: Peer-to-peer transmission propensity.
        - $m$: Platform moderation effectiveness ($m \\in [0, 1]$).
        """
    )

    st.markdown("#### Model B: Microscopic Network Diffusion")
    st.markdown(
        """
        Misinformation diffuses across an explicit graph $G = (V, E)$:
        - **Transmission:** At each round, an exposed node attempts to transmit to each susceptible neighbor with probability $P_{\\text{transmit}} = \\beta (1 - m)$.
        - **Moderation Detection:** Active sharers are independently inspected and quarantined into a moderated state with probability $m$.
        - **Topologies:** Scale-Free (Barabási–Albert preferential attachment) featuring hub super-spreaders, and Random Graphs (Erdős–Rényi).
        """
    )

with tab_assump:
    st.subheader("3. Model Assumptions & Limitations")
    col_a1, col_a2 = st.columns(2)

    with col_a1:
        st.markdown("#### Core Assumptions")
        st.markdown(
            """
            - **Rational Payoff Maximization:** Agents evaluate expected utilities based on known payoff matrices.
            - **Deterministic Benchmark:** Population model provides reproducible macroscopic curves.
            - **Binary Policy State:** Moderation intensity is parameterized along an effective discount $m \\in [0, 1]$.
            """
        )

    with col_a2:
        st.markdown("#### Key Limitations & Future Work")
        st.markdown(
            """
            - **Empirical Calibration:** Payoffs reflect ordinal utility rather than direct advertising dollars.
            - **Network Homogeneity:** Real platforms exhibit algorithmic echo chambers and multi-layer networks.
            - **Continuous Control:** Future research can extend this to differential games where $m(t)$ is controlled via optimal control theory.
            """
        )
