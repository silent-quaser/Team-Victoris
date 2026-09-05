"""
GridGuard — Power Flow Validation Module

Wraps pandapower power flow execution with:
    - Voltage violation detection (< 0.95 or > 1.05 pu)
    - Line overload detection (> 100% rated current)
    - Convergence checking
    - Feasibility verdict for candidate recovery actions

Main functions:
    run_power_flow()           → run PF on current network, return results
    get_voltage_violations()   → list of buses with V outside [0.95, 1.05]
    get_line_overloads()       → list of lines loaded > threshold %
    check_grid_feasibility()   → True/False + reason string
    simulate_action_pf(action) → copy net, apply action, check feasibility
"""
from __future__ import annotations
import warnings
from copy import deepcopy
from typing import Any, Dict, List, Optional, Tuple

import pandapower as pp
import numpy as np

from grid.ieee33 import build_ieee33_net

# Voltage limits (per-unit)
V_MIN_PU = 0.95
V_MAX_PU = 1.05
LINE_LOADING_MAX_PCT = 100.0
TRANSFORMER_LOADING_MAX_PCT = 100.0


def run_power_flow(net: Optional[pp.pandapowerNet] = None) -> Dict[str, Any]:
    """
    Run Newton-Raphson AC power flow on the given (or active singleton) network.

    Returns
    -------
    dict with:
        converged    (bool)
        vm_pu        (list of voltage magnitudes per bus)
        loading_pct  (list of line loading percentages)
        violations   (dict of voltage/overload violations)
        summary      (dict of key metrics)
    """
    from grid.grid_engine import get_net
    if net is None:
        net = get_net()

    result: Dict[str, Any] = {"converged": False}

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            pp.runpp(net, numba=False, verbose=False, algorithm="nr")

        result["converged"] = True
        result["vm_pu"] = net.res_bus["vm_pu"].tolist()
        result["va_degree"] = net.res_bus["va_degree"].tolist()
        result["loading_pct"] = net.res_line["loading_percent"].tolist()
        result["i_ka"] = net.res_line["i_ka"].tolist()
        result["pl_mw"] = float(net.res_line["pl_mw"].sum())
        result["summary"] = {
            "vm_min": float(net.res_bus["vm_pu"].min()),
            "vm_max": float(net.res_bus["vm_pu"].max()),
            "loading_max": float(net.res_line["loading_percent"].max()),
            "total_loss_mw": float(net.res_line["pl_mw"].sum()),
            "total_gen_mw": float(net.res_ext_grid["p_mw"].sum()),
        }
        result["violations"] = _collect_violations(net)

    except pp.powerflow.LoadflowNotConverged:
        result["converged"] = False
        result["error"] = "LoadflowNotConverged"
        result["violations"] = {"convergence": "Power flow did not converge"}

    except Exception as e:
        result["converged"] = False
        result["error"] = str(e)
        result["violations"] = {}

    return result


def get_voltage_violations(net: Optional[pp.pandapowerNet] = None) -> List[Dict]:
    """
    Return list of buses with voltage outside [V_MIN_PU, V_MAX_PU].
    Assumes power flow has already been run.
    """
    from grid.grid_engine import get_net
    if net is None:
        net = get_net()

    if net.res_bus.empty:
        return []

    violations = []
    for idx, row in net.res_bus.iterrows():
        vm = row["vm_pu"]
        if np.isnan(vm):
            violations.append({"bus": int(idx), "vm_pu": None, "type": "DISCONNECTED"})
        elif vm < V_MIN_PU:
            violations.append({"bus": int(idx), "vm_pu": round(float(vm), 4),
                                "type": "UNDERVOLTAGE", "limit": V_MIN_PU})
        elif vm > V_MAX_PU:
            violations.append({"bus": int(idx), "vm_pu": round(float(vm), 4),
                                "type": "OVERVOLTAGE", "limit": V_MAX_PU})
    return violations


def get_line_overloads(
    net: Optional[pp.pandapowerNet] = None,
    threshold_pct: float = LINE_LOADING_MAX_PCT,
) -> List[Dict]:
    """Return list of lines with loading_percent > threshold."""
    from grid.grid_engine import get_net
    if net is None:
        net = get_net()

    if net.res_line.empty:
        return []

    overloads = []
    for idx, row in net.res_line.iterrows():
        loading = row["loading_percent"]
        if loading > threshold_pct:
            asset_id = net.line.at[idx, "asset_id"] if "asset_id" in net.line.columns else f"LINE_{idx}"
            overloads.append({
                "line_idx": int(idx),
                "asset_id": asset_id,
                "loading_pct": round(float(loading), 2),
                "limit_pct": threshold_pct,
            })
    return overloads


def check_grid_feasibility(
    net: Optional[pp.pandapowerNet] = None,
) -> Tuple[bool, str]:
    """
    Check if the current grid state is electrically feasible.

    Returns (feasible: bool, reason: str)
    """
    from grid.grid_engine import get_net
    if net is None:
        net = get_net()

    pf = run_power_flow(net)
    if not pf["converged"]:
        return False, f"Power flow did not converge: {pf.get('error', 'unknown')}"

    v_violations = get_voltage_violations(net)
    if v_violations:
        worst = min(
            (v for v in v_violations if v.get("vm_pu") is not None),
            key=lambda v: abs(v["vm_pu"] - 1.0),
            default=None
        )
        if worst:
            return False, (
                f"Voltage violation at bus {worst['bus']}: "
                f"{worst['vm_pu']:.4f} pu ({worst['type']})"
            )

    overloads = get_line_overloads(net)
    if overloads:
        worst = max(overloads, key=lambda x: x["loading_pct"])
        return False, (
            f"Line overload: {worst['asset_id']} at "
            f"{worst['loading_pct']:.1f}% (limit {worst['limit_pct']:.0f}%)"
        )

    return True, "All electrical constraints satisfied"


def simulate_action_pf(
    action: Dict[str, Any],
    base_net: Optional[pp.pandapowerNet] = None,
) -> Tuple[bool, str, Dict]:
    """
    Create a network copy, apply action, run PF, check feasibility.
    Used by the decision engine to pre-validate actions without modifying state.

    Returns (feasible, reason, pf_results)
    """
    from grid.grid_engine import get_net, _resolve_asset_to_line
    if base_net is None:
        base_net = get_net()

    # Deep copy to avoid mutation
    test_net = deepcopy(base_net)
    action_type = action.get("action_type", "DEFER")
    asset_id = action.get("target_asset", "")

    # INSPECT and DEFER never change topology
    if action_type in ("INSPECT", "DEFER"):
        return True, f"{action_type} has no electrical impact", {}

    # Apply action to test network
    if action_type == "REPAIR":
        line_idx = _resolve_asset_to_line(asset_id)
        if line_idx is not None:
            test_net.line.at[line_idx, "in_service"] = True

    elif action_type == "RECONFIGURE":
        # Try closing a tie switch
        for sw_idx in test_net.switch.index:
            if not test_net.switch.at[sw_idx, "closed"]:
                test_net.switch.at[sw_idx, "closed"] = True
                break

    # Run feasibility check on the test network
    pf_results = run_power_flow(test_net)
    if not pf_results["converged"]:
        return False, "Power flow did not converge after action", pf_results

    v_viol = get_voltage_violations(test_net)
    overloads = get_line_overloads(test_net)

    if v_viol:
        return False, f"Voltage violation after {action_type}", pf_results
    if overloads:
        return False, f"Line overload after {action_type}", pf_results

    return True, f"Action {action_type} is electrically feasible", pf_results


def _collect_violations(net: pp.pandapowerNet) -> Dict[str, List]:
    """Internal: collect all violations from a converged power flow."""
    return {
        "voltage": [
            {"bus": int(idx), "vm_pu": round(float(vm), 4),
             "type": "UNDERVOLTAGE" if vm < V_MIN_PU else "OVERVOLTAGE"}
            for idx, vm in net.res_bus["vm_pu"].items()
            if not np.isnan(vm) and (vm < V_MIN_PU or vm > V_MAX_PU)
        ],
        "overload": [
            {"line_idx": int(idx),
             "asset_id": net.line.at[idx, "asset_id"] if "asset_id" in net.line.columns else f"LINE_{idx}",
             "loading_pct": round(float(loading), 2)}
            for idx, loading in net.res_line["loading_percent"].items()
            if loading > LINE_LOADING_MAX_PCT
        ],
    }
