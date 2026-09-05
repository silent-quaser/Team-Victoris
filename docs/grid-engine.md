# GridGuard — Grid Engine Documentation

## Overview

The grid engine is built on **pandapower** and implements the IEEE 33-bus
radial distribution feeder (Baran & Wu, 1989). It provides the component-level
simulation environment that real public outage datasets cannot offer.

---

## IEEE 33-Bus Network

### Base topology

The `case33bw()` pandapower network is the standard IEEE 33-bus Baran & Wu
radial distribution system:

- **33 buses**, 12.66 kV base
- **32 radial lines** (forming the main feeder branches)
- **5 normally-open tie switches** (for reconfiguration)
- **Total load**: ~3.7 MW + 2.3 MVAr (base case)
- **Substation**: External grid at Bus 0 (slack bus)

### GridGuard overlay

We augment the base network with:

| Addition | Detail |
|---|---|
| Critical service loads | Hospital (2.4 MW), Water Plant (1.8 MW), Emergency Center (0.8 MW), Telecom Tower (0.6 MW) |
| Asset IDs | Named lines: `L6-7`, `L12-13`, `L25-26`, `T3_LINE` |
| Fault metadata | `failure_probability` and `is_uncertain` columns on `net.line` |
| Tie switches | 5 normally-open switches for reconfiguration scenarios |

### Critical service bus assignments

| Service | Bus | MW | Bus role |
|---|---|---|---|
| HOSPITAL | 6 (idx 5) | 2.4 | Mid-feeder branch |
| WATER_PLANT | 10 (idx 9) | 1.8 | Mid-feeder branch |
| EMERGENCY_CENTER | 18 (idx 17) | 0.8 | End of feeder |
| TELECOM_TOWER | 22 (idx 21) | 0.6 | End of lateral |

### Named asset → line index mapping

| Asset ID | Line index | From bus | To bus |
|---|---|---|---|
| `L6-7` | 5 | 5 | 6 |
| `L12-13` | 11 | 11 | 12 |
| `L25-26` | 24 | 24 | 25 |
| `T3_LINE` | 2 | 2 | 3 |

---

## Power Flow

All state assessments run **Newton-Raphson AC power flow** via `pandapower.runpp()`.

### Settings

```python
pp.runpp(net, numba=False, verbose=False, algorithm="nr")
```

- `numba=False` — CPU-only, no JIT compilation required
- `algorithm="nr"` — Newton-Raphson (default, most accurate)
- Voltage limits: `[0.95, 1.05]` pu
- Line loading limit: 100% rated current

### Known behaviour

The IEEE 33-bus base case has relatively low end-voltage (≈ 0.91 pu at Bus 18)
due to the long radial feeder. This is expected and documented in the original
Baran & Wu paper. Voltage violations are flagged but do not prevent scenario
generation (they are realistic feeder characteristics).

---

## Grid Engine API

All functions are in [`grid/grid_engine.py`](file:///d:/GridGuard/grid/grid_engine.py).

### `create_grid() → pandapowerNet`
Create a fresh IEEE 33-bus network. Clears fault history.

### `reset_grid() → pandapowerNet`
Alias for `create_grid()`. Use to restore base state between scenarios.

### `inject_fault(asset_id, fault_type, failure_probability, is_uncertain) → dict`
Inject a fault into the active network.

```python
inject_fault("T3_LINE", fault_type="UNCERTAIN", failure_probability=0.62, is_uncertain=True)
# T3 stays in service (uncertain) but gets failure_probability=0.62

inject_fault("L6-7", fault_type="OPEN_CIRCUIT", failure_probability=1.0)
# L6-7 taken out of service immediately
```

### `get_grid_state() → dict`
Return comprehensive state dict:
- Buses (index, voltage, in_service)
- Lines (asset_id, in_service, failure_prob, loading_pct)
- Loads (bus, MW, critical_service)
- Critical services (energised, status, MW)
- Power flow results

### `execute_simulated_action(action) → dict`
Apply a recovery action to the simulation and return updated state.

```python
execute_simulated_action({"action_type": "REPAIR", "target_asset": "L6-7"})
```

Supported action types: `REPAIR`, `INSPECT`, `RECONFIGURE`, `ISLAND`, `RESTORE`, `DEFER`.

---

## Power Flow API

All functions in [`grid/power_flow.py`](file:///d:/GridGuard/grid/power_flow.py).

### `run_power_flow(net) → dict`
Run AC power flow, return voltages, loadings, losses, and violations.

### `get_voltage_violations(net) → list`
Return buses with voltage outside `[0.95, 1.05]` pu.

### `get_line_overloads(net, threshold_pct=100) → list`
Return lines loaded above `threshold_pct`.

### `check_grid_feasibility(net) → (bool, str)`
Return `(feasible, reason)`. Runs power flow and checks all constraints.

### `simulate_action_pf(action, base_net) → (bool, str, dict)`
Pre-validate an action on a **copy** of the network without modifying state.
Used by P3's decision engine to gate candidate actions.

---

## Impact Calculator

[`impact/calculator.py`](file:///d:/GridGuard/impact/calculator.py)

### `calculate_grid_impact(net, run_pf) → dict`

Returns comprehensive impact assessment:

```python
{
    "mw_unavailable": 6.6,          # MW without power
    "pct_load_served": 0.63,        # 63% of load served
    "buses_affected": 7,            # disconnected buses
    "critical_services": {
        "HOSPITAL": {"energised": False, "status": "OFFLINE", "mw_lost": 2.4},
        "WATER_PLANT": {"energised": False, "status": "OFFLINE", "mw_lost": 1.8},
        ...
    },
    "critical_mw_lost": 5.6,
    "n_critical_down": 3,
    "restoration_pct": 63.0,
    "impact_score": 0.97,
}
```

Bus connectivity is determined by **NetworkX graph traversal** from the slack
bus through in-service lines, not by voltage threshold alone.

---

## Demo Scenario (Severe Storm Event)

The demo scenario in [`scenario/demo.py`](file:///d:/GridGuard/scenario/demo.py) injects:

| Asset | Type | Failure Prob | Status |
|---|---|---|---|
| `L6-7` | OPEN_CIRCUIT | 1.00 | FAILED (confirmed) |
| `T3_LINE` | UNCERTAIN | 0.62 | UNCERTAIN (inspect recommended) |
| `L12-13` | OPEN_CIRCUIT | 1.00 | FAILED (confirmed) |
| `L25-26` | OPEN_CIRCUIT | 1.00 | FAILED (confirmed) |

The 0.62 probability for T3 comes from the **ML model + uncertainty engine**
applied to the demo scenario features, not a hardcoded constant.

---

## Scenario Generator

[`scenario/generator.py`](file:///d:/GridGuard/scenario/generator.py)

Generates reproducible scenarios from the IEEE 33-bus model:

```python
gen = ScenarioGenerator(seed=42)
dfs = gen.generate(n=2000)
```

Each scenario independently:
1. Samples an event type from calibrated storm profiles
2. Samples environment (wind, rain, temperature, load factor)
3. Computes failure probabilities per line from asset metadata × weather × loading
4. Samples TRUE states: `Bernoulli(failure_probability)`
5. Generates OBSERVED states with sensor noise
6. Runs pandapower power flow on the faulted network
7. Computes critical service impacts

### Asset metadata

[`scenario/generator.py LINE_METADATA`](file:///d:/GridGuard/scenario/generator.py) assigns per-line:
- `exposed`: True if overhead (higher weather exposure)
- `age_factor`: [1.0, 2.5] — older equipment has higher base failure rate
- `dist`: [0, 1] — normalised distance from substation

---

## References

- Baran, M.E. and Wu, F.F. (1989). "Network reconfiguration in distribution systems for loss reduction and load balancing." *IEEE Transactions on Power Delivery*, 4(2), 1401-1407.
- pandapower documentation: https://pandapower.readthedocs.io/
- `pandapower.networks.case33bw()` — built-in IEEE 33-bus test case
