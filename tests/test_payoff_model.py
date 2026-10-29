"""
Unit tests for the Payoff Matrix model.
"""

import pytest
import numpy as np
from src.payoff_model import PayoffMatrix


def test_initial_example_payoff_values():
    """Verify default initial matrix exactly matches the problem specification."""
    m = PayoffMatrix.default()
    assert m.get_payoff("S", "W") == (5.0, -4.0)
    assert m.get_payoff("S", "M") == (-2.0, 3.0)
    assert m.get_payoff("N", "W") == (1.0, 0.0)
    assert m.get_payoff("N", "M") == (0.0, 2.0)


def test_case_insensitive_strategy_lookup():
    """Verify strategy retrieval works regardless of case."""
    m = PayoffMatrix.default()
    assert m.get_payoff("s", "w") == (5.0, -4.0)
    assert m.get_payoff("S", "m") == (-2.0, 3.0)
    assert m.get_payoff("n", "W") == (1.0, 0.0)
    assert m.get_payoff("N", "M") == (0.0, 2.0)


def test_invalid_strategy_lookup():
    """Verify looking up invalid strategies raises ValueError."""
    m = PayoffMatrix.default()
    with pytest.raises(ValueError):
        m.get_payoff("X", "W")
    with pytest.raises(ValueError):
        m.get_payoff("S", "Z")


def test_custom_payoffs_and_serialization():
    """Verify payoffs can be customized and serialized to/from dictionary."""
    custom = PayoffMatrix(
        sharer_SW=10.0,
        platform_SW=-10.0,
        sharer_SM=-5.0,
        platform_SM=8.0,
        sharer_NW=2.0,
        platform_NW=1.0,
        sharer_NM=0.0,
        platform_NM=5.0,
    )
    custom.validate()
    d = custom.to_dict()
    restored = PayoffMatrix.from_dict(d)
    assert restored.sharer_SW == 10.0
    assert restored.platform_SW == -10.0
    assert restored.platform_SM == 8.0


def test_validation_rejects_non_finite_values():
    """Verify that infinite or NaN payoffs are rejected."""
    with pytest.raises(ValueError):
        PayoffMatrix(sharer_SW=np.nan).validate()
    with pytest.raises(ValueError):
        PayoffMatrix(platform_SM=np.inf).validate()
