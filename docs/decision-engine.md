# GridGuard — Decision Engine Documentation

## Overview

GridGuard is an **impact-aware grid recovery system under uncertainty**. At its core is a decision engine that determines whether to:

1. **ACT** — execute a recovery action immediately
2. **INSPECT / ACQUIRE INFORMATION** — dispatch an inspection drone to resolve uncertainty
3. **CHOOSE AN ALTERNATIVE** — reconfigure the network or island a segment

The engine integrates five subsystems:

| Subsystem | Module | Role |
|-----------|--------|------|
| Dependency Graph | `engine/dependency.py` | NetworkX graph of infrastructure → services |
| Criticality Model | `engine/criticality.py` | Weights for service importance |
| VOI Engine | `engine/voi.py` | Value of Information calculation |
| Optimizer | `engine/optimizer.py` | Multi-objective scoring |
| Decision Engine | `engine/decision.py` | Recommendation assembly |

---

## 1. Decision Objective

The engine maximises the following composite score for each candidate action `a`:

```
score(a) =
    W_crit  × E[critical_service_recovery(a)]
  + W_mw    × E[load_restoration_mw(a)]
  + W_risk  × risk(a)                          [negative weight]
  + W_res   × resource_cost(a)                 [negative weight]
  + W_time  × estimated_time(a)                [negative weight]
  + W_uncert× uncertainty_penalty(a)            [negative weight]
  + quadrant_bonus(a)
  + voi_bonus(a)                               [for INSPECT only]
```

**Default weights** (configurable in `config.py`):

| Parameter | Weight | Rationale |
|-----------|--------|-----------|
| `W_crit` | +3.0 | Critical service recovery is the primary objective |
| `W_mw` | +0.5 | Secondary: maximise MW restored |
| `W_risk` | −2.0 | Penalise high-risk actions |
| `W_res` | −0.3 | Penalise resource consumption |
| `W_time` | −0.01/min | Penalise delay (per minute) |
| `W_uncert` | −1.5 | Penalise committing to uncertain situations |

**Constraints:**
- `electrically_feasible(a) == True` (validated by pandapower)
- `resource_available(a) == True` (checked before candidate generation)
- Network topology and islanding constraints

---

## 2. Value of Information (VOI)

### Formulation

For a binary uncertain asset `x` (FAILED / HEALTHY):

```
VOI(x) = E[best_outcome | observing x] − best_outcome_without_info − cost(inspection)
```

Expanded:

```
VOI(x) = [p(F) × score(best_action | FAILED) + p(H) × score(best_action | HEALTHY)]
         − max_{a} [p(F) × score(a | FAILED) + p(H) × score(a | HEALTHY)]
         − inspection_cost
```

### Algorithm

1. Read `p(FAILED)` from the current fault belief state
2. Enumerate possible observations: `{FAILED, HEALTHY}`
3. For each observation, find `best_action` by scoring all candidate actions given the known state
4. Compute `E_with_info = p(F) × score(best|F) + p(H) × score(best|H)`
5. Find `best_without_info` by choosing the action that maximises expected score without knowing the true state
6. `raw_VOI = E_with_info − best_without_info − inspection_cost`
7. Normalise to [0, 1] for comparability across assets
8. Compute `decision_sensitivity = |score(best|F) − score(best|H)|` — measures how much the decision changes

### Why T3 Gets INSPECT

In the demo scenario:
- T3 failure probability = **0.62** (high uncertainty)
- T3 feeds Hospital and Water Plant path (high critical-service impact)
- `best_action_if_FAILED` = REPAIR (high score)
- `best_action_if_HEALTHY` = DEFER (T3 not the bottleneck)
- Without inspection, acting on 0.62 probability means either:
  - Waste a repair crew if T3 is healthy, or
  - Leave Hospital without power if we defer and T3 is failed
- VOI is high → INSPECT wins

This is computed, not hardcoded.

---

## 3. Criticality Model

Four levels with numeric weights:

| Level | Weight | Assigned to |
|-------|--------|-------------|
| CRITICAL | 1.00 | Hospital, Water Plant, Emergency Center, T3, L6-7, L12-13 |
| HIGH | 0.75 | Telecom Tower, L25-26, Feeder A |
| MEDIUM | 0.40 | Lines, feeders |
| LOW | 0.15 | Residential zones, buses |

**Criticality-weighted impact** for an asset is the sum of `weight × load_mw` for all downstream nodes, normalised by the system maximum (40 MW):

```
crit_impact(asset) = min( Σ(w_i × mw_i) / 40.0 , 1.0 )
```

This ensures the decision engine does **not** simply optimise MW — a 3.5 MW hospital outweighs a 10 MW residential zone.

---

## 4. Dependency Model

Built using **NetworkX DiGraph**:

```
SUBSTATION_HV
├── FEEDER_A → BUS_1 → BUS_6 → [L6-7] → BUS_7 → EMERGENCY_CENTER
├── FEEDER_B → BUS_3 → [T3] → BUS_12 → [L12-13] → BUS_13 → WATER_PLANT
│             └── BUS_10 → HOSPITAL
├── FEEDER_C → BUS_5 → BUS_25 → [L25-26] → BUS_26 → TELECOM_TOWER
└── FEEDER_D → BUS_2 → BUS_20 → RESIDENTIAL_A
              → BUS_4 → BUS_30 → RESIDENTIAL_B
```

**Key functions:**
- `get_downstream_dependencies(asset)` — BFS traversal of all dependent nodes
- `calculate_service_impact(asset)` — aggregated criticality-weighted impact
- `find_upstream_assets(asset)` — all ancestors (for power-path analysis)

---

## 5. Uncertainty × Impact Quadrants

| | **Low Impact** | **High Impact** |
|---|---|---|
| **Low Uncertainty** | DEFER | ACT immediately |
| **High Uncertainty** | ACT (low cost of error) | **INSPECT** (acquire information) |

Thresholds (configurable):
- `UNCERTAINTY_HIGH_THRESHOLD = 0.40` — failure probability above this = high uncertainty
- `IMPACT_HIGH_THRESHOLD = 0.50` — criticality-weighted impact above this = high impact

The quadrant bonus in the optimizer:
- **HIGH-U × HIGH-I** → INSPECT gets +1.5, REPAIR gets −0.5
- **LOW-U × HIGH-I** → REPAIR/RECONFIGURE gets +0.8
- **LOW-U × LOW-I** → DEFER gets +0.2

---

## 6. Electrical Feasibility (pandapower)

Every candidate action is validated before scoring:

1. Build a pandapower network from the current grid state
2. Apply the proposed action (repair → mark asset in-service; island → apply generator)
3. Run AC Newton-Raphson power flow
4. Check:
   - Voltage: `0.95 pu ≤ V ≤ 1.05 pu`
   - Line loading: `≤ 100%`
   - Transformer loading: `≤ 100%`
   - Power flow convergence
5. If any check fails → `electrically_feasible = False` → action score = −999

**INSPECT and DEFER** are always electrically feasible (no topology change).

---

## 7. Action Types

| Type | Description | Reversibility | Resources |
|------|-------------|---------------|-----------|
| REPAIR | Dispatch crew to fix a failed asset | 0.8 | REPAIR_CREW |
| INSPECT | Dispatch drone to resolve uncertainty | 1.0 | INSPECTION_DRONE |
| RECONFIGURE | Switch to alternate network path (bypass) | 0.9 | None |
| ISLAND | Isolate a segment with mobile generator | 0.7 | MOBILE_GENERATOR |
| RESTORE | Re-energise a repaired/isolated asset | 1.0 | None |
| DEFER | No immediate action | 1.0 | None |

---

## 8. Sequential Recovery

The system supports step-by-step recovery:

```
state_0  →  action_0  →  state_1  →  action_1  →  state_2  →  ...
```

After each action:
- Asset statuses update
- Fault list updates (resolved faults removed)
- Resources update (consumed / released)
- Restoration progress recalculates
- Decision engine re-evaluates from the new state

---

## 9. Resource Constraints

Initial resources:

| Resource | Count | Cost |
|----------|-------|------|
| Repair Crews | 2 | 0.5 per action |
| Inspection Drone | 1 | 0.2 per inspection |
| Mobile Generator | 1 | 0.5 per island |

Resource availability is checked **before** including a candidate in the action set — infeasible-resource actions never appear.

---

## 10. Audit and Explainability

Every recommendation is logged with:
- Timestamp
- State snapshot (step, faults, restoration %)
- All candidate actions and their scores
- Selected action
- Why it was selected (reason codes + text explanation)
- Feasibility results

Accessible at `GET /audit/log`.

Explanation text is generated from **computed values**, not templates. Example:

> "Recommended action: INSPECT on T3 (composite score: 2.847). Current failure probability of T3 is 62%. Inspection VOI = 0.312 (expected gain 0.512, cost 0.200). Decision sensitivity is 0.743: if T3 is FAILED the best action is REPAIR, if HEALTHY the best action is DEFER. Without inspection, the system would choose REPAIR. Criticality-weighted impact score of T3: 0.824. High uncertainty (62%) combined with high critical-service impact places this in the HIGH-UNCERTAINTY × HIGH-IMPACT quadrant, strongly favouring information acquisition before committing resources."

---

## 11. Limitations

1. **Binary VOI**: The current VOI implementation assumes binary observations (FAILED / HEALTHY). Continuous degradation states (partial faults) are not yet modelled.

2. **Sequential single-asset VOI**: VOI is computed per asset independently. Joint VOI for multiple uncertain assets (correlated failures) is not implemented.

3. **Simplified pandapower topology**: The pandapower network uses simplified line impedances. For a production deployment, real network parameters from a GIS/SCADA system should be used.

4. **Static dependency graph**: The NetworkX graph is built once at startup. Dynamic topology changes (switching, reconfiguration) partially update asset statuses but do not rebuild the graph structure.

5. **No temporal horizon**: The decision engine optimises the immediate next step. It does not solve the full multi-step sequential recovery as an MDP. A POMDP formulation would capture multi-step decision value more accurately.

6. **Resource replenishment**: Resources are not modelled as returning over time (e.g., crew finishing one repair and moving to the next). Resources are released only when explicitly freed by the inspection endpoint.
