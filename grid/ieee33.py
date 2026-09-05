"""
GridGuard — IEEE 33-Bus Distribution Feeder (pandapower)

Loads the standard Baran & Wu 33-bus radial distribution system via
pandapower's case33bw() and overlays GridGuard-specific critical
service loads, switches, and asset metadata.

Bus → Critical service mapping (added as loads):
    Bus 6  → Hospital          2.4 MW  (originally 0.2 MW residential)
    Bus 10 → Water Plant       1.8 MW
    Bus 18 → Emergency Center  0.8 MW
    Bus 22 → Telecom Tower     0.6 MW

These are annotated in net.load with 'name' and 'critical_service' columns.

The base IEEE 33-bus has:
    33 buses, 32 lines (radial), 5 normally-open tie-switches,
    12.66 kV base, total load ≈ 3.715 MW + 2.3 MVAr
"""
from __future__ import annotations
import warnings
from copy import deepcopy
from typing import Any, Dict, List, Optional

import pandapower as pp
import pandapower.networks as pn
import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# Critical service overlay
# ---------------------------------------------------------------------------

# (bus_idx 0-based in case33bw, load_name, p_mw, q_mvar, service_id)
CRITICAL_SERVICE_LOADS = [
    (5,  "HOSPITAL",        2.4,  0.8,  "HOSPITAL"),
    (9,  "WATER_PLANT",     1.8,  0.6,  "WATER_PLANT"),
    (17, "EMERGENCY_CENTER",0.8,  0.2,  "EMERGENCY_CENTER"),
    (21, "TELECOM_TOWER",   0.6,  0.1,  "TELECOM_TOWER"),
]

# Bus indices of major components for fault injection (0-based)
BUS_TO_ASSET: Dict[int, str] = {
    5:  "BUS_6",
    9:  "BUS_10",
    17: "BUS_18",
    21: "BUS_22",
}

# Line indices → asset IDs (line DataFrame index, 0-based)
LINE_ASSET_MAP: Dict[int, str] = {
    5:  "L6-7",
    11: "L12-13",
    24: "L25-26",
    2:  "T3_LINE",   # Line feeding the transformer zone (Bus 2→3)
}

# Transformer T3 represented as the line between buses 2–3 in our overlay
# In a real system this would be a proper transformer element.
# For IEEE 33-bus (all 12.66 kV), we model T3 as a high-impedance line
# with a flag; the uncertainty is injected into failure probability.
T3_LINE_IDX = 2   # line index 2 (Bus2→Bus3 in case33bw)


def build_ieee33_net(with_tie_switches: bool = True) -> pp.pandapowerNet:
    """
    Load and augment the IEEE 33-bus network.

    Returns a pandapowerNet with:
        - Original 33-bus Baran & Wu topology
        - Critical service loads added (named loads with metadata)
        - 5 normally-open tie switches
        - 'critical_service' column on net.load
        - 'asset_id' column on net.line
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        net = pn.case33bw()

    # ── Add critical service load metadata ──────────────────────────────────
    if "critical_service" not in net.load.columns:
        net.load["critical_service"] = None
    if "service_id" not in net.load.columns:
        net.load["service_id"] = None

    # Add overlay loads for critical services
    for bus_idx, name, p_mw, q_mvar, svc_id in CRITICAL_SERVICE_LOADS:
        idx = pp.create_load(
            net, bus=bus_idx, p_mw=p_mw, q_mvar=q_mvar, name=name
        )
        net.load.at[idx, "critical_service"] = True
        net.load.at[idx, "service_id"] = svc_id

    # Mark original loads as non-critical
    net.load["critical_service"] = net.load["critical_service"].fillna(False).astype(bool)

    # ── Add asset_id to lines ───────────────────────────────────────────────
    if "asset_id" not in net.line.columns:
        net.line["asset_id"] = [f"LINE_{i}" for i in range(len(net.line))]
    for line_idx, asset_id in LINE_ASSET_MAP.items():
        if line_idx < len(net.line):
            net.line.at[line_idx, "asset_id"] = asset_id

    # ── Add 'failure_probability' column (initialized to 0) ────────────────
    net.line["failure_probability"] = 0.0
    net.line["is_uncertain"] = False

    # ── Tie switches (normally open) ────────────────────────────────────────
    if with_tie_switches and len(net.switch) == 0:
        _add_tie_switches(net)

    return net


def _add_tie_switches(net: pp.pandapowerNet) -> None:
    """Add 5 normally-open tie switches for reconfiguration (standard IEEE 33)."""
    # Standard IEEE 33-bus tie lines: 33-37 (0-indexed: 32-36 but they don't
    # exist in case33bw which is purely radial). We add them as open switches.
    tie_pairs = [
        (32, 7),   # Switch between bus 33 and bus 8
        (8,  20),  # Bus 9 and 21
        (11, 20),  # Bus 12 and 21
        (13, 14),  # Bus 14 and 15
        (24, 28),  # Bus 25 and 29
    ]
    for from_bus, to_bus in tie_pairs:
        if from_bus < len(net.bus) and to_bus < len(net.bus):
            pp.create_switch(
                net, bus=from_bus, element=to_bus,
                et="b", type="LS", closed=False,
                name=f"TIE_SW_{from_bus}_{to_bus}"
            )


def get_line_info(net: pp.pandapowerNet) -> pd.DataFrame:
    """Return a summary DataFrame of all lines with asset IDs."""
    result = net.line[["from_bus", "to_bus", "asset_id",
                        "in_service", "failure_probability"]].copy()
    result["from_bus_name"] = result["from_bus"].apply(
        lambda b: net.bus.at[b, "name"] if "name" in net.bus.columns else f"BUS_{b}"
    )
    result["to_bus_name"] = result["to_bus"].apply(
        lambda b: net.bus.at[b, "name"] if "name" in net.bus.columns else f"BUS_{b}"
    )
    return result


def get_critical_service_buses(net: pp.pandapowerNet) -> Dict[str, int]:
    """Return mapping of service_id → bus index for critical services."""
    svc_loads = net.load[net.load["critical_service"] == True]
    return dict(zip(svc_loads["service_id"], svc_loads["bus"]))
