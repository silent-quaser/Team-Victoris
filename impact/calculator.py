"""
GridGuard — Grid Impact Calculator

Deterministic computation of restoration impact metrics from the
IEEE 33-bus simulation state.

This is NOT an ML problem. Impact is calculated directly from topology
and power flow results.

Functions:
    calculate_grid_impact()          → full impact summary dict
    get_critical_service_status()    → service-by-service status
    get_mw_unavailable()             → total MW without power
    get_affected_buses()             → set of de-energised bus indices
    get_feeder_status()              → which feeders are operational

Critical services and their loads (MW):
    HOSPITAL        2.4 MW  → Bus 6
    WATER_PLANT     1.8 MW  → Bus 10
    EMERGENCY_CENTER 0.8 MW → Bus 18
    TELECOM_TOWER   0.6 MW  → Bus 22

These values are used by P3's decision engine to prioritise recovery.
"""
from __future__ import annotations
import warnings
from typing import Any, Dict, List, Optional, Set

import numpy as np
import pandapower as pp

from grid.ieee33 import CRITICAL_SERVICE_LOADS


# Critical service definitions (bus_idx, service_id, mw)
CRITICAL_SERVICES = [
    {"service_id": "EMERGENCY_CENTER", "bus_idx": 6,  "p_mw": 0.2, "weight": 0.90},
    {"service_id": "HOSPITAL",         "bus_idx": 10, "p_mw": 0.6, "weight": 1.00},
    {"service_id": "WATER_PLANT",      "bus_idx": 12, "p_mw": 0.45, "weight": 0.95},
    {"service_id": "TELECOM_TOWER",    "bus_idx": 25, "p_mw": 0.15, "weight": 0.75},
]


def calculate_grid_impact(
    net: Optional[pp.pandapowerNet] = None,
    run_pf: bool = True,
) -> Dict[str, Any]:
    """
    Compute a comprehensive impact assessment for the current grid state.

    Parameters
    ----------
    net:    pandapower network (default: active singleton)
    run_pf: Whether to run power flow before assessment

    Returns
    -------
    dict with:
        mw_unavailable        float  — total MW without power
        pct_load_served       float  — fraction of load served [0, 1]
        buses_affected        int    — number of de-energised buses
        critical_services     dict   — per-service status
        critical_mw_lost      float  — total critical-service MW offline
        n_critical_down       int    — number of critical services offline
        faulted_lines         list   — list of out-of-service lines
        n_faulted_lines       int    — count of faults
        restoration_pct       float  — % of load restored
        impact_score          float  — weighted criticality score [0, 1]
    """
    from grid.grid_engine import get_net
    if net is None:
        net = get_net()

    # Run power flow
    pf_ok = False
    if run_pf:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                pp.runpp(net, numba=False, verbose=False)
            pf_ok = True
        except Exception:
            pf_ok = False

    # Identify de-energised buses
    affected_buses = _get_affected_buses(net, pf_ok)

    # MW unavailable
    mw_unavailable = 0.0
    total_load_mw = float(net.load["p_mw"].sum())
    for idx, row in net.load.iterrows():
        if int(row["bus"]) in affected_buses:
            mw_unavailable += float(row["p_mw"])

    mw_served = total_load_mw - mw_unavailable
    pct_served = float(mw_served / max(total_load_mw, 0.001))

    # Critical services
    services = get_critical_service_status(net, affected_buses, pf_ok)
    critical_mw_lost = sum(s["mw_lost"] for s in services.values())
    n_critical_down = sum(1 for s in services.values() if not s["energised"])

    # Faulted lines
    faulted = []
    for idx, row in net.line.iterrows():
        if not row["in_service"]:
            faulted.append({
                "line_idx": int(idx),
                "asset_id": row.get("asset_id", f"LINE_{idx}"),
                "from_bus": int(row["from_bus"]),
                "to_bus": int(row["to_bus"]),
            })

    # Impact score: weighted sum of critical service losses, normalised to [0,1]
    max_critical_mw = sum(s["p_mw"] for s in CRITICAL_SERVICES)
    impact_score = float(min(critical_mw_lost / max(max_critical_mw, 0.001), 1.0))

    restoration_pct = float(pct_served * 100)

    return {
        "mw_unavailable": round(mw_unavailable, 3),
        "mw_served": round(mw_served, 3),
        "total_load_mw": round(total_load_mw, 3),
        "pct_load_served": round(pct_served, 4),
        "buses_affected": len(affected_buses),
        "buses_affected_list": sorted(affected_buses),
        "critical_services": services,
        "critical_mw_lost": round(critical_mw_lost, 3),
        "n_critical_down": n_critical_down,
        "faulted_lines": faulted,
        "n_faulted_lines": len(faulted),
        "restoration_pct": round(restoration_pct, 2),
        "impact_score": round(impact_score, 4),
        "pf_converged": pf_ok,
    }


def get_critical_service_status(
    net: Optional[pp.pandapowerNet] = None,
    affected_buses: Optional[Set[int]] = None,
    pf_ok: bool = False,
) -> Dict[str, Dict[str, Any]]:
    """
    Return per-critical-service status.

    Returns dict of service_id → {energised, status, p_mw, mw_lost, bus}
    """
    from grid.grid_engine import get_net
    if net is None:
        net = get_net()
    if affected_buses is None:
        affected_buses = _get_affected_buses(net, pf_ok)

    result = {}
    for svc in CRITICAL_SERVICES:
        bus = svc["bus_idx"]
        energised = bus not in affected_buses

        # Check voltage as secondary confirmation
        if pf_ok and not net.res_bus.empty:
            try:
                vm = net.res_bus.at[bus, "vm_pu"]
                if np.isnan(vm) or vm < 0.5:
                    energised = False
            except Exception:
                pass

        p_mw = svc["p_mw"]
        mw_lost = 0.0 if energised else p_mw

        result[svc["service_id"]] = {
            "service_id": svc["service_id"],
            "bus_idx": bus,
            "energised": energised,
            "status": "ONLINE" if energised else "OFFLINE",
            "p_mw": p_mw,
            "mw_lost": mw_lost,
            "criticality_weight": svc["weight"],
        }

    return result


def get_mw_unavailable(net: Optional[pp.pandapowerNet] = None) -> float:
    """Return total MW currently without power."""
    impact = calculate_grid_impact(net, run_pf=False)
    return impact["mw_unavailable"]


def get_affected_buses(net: Optional[pp.pandapowerNet] = None) -> List[int]:
    """Return list of de-energised bus indices."""
    from grid.grid_engine import get_net
    if net is None:
        net = get_net()
    return sorted(_get_affected_buses(net, False))


def get_feeder_status(net: Optional[pp.pandapowerNet] = None) -> Dict[str, Any]:
    """
    Simple feeder-level status based on which main lines are in service.
    In IEEE 33-bus, the main feeders branch from bus 0 (slack).
    """
    from grid.grid_engine import get_net
    if net is None:
        net = get_net()

    # Lines from slack bus (bus 0) are the main feeder segments
    main_feeder_lines = net.line[net.line["from_bus"] == 0]
    feeders = {}
    for idx, row in main_feeder_lines.iterrows():
        feeders[f"FEEDER_{idx}"] = {
            "line_idx": int(idx),
            "to_bus": int(row["to_bus"]),
            "in_service": bool(row["in_service"]),
        }
    return feeders


def _get_affected_buses(net: pp.pandapowerNet, pf_ok: bool) -> Set[int]:
    """
    Identify de-energised buses using graph connectivity.
    A bus is de-energised if it is not reachable from the slack bus
    through in-service lines.
    """
    import networkx as nx

    # Build connectivity graph of in-service lines
    G = nx.Graph()
    G.add_nodes_from(range(len(net.bus)))
    for idx, row in net.line.iterrows():
        if row["in_service"]:
            G.add_edge(int(row["from_bus"]), int(row["to_bus"]))

    # Slack bus is bus 0 (external grid connection)
    slack_bus = 0
    if slack_bus not in G:
        return set(range(len(net.bus)))

    connected = nx.node_connected_component(G, slack_bus)
    all_buses = set(range(len(net.bus)))
    disconnected = all_buses - connected

    # Also check voltage violations from PF
    if pf_ok and not net.res_bus.empty:
        for idx, row in net.res_bus.iterrows():
            vm = row["vm_pu"]
            if np.isnan(vm) or vm < 0.5:
                disconnected.add(int(idx))

    return disconnected
