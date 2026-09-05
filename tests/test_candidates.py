"""
Tests for the candidate action generator.
"""
import pytest
from engine.candidate_generator import generate_candidates
from engine.state_manager import get_state
from config import ActionType, ResourceType, AssetStatus


def test_candidates_generated():
    state = get_state()
    candidates = generate_candidates(state)
    assert len(candidates) > 0


def test_inspect_t3_generated():
    """T3 is UNCERTAIN and drone is available → INSPECT should be generated."""
    state = get_state()
    candidates = generate_candidates(state)
    inspect_t3 = [
        c for c in candidates
        if c.action_type == ActionType.INSPECT and c.target_asset == "T3_LINE"
    ]
    assert len(inspect_t3) >= 1


def test_repair_candidates_for_failed_assets():
    """Failed lines should get REPAIR candidates if crew is available."""
    state = get_state()
    candidates = generate_candidates(state)
    repair_actions = [c for c in candidates if c.action_type == ActionType.REPAIR]
    assert len(repair_actions) > 0


def test_defer_always_present():
    state = get_state()
    candidates = generate_candidates(state)
    defer = [c for c in candidates if c.action_type == ActionType.DEFER]
    assert len(defer) >= 1


def test_inspect_not_generated_without_drone():
    """If drone is unavailable, INSPECT should not be generated."""
    state = get_state()
    # Deplete the drone
    state.resources[ResourceType.INSPECTION_DRONE].available = 0
    state.resources[ResourceType.INSPECTION_DRONE].in_use = 1
    candidates = generate_candidates(state)
    inspect = [c for c in candidates if c.action_type == ActionType.INSPECT]
    assert len(inspect) == 0


def test_repair_not_generated_without_crew():
    """If all crews are busy, REPAIR should not be generated."""
    state = get_state()
    state.resources[ResourceType.REPAIR_CREW].available = 0
    state.resources[ResourceType.REPAIR_CREW].in_use = 2
    candidates = generate_candidates(state)
    repair = [c for c in candidates if c.action_type == ActionType.REPAIR]
    assert len(repair) == 0


def test_reconfigure_for_failed_lines():
    state = get_state()
    candidates = generate_candidates(state)
    reconfig = [c for c in candidates if c.action_type == ActionType.RECONFIGURE]
    assert len(reconfig) > 0


def test_candidate_has_required_fields():
    state = get_state()
    candidates = generate_candidates(state)
    for c in candidates:
        assert c.action_id is not None and len(c.action_id) > 0
        assert c.action_type is not None
        assert c.target_asset is not None
        assert c.estimated_time_minutes >= 0
        assert 0.0 <= c.risk_score <= 1.0
        assert 0.0 <= c.reversibility <= 1.0


def test_island_candidate_only_for_small_loads():
    """ISLAND should only appear when downstream load ≤ 2.5 MW (mobile gen capacity)."""
    state = get_state()
    candidates = generate_candidates(state)
    island = [c for c in candidates if c.action_type == ActionType.ISLAND]
    for c in island:
        assert c.expected_benefit_mw <= 2.5


def test_uncertainty_dependence_for_inspect():
    state = get_state()
    candidates = generate_candidates(state)
    inspect = [c for c in candidates if c.action_type == ActionType.INSPECT]
    for c in inspect:
        assert c.uncertainty_dependence == 1.0
