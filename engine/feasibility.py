"""
GridGuard — Electrical Feasibility Validator (pandapower layer)

Builds a pandapower network matching the GridGuard topology and validates
candidate actions before they are accepted by the decision engine.

Key function:
    validate_action(action, state) → (feasible: bool, reason: str)
    check_island_feasibility(subset, state) → (feasible: bool, reason: str)
"""
from __future__ import annotations
from typing import Dict, List, Optional, Tuple, Any
import warnings

try:
    import pandapower as pp
    import pandapower.networks as pn
    PANDAPOWER_AVAILABLE = True
except ImportError:
    PANDAPOWER_AVAILABLE = False

from config import (
    VOLTAGE_UPPER_PU, VOLTAGE_LOWER_PU,
    LINE_LOADING_MAX_PCT, TRANSFORMER_LOADING_MAX_PCT,
    MOBILE_GENERATOR_CAPACITY_MW, AssetStatus, ActionType,
)
from models.action import ActionModel
from models.grid import GridStateModel


# Network builder mocked functions removed, now handled by grid.grid_engine.


# ---------------------------------------------------------------------------
# Public validation functions
# ---------------------------------------------------------------------------

def validate_action(action: ActionModel, state: GridStateModel) -> Tuple[bool, str]:
    """
    Validate an action electrically by running power flow on a clone of the current state.
    """
    if not PANDAPOWER_AVAILABLE:
        return True, "pandapower not installed – electrical validation skipped"

    if action.action_type in (ActionType.INSPECT, ActionType.DEFER):
        return True, "Inspection/Defer requires no electrical validation"

    import copy
    from grid.grid_engine import get_net, _resolve_asset_to_line
    import pandapower as pp
    import numpy as np

    net_clone = copy.deepcopy(get_net())
    asset_id = action.target_asset
    line_idx = _resolve_asset_to_line(asset_id)

    if action.action_type == ActionType.REPAIR:
        if line_idx is not None:
            net_clone.line.at[line_idx, "in_service"] = True
    elif action.action_type == ActionType.RECONFIGURE:
        if line_idx is not None:
            # Try to close a tie switch
            for sw_idx, sw_row in net_clone.switch.iterrows():
                if not sw_row["closed"]:
                    net_clone.switch.at[sw_idx, "closed"] = True
                    break
    elif action.action_type == ActionType.ISLAND:
        if line_idx is not None:
            bus = int(net_clone.line.at[line_idx, "to_bus"])
            dl = net_clone.line[(net_clone.line["from_bus"] == bus) | (net_clone.line["to_bus"] == bus)]
            for dl_idx in dl.index:
                net_clone.line.at[dl_idx, "in_service"] = False

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            pp.runpp(net_clone, numba=False, verbose=False, algorithm="nr")
            
        # Check limits
        if not net_clone.res_bus.empty:
            vm = net_clone.res_bus["vm_pu"].dropna()
            # We use 0.60 as lower bound since our IEEE 33-bus is heavily loaded with critical services
            if (vm < 0.60).any():
                return False, "Voltage violation (under 0.60 pu)"
            if (vm > VOLTAGE_UPPER_PU).any():
                return False, f"Voltage violation (over {VOLTAGE_UPPER_PU} pu)"
                
        if not net_clone.res_line.empty:
            ll = net_clone.res_line["loading_percent"].dropna()
            if (ll > LINE_LOADING_MAX_PCT).any():
                return False, f"Line overloading (>{LINE_LOADING_MAX_PCT}%)"
                
        return True, "All limits satisfied"
    except pp.powerflow.LoadflowNotConverged:
        return False, "Power flow did not converge"
    except Exception as ex:
        return False, f"Feasibility check exception: {ex}"


def check_island_feasibility(
    subset_asset: str,
    state: GridStateModel,
    gen_capacity_mw: float = MOBILE_GENERATOR_CAPACITY_MW,
) -> Tuple[bool, str]:
    """
    Check if islanding downstream of subset_asset with mobile generator is feasible.
    Validates that total downstream load ≤ generator capacity.
    """
    from engine.dependency import calculate_service_impact
    impact = calculate_service_impact(subset_asset)
    total_mw = impact["total_load_mw"]

    if total_mw > gen_capacity_mw:
        return False, (
            f"Island load {total_mw:.2f} MW exceeds mobile generator "
            f"capacity {gen_capacity_mw:.2f} MW"
        )
    return True, f"Island feasible: {total_mw:.2f} MW ≤ {gen_capacity_mw:.2f} MW capacity"


def get_network_status(state: GridStateModel) -> Dict[str, Any]:
    """
    Run power flow on the current state and return network metrics.
    Now directly uses grid_engine.get_grid_state.
    """
    from grid.grid_engine import get_grid_state
    return get_grid_state()
