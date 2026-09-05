"""
GridGuard — Criticality Engine

Assigns and queries criticality for assets and services.
Criticality influences recovery ranking beyond simple MW restoration.
"""
from __future__ import annotations
from typing import Dict, List, Optional

from config import CriticalityLevel, CRITICALITY_WEIGHTS
from engine.dependency import get_graph, NODE_CRITICALITY, NODE_IS_SERVICE, NODE_LOAD_MW


# ---------------------------------------------------------------------------
# Asset-level criticality overrides (infrastructure assets)
# ---------------------------------------------------------------------------
ASSET_CRITICALITY_MAP: Dict[str, CriticalityLevel] = {
    # Transformer
    "T3_LINE": CriticalityLevel.CRITICAL,   # feeds Hospital + Water Plant path

    # Lines
    "L6-7":   CriticalityLevel.CRITICAL,   # feeds Emergency Center
    "L12-13": CriticalityLevel.CRITICAL,   # feeds Water Plant
    "L25-26": CriticalityLevel.HIGH,       # feeds Telecom Tower

    # Feeders
    "FEEDER_A": CriticalityLevel.HIGH,
    "FEEDER_B": CriticalityLevel.CRITICAL,
    "FEEDER_C": CriticalityLevel.MEDIUM,
    "FEEDER_D": CriticalityLevel.LOW,

    # Services
    "HOSPITAL":         CriticalityLevel.CRITICAL,
    "WATER_PLANT":      CriticalityLevel.CRITICAL,
    "EMERGENCY_CENTER": CriticalityLevel.CRITICAL,
    "TELECOM_TOWER":    CriticalityLevel.HIGH,
    "RESIDENTIAL_A":    CriticalityLevel.LOW,
    "RESIDENTIAL_B":    CriticalityLevel.LOW,
}

CRITICALITY_NUMERIC: Dict[CriticalityLevel, float] = {
    CriticalityLevel.CRITICAL: 1.00,
    CriticalityLevel.HIGH:     0.75,
    CriticalityLevel.MEDIUM:   0.40,
    CriticalityLevel.LOW:      0.15,
}


def get_criticality(asset_id: str) -> CriticalityLevel:
    """Return criticality level for an asset (map override → graph → LOW)."""
    if asset_id in ASSET_CRITICALITY_MAP:
        return ASSET_CRITICALITY_MAP[asset_id]
    G = get_graph()
    if asset_id in G:
        return G.nodes[asset_id].get(NODE_CRITICALITY, CriticalityLevel.LOW)
    return CriticalityLevel.LOW


def get_criticality_score(asset_id: str) -> float:
    """Return numeric criticality score [0, 1]."""
    return CRITICALITY_NUMERIC[get_criticality(asset_id)]


def get_affected_critical_services(asset_id: str) -> List[str]:
    """
    Return list of critical-service node IDs downstream of asset_id.
    Performs BFS on the dependency graph.
    """
    import networkx as nx
    G = get_graph()
    if asset_id not in G:
        return []
    services = []
    for node in nx.bfs_tree(G, asset_id).nodes():
        if node == asset_id:
            continue
        if G.nodes[node].get(NODE_IS_SERVICE, False):
            services.append(node)
    return services


def score_criticality_impact(asset_id: str) -> float:
    """
    Return a [0, 1] score representing the total criticality-weighted impact
    of losing this asset, using downstream dependency traversal.
    """
    import networkx as nx
    from config import CRITICALITY_WEIGHTS
    G = get_graph()
    if asset_id not in G:
        return 0.0

    total_weighted = 0.0
    SYSTEM_MAX_MW = 40.0

    for node in nx.bfs_tree(G, asset_id).nodes():
        if node == asset_id:
            continue
        attrs = G.nodes[node]
        crit = attrs.get(NODE_CRITICALITY, CriticalityLevel.LOW)
        mw   = attrs.get(NODE_LOAD_MW, 0.0)
        total_weighted += CRITICALITY_WEIGHTS.get(crit, 0.15) * mw

    return min(total_weighted / SYSTEM_MAX_MW, 1.0)


def rank_assets_by_criticality(asset_ids: List[str]) -> List[str]:
    """Return asset_ids sorted by criticality score descending."""
    return sorted(asset_ids, key=get_criticality_score, reverse=True)


def is_critical_service(node_id: str) -> bool:
    G = get_graph()
    if node_id not in G:
        return False
    return G.nodes[node_id].get(NODE_IS_SERVICE, False)
