# GridGuard — Frontend API Contract

> This document defines the typed interfaces used by the GridGuard frontend.
> Backend team: implement API endpoints returning data conforming to these interfaces.

---

## Data Flow Architecture

```
Backend API  ──▶  src/types/index.ts (contracts)
                        │
                        ▼
              src/data/mock-data.ts (dev stubs)
                        │
                        ▼
              src/store/grid-store.ts (Zustand state)
                        │
                        ▼
              React Components (consume via selectors)
```

The frontend currently uses **mock data** (`src/data/mock-data.ts`) shaped to match the
type contracts. When the backend is ready, replace mock imports with `fetch()`/API calls
and hydrate the same Zustand store.

---

## Core Type Contracts

All types are defined in **`src/types/index.ts`**.

### Grid Topology

| Interface | Description |
|-----------|-------------|
| `Bus` | A node in the distribution network. Fields: `id`, `number`, `name`, `status`, `voltage_kv`, `load_mw`, `has_der`, `is_critical`, `critical_facility?`, `x`, `y`, `feeder?` |
| `Line` | An edge connecting two buses. Fields: `id`, `from_bus`, `to_bus`, `status`, `type` (feeder/lateral/tie), `length_km`, `capacity_mw`, `current_flow_mw` |
| `Transformer` | A power transformer at a bus. Fields: `id`, `name`, `bus_id`, `status`, `rating_mva`, `load_pct`, `tap_position` |
| `DER` | Distributed Energy Resource. Fields: `id`, `bus_id`, `type` (solar/battery/diesel/wind), `capacity_mw`, `current_output_mw`, `status` |
| `Asset` | Generic asset wrapper. Fields: `id`, `type`, `name`, `status`, `details` |

### Faults & Scenarios

| Interface | Description |
|-----------|-------------|
| `Fault` | A fault on an asset. Fields: `id`, `asset_id`, `asset_name`, `asset_type`, `status` (failed/uncertain), `confidence_pct`, `detected_at`, `description?` |
| `WeatherConditions` | Current weather. Fields: `wind_kmh`, `rain`, `temperature_c` |
| `Scenario` | An event scenario. Fields: `id`, `name`, `description`, `started_at`, `weather`, `faults[]`, `is_active` |

### Critical Services

| Interface | Description |
|-----------|-------------|
| `CriticalService` | A critical infrastructure service. Fields: `id`, `name`, `type`, `status` (online/offline/degraded/partially_supplied), `load_mw`, `priority`, `bus_id`, `backup_available`, `estimated_restore?` |

### Recovery & Recommendations

| Interface | Description |
|-----------|-------------|
| `RecoveryAction` | A recovery action. Fields: `id`, `name`, `description`, `type` (inspect/repair/reconfigure/island/switch/deploy), `target_asset_id`, `priority`, `estimated_duration_min`, `crew_required`, `decision_value` |
| `Recommendation` | A recommended action with alternatives. Fields: `id`, `action`, `uncertainty_pct`, `critical_impact`, `explanation`, `label`, `alternatives[]` |

### Impact Analysis

| Interface | Description |
|-----------|-------------|
| `ImpactAnalysis` | Aggregated impact metrics. Fields: `services[]`, `total_load_mw`, `recoverable_load_pct`, `customers_affected`, `buses_out`, `critical_facilities_offline` |

### Restoration Progress

| Interface | Description |
|-----------|-------------|
| `RestorationProgress` | Current restoration state. Fields: `current_stage`, `pct_complete`, `stages[]` with `id`, `label`, `status`, `timestamp?` |

### Grid State (Top-Level Aggregate)

| Interface | Description |
|-----------|-------------|
| `GridState` | Full grid snapshot. Fields: `buses[]`, `lines[]`, `transformers[]`, `ders[]`, `scenario`, `impact`, `recommendation`, `restoration`, `services[]`, `timestamp` |

### Resources

| Interface | Description |
|-----------|-------------|
| `Crew` | A field crew. Fields: `id`, `name`, `status` (available/deployed/en_route/off_duty), `current_task?`, `location?`, `members`, `specialization` |
| `Resource` | Equipment/material. Fields: `id`, `type`, `name`, `quantity`, `available`, `unit` |

### Activity Log

| Interface | Description |
|-----------|-------------|
| `ActivityEntry` | A log entry. Fields: `id`, `timestamp`, `type` (action/alert/system/operator), `severity` (info/warning/error/success), `message`, `details?`, `user?` |

### What-If Analysis

| Interface | Description |
|-----------|-------------|
| `WhatIfScenario` | A what-if scenario. Fields: `id`, `name`, `description`, `base_scenario_id`, `modifications[]`, `results?` (load_restored_pct, customers_restored, time_to_restore_min, risk_score) |

### Risk & Uncertainty

| Interface | Description |
|-----------|-------------|
| `RiskAssessment` | Risk assessment for an asset. Fields: `id`, `asset_id`, `asset_name`, `risk_level` (critical/high/medium/low), `probability`, `impact_score`, `uncertainty`, `mitigation?` |

### Settings

| Interface | Description |
|-----------|-------------|
| `AppSettings` | Application settings. Fields: `simulation_mode`, `auto_refresh_sec`, `operator_name`, `operator_role`, `notifications_enabled`, `theme` |

---

## API Response Wrapper

All backend endpoints should return responses wrapped in:

```typescript
interface ApiResponse<T> {
  data: T;
  timestamp: string;    // ISO 8601
  status: 'ok' | 'error';
  message?: string;
}
```

---

## Suggested API Endpoints

| Endpoint | Method | Returns | Description |
|----------|--------|---------|-------------|
| `/api/grid/state` | GET | `ApiResponse<GridState>` | Full grid snapshot |
| `/api/grid/buses` | GET | `ApiResponse<Bus[]>` | All buses |
| `/api/grid/lines` | GET | `ApiResponse<Line[]>` | All lines |
| `/api/grid/transformers` | GET | `ApiResponse<Transformer[]>` | All transformers |
| `/api/grid/ders` | GET | `ApiResponse<DER[]>` | All DERs |
| `/api/scenarios/active` | GET | `ApiResponse<Scenario>` | Active scenario |
| `/api/scenarios` | GET | `ApiResponse<Scenario[]>` | All scenarios |
| `/api/faults` | GET | `ApiResponse<Fault[]>` | Active faults |
| `/api/services` | GET | `ApiResponse<CriticalService[]>` | Critical services |
| `/api/recommendation` | GET | `ApiResponse<Recommendation>` | Current recommendation |
| `/api/impact` | GET | `ApiResponse<ImpactAnalysis>` | Impact analysis |
| `/api/restoration` | GET | `ApiResponse<RestorationProgress>` | Restoration progress |
| `/api/resources/crews` | GET | `ApiResponse<Crew[]>` | Field crews |
| `/api/resources/equipment` | GET | `ApiResponse<Resource[]>` | Equipment & materials |
| `/api/activity-log` | GET | `ApiResponse<ActivityEntry[]>` | Activity log entries |
| `/api/risk` | GET | `ApiResponse<RiskAssessment[]>` | Risk assessments |
| `/api/what-if` | GET | `ApiResponse<WhatIfScenario[]>` | What-if scenarios |
| `/api/what-if` | POST | `ApiResponse<WhatIfScenario>` | Run what-if simulation |
| `/api/actions/confirm` | POST | `ApiResponse<{success: boolean}>` | Confirm a recovery action |
| `/api/actions/inspect` | POST | `ApiResponse<{asset_id: string, result: AssetStatus}>` | Inspect an asset |

---

## Frontend State Transitions

The frontend implements one demo state transition:

### Inspect Transformer T3

**Trigger:** User clicks "Confirm Action" on the recommended action (Inspect T3)

**Before:**
- T3 status: `uncertain`
- T3 confidence: 62%
- Recommendation: Inspect T3 (VOI = 0.87)

**After:**
- T3 status: `failed` (confirmed)
- T3 confidence: 100%
- New recommendation: Island Hospital Microgrid (VOI = 0.92)
- Restoration progress advances to "Execute Action" (45%)
- Activity log updated with inspection result
- Telecom Tower status changes to `offline`

**Backend contract:** When connected, the `POST /api/actions/inspect` endpoint should return the new asset status, and the frontend should re-fetch `/api/grid/state` to get the updated state.

---

## Status Enumerations

### AssetStatus
`'healthy' | 'failed' | 'uncertain' | 'selected'`

### ServiceStatus
`'online' | 'offline' | 'degraded' | 'partially_supplied'`

### RestorationStage
`'initial_state' | 'fault_detection' | 'impact_assessment' | 'next_action' | 'execute_action' | 're_evaluate'`

---

## Color Mapping (UI Convention)

| Status | Color | Hex |
|--------|-------|-----|
| healthy / online / success | Green | `#22c55e` |
| failed / offline / error | Red | `#ef4444` |
| uncertain / degraded / warning | Amber | `#f59e0b` |
| selected / recommended / info | Blue | `#3b82f6` |
