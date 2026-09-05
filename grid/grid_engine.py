"""
GridGuard — Grid Engine

Central controller for the IEEE 33-bus simulation.
Provides the clean API that P3's decision engine calls.

Key functions:
    create_grid()                   → fresh pandapower net
    reset_grid()                    → reset to base state
    inject_fault(asset_id, ...)     → mark line/bus as failed
    get_grid_state()                → structured dict of current state
    execute_simulated_action(action)→ apply action to simulation
    get_asset_status(asset_id)      → status of a single asset
"""
from __future__ import annotations
import warnings
from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import pandapower as pp
import numpy as np

from grid.ieee33 import (
    build_ieee33_net, LINE_ASSET_MAP, T3_LINE_IDX,
    get_critical_service_buses, CRITICAL_SERVICE_LOADS
)

# ---------------------------------------------------------------------------
# Singleton network
# ---------------------------------------------------------------------------
_NET: Optional[pp.pandapowerNet] = None
_FAULT_HISTORY: List[Dict] = []


def create_grid() -> pp.pandapowerNet:
    """Create a fresh IEEE 33-bus network and set as the active singleton."""
    global _NET, _FAULT_HISTORY
    _NET = build_ieee33_net()
    _FAULT_HISTORY = []
    return _NET


def reset_grid() -> pp.pandapowerNet:
    """Reset the active grid to its base state (no faults)."""
    return create_grid()


def get_net() -> pp.pandapowerNet:
    """Return the active network, creating it if needed."""
    global _NET
    if _NET is None:
        _NET = build_ieee33_net()
    return _NET


# ---------------------------------------------------------------------------
# Fault injection
# ---------------------------------------------------------------------------

def inject_fault(
    asset_id: str,
    fault_type: str = "OPEN_CIRCUIT",
    failure_probability: float = 1.0,
    is_uncertain: bool = False,
) -> Dict[str, Any]:
    """
    Inject a fault into the active IEEE 33-bus network.

    Parameters
    ----------
    asset_id:            Asset identifier (e.g. 'L6-7', 'T3_LINE', 'LINE_5')
    fault_type:          OPEN_CIRCUIT | SHORT_CIRCUIT | UNCERTAIN
    failure_probability: Prior probability of failure [0,1]
    is_uncertain:        True if the state is observed with uncertainty

    Returns dict with outcome information.
    """
    net = get_net()
    applied = []

    # Resolve asset_id → line index
    line_idx = _resolve_asset_to_line(asset_id)

    if line_idx is not None:
        if fault_type in ("OPEN_CIRCUIT",) or (not is_uncertain and failure_probability >= 0.95):
            net.line.at[line_idx, "in_service"] = False
            applied.append(f"Line {line_idx} ({asset_id}) set out of service")

        net.line.at[line_idx, "failure_probability"] = failure_probability
        net.line.at[line_idx, "is_uncertain"] = is_uncertain

    fault_record = {
        "asset_id": asset_id,
        "fault_type": fault_type,
        "failure_probability": failure_probability,
        "is_uncertain": is_uncertain,
        "timestamp": datetime.utcnow().isoformat(),
        "line_idx": line_idx,
    }
    _FAULT_HISTORY.append(fault_record)

    return {
        "success": True,
        "asset_id": asset_id,
        "applied": applied,
        "fault_record": fault_record,
    }


def _resolve_asset_to_line(asset_id: str) -> Optional[int]:
    """Map asset_id string to pandapower line DataFrame index."""
    net = get_net()

    # Direct match in LINE_ASSET_MAP (reversed)
    reverse_map = {v: k for k, v in LINE_ASSET_MAP.items()}
    if asset_id in reverse_map:
        return reverse_map[asset_id]

    # Match by asset_id column
    if "asset_id" in net.line.columns:
        matches = net.line[net.line["asset_id"] == asset_id]
        if not matches.empty:
            return matches.index[0]

    # Match by 'LINE_N' convention
    if asset_id.startswith("LINE_"):
        try:
            idx = int(asset_id.split("_")[1])
            if 0 <= idx < len(net.line):
                return idx
        except (IndexError, ValueError):
            pass

    return None


# ---------------------------------------------------------------------------
# Grid state
# ---------------------------------------------------------------------------

def get_grid_state() -> Dict[str, Any]:
    """
    Return a comprehensive structured state of the current IEEE 33-bus network.
    Includes bus voltages, line statuses, loads, faults, and critical services.
    """
    net = get_net()

    # Run power flow (silently)
    pf_converged = False
    pf_result: Dict = {}
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            pp.runpp(net, numba=False, verbose=False, algorithm="nr")
        pf_converged = True
        pf_result = _extract_pf_results(net)
    except Exception as e:
        pf_result = {"error": str(e)}

    # Lines
    lines = []
    for idx, row in net.line.iterrows():
        line_entry = {
            "line_idx": int(idx),
            "asset_id": row.get("asset_id", f"LINE_{idx}"),
            "from_bus": int(row["from_bus"]),
            "to_bus": int(row["to_bus"]),
            "in_service": bool(row["in_service"]),
            "failure_probability": float(row.get("failure_probability", 0.0)),
            "is_uncertain": bool(row.get("is_uncertain", False)),
        }
        if pf_converged and idx in net.res_line.index:
            line_entry["loading_pct"] = round(float(net.res_line.at[idx, "loading_percent"]), 2)
            line_entry["i_ka"] = round(float(net.res_line.at[idx, "i_ka"]), 4)
        lines.append(line_entry)

    # Buses
    buses = []
    for idx, row in net.bus.iterrows():
        bus_entry = {
            "bus_idx": int(idx),
            "vn_kv": float(row["vn_kv"]),
            "in_service": bool(row.get("in_service", True)),
        }
        if pf_converged and idx in net.res_bus.index:
            bus_entry["vm_pu"] = round(float(net.res_bus.at[idx, "vm_pu"]), 4)
            bus_entry["va_degree"] = round(float(net.res_bus.at[idx, "va_degree"]), 4)
        buses.append(bus_entry)

    # Loads
    loads = []
    for idx, row in net.load.iterrows():
        load_entry = {
            "load_idx": int(idx),
            "bus": int(row["bus"]),
            "p_mw": float(row["p_mw"]),
            "q_mvar": float(row["q_mvar"]),
            "name": str(row.get("name", f"LOAD_{idx}")),
            "critical_service": bool(row.get("critical_service", False)),
            "service_id": str(row.get("service_id", "")),
            "in_service": bool(row.get("in_service", True)),
        }
        loads.append(load_entry)

    # Active faults
    faulted_lines = net.line[~net.line["in_service"]].index.tolist()
    uncertain_lines = net.line[net.line.get("is_uncertain", False) == True].index.tolist() if "is_uncertain" in net.line.columns else []

    # Critical service status
    critical_status = _get_critical_service_status(net, pf_converged)

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "pf_converged": pf_converged,
        "pf_result": pf_result,
        "buses": buses,
        "lines": lines,
        "loads": loads,
        "faulted_line_indices": faulted_lines,
        "uncertain_line_indices": uncertain_lines,
        "fault_history": _FAULT_HISTORY,
        "critical_services": critical_status,
        "total_load_mw": round(float(net.load[net.load["in_service"] == True]["p_mw"].sum()), 3),
    }


def _extract_pf_results(net: pp.pandapowerNet) -> Dict[str, Any]:
    """Extract key power flow results."""
    return {
        "vm_pu_min": round(float(net.res_bus["vm_pu"].min()), 4),
        "vm_pu_max": round(float(net.res_bus["vm_pu"].max()), 4),
        "line_loading_max_pct": round(float(net.res_line["loading_percent"].max()), 2),
        "total_load_mw": round(float(net.res_load["p_mw"].sum()), 3),
        "total_gen_mw": round(float(net.res_ext_grid["p_mw"].sum()), 3),
        "losses_mw": round(float(net.res_line["pl_mw"].sum()), 4),
    }


def _get_critical_service_status(
    net: pp.pandapowerNet, pf_converged: bool
) -> Dict[str, Any]:
    """Determine which critical services are energised."""
    svc_buses = get_critical_service_buses(net)
    status = {}
    for svc_id, bus_idx in svc_buses.items():
        powered = _is_bus_energised(net, bus_idx, pf_converged)
        load_row = net.load[net.load["service_id"] == svc_id]
        p_mw = float(load_row["p_mw"].sum()) if not load_row.empty else 0.0
        status[svc_id] = {
            "bus": int(bus_idx),
            "energised": powered,
            "p_mw": p_mw,
            "status": "ONLINE" if powered else "OFFLINE",
        }
    return status


def _is_bus_energised(
    net: pp.pandapowerNet, bus_idx: int, pf_converged: bool
) -> bool:
    """Check if a bus is energised (simplified: check connectivity)."""
    if pf_converged:
        try:
            vm = net.res_bus.at[bus_idx, "vm_pu"]
            return not (np.isnan(vm) or vm < 0.5)
        except Exception:
            pass
    # Fallback: check if any upstream line feeding this bus is out of service
    upstream_lines = net.line[net.line["to_bus"] == bus_idx]
    if upstream_lines.empty:
        return True  # Slack bus / direct connection
    return bool(upstream_lines["in_service"].any())


# ---------------------------------------------------------------------------
# Action execution
# ---------------------------------------------------------------------------

def execute_simulated_action(action: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply an action to the IEEE 33-bus simulation.

    Supported action types:
        REPAIR      → set line in_service=True, failure_prob=0
        INSPECT     → no topology change (uncertainty resolved externally)
        RECONFIGURE → open/close switches to bypass a faulted line
        ISLAND      → disconnect a bus segment from the main grid
        RESTORE     → re-energise a previously isolated segment
        DEFER       → no change

    Returns dict with changes applied and updated PF result.
    """
    net = get_net()
    action_type = action.get("action_type", "DEFER")
    asset_id = action.get("target_asset", "")
    changes = []

    if action_type == "REPAIR":
        line_idx = _resolve_asset_to_line(asset_id)
        if line_idx is not None:
            net.line.at[line_idx, "in_service"] = True
            net.line.at[line_idx, "failure_probability"] = 0.0
            net.line.at[line_idx, "is_uncertain"] = False
            changes.append(f"LINE {line_idx} ({asset_id}) restored to service")
            # Remove from fault history
            global _FAULT_HISTORY
            _FAULT_HISTORY = [f for f in _FAULT_HISTORY if f["asset_id"] != asset_id]

    elif action_type == "RECONFIGURE":
        line_idx = _resolve_asset_to_line(asset_id)
        if line_idx is not None:
            # Try to close a tie switch to restore power
            for sw_idx, sw_row in net.switch.iterrows():
                if not sw_row["closed"]:
                    net.switch.at[sw_idx, "closed"] = True
                    changes.append(f"Tie switch {sw_idx} closed for reconfiguration")
                    break

    elif action_type == "ISLAND":
        # Disconnect all lines feeding the bus associated with asset
        line_idx = _resolve_asset_to_line(asset_id)
        if line_idx is not None:
            bus = int(net.line.at[line_idx, "to_bus"])
            downstream_lines = net.line[
                (net.line["from_bus"] == bus) | (net.line["to_bus"] == bus)
            ]
            for dl_idx in downstream_lines.index:
                net.line.at[dl_idx, "in_service"] = False
            changes.append(f"Bus {bus} islanded (all connecting lines opened)")

    elif action_type in ("DEFER", "INSPECT"):
        changes.append(f"Action {action_type} — no topology change")

    # Re-run power flow
    pf_ok = False
    pf_result = {}
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            pp.runpp(net, numba=False, verbose=False)
        pf_ok = True
        pf_result = _extract_pf_results(net)
    except Exception as e:
        pf_result = {"error": str(e)}

    return {
        "success": True,
        "action_type": action_type,
        "target_asset": asset_id,
        "changes": changes,
        "pf_converged": pf_ok,
        "pf_result": pf_result,
        "critical_services": _get_critical_service_status(net, pf_ok),
    }


def get_asset_status(asset_id: str) -> Dict[str, Any]:
    """Return status of a single asset."""
    net = get_net()
    line_idx = _resolve_asset_to_line(asset_id)
    if line_idx is None:
        return {"asset_id": asset_id, "found": False}
    row = net.line.loc[line_idx]
    return {
        "asset_id": asset_id,
        "found": True,
        "line_idx": int(line_idx),
        "in_service": bool(row["in_service"]),
        "failure_probability": float(row.get("failure_probability", 0.0)),
        "is_uncertain": bool(row.get("is_uncertain", False)),
        "from_bus": int(row["from_bus"]),
        "to_bus": int(row["to_bus"]),
    }
