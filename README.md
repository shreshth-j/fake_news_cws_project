# Interactive Fake News Simulation & Game Theory Laboratory

> **Game Theory Project by:**  
> • **Shreshth Juneja** (2427030246)  
> • **Devaanshee Agarwal** (2427030504)

A **simulation-first** interactive research dashboard modeling the strategic interaction between **Content Sharers** and **Social Media Platforms**, coupled with macroscopic epidemiological diffusion and microscopic network propagation.

Designed for university-level Game Theory courses, research demonstrations, and interactive laboratory presentations.

---

## 1. Project Overview & Philosophy

The application balances **70% interactive simulations and visual experiments**, **20% results and scenario comparisons**, and **10% mathematical theory**. 

Instead of reading a textbook, students and professors can:
- Run full or step-by-step simulations of misinformation spread.
- Watch peer-to-peer transmission across synthetic social network graphs (scale-free and random graphs).
- Compare platform content moderation policies side-by-side.
- Test early intervention against delayed intervention.
- Inspect the strategic incentives of the underlying 2-player normal-form game.
- Save and overlay experimental runs.

---

## 2. Reorganized Laboratory Navigation

1. **🧪 Simulation Lab (`app.py`):** The primary interactive landing page. Features live sliders, Full Simulation mode, Step-by-Step interactive progression, live KPI cards, and baseline comparison charts.
2. **⚖️ Moderation Experiments (`pages/1_Moderation_Experiments.py`):** Simultaneous 4-policy benchmarks, one-click experiment presets, Early vs. Late intervention dynamics, and sensitivity sweeps for $m$ and $\beta$.
3. **🕸️ Network Spread (`pages/2_Network_Spread.py`):** Explicit graph diffusion simulator. Demonstrates how misinformation spreads across Scale-Free (Barabási–Albert) and Random (Erdős–Rényi) network topologies with interactive node inspection.
4. **🎯 Game Strategy & Payoffs (`pages/3_Game_Strategy_and_Payoffs.py`):** Compact payoff matrix, best-response analysis, pure and mixed-strategy Nash equilibria, and direct linkage between strategy profiles and diffusion trajectories.
5. **📁 Experiment Comparison (`pages/4_Experiment_Comparison.py`):** Multi-run overlay comparison chart, parameter summary table, delete controls, and CSV export.
6. **📖 Methodology (`pages/5_Methodology.py`):** Concise, tabbed documentation of mathematical formulations, equations, and modeling assumptions.

---

## 3. Mathematical & Simulation Formulations

### Model A: Macroscopic Population Diffusion
Misinformation diffusion follows the discrete-time non-linear exposure equation:

$$I_{t+1} = \min\left(N, \max\left(0, I_t + \beta \cdot (1 - m) \cdot I_t \cdot \left(1 - \frac{I_t}{N}\right)\right)\right)$$

Where:
- $N$: Total simulated population.
- $I_t$: Exposed individuals at time step $t$.
- $\beta$: Peer-to-peer sharing propensity.
- $m$: Platform moderation effectiveness ($m \in [0, 1]$).

### Model B: Microscopic Network Diffusion
On an explicit graph $G = (V, E)$:
- **Transmission:** Active infected nodes attempt to infect susceptible neighbors with probability $P_{\text{transmit}} = \beta \cdot (1 - m)$.
- **Moderation:** Platforms inspect and quarantine active sharers with detection probability $m$.

### Model C: Strategic Normal-Form Game
- **Player 1 (Content Sharer):** Strategies $S$ (Spread) and $N$ (Do Not Spread).
- **Player 2 (Platform):** Strategies $W$ (Weak Moderation) and $M$ (Strong Moderation).
- Initial matrix: $(S, W) = (5, -4)$, $(S, M) = (-2, 3)$, $(N, W) = (1, 0)$, $(N, M) = (0, 2)$.
- Unique pure-strategy Nash equilibrium at **$(N, M)$** with payoffs **$(0, 2)$**.

---

## 4. Experiment Presets

- **🔥 Preset A: Viral Misinformation:** High sharing rate ($\beta = 0.55$), weak moderation ($m = 0.15$). Rapid exponential outbreak.
- **🛡️ Preset B: Effective Intervention:** High sharing rate ($\beta = 0.55$), strong moderation ($m = 0.75$). Rapid curve flattening.
- **⚡ Preset C: High Sharing Pressure:** Severe transmission pressure ($\beta = 0.85$), moderate moderation ($m = 0.40$).
- **⏱️ Preset D: Early vs. Late Intervention:** Compares immediate moderation ($t=0$) against delayed intervention ($t=t_{\text{delay}}$) to quantify the delay penalty.
- **🕸️ Preset E: Network Structure:** Contrasts Scale-Free networks (hub super-spreaders) against Random graphs.
- **📊 Preset F: Sensitivity Analysis:** Automated parameter sweeps across $m \in [0, 1]$ and $\beta \in [0.05, 1.20]$.

---

## 5. Installation & Execution

### Prerequisites
- Python 3.9+

### Setup Environment
```bash
# 1. Activate virtual environment
source .venv/bin/activate
# Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt
```

### Run Tests
```bash
python -m pytest -v
```
All 27 automated unit tests verify:
- Bounded population diffusion ($I_{t+1} \le N$).
- Network graph generation and state progression bounds.
- Delayed intervention intermediate dynamics.
- Pure and mixed-strategy Nash equilibrium solvers with tie handling.
- Monotonicity of sensitivity sweeps.

### Launch Application
```bash
streamlit run app.py
```
Open **`http://localhost:8501`** in any web browser.

---

## 6. Assumptions & Limitations

1. **Pedagogical Model:** Payoffs and parameters are illustrative assumptions for education and demonstration, not empirical corporate data.
2. **Network Topologies:** NetworkX graphs demonstrate structural mechanics, but real platforms feature proprietary algorithmic recommendation feeds.
3. **Session Persistence:** Saved experiments persist within browser session state; use the CSV Export buttons on the Experiment Comparison page to download data.
