"""
Tests for the state manager: execute_action, apply_inspection_result, inject_fault.
"""
import pytest
from engine.state_manager import (
    get_state, execute_action, apply_inspection_result, inject_fault, state_snapshot
)
from engine.candidate_generator import generate_candidates
from config import ActionType, AssetStatus, ResourceType


def test_state_initialised():
    state = get_state()
    assert state is not None
    assert state.scenario_id is not None
    assert len(state.faults) == 4  # demo has 4 faults


def test_inspection_result_failed_resolves_uncertainty():
    state = get_state()
    assert state.assets["T3_LINE"].status == AssetStatus.UNCERTAIN

    result = apply_inspection_result("T3_LINE", "FAILED")
    assert result["success"] is True

    state_after = result["new_state"]
    assert state_after.assets["T3_LINE"].status == AssetStatus.FAILED
    assert state_after.assets["T3_LINE"].failure_probability == 1.0


def test_inspection_result_healthy_resolves_uncertainty():
    result = apply_inspection_result("T3_LINE", "HEALTHY")
    assert result["success"] is True

    state_after = result["new_state"]
    assert state_after.assets["T3_LINE"].status == AssetStatus.HEALTHY
    assert state_after.assets["T3_LINE"].failure_probability == 0.0


def test_inspection_releases_drone():
    state = get_state()
    # Consume the drone first
    state.consume_resource(ResourceType.INSPECTION_DRONE)
    assert state.resources[ResourceType.INSPECTION_DRONE].available == 0

    apply_inspection_result("T3_LINE", "FAILED")
    state_after = get_state()
    assert state_after.resources[ResourceType.INSPECTION_DRONE].available == 1


def test_execute_repair_action():
    state = get_state()
    candidates = generate_candidates(state)
    repair = next(
        (c for c in candidates if c.action_type == ActionType.REPAIR and c.target_asset == "L6-7"),
        None
    )
    assert repair is not None, "REPAIR L6-7 should be a candidate"

    result = execute_action(repair)
    assert result["success"] is True
    state_after = result["new_state"]
    assert state_after.assets["L6-7"].status == AssetStatus.RESTORED


def test_execute_action_increments_step():
    state = get_state()
    step_before = state.step
    candidates = generate_candidates(state)
    repair = next(
        (c for c in candidates if c.action_type == ActionType.REPAIR),
        None
    )
    if repair:
        execute_action(repair)
        assert get_state().step == step_before + 1


def test_execute_consumes_resources():
    state = get_state()
    crews_before = state.resources[ResourceType.REPAIR_CREW].available
    candidates = generate_candidates(state)
    repair = next(
        (c for c in candidates if c.action_type == ActionType.REPAIR),
        None
    )
    if repair:
        execute_action(repair)
        state_after = get_state()
        assert state_after.resources[ResourceType.REPAIR_CREW].available == crews_before - 1


def test_inject_fault():
    state = get_state()
    faults_before = len(state.faults)
    fault = inject_fault("LINE_3", "OPEN_CIRCUIT", 1.0)
    state_after = get_state()
    assert len(state_after.faults) == faults_before + 1
    assert state_after.assets["LINE_3"].status == AssetStatus.FAILED


def test_state_snapshot_is_independent():
    """Snapshot should not be affected by subsequent state changes."""
    snap = state_snapshot()
    state = get_state()
    state.step += 100
    assert snap.step != state.step
