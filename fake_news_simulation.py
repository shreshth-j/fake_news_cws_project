"""
Game-Theoretic Model of Fake News Propagation and Platform Moderation
CWS project simulation.

Requirements:
    pip install numpy pandas matplotlib networkx

Run:
    python fake_news_simulation.py

All numerical parameters are illustrative assumptions for experimentation,
not empirical estimates about any real platform.
"""
from dataclasses import dataclass
from pathlib import Path
import numpy as np
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

OUTPUT_DIR = Path("simulation_outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

@dataclass(frozen=True)
class ModerationPolicy:
    name: str
    detection_probability: float
    false_positive_rate: float
    cost_per_action: float
    sanction_penalty: float

POLICIES = [
    ModerationPolicy("No moderation", 0.00, 0.00, 0.00, 0.00),
    ModerationPolicy("Weak moderation", 0.30, 0.01, 0.10, 0.50),
    ModerationPolicy("Moderate moderation", 0.60, 0.03, 0.18, 0.90),
    ModerationPolicy("Strong moderation", 0.90, 0.08, 0.30, 1.40),
]

@dataclass
class ModelParameters:
    n_users: int = 150
    network_m: int = 3
    max_rounds: int = 15
    initial_seed_users: int = 3
    engagement_benefit: float = 1.25
    social_cost: float = 0.35
    removal_penalty_weight: float = 1.0
    choice_temperature: float = 0.65
    legitimate_posts_per_round: int = 25
    harm_per_exposure: float = 0.12
    false_positive_harm: float = 0.70
    random_seed: int = 2026

def logistic(x):
    """Numerically stable logistic choice function."""
    x = np.clip(x, -30, 30)
    return 1.0 / (1.0 + np.exp(-x))

def simulate_once(policy, params, seed):
    """
    Run one stochastic diffusion experiment on a Barabasi-Albert social network.

    A node may be:
      0 = not yet exposed
      1 = exposed but did not share
      2 = shared the fake-news item

    A successful share can expose susceptible neighbours in the next round.
    A platform may remove a share according to its detection probability.
    """
    rng = np.random.default_rng(seed)
    graph = nx.barabasi_albert_graph(params.n_users, params.network_m, seed=seed)

    state = np.zeros(params.n_users, dtype=int)
    seed_nodes = rng.choice(params.n_users, size=params.initial_seed_users, replace=False)
    state[seed_nodes] = 2

    first_round_exposed = np.zeros(params.n_users, dtype=bool)
    first_round_exposed[seed_nodes] = True
    exposed_count = int(len(seed_nodes))
    attempted_shares = int(len(seed_nodes))
    removed_shares = 0
    spread_by_round = [exposed_count]
    removed_by_round = [0]
    active_nodes = set(seed_nodes.tolist())

    # Initial seed posts are also subject to moderation.
    survivors = []
    for node in active_nodes:
        if rng.random() < policy.detection_probability:
            state[node] = 1
            removed_shares += 1
        else:
            survivors.append(node)
    active_nodes = set(survivors)
    removed_by_round[0] = removed_shares

    for round_no in range(1, params.max_rounds + 1):
        newly_exposed = set()
        for node in active_nodes:
            for neighbour in graph.neighbors(node):
                if state[neighbour] == 0:
                    newly_exposed.add(neighbour)

        if not newly_exposed:
            spread_by_round.append(0)
            removed_by_round.append(0)
            break

        next_active = set()
        round_removed = 0
        for node in newly_exposed:
            state[node] = 1  # seen the content
            exposed_count += 1

            # User's expected utility from sharing:
            # engagement benefit - social cost - expected moderation sanction.
            share_utility = (
                params.engagement_benefit
                - params.social_cost
                - policy.detection_probability
                  * policy.sanction_penalty
                  * params.removal_penalty_weight
            )
            share_probability = logistic(share_utility / params.choice_temperature)

            if rng.random() < share_probability:
                attempted_shares += 1
                if rng.random() < policy.detection_probability:
                    round_removed += 1
                else:
                    state[node] = 2
                    next_active.add(node)

        removed_shares += round_removed
        active_nodes = next_active
        spread_by_round.append(len(newly_exposed))
        removed_by_round.append(round_removed)

    # Illustrative expected count of legitimate posts incorrectly removed.
    legitimate_posts = params.legitimate_posts_per_round * len(spread_by_round)
    false_positives = int(rng.binomial(legitimate_posts, policy.false_positive_rate))

    moderation_actions = removed_shares + false_positives
    moderation_cost = policy.cost_per_action * moderation_actions
    misinformation_harm = params.harm_per_exposure * exposed_count
    false_positive_cost = params.false_positive_harm * false_positives

    # Platform utility: lower misinformation harm and lower operating costs are better.
    platform_utility = -(misinformation_harm + moderation_cost + false_positive_cost)

    return {
        "policy": policy.name,
        "exposed_users": exposed_count,
        "attempted_fake_shares": attempted_shares,
        "fake_posts_removed": removed_shares,
        "false_positives": false_positives,
        "moderation_cost": moderation_cost,
        "misinformation_harm": misinformation_harm,
        "false_positive_cost": false_positive_cost,
        "platform_utility": platform_utility,
        "rounds_observed": len(spread_by_round) - 1,
        "spread_by_round": spread_by_round,
        "removed_by_round": removed_by_round,
        "graph": graph,
        "final_state": state,
    }

def run_experiment(params, runs=40):
    """Run multiple trials per policy to reduce the impact of random variation."""
    metric_rows = []
    curve_rows = []
    example_runs = {}

    for policy_index, policy in enumerate(POLICIES):
        all_curves = []
        for run_index in range(runs):
            seed = params.random_seed + policy_index * 10000 + run_index
            result = simulate_once(policy, params, seed)
            metric_rows.append({k: v for k, v in result.items()
                                if k not in {"spread_by_round", "removed_by_round", "graph", "final_state"}})
            curve = result["spread_by_round"]
            all_curves.append(curve)
            for t, value in enumerate(curve):
                curve_rows.append({"policy": policy.name, "run": run_index,
                                   "round": t, "newly_exposed": value})
            if run_index == 0:
                example_runs[policy.name] = result

    raw = pd.DataFrame(metric_rows)
    curves = pd.DataFrame(curve_rows)

    summary = raw.groupby("policy", sort=False).agg(
        exposed_mean=("exposed_users", "mean"),
        exposed_sd=("exposed_users", "std"),
        attempted_shares_mean=("attempted_fake_shares", "mean"),
        removed_mean=("fake_posts_removed", "mean"),
        false_positives_mean=("false_positives", "mean"),
        moderation_cost_mean=("moderation_cost", "mean"),
        misinformation_harm_mean=("misinformation_harm", "mean"),
        platform_utility_mean=("platform_utility", "mean"),
        platform_utility_sd=("platform_utility", "std"),
    ).reset_index()

    # Build aligned time series: each run contributes zero after its cascade ends.
    max_round = params.max_rounds + 1
    curve_summary_rows = []
    for policy in POLICIES:
        subset = curves[curves["policy"] == policy.name]
        for t in range(max_round + 1):
            values = subset.loc[subset["round"] == t, "newly_exposed"].to_numpy()
            if len(values) < runs:
                values = np.pad(values, (0, runs - len(values)))
            curve_summary_rows.append({
                "policy": policy.name,
                "round": t,
                "mean_newly_exposed": float(np.mean(values)) if len(values) else 0.0,
            })
    curve_summary = pd.DataFrame(curve_summary_rows)
    return raw, summary, curve_summary, example_runs

def create_plots(summary, curve_summary, example_runs, params):
    plt.figure(figsize=(9, 5.5))
    for policy in POLICIES:
        subset = curve_summary[curve_summary["policy"] == policy.name]
        plt.plot(subset["round"], subset["mean_newly_exposed"], marker="o",
                 markersize=3, label=policy.name)
    plt.title("Average New Fake-News Exposures by Round")
    plt.xlabel("Round")
    plt.ylabel("Mean newly exposed users")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "01_spread_over_time.png", dpi=180)
    plt.close()

    fig, ax = plt.subplots(figsize=(9, 5.5))
    x = np.arange(len(summary))
    ax.bar(x, summary["exposed_mean"])
    ax.set_xticks(x, summary["policy"], rotation=15, ha="right")
    ax.set_ylabel("Mean users exposed")
    ax.set_title("Total Fake-News Exposure by Moderation Policy")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "02_total_exposure.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.bar(x, summary["platform_utility_mean"])
    ax.set_xticks(x, summary["policy"], rotation=15, ha="right")
    ax.set_ylabel("Mean platform utility (higher is better)")
    ax.set_title("Platform Utility by Moderation Policy")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "03_platform_utility.png", dpi=180)
    plt.close(fig)

    # Example network snapshot from one run per policy.
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    for ax, policy in zip(axes.flat, POLICIES):
        result = example_runs[policy.name]
        graph = result["graph"]
        state = result["final_state"]
        node_colors = []
        for node in graph.nodes():
            if state[node] == 2:
                node_colors.append("tomato")      # successful fake-news sharer
            elif state[node] == 1:
                node_colors.append("gold")        # exposed, did not spread
            else:
                node_colors.append("lightgray")   # not exposed
        pos = nx.spring_layout(graph, seed=42)
        nx.draw_networkx(graph, pos=pos, ax=ax, node_size=22, width=0.35,
                         with_labels=False, node_color=node_colors, edge_color="gray")
        ax.set_title(policy.name)
        ax.axis("off")
    fig.suptitle("Example Social-Network Outcomes\nRed = shared fake news, yellow = exposed but did not share")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "04_network_snapshots.png", dpi=180)
    plt.close(fig)

def main():
    params = ModelParameters()
    runs = 40
    raw, summary, curve_summary, example_runs = run_experiment(params, runs=runs)

    raw.to_csv(OUTPUT_DIR / "all_simulation_runs.csv", index=False)
    summary.to_csv(OUTPUT_DIR / "policy_summary.csv", index=False)
    curve_summary.to_csv(OUTPUT_DIR / "spread_curve_summary.csv", index=False)
    create_plots(summary, curve_summary, example_runs, params)

    print("\n=== MODEL PARAMETERS ===")
    print(pd.Series(params.__dict__).to_string())
    print(f"\nTrials per policy: {runs}")
    print("\n=== RESULTS (means across trials) ===")
    print(summary.round(3).to_string(index=False))
    best = summary.loc[summary["platform_utility_mean"].idxmax()]
    print(f"\nBest policy under this illustrative utility function: {best['policy']}")
    print("Interpret results as model outputs under stated assumptions, not real-world forecasts.")
    print(f"\nFiles saved in: {OUTPUT_DIR.resolve()}")

if __name__ == "__main__":
    main()
