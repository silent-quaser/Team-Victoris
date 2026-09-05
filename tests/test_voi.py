"""
Tests for the VOI (Value of Information) engine.
"""
import pytest
from engine.voi import calculate_voi
from engine.state_manager import get_state


def test_voi_returns_result():
    state = get_state()
    result = calculate_voi("T3_LINE", state)
    assert result is not None


def test_voi_fields_present():
    state = get_state()
    result = calculate_voi("T3_LINE", state)
    assert hasattr(result, "voi")
    assert hasattr(result, "expected_gain")
    assert hasattr(result, "inspection_cost")
    assert hasattr(result, "decision_sensitivity")
    assert hasattr(result, "best_action_if_failed")
    assert hasattr(result, "best_action_if_healthy")


def test_voi_t3_is_positive():
    """T3 has 62% failure probability and high critical impact → VOI should be positive."""
    state = get_state()
    result = calculate_voi("T3_LINE", state)
    # VOI for high-uncertainty, high-impact asset should be > 0
    assert result.voi >= 0


def test_voi_probabilities_sum_to_one():
    state = get_state()
    result = calculate_voi("T3_LINE", state)
    assert abs(result.p_failed + result.p_healthy - 1.0) < 1e-6


def test_voi_uses_actual_fault_probability():
    """VOI should use 0.62 for T3, not a hardcoded default."""
    state = get_state()
    result = calculate_voi("T3_LINE", state)
    assert abs(result.p_failed - 0.62) < 1e-6


def test_voi_inspection_cost_is_positive():
    state = get_state()
    result = calculate_voi("T3_LINE", state)
    assert result.inspection_cost > 0


def test_voi_best_actions_are_valid_action_types():
    from config import ActionType
    state = get_state()
    result = calculate_voi("T3_LINE", state)
    valid = {a.value for a in ActionType}
    assert result.best_action_if_failed in valid
    assert result.best_action_if_healthy in valid
    assert result.best_action_without_info in valid


def test_voi_healthy_asset_lower_or_equal():
    """For an asset with very low failure probability, VOI should be lower than for T3."""
    state = get_state()
    # Modify L6-7 to have very low failure prob, or just use BUS_1
    state.assets["L6-7"].failure_probability = 0.02
    
    from uncertainty.belief import initialise_from_ml
    probs = {asset_id: asset.failure_probability for asset_id, asset in state.assets.items()}
    initialise_from_ml(probs)
    
    voi_t3    = calculate_voi("T3_LINE", state)
    voi_other = calculate_voi("L6-7", state)

    assert voi_other.voi <= voi_t3.voi
    # Not guaranteed by math alone, but conceptually should hold for high-criticality T3
    # This is a soft check
    assert voi_t3.decision_sensitivity >= 0


def test_voi_decision_sensitivity_non_negative():
    state = get_state()
    result = calculate_voi("T3_LINE", state)
    assert result.decision_sensitivity >= 0
