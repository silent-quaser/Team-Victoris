"""
Tests for the electrical feasibility engine (pandapower).
"""
import pytest
from engine.feasibility import validate_action, check_island_feasibility, get_network_status
from engine.state_manager import get_state
from engine.candidate_generator import generate_candidates
from config import ActionType


def test_network_status_returns_dict():
    state = get_state()
    status = get_network_status(state)
    assert isinstance(status, dict)
    assert "available" in status


def test_inspect_action_always_feasible():
    """INSPECT is never electrically infeasible."""
    state = get_state()
    candidates = generate_candidates(state)
    inspect = [c for c in candidates if c.action_type == ActionType.INSPECT]
    for c in inspect:
        feasible, reason = validate_action(c, state)
        assert feasible is True


def test_defer_always_feasible():
    state = get_state()
    candidates = generate_candidates(state)
    defer = [c for c in candidates if c.action_type == ActionType.DEFER]
    for c in defer:
        feasible, reason = validate_action(c, state)
        assert feasible is True


def test_island_feasibility_check_small_load():
    """Small load (< 2.5 MW) downstream should be feasible to island."""
    feasible, reason = check_island_feasibility("L25-26", get_state())
    # Telecom Tower is 0.8 MW → feasible
    assert feasible is True


def test_island_feasibility_check_large_load():
    """Large load (> 2.5 MW) downstream should be infeasible to island."""
    feasible, reason = check_island_feasibility("FEEDER_B", get_state())
    # FEEDER_B feeds multiple large loads → exceeds 2.5 MW
    assert feasible is False


def test_validate_repair_runs_without_exception():
    state = get_state()
    candidates = generate_candidates(state)
    repair = next(
        (c for c in candidates if c.action_type == ActionType.REPAIR),
        None
    )
    if repair:
        feasible, reason = validate_action(repair, state)
        assert isinstance(feasible, bool)
        assert isinstance(reason, str)
