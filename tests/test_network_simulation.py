"""
Unit tests for the Network-Based Fake News Propagation model.
"""

import pytest
import numpy as np
import networkx as nx

from src.network_simulation import (
    generate_synthetic_network,
    run_full_network_simulation,
    STATE_SUSCEPTIBLE,
    STATE_EXPOSED,
    STATE_MODERATED,
)


def test_generate_preferential_attachment_network():
    """Verify Barabasi-Albert graph generation."""
    G, pos = generate_synthetic_network(network_type="preferential_attachment", n_nodes=40, seed=123)
    assert isinstance(G, nx.Graph)
    assert G.number_of_nodes() == 40
    assert len(pos) == 40
    # Scale free graph should be connected
    assert nx.is_connected(G)


def test_generate_random_network():
    """Verify Erdos-Renyi graph generation."""
    G, pos = generate_synthetic_network(network_type="random", n_nodes=35, seed=123)
    assert isinstance(G, nx.Graph)
    assert G.number_of_nodes() == 35
    assert len(pos) == 35


def test_network_simulation_progression_and_bounds():
    """Ensure network simulation tracks states accurately and never exceeds total nodes."""
    G, pos = generate_synthetic_network(network_type="preferential_attachment", n_nodes=50, seed=42)
    res = run_full_network_simulation(
        graph=G,
        pos=pos,
        n_initial_exposed=3,
        transmission_rate=0.5,
        moderation_effectiveness=0.2,
        max_steps=10,
        seed=42,
    )
    assert len(res.steps) == 11  # step 0 to 10
    assert res.steps[0].cumulative_exposed == 3

    for rec in res.steps:
        # Sum of susceptible + active + moderated must equal total nodes
        total = rec.susceptible_count + rec.active_sharers + rec.moderated_count
        assert total == 50
        assert rec.cumulative_exposed <= 50
        assert rec.cumulative_exposed >= 3


def test_network_simulation_reproducibility():
    """Verify fixed random seed yields identical progression."""
    G, pos = generate_synthetic_network(network_type="preferential_attachment", n_nodes=30, seed=99)
    run1 = run_full_network_simulation(G, pos, n_initial_exposed=2, transmission_rate=0.4, moderation_effectiveness=0.3, max_steps=8, seed=99)
    run2 = run_full_network_simulation(G, pos, n_initial_exposed=2, transmission_rate=0.4, moderation_effectiveness=0.3, max_steps=8, seed=99)

    for r1, r2 in zip(run1.steps, run2.steps):
        assert r1.cumulative_exposed == r2.cumulative_exposed
        assert r1.newly_exposed == r2.newly_exposed
        assert r1.node_states == r2.node_states


def test_zero_transmission_network():
    """When transmission rate is 0, no new nodes should become exposed."""
    G, pos = generate_synthetic_network(network_type="preferential_attachment", n_nodes=25, seed=7)
    res = run_full_network_simulation(G, pos, n_initial_exposed=2, transmission_rate=0.0, moderation_effectiveness=0.0, max_steps=5, seed=7)
    for rec in res.steps:
        assert rec.cumulative_exposed == 2
        assert rec.newly_exposed == (2 if rec.step == 0 else 0)
