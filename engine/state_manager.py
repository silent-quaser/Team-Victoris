"""
GridGuard — State Manager

Manages GridState: the mutable system state that evolves through
sequential recovery actions.

Key responsibilities:
    - Initialise state from a scenario
    - Execute actions (consume resources, update asset statuses)
    - Apply inspection results (resolve uncertainty)
    - Provide state snapshots for the decision engine
"""
from __future__ import annotations
from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List, Optional

from config import (
    ActionType, AssetStatus, ResourceType,
    INITIAL_RESOURCES, MOBILE_GENERATOR_CAPACITY_MW
)
from models.grid import AssetModel, FaultModel, GridStateModel, ResourceModel
from models.action import ActionModel


# Singleton state – replaced on reset
_STATE: Optional[GridStateModel] = None


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

def init_state(scenario: GridStateModel) -> GridStateModel:
    global _STATE
    _STATE = deepcopy(scenario)
    return _STATE


def get_state() -> GridStateModel:
    global _STATE
    if _STATE is None:
        raise RuntimeError("State not initialised. Call init_state() first.")
    return _STATE


def state_snapshot() -> GridStateModel:
    return deepcopy(get_state())


# ---------------------------------------------------------------------------
# Resource helpers
# ---------------------------------------------------------------------------

def _check_resources(action: ActionModel, state: GridStateModel) -> bool:
    for rtype in action.required_resources:
        if not state.resource_available(rtype):
            return False
    return True


def _consume_resources(action: ActionModel, state: GridStateModel) -> None:
    for rtype in action.required_resources:
        state.consume_resource(rtype)


def _release_resources(action: ActionModel, state: GridStateModel) -> None:
    for rtype in action.required_resources:
        state.release_resource(rtype)


# ---------------------------------------------------------------------------
# Action execution
# ---------------------------------------------------------------------------

def execute_action(action: ActionModel) -> Dict[str, Any]:
    """
    Execute an action against the current global state.

    Returns a dict with:
        success: bool
        message: str
        state_changes: list of changes applied
        new_state: GridStateModel snapshot
    """
    state = get_state()

    if not _check_resources(action, state):
        return {
            "success": False,
            "message": f"Insufficient resources for action {action.action_id}",
            "state_changes": [],
            "new_state": state_snapshot(),
        }

    _consume_resources(action, state)
    changes: List[str] = []
    asset_id = action.target_asset

    if action.action_type == ActionType.REPAIR:
        if asset_id in state.assets:
            state.assets[asset_id].status = AssetStatus.RESTORED
            state.assets[asset_id].failure_probability = 0.0
            changes.append(f"{asset_id} repaired → RESTORED")
        # Resolve associated fault
        for fid, fault in state.faults.items():
            if fault.asset_id == asset_id and not fault.resolved:
                fault.resolved = True
                fault.resolved_at = datetime.utcnow()
                changes.append(f"Fault {fid} resolved")

    elif action.action_type == ActionType.INSPECT:
        # Inspection is handled via POST /inspection; here just mark in-progress
        if asset_id in state.assets:
            changes.append(f"Inspection of {asset_id} dispatched")

    elif action.action_type == ActionType.RECONFIGURE:
        if asset_id in state.assets:
            state.assets[asset_id].status = AssetStatus.DEGRADED
            changes.append(f"{asset_id} reconfigured → DEGRADED (partial)")
        state.topology_changes.append(f"RECONFIGURE:{asset_id}")

    elif action.action_type == ActionType.ISLAND:
        if asset_id in state.assets:
            state.assets[asset_id].status = AssetStatus.ISOLATED
            changes.append(f"{asset_id} islanded → ISOLATED")
        state.topology_changes.append(f"ISLAND:{asset_id}")

    elif action.action_type == ActionType.RESTORE:
        if asset_id in state.assets:
            state.assets[asset_id].status = AssetStatus.RESTORED
            state.assets[asset_id].failure_probability = 0.0
            changes.append(f"{asset_id} restored → RESTORED")

    elif action.action_type == ActionType.DEFER:
        changes.append(f"Action deferred for {asset_id}")
        # Resources not consumed on defer
        _release_resources(action, state)

    # Sync with physical grid
    from grid.grid_engine import execute_simulated_action
    execute_simulated_action(action.action_type.value, asset_id)

    # Update step counter
    state.step += 1
    state.timestamp = datetime.utcnow()

    # Recalculate restoration progress
    _update_restoration_progress(state)

    return {
        "success": True,
        "message": f"Action {action.action_type} on {asset_id} executed",
        "state_changes": changes,
        "new_state": state_snapshot(),
    }


# ---------------------------------------------------------------------------
# Inspection result application
# ---------------------------------------------------------------------------

def apply_inspection_result(
    asset_id: str,
    result: str,             # "FAILED" or "HEALTHY"
    inspection_notes: str = ""
) -> Dict[str, Any]:
    """
    Apply the outcome of an inspection, resolving uncertainty for asset_id.
    Returns release of inspection drone resource and updated state.
    """
    state = get_state()
    changes: List[str] = []

    if result == "FAILED":
        if asset_id in state.assets:
            state.assets[asset_id].status = AssetStatus.FAILED
            state.assets[asset_id].failure_probability = 1.0
            changes.append(f"{asset_id} confirmed FAILED after inspection")
        for fid, fault in state.faults.items():
            if fault.asset_id == asset_id:
                fault.fault_type = "OPEN_CIRCUIT"
                fault.failure_probability = 1.0
                changes.append(f"Fault {fid} confirmed as OPEN_CIRCUIT")

    elif result == "HEALTHY":
        if asset_id in state.assets:
            state.assets[asset_id].status = AssetStatus.HEALTHY
            state.assets[asset_id].failure_probability = 0.0
            changes.append(f"{asset_id} confirmed HEALTHY after inspection")
        for fid, fault in state.faults.items():
            if fault.asset_id == asset_id:
                fault.resolved = True
                fault.resolved_at = datetime.utcnow()
                fault.failure_probability = 0.0
                changes.append(f"Fault {fid} cleared (asset healthy)")

    # Release inspection drone
    state.release_resource(ResourceType.INSPECTION_DRONE)
    changes.append("Inspection drone released")

    state.step += 1
    state.timestamp = datetime.utcnow()
    _update_restoration_progress(state)

    return {
        "success": True,
        "message": f"Inspection of {asset_id}: {result}",
        "state_changes": changes,
        "new_state": state_snapshot(),
    }


# ---------------------------------------------------------------------------
# Restoration progress
# ---------------------------------------------------------------------------

def _update_restoration_progress(state: GridStateModel) -> None:
    """Recalculate restored_load_mw and restoration_pct from the actual power flow."""
    from impact.calculator import calculate_grid_impact
    from grid.grid_engine import get_net
    
    impact = calculate_grid_impact(get_net(), run_pf=True)
    state.total_load_mw = impact["total_load_mw"]
    state.restored_load_mw = impact["mw_served"]
    state.restoration_pct = impact["restoration_pct"]

def _is_powered(node_id: str, state: GridStateModel) -> bool:
    """Deprecated, replaced by power flow."""
    return True


# ---------------------------------------------------------------------------
# Fault injection
# ---------------------------------------------------------------------------

def inject_fault(
    asset_id: str,
    fault_type: str,
    failure_probability: float,
    fault_id: Optional[str] = None,
) -> FaultModel:
    state = get_state()
    fid = fault_id or f"FAULT_{asset_id}_{int(datetime.utcnow().timestamp())}"

    fault = FaultModel(
        fault_id=fid,
        asset_id=asset_id,
        fault_type=fault_type,
        failure_probability=failure_probability,
    )
    state.faults[fid] = fault

    # Update asset status
    if asset_id in state.assets:
        if fault_type == "UNCERTAIN":
            state.assets[asset_id].status = AssetStatus.UNCERTAIN
            state.assets[asset_id].failure_probability = failure_probability
        else:
            state.assets[asset_id].status = AssetStatus.FAILED
            state.assets[asset_id].failure_probability = 1.0

    state.step += 1
    
    # Sync physical fault
    from grid.grid_engine import inject_fault as phys_inject
    phys_inject(asset_id, fault_type, failure_probability, fault_type == "UNCERTAIN")
    
    _update_restoration_progress(state)
    return fault
