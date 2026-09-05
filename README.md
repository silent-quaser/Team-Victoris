

### README.md

# GridGuard

### Impact-Aware Grid Recovery Under Uncertainty

GridGuard is a decision-support platform for post-disaster electric distribution-grid recovery. It combines electrical simulation, probabilistic failure estimation, evidence fusion, dependency-aware impact analysis, Value of Information (VOI), and resource-aware action ranking to recommend the safest and highest-impact next recovery action.

The system is split into two layers:

- **Prediction and state estimation** — estimate the probability that an asset has failed from environmental, electrical, and observational evidence.
- **Decision and recovery** — determine whether to act, inspect/acquire information, reconfigure, island, or defer based on impact, uncertainty, resources, and electrical feasibility.

---

## Core Idea

Traditional restoration logic often starts with:

> “Which component failed, and how quickly can we repair it?”

GridGuard instead asks:

> **“Given what we currently know, what is the best next action, and is it better to act now or acquire information first?”**

This enables decisions such as:

```text
High-confidence + high-impact  → ACT
High-uncertainty + high-impact  → INSPECT / ACQUIRE INFORMATION
High-uncertainty + low-impact   → ACT or DEFER depending on constraints
Low-impact                      → DEFER
````

The central decision concept is **Value of Information**:

```text
VOI(x)
= Expected outcome after learning x
  - Best expected outcome without learning x
  - Cost of acquiring the information
```

---

# Architecture

```text
                         ┌─────────────────────────┐
                         │      Frontend (Next.js) │
                         │                         │
                         │ Dashboard / Map / Risk │
                         │ Recovery / What-If     │
                         └────────────┬────────────┘
                                      │ HTTP
                                      ▼
                         ┌─────────────────────────┐
                         │      FastAPI Backend    │
                         └────────────┬────────────┘
                                      │
              ┌───────────────────────┼───────────────────────┐
              │                       │                       │
              ▼                       ▼                       ▼
      ┌───────────────┐      ┌────────────────┐      ┌────────────────┐
      │ Grid Engine   │      │ Decision Engine│      │ ML / Belief    │
      │               │      │                │      │                │
      │ pandapower    │      │ VOI            │      │ XGBoost        │
      │ IEEE-33 bus   │      │ Optimizer      │      │ Bayesian Fusion│
      │ Power Flow    │      │ Candidates     │      │ Failure Prob.  │
      └───────┬───────┘      └────────┬───────┘      └────────┬───────┘
              │                       │                       │
              └───────────────────────┼───────────────────────┘
                                      ▼
                         ┌─────────────────────────┐
                         │ Impact + Dependency     │
                         │ Criticality + Resources │
                         └─────────────────────────┘
```

---

# Repository Structure

```text
Team-Victoris/
├── api/                         # FastAPI entry point and routes
├── audit/                       # Audit / activity logging
├── config.py                    # Shared configuration and enums
├── models/                      # Typed application state models
│
├── engine/                      # Decision intelligence
│   ├── candidate_generator.py  # Creates possible recovery actions
│   ├── criticality.py          # Service/asset criticality model
│   ├── decision.py              # Main recommendation orchestration
│   ├── dependency.py            # NetworkX dependency graph
│   ├── feasibility.py           # Electrical/action feasibility checks
│   ├── optimizer.py              # Multi-objective action ranking
│   ├── state_manager.py         # Logical state + action lifecycle
│   └── voi.py                   # Value of Information engine
│
├── grid/                        # Physical grid simulation
│   ├── ieee33.py                # IEEE 33-bus network + critical-service overlay
│   ├── grid_engine.py           # Active pandapower network controller
│   └── power_flow.py            # AC power-flow validation utilities
│
├── impact/
│   └── calculator.py             # Deterministic physical impact calculation
│
├── uncertainty/
│   └── belief.py                 # Belief state + evidence fusion
│
├── ml/                           # Failure-probability estimation
│   ├── features.py              # Feature construction
│   ├── predictor.py             # Runtime XGBoost prediction
│   ├── trainer.py               # Model training/evaluation
│   └── models/
│       ├── failure_model.json
│       └── training_metrics.json
│
├── scenario/                     # Simulation scenarios
│   ├── demo.py                  # Deterministic demo scenario
│   ├── generator.py             # Synthetic scenario generation
│   └── profiles.py              # Storm/event profiles
│
├── data_pipeline/               # Real-data calibration
│   ├── downloader.py            # Event-Correlated Outage Dataset downloader
│   └── preprocessor.py          # Calibration/statistics pipeline
│
├── docs/                         # Module and API documentation
├── tests/                        # Unit + integration + E2E tests
├── frontend/                     # Operator-facing web interface
├── requirements.txt
└── pytest.ini
```

---

# Module Guide

## `engine/candidate_generator.py`

Generates candidate recovery actions:

```text
INSPECT
REPAIR
RECONFIGURE
ISLAND
DEFER
```

Each action carries metadata such as:

```text
action_id
action_type
target_asset
expected_benefit_mw
critical_service_score
risk_score
resource_type
resource_cost
estimated_time
reversibility
uncertainty_dependence
```

This module defines the current **action space**.

---

## `engine/criticality.py`

Models operational importance and downstream service consequences.

Current policy levels:

```text
CRITICAL
HIGH
MEDIUM
LOW
```

Criticality combines downstream dependency information, load, and service importance.

---

## `engine/dependency.py`

Builds a directed NetworkX graph representing relationships between grid infrastructure and dependent services.

Example:

```text
Substation
    │
   Bus
    │
  Line
    │
   Bus
    ├── Hospital
    ├── Water Plant
    └── Emergency Service
```

Capabilities include:

* Dependency graph construction
* Downstream dependency analysis
* Upstream asset discovery
* Critical-service discovery
* Service-impact estimation
* Asset information lookup

---

## `engine/feasibility.py`

Validates whether a proposed recovery action is electrically feasible.

Checks include:

* Power-flow convergence
* Voltage limits
* Line loading
* Action-specific constraints
* Island capacity constraints

Current policy:

```text
Voltage: 0.95–1.05 pu
Line loading: ≤ 100%
```

---

## `engine/optimizer.py`

Ranks candidate actions using multi-objective decision scoring.

Objective dimensions include:

```text
Critical service recovery
Load restoration (MW)
Risk
Resource consumption
Estimated time
Uncertainty
VOI / information benefit
```

Conceptually:

```text
score(action) =
    criticality benefit
  + MW recovery benefit
  - risk
  - resource cost
  - time cost
  - uncertainty penalty
  + decision-specific bonuses
```

---

## `engine/voi.py`

Computes the **Value of Information** for uncertain assets.

For binary uncertainty:

```text
FAILED
HEALTHY
```

VOI asks whether learning the true state before acting produces a better expected outcome.

```text
VOI =
Expected best outcome after observation
- Best expected outcome without observation
- Information cost
```

The module exposes:

* Failure probability
* Expected gain
* Inspection cost
* VOI
* Best action if failed
* Best action if healthy
* Best action without information
* Decision sensitivity

---

## `engine/decision.py`

Orchestrates the complete recommendation process:

```text
Current state
    ↓
Generate candidates
    ↓
Validate feasibility
    ↓
Calculate uncertainty / VOI
    ↓
Rank candidates
    ↓
Select best feasible action
    ↓
Generate explanation + alternatives
```

This is the main module that converts the analytical subsystems into an operator-facing recommendation.

---

## `engine/state_manager.py`

Maintains the live logical GridGuard state.

Responsibilities:

* Asset states
* Fault states
* Resource states
* Action execution
* Inspection results
* State transitions
* Restoration progress
* Synchronization with the physical grid simulator

Typical transition:

```text
UNCERTAIN
   ↓
INSPECT
   ↓
FAILED / HEALTHY
```

Recovery transition:

```text
FAILED
   ↓
REPAIR / RECONFIGURE / ISLAND
   ↓
RESTORED / DEGRADED / ISOLATED
```

---

# Grid Simulation

## `grid/ieee33.py`

Builds the GridGuard version of the IEEE 33-bus distribution feeder.

Base model:

```text
33 buses
32 radial feeder lines
5 normally-open tie switches
12.66 kV base
Baran & Wu feeder
```

GridGuard overlays:

```text
Hospital           2.4 MW
Water Plant        1.8 MW
Emergency Center   0.8 MW
Telecom Tower      0.6 MW
```

Named assets include:

```text
L6-7
L12-13
L25-26
T3_LINE
```

`T3_LINE` is a **transformer-zone proxy represented by a line** in the current single-voltage-level IEEE-33 model, rather than a physical transformer element.

---

## `grid/grid_engine.py`

Central controller for the active pandapower network.

Responsibilities:

* Create network
* Reset network
* Inject faults
* Read grid state
* Execute simulated actions
* Read asset state
* Maintain fault history

---

## `grid/power_flow.py`

Provides reusable electrical validation.

Main functions:

```text
run_power_flow()
get_voltage_violations()
get_line_overloads()
check_grid_feasibility()
simulate_action_pf()
```

Outputs include:

* Voltage magnitudes
* Line loading
* Current
* Losses
* Generator output
* Constraint violations
* Convergence status

---

# Impact Analysis

## `impact/calculator.py`

Calculates the actual operational impact of the current simulated grid state.

This is intentionally deterministic rather than ML-based.

Metrics include:

* MW unavailable
* Percentage of load served
* Affected buses
* Critical-service status
* Critical MW lost
* Number of critical services down
* Faulted lines
* Restoration percentage
* Weighted impact score

The system therefore evaluates what a failure actually causes in the network instead of relying solely on predicted consequences.

---

# Uncertainty Engine

## `uncertainty/belief.py`

Maintains an interpretable belief state for each asset.

Evidence sources include:

```text
SCADA
Technician report
Weather
Sensor health
Communication availability
ML prior
Historical evidence
```

Belief state contains:

```text
p_failed
p_healthy
confidence
entropy
resolved
resolved_state
evidence_log
```

Current policy bands:

```text
P < 0.25        → Probably healthy
0.25–0.75       → Uncertain
P > 0.75        → Probably failed
```

---

# Machine Learning

The ML subsystem estimates component failure probability. It does **not** directly select recovery actions.

## `ml/features.py`

Builds the feature vector using four groups.

### Asset

```text
asset type
weather exposure
age factor
distance from substation
previous faults
```

### Electrical

```text
loading percentage
```

### Environment

```text
weather severity
wind
rain
temperature
load factor
```

### Observation quality

```text
SCADA reading
sensor health
communication status
technician confidence
weather evidence
```

Target:

```text
true_failed
```

---

## `ml/predictor.py`

Loads the trained XGBoost classifier and returns:

```text
P(component failed)
```

A physics-based fallback is available when the trained model is unavailable.

---

## `ml/trainer.py`

Training pipeline:

```text
Synthetic data
      ↓
Feature matrix
      ↓
Train / validation / test split
      ↓
XGBoost
      ↓
Evaluation
      ↓
Model + metrics
```

Tracked metrics include:

```text
ROC-AUC
Accuracy
Precision
Recall
F1
Confusion matrix
Feature importance
```

Probability calibration should also be evaluated before treating classifier outputs as operationally calibrated probabilities.

---

## `ml/models/failure_model.json`

Serialized trained XGBoost model.

---

## `ml/models/training_metrics.json`

Stores training/evaluation metrics and feature importance.

---

# Scenario System

## `scenario/profiles.py`

Defines event profiles such as:

```text
NORMAL
SEVERE_STORM
HIGH_WIND
ICE_STORM
HURRICANE
```

Profiles contain:

* Duration
* Outage magnitude
* Base failure probabilities
* Weather severity
* Wind statistics
* Rain statistics
* Multi-fault probability

---

## `scenario/generator.py`

Generates synthetic scenarios with two distinct worlds:

```text
TRUE STATE
What actually happened

OBSERVED STATE
What the operator sees
```

Generated datasets:

```text
scenarios.csv
component_states.csv
observations.csv
powerflow_results.csv
critical_impacts.csv
```

This allows decisions to be evaluated under incomplete and noisy information.

---

## `scenario/demo.py`

Creates the deterministic demonstration scenario.

Initial state:

```text
L6-7       FAILED
T3_LINE    UNCERTAIN, P(failed)=0.62
L12-13     FAILED
L25-26     FAILED
```

The scenario is designed to demonstrate why the system can recommend:

```text
INSPECT T3
```

rather than immediately committing a repair resource.

---

# Real-Data Pipeline

## `data_pipeline/downloader.py`

Provides automated access to the Event-Correlated Outage Dataset v2 and references EAGLE-I/DOE-417 sources.

Used for:

* Event characteristics
* Storm type
* Duration
* Magnitude
* Geographic context
* Scenario calibration
* Validation

The real data is not treated as component-level SCADA/failure labels.

---

## `data_pipeline/preprocessor.py`

Transforms event-level outage data into calibrated storm profiles.

Flow:

```text
Raw outage dataset
      ↓
Parse / normalize columns
      ↓
Normalize event types
      ↓
Aggregate statistics
      ↓
Calibrate storm profiles
      ↓
scenario/profiles.py
```

Outputs:

```text
data/processed/storm_profiles.csv
data/processed/event_statistics.csv
```

Empirical fallback profiles are available if the real dataset is unavailable.

---

# Shared Models

## `models/grid.py`

Defines typed application models used throughout the system.

Typical entities include:

```text
AssetModel
FaultModel
GridStateModel
ResourceModel
ActionModel
```

These models keep the API, state manager, and decision engine consistent.

---

# Audit

## `audit/log.py`

Records important operational events and state transitions.

Useful for:

* Action history
* Inspection history
* Explainability
* Debugging
* Demonstration replay
* Future audit workflows

---

# Frontend

The frontend is the operator-facing control surface.

Core views:

```text
Overview
Activity Log
Critical Services
Data Models
Dependency Map
Grid Model
Recovery Planner
Resources
Risk
Scenarios
Settings
What-If
```

### Overview

Displays:

* Current scenario
* Restoration progress
* Grid visualization
* Current recommendation
* Impact analysis

### Recovery Planner

Displays:

* Recommended action
* Target asset
* Expected impact
* Risk
* Uncertainty
* VOI
* Alternative actions

### Critical Services

Displays the status of:

```text
Hospital
Water Plant
Emergency Center
Telecom Tower
```

### Dependency Map

Visualizes:

```text
Grid assets → buses → downstream services
```

### Grid Model

Displays the simulated IEEE-33 network.

### Risk

Surfaces current risk and system-level impact metrics.

### Resources

Tracks:

```text
Repair crews
Inspection drone
Mobile generator
```

### Scenarios

Provides scenario inspection and simulated disaster conditions.

### What-If

Supports counterfactual exploration:

```text
What happens if we repair this?
What happens if we reconfigure?
What happens if we island?
What happens if we inspect first?
```

### Activity Log

Shows the decision trail and resulting state transitions.

### Data Models

Documents entities and data structures used by the system.

---

# Tests

The test suite covers the system from individual modules through end-to-end API behavior.

```text
tests/
├── test_candidates.py
├── test_decision.py
├── test_dependency.py
├── test_e2e.py
├── test_feasibility.py
├── test_grid_engine.py
├── test_ml.py
├── test_scenario_gen.py
├── test_state.py
├── test_uncertainty.py
└── test_voi.py
```

Coverage includes:

```text
Candidate generation
Decision logic
Dependency analysis
End-to-end behavior
Electrical feasibility
IEEE-33 simulation
ML feature extraction/prediction
Scenario generation
State transitions
Uncertainty fusion
VOI
```

The primary E2E workflow is:

```text
Get recommendation
      ↓
Inspect T3
      ↓
Resolve T3 as FAILED / HEALTHY
      ↓
Recompute recommendation
```

---

# Decision Lifecycle

```text
Current grid state
      ↓
Failure probability
      ↓
Evidence fusion / belief state
      ↓
Dependency + criticality analysis
      ↓
Candidate generation
      ↓
Electrical feasibility
      ↓
VOI + multi-objective ranking
      ↓
ACT / INSPECT / RECONFIGURE / ISLAND / DEFER
      ↓
Simulate / execute
      ↓
Recalculate grid impact and state
      ↓
Repeat
```

---

# Demonstration Flow

Initial state:

```text
T3_LINE
P(failed) = 0.62
Critical downstream impact = High
Inspection resource = Available
```

Compare:

```text
REPAIR
- High benefit if failed
- Wastes a repair resource if healthy
- Does not resolve uncertainty first

INSPECT
- Resolves failed/healthy state
- Costs time and inspection resources
- Can change the downstream optimal action

DEFER
- No immediate resource cost
- Risks leaving an important uncertainty unresolved
```

The intended demonstration recommendation is:

```text
INSPECT T3
```

After inspection:

```text
T3 = FAILED
```

The state is resolved and the next recovery action is recomputed.

---

# Data Architecture

```text
Real public outage data
        ↓
Event / storm calibration
        ↓
IEEE-33 pandapower simulation
        ↓
Synthetic scenarios
  ├── true component state
  ├── noisy observations
  └── physical power-flow impact
        ↓
XGBoost failure probability
        ↓
Bayesian evidence fusion
        ↓
Decision engine + VOI
```

Real public outage data is used for event-level calibration because it does not provide all component-level SCADA, topology, and failure labels required for the component-level simulation task.

---

# Installation

## Python Backend

Create a virtual environment:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Core dependencies include:

```text
FastAPI
Uvicorn
Pydantic
pandapower
NumPy
NetworkX
Pandas
XGBoost
scikit-learn
Pytest
SciPy
```

## Frontend

From the frontend directory:

```bash
npm install
npm run dev
```

Use the scripts defined by the active frontend `package.json` if they differ.

---

# Generate Synthetic Data

```bash
python -m scenario.generator
```

Generated data is written under:

```text
data/synthetic/
```

---

# Train the ML Model

```bash
python -m ml.trainer
```

Outputs:

```text
ml/models/failure_model.json
ml/models/training_metrics.json
```

---

# Preprocess Real Outage Data

```bash
python -m data_pipeline.preprocessor
```

Outputs:

```text
data/processed/storm_profiles.csv
data/processed/event_statistics.csv
```

---

# Run the Backend

Example:

```bash
uvicorn main:app --reload
```

Use the application module defined by the active API layout.

---

# Run Tests

```bash
pytest
```

---

# API Concept

The frontend communicates with the backend through HTTP/JSON.

Representative resources include:

```text
/grid/state
/recommendation
/actions
/resources
/impact
/risk
/voi/{asset}
/inspection
```

The definitive route set should follow the active FastAPI implementation and:

```text
docs/frontend-contract.md
```

---

# Technology Stack

| Layer    | Technologies                               |
| -------- | ------------------------------------------ |
| Frontend | Next.js, React, TypeScript, Tailwind CSS   |
| API      | FastAPI, Uvicorn, Pydantic                 |
| Grid     | pandapower, IEEE-33 feeder                 |
| Graph    | NetworkX                                   |
| ML       | XGBoost, scikit-learn                      |
| Data     | Pandas, NumPy, SciPy                       |
| Testing  | Pytest, pytest-asyncio, FastAPI TestClient |

---

# Current Limitations

GridGuard is a simulation and decision-support prototype rather than a production utility-control system.

* IEEE-33 is a research feeder rather than a utility-specific network.
* `T3_LINE` is a transformer-zone proxy.
* Component-level ML labels are generated by simulation.
* ML probabilities require careful generalization and calibration evaluation before operational interpretation.
* Criticality weights are configurable policy parameters.
* Recovery operations are simulated and are not sent to real field equipment.
* Public outage data provides event-level calibration rather than full SCADA telemetry.

---

# Future Improvements

```text
1. Shared physically-feasible counterfactual evaluator
2. Scenario-level ML validation and probability calibration
3. Improved topology-aware reconfiguration
4. More realistic island simulation
5. Dynamic resource lifecycle modeling
6. Larger IEEE feeders (69/123 bus)
7. More realistic component and sensor failure models
8. Multi-step recovery optimization
9. Human approval / escalation workflows
10. Real-time telemetry integration
```

---

# Security and Operational Scope

GridGuard is intended for **simulation, research, and decision support**.

It should not directly control operational utility equipment without:

* Utility-specific engineering validation
* Protection-system coordination
* Cybersecurity controls
* Human authorization
* Appropriate operational safety procedures

---

# Documentation

Detailed documentation is maintained in:

```text
docs/data.md
docs/decision-engine.md
docs/grid-engine.md
docs/frontend-contract.md
```

---

# Team

**Team Victoris**

Repository:

[https://github.com/silent-quaser/Team-Victoris](https://github.com/silent-quaser/Team-Victoris)

---

# License

Add the project's final license before public release.

```

This is deliberately fairly comprehensive because you said **all modules**. GitHub recommends keeping the README focused on getting users productive and moving long-form documentation into separate docs/wiki pages, so the module-specific material you already have in `docs/` can remain the detailed reference while this file serves as the repository's main entry point. :contentReference[oaicite:1]{index=1}

One thing I would change before committing: **don't include the current 99.86% ML accuracy in the README as a headline metric** until we finish the leakage/generalization validation we discussed. Your saved training metrics report that number, but it would be premature to present it as evidence of real-world predictive performance. :contentReference[oaicite:2]{index=2}
```

[1]: https://docs.github.com/en/repositories/creating-and-managing-repositories/best-practices-for-repositories?utm_source=chatgpt.com "Best practices for repositories - GitHub Docs"
