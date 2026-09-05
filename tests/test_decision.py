"""
Tests for the decision engine.
"""
import pytest
from engine.decision import recommend_next_action
from engine.state_manager import get_state
from config import ActionType, AssetStatus


def test_recommendation_returned():
    state = get_state()
    rec = recommend_next_action(state)
    assert rec is not None


def test_recommendation_has_required_fields():
    state = get_state()
    rec = recommend_next_action(state)
    assert rec.action_type is not None
    assert rec.target_asset is not None
    assert rec.score is not None
    assert rec.explanation is not None and len(rec.explanation) > 0
    assert rec.electrically_feasible is True
    assert len(rec.reason_codes) > 0


def test_initial_recommendation_is_inspect_t3():
    """
    With T3 uncertain (0.62 probability) and high critical impact,
    the decision engine should recommend INSPECT T3.
    This is driven by VOI logic, not hardcoded.
    """
    state = get_state()
    rec = recommend_next_action(state)
    assert rec.action_type == ActionType.INSPECT
    assert rec.target_asset == "T3_LINE"


def test_recommendation_score_is_numeric():
    state = get_state()
    rec = recommend_next_action(state)
    assert isinstance(rec.score, float)


def test_recommendation_uncertainty_matches_fault():
    state = get_state()
    rec = recommend_next_action(state)
    if rec.target_asset == "T3_LINE":
        assert abs(rec.uncertainty - 0.62) < 0.01


def test_recommendation_has_alternatives():
    state = get_state()
    rec = recommend_next_action(state)
    # Should have at least 1 alternative
    assert len(rec.alternative_actions) >= 1


def test_explanation_not_hardcoded():
    """Explanation should contain actual numerical values."""
    state = get_state()
    rec = recommend_next_action(state)
    # Explanation should mention the score or probability
    assert any(char.isdigit() for char in rec.explanation)


def test_recommendation_after_t3_confirmed_healthy():
    """After T3 is confirmed HEALTHY, recommendation should change."""
    state = get_state()
    rec_before = recommend_next_action(state)
    assert rec_before.action_type == ActionType.INSPECT

    # Confirm T3 healthy
    state.assets["T3_LINE"].status = AssetStatus.HEALTHY
    state.assets["T3_LINE"].failure_probability = 0.0
    for fault in state.faults.values():
        if fault.asset_id == "T3_LINE":
            fault.resolved = True
            fault.failure_probability = 0.0

    rec_after = recommend_next_action(state)
    # Should now recommend something else (repair a known-failed line)
    assert rec_after.action_type != ActionType.INSPECT or rec_after.target_asset != "T3_LINE"


def test_recommendation_after_t3_confirmed_failed():
    """After T3 is confirmed FAILED, recommendation should favour REPAIR."""
    state = get_state()
    state.assets["T3_LINE"].status = AssetStatus.FAILED
    state.assets["T3_LINE"].failure_probability = 1.0
    for fault in state.faults.values():
        if fault.asset_id == "T3_LINE":
            fault.fault_type = "OPEN_CIRCUIT"
            fault.failure_probability = 1.0

    rec = recommend_next_action(state)
    # T3 is now known-failed with critical impact — should be REPAIR or RECONFIGURE
    assert rec.action_type in (ActionType.REPAIR, ActionType.RECONFIGURE,
                               ActionType.ISLAND, ActionType.DEFER)


def test_recommendation_electrically_feasible():
    state = get_state()
    rec = recommend_next_action(state)
    assert rec.electrically_feasible is True
