"""
GridGuard — Dependency Graph Engine (Dynamic IEEE 33-bus)

Builds a NetworkX DiGraph dynamically from the pandapower network:
    Power infrastructure → Critical services → Downstream consequences

Key functions:
    build_dependency_graph()              Build from active pandapower net
    get_downstream_dependencies(asset)    BFS traversal of dependents
    calculate_service_impact(asset)       N-1 physical simulation for impact
"""
from __future__ import annotations
from typing import Dict, List, Tuple, Any

import networkx as nx

from config import CriticalityLevel, CRITICALITY_WEIGHTS

# ---------------------------------------------------------------------------
# Node attribute keys
# ---------------------------------------------------------------------------
NODE_TYPE        = "node_type"      # FEEDER | TRANSFORMER | LINE | BUS | SERVICE | SUBSTATION | LOAD
NODE_CRITICALITY = "criticality"
NODE_LOAD_MW     = "load_mw"
NODE_IS_SERVICE  = "is_critical_service"
NODE_DESC        = "description"

# ---------------------------------------------------------------------------
# Edge attribute keys
# ---------------------------------------------------------------------------
EDGE_TYPE        = "edge_type"      # POWERS | DEPENDS_ON | FEEDS
EDGE_WEIGHT      = "weight"


def build_dependency_graph() -> nx.DiGraph:
    """
    Construct the GridGuard infrastructure dependency graph dynamically
    from the active IEEE 33-bus pandapower network.
    """
    G = nx.DiGraph()
    from grid.grid_engine import get_net
    net = get_net()

    # -----------------------------------------------------------------------
    # Substations
    # -----------------------------------------------------------------------
    G.add_node("SUBSTATION_HV", **{
        NODE_TYPE: "SUBSTATION", NODE_CRITICALITY: CriticalityLevel.LOW,
        NODE_LOAD_MW: 0.0, NODE_IS_SERVICE: False,
        NODE_DESC: "High-voltage substation (grid source)"
    })
    # Slack bus is Bus 0 in case33bw
    G.add_edge("SUBSTATION_HV", "BUS_0", **{EDGE_TYPE: "FEEDS", EDGE_WEIGHT: 1.0})

    # -----------------------------------------------------------------------
    # Buses
    # -----------------------------------------------------------------------
    for idx, row in net.bus.iterrows():
        G.add_node(f"BUS_{idx}", **{
            NODE_TYPE: "BUS", NODE_CRITICALITY: CriticalityLevel.LOW,
            NODE_LOAD_MW: 0.0, NODE_IS_SERVICE: False,
            NODE_DESC: f"Bus {idx} ({row['vn_kv']} kV)"
        })

    # -----------------------------------------------------------------------
    # Lines
    # -----------------------------------------------------------------------
    for idx, row in net.line.iterrows():
        asset_id = row.get("asset_id", f"LINE_{idx}")
        G.add_node(asset_id, **{
            NODE_TYPE: "LINE", NODE_CRITICALITY: CriticalityLevel.MEDIUM,
            NODE_LOAD_MW: 0.0, NODE_IS_SERVICE: False, NODE_DESC: f"Line {idx} ({asset_id})"
        })
        G.add_edge(f"BUS_{int(row['from_bus'])}", asset_id, **{EDGE_TYPE: "FEEDS", EDGE_WEIGHT: 1.0})
        G.add_edge(asset_id, f"BUS_{int(row['to_bus'])}", **{EDGE_TYPE: "FEEDS", EDGE_WEIGHT: 1.0})

    # -----------------------------------------------------------------------
    # Loads and Critical Services
    # -----------------------------------------------------------------------
    for idx, row in net.load.iterrows():
        bus = int(row["bus"])
        svc_id = row.get("service_id")
        p_mw = float(row["p_mw"])
        is_crit = bool(row.get("critical_service", False))

        node_id = str(svc_id) if (svc_id and is_crit) else f"LOAD_{idx}"
        desc = str(row.get("name", node_id))

        # Determine criticality
        crit_level = CriticalityLevel.LOW
        if is_crit:
            if "HOSPITAL" in node_id or "WATER" in node_id or "EMERGENCY" in node_id:
                crit_level = CriticalityLevel.CRITICAL
            elif "TELECOM" in node_id:
                crit_level = CriticalityLevel.HIGH
            else:
                crit_level = CriticalityLevel.MEDIUM

        G.add_node(node_id, **{
            NODE_TYPE: "SERVICE" if is_crit else "LOAD", 
            NODE_CRITICALITY: crit_level,
            NODE_LOAD_MW: p_mw, 
            NODE_IS_SERVICE: is_crit, 
            NODE_DESC: desc
        })
        G.add_edge(f"BUS_{bus}", node_id, **{EDGE_TYPE: "POWERS", EDGE_WEIGHT: 1.0})

    return G


# ---------------------------------------------------------------------------
# Graph queries
# ---------------------------------------------------------------------------

_GRAPH: nx.DiGraph | None = None


def get_graph() -> nx.DiGraph:
    global _GRAPH
    if _GRAPH is None:
        _GRAPH = build_dependency_graph()
    return _GRAPH


def reset_graph() -> None:
    global _GRAPH
    _GRAPH = None


def get_downstream_dependencies(asset_id: str) -> List[Dict[str, Any]]:
    """
    Return all nodes reachable from *asset_id* in the dependency graph.
    Uses BFS. Excludes the source node itself.
    """
    G = get_graph()
    if asset_id not in G:
        return []

    reachable = []
    for node in nx.bfs_tree(G, asset_id).nodes():
        if node == asset_id:
            continue
        attrs = G.nodes[node]
        reachable.append({
            "node_id": node,
            "node_type": attrs.get(NODE_TYPE, "UNKNOWN"),
            "description": attrs.get(NODE_DESC, node),
            "criticality": attrs.get(NODE_CRITICALITY, CriticalityLevel.LOW),
            "is_critical_service": attrs.get(NODE_IS_SERVICE, False),
            "load_mw": attrs.get(NODE_LOAD_MW, 0.0),
        })
    return reachable


def calculate_service_impact(asset_id: str) -> Dict[str, Any]:
    """
    Calculate the aggregated impact of losing *asset_id* by performing an
    N-1 contingency analysis on the physical power flow simulation.
    """
    from impact.calculator import calculate_grid_impact
    from grid.grid_engine import get_net, _resolve_asset_to_line
    import copy
    
    # Clone the network for physical N-1 simulation
    net_clone = copy.deepcopy(get_net())
    
    # Inject fault to simulate loss of asset
    line_idx = _resolve_asset_to_line(asset_id)
    if line_idx is not None:
        net_clone.line.at[line_idx, "in_service"] = False
        
    impact = calculate_grid_impact(net_clone, run_pf=True)
    
    # Extract affected services
    affected_services = [
        svc_id for svc_id, svc_data in impact["critical_services"].items() 
        if not svc_data["energised"]
    ]
    
    # Determine max criticality of affected downstream nodes
    max_crit = CriticalityLevel.LOW
    crit_order = [
        CriticalityLevel.LOW,
        CriticalityLevel.MEDIUM,
        CriticalityLevel.HIGH,
        CriticalityLevel.CRITICAL,
    ]
    
    G = get_graph()
    for sid in affected_services:
        if sid in G:
            c = G.nodes[sid].get(NODE_CRITICALITY, CriticalityLevel.CRITICAL)
            if crit_order.index(c) > crit_order.index(max_crit):
                max_crit = c

    return {
        "asset_id": asset_id,
        "total_load_mw": impact["mw_unavailable"],
        "critical_service_score": impact["impact_score"],
        "affected_services": affected_services,
        "downstream_count": impact["buses_affected"],
        "max_criticality": max_crit,
    }


def get_all_critical_services() -> List[str]:
    """Return all critical-service node IDs."""
    G = get_graph()
    return [
        n for n, attr in G.nodes(data=True)
        if attr.get(NODE_IS_SERVICE, False)
    ]


def get_asset_info(asset_id: str) -> Dict[str, Any] | None:
    G = get_graph()
    if asset_id not in G:
        return None
    attrs = dict(G.nodes[asset_id])
    attrs["asset_id"] = asset_id
    return attrs


def find_upstream_assets(asset_id: str) -> List[str]:
    """Return all nodes that have a path TO asset_id (ancestors)."""
    G = get_graph()
    if asset_id not in G:
        return []
    return list(nx.ancestors(G, asset_id))
