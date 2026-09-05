# GridGuard — Data Documentation

## Overview

GridGuard uses a hybrid data architecture that combines real public outage data
for calibration with IEEE 33-bus simulation data for component-level ML training.

This is a deliberate design decision: public outage datasets do not provide the
detailed SCADA/component/topology labels required for component-level failure
classification. The IEEE 33-bus simulation fills this gap, calibrated by real data.

```
REAL OUTAGE DATA
(EAGLE-I + DOE-417 via Event-Correlated Dataset v2)
        ↓
Extract storm characteristics
(duration, magnitude, severity, cause)
        ↓
Calibrate storm profiles in scenario/profiles.py
        ↓
IEEE 33-Bus pandapower simulation
        ↓
Generate 2000+ synthetic scenarios
(TRUE component states + OBSERVED noisy states)
        ↓
Train XGBoost failure-probability model
        ↓
Uncertainty engine (Bayesian fusion)
        ↓
P3 Decision Engine
```

---

## Dataset 1: Event-Correlated Outage Dataset v2 [PRIMARY]

| Field | Value |
|---|---|
| **Name** | Event-Correlated Outage Dataset in America (v2) |
| **Publisher** | Pacific Northwest National Laboratory (PNNL) / Department of Energy |
| **Type** | Real-world, processed |
| **License** | Public Domain (U.S. Government) |
| **Official page** | https://catalog.data.gov/dataset/event-correlated-outage-dataset-in-america |
| **Download URL** | https://data.openei.org/files/6458/Outage_Dataset_R1.zip |
| **Guidelines** | https://data.openei.org/files/6458/Guideline_OEDI_Updated.docx |

### What it contains

This **processed, integrated** dataset combines three primary sources:
- **EAGLE-I** — county-level, 15-minute outage observations (2014–2023)
- **DOE-417** — electric emergency and disturbance incident reports
- **CO-EST2024-POP** — 2024 US Census Bureau county population estimates

### Relevant fields

| Field | Description |
|---|---|
| `event_type` | Storm category (thunderstorm, hurricane, ice, wind, equipment, etc.) |
| `event_start` | UTC start timestamp of the disturbance event |
| `event_end` | UTC end timestamp |
| `duration_hours` | Duration of associated outage period |
| `customers_out_max` | Peak customers without power |
| `mw_affected` | Estimated MW demand affected |
| `state` | US state |
| `county` | County name |
| `cause` | Primary cause (wind, ice, lightning, tree contact, etc.) |

### How we use it

1. **Storm profile calibration** — Group events by type, compute mean/std of duration and magnitude
2. **Failure probability scaling** — MW affected is used to scale base failure probabilities per event type
3. **Scenario validation** — Our synthetic storms must resemble the magnitude/duration of real events

### What we do NOT use it for

- Component-level transformer/line failure labels (not available)
- Direct ML training targets (insufficient resolution)
- SCADA telemetry (not included in public data)

---

## Dataset 2: EAGLE-I (Environment for Analysis of Geolocated Energy Information)

| Field | Value |
|---|---|
| **Name** | EAGLE-I Power Outage Data |
| **Publisher** | Oak Ridge National Laboratory (ORNL) |
| **Type** | Real-world, county-level |
| **2014 data** | https://openenergyhub.ornl.gov/explore/dataset/eaglei_outages_2014/ |
| **2014–2022** | https://impact.ornl.gov/en/datasets/eagle-i-power-outage-data-2014-2022/ |
| **2025 release** | https://doi.ccs.ornl.gov/dataset/c09fce3f-5faa-54ef-878a-cb0af6851cb6 |

### What it contains

County-level power outage data at **15-minute intervals**.

| Field | Description |
|---|---|
| `fips_code` | 5-digit county FIPS code |
| `county` | County name |
| `state` | US state |
| `sum_c` | Customers without power (count) |
| `run_start_time` | Timestamp of 15-minute observation window |

### How we use it

- Already incorporated in the **Event-Correlated v2 dataset** (primary download)
- For extended temporal validation: outage evolution over 15-minute intervals
- For geographic spread analysis: county-level spatial patterns
- The 2025 ORNL release provides a newer validation period for future work

> [!NOTE]
> We do **not** download the full multi-year EAGLE-I archive automatically (several GB). The Event-Correlated v2 dataset provides pre-processed EAGLE-I data in a manageable form.

---

## Dataset 3: DOE-417 (Electric Emergency Incident and Disturbance Reports)

| Field | Value |
|---|---|
| **Name** | DOE Form OE-417 |
| **Publisher** | U.S. Department of Energy / Energy Information Administration |
| **Official** | https://doe417.energy.gov/ |
| **Archive** | https://www.eia.gov/electricity/data/disturbance/disturb_events_archive.html |

### How we use it

- Already incorporated in the Event-Correlated v2 dataset
- Provides utility name, NERC region, event cause, states affected, demand loss (MW)
- Used for event-level metadata enrichment

---

## Dataset 4: Synthetic Scenarios [ML TRAINING DATA]

| Field | Value |
|---|---|
| **Name** | GridGuard Synthetic Scenarios |
| **Type** | Simulated (IEEE 33-bus + pandapower) |
| **Generated by** | `scenario/generator.py` |
| **Seed** | 42 (reproducible) |
| **Count** | 2,000 scenarios (5 event types) |

### Files (in `data/synthetic/`)

| File | Rows | Description |
|---|---|---|
| `scenarios.csv` | 2,000 | Scenario metadata: event_type, weather, load_factor |
| `component_states.csv` | 74,000 (2000×37) | **TRUE** component states per line per scenario |
| `observations.csv` | 74,000 | **OBSERVED** (noisy) states: SCADA, technician, weather |
| `powerflow_results.csv` | 2,000 | PF convergence, voltage bounds, line loading |
| `critical_impacts.csv` | 2,000 | MW unavailable, critical services offline |

### Key columns

**component_states.csv:**

| Column | Description |
|---|---|
| `scenario_id` | Scenario identifier |
| `line_idx` | pandapower line index (0–36) |
| `asset_id` | Asset name (L6-7, T3_LINE, etc.) |
| `true_failed` | **Ground truth** (1=failed, 0=healthy) — from simulator |
| `failure_probability` | Physics-based probability used to sample true state |
| `loading_pct` | Line loading fraction [0, 1] |
| `is_exposed` | 1 if overhead/weather-exposed |
| `age_factor` | Equipment age proxy [1.0, 2.5] |

**observations.csv:**

| Column | Description |
|---|---|
| `scada_reading` | Noisy SCADA failure indicator [0, 1] |
| `technician_confidence` | Human report confidence [0, 1] |
| `weather_evidence` | Weather-based evidence [0, 1] |
| `sensor_health` | SCADA reliability [0.1, 1] |
| `comm_available` | Communication link status (0/1) |
| `fused_probability` | Pre-fused Bayesian estimate [0, 1] |
| `is_uncertain` | 1 if fused_probability ∈ [0.25, 0.75] |

### Generation methodology

1. Select event type probabilistically (NORMAL 40%, SEVERE_STORM 30%, HIGH_WIND 15%, ICE_STORM 10%, HURRICANE 5%)
2. Sample environmental conditions from calibrated storm profile
3. Compute failure probability per line: `base_prob × loading_factor × age_factor × weather_severity_modifier`
4. Sample TRUE state: `Bernoulli(failure_probability)`
5. Generate OBSERVED state: add sensor noise proportional to weather severity
6. Run pandapower AC power flow on faulted network
7. Compute MW loss and critical service impacts

### Reproducibility

All scenarios are generated with `np.random.default_rng(seed=42)`. The same seed always produces identical scenarios.

---

## Data Pipeline

```
python -m data_pipeline.downloader          # Download Event-Correlated v2
python -m data_pipeline.preprocessor       # Build storm_profiles.csv
python run_pipeline.py                      # Full pipeline: preprocess → generate → train
```

---

## .gitignore

Raw datasets are not committed to the repository:
```
data/raw/
data/synthetic/
ml/models/
```

Download instructions are in `data_pipeline/downloader.py`.
