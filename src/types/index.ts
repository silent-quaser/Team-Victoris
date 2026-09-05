// ============================================================
// GridGuard — Frontend Type Contracts
// All types used by the UI. Backend team: implement these interfaces.
// ============================================================

// ---- Grid Topology ----

export type AssetStatus = 'healthy' | 'failed' | 'uncertain' | 'selected';

export interface Bus {
  id: string;
  number: number;
  name: string;
  status: AssetStatus;
  voltage_kv: number;
  load_mw: number;
  has_der: boolean;
  is_critical: boolean;
  critical_facility?: string;
  x: number;       // layout x position (for visualization)
  y: number;       // layout y position (for visualization)
  feeder?: string;
}

export interface Line {
  id: string;
  from_bus: string;
  to_bus: string;
  status: AssetStatus;
  type: 'feeder' | 'lateral' | 'tie';
  length_km: number;
  capacity_mw: number;
  current_flow_mw: number;
}

export interface Transformer {
  id: string;
  name: string;
  bus_id: string;
  status: AssetStatus;
  rating_mva: number;
  load_pct: number;
  tap_position: number;
}

export interface DER {
  id: string;
  bus_id: string;
  type: 'solar' | 'battery' | 'diesel' | 'wind';
  capacity_mw: number;
  current_output_mw: number;
  status: AssetStatus;
}

export interface Asset {
  id: string;
  type: 'bus' | 'line' | 'transformer' | 'der';
  name: string;
  status: AssetStatus;
  details: Record<string, string | number | boolean>;
}

// ---- Faults & Scenarios ----

export interface Fault {
  id: string;
  asset_id: string;
  asset_name: string;
  asset_type: 'line' | 'transformer' | 'bus';
  status: 'failed' | 'uncertain';
  confidence_pct: number;
  detected_at: string;      // ISO timestamp
  description?: string;
}

export interface WeatherConditions {
  wind_kmh: number;
  rain: 'None' | 'Light' | 'Moderate' | 'Heavy';
  temperature_c: number;
}

export interface Scenario {
  id: string;
  name: string;
  description: string;
  started_at: string;        // ISO timestamp
  weather: WeatherConditions;
  faults: Fault[];
  is_active: boolean;
}

// ---- Critical Services ----

export type ServiceStatus = 'online' | 'offline' | 'degraded' | 'partially_supplied';

export interface CriticalService {
  id: string;
  name: string;
  type: 'hospital' | 'water' | 'telecom' | 'emergency' | 'residential' | 'commercial' | 'industrial';
  status: ServiceStatus;
  load_mw: number;
  priority: number;          // 1 = highest
  bus_id: string;
  backup_available: boolean;
  estimated_restore?: string; // ISO timestamp
}

// ---- Recovery & Recommendations ----

export interface RecoveryAction {
  id: string;
  name: string;
  description: string;
  type: 'inspect' | 'repair' | 'reconfigure' | 'island' | 'switch' | 'deploy';
  target_asset_id: string;
  priority: 'critical' | 'high' | 'medium' | 'low';
  estimated_duration_min: number;
  crew_required: number;
  decision_value: number;    // 0–1, value-of-information score
}

export interface Recommendation {
  id: string;
  action: RecoveryAction;
  uncertainty_pct: number;
  critical_impact: 'high' | 'medium' | 'low';
  explanation: string;
  label: string;             // e.g., "VALUE OF INFORMATION"
  alternatives: RecoveryAction[];
}

// ---- Impact Analysis ----

export interface ImpactAnalysis {
  services: CriticalService[];
  total_load_mw: number;
  recoverable_load_pct: number;
  customers_affected: number;
  buses_out: number;
  critical_facilities_offline: number;
}

// ---- Restoration Progress ----

export type RestorationStage =
  | 'initial_state'
  | 'fault_detection'
  | 'impact_assessment'
  | 'next_action'
  | 'execute_action'
  | 're_evaluate';

export interface RestorationProgress {
  current_stage: RestorationStage;
  pct_complete: number;
  stages: {
    id: RestorationStage;
    label: string;
    status: 'completed' | 'active' | 'pending';
    timestamp?: string;
  }[];
}

// ---- Grid State (top-level aggregate) ----

export interface GridState {
  buses: Bus[];
  lines: Line[];
  transformers: Transformer[];
  ders: DER[];
  scenario: Scenario;
  impact: ImpactAnalysis;
  recommendation: Recommendation;
  restoration: RestorationProgress;
  services: CriticalService[];
  timestamp: string;
}

// ---- Resources ----

export interface Crew {
  id: string;
  name: string;
  status: 'available' | 'deployed' | 'en_route' | 'off_duty';
  current_task?: string;
  location?: string;
  members: number;
  specialization: string;
}

export interface Resource {
  id: string;
  type: 'crew' | 'equipment' | 'material';
  name: string;
  quantity: number;
  available: number;
  unit: string;
}

// ---- Activity Log ----

export interface ActivityEntry {
  id: string;
  timestamp: string;
  type: 'action' | 'alert' | 'system' | 'operator';
  severity: 'info' | 'warning' | 'error' | 'success';
  message: string;
  details?: string;
  user?: string;
}

// ---- What-If Analysis ----

export interface WhatIfScenario {
  id: string;
  name: string;
  description: string;
  base_scenario_id: string;
  modifications: {
    asset_id: string;
    field: string;
    original_value: string | number;
    new_value: string | number;
  }[];
  results?: {
    load_restored_pct: number;
    customers_restored: number;
    time_to_restore_min: number;
    risk_score: number;
  };
}

// ---- Risk & Uncertainty ----

export interface RiskAssessment {
  id: string;
  asset_id: string;
  asset_name: string;
  risk_level: 'critical' | 'high' | 'medium' | 'low';
  probability: number;       // 0–1
  impact_score: number;      // 0–1
  uncertainty: number;       // 0–1
  mitigation?: string;
}

// ---- Settings ----

export interface AppSettings {
  simulation_mode: 'local' | 'connected';
  auto_refresh_sec: number;
  operator_name: string;
  operator_role: string;
  notifications_enabled: boolean;
  theme: 'light';            // only light theme
}

// ---- API Response Wrapper ----

export interface ApiResponse<T> {
  data: T;
  timestamp: string;
  status: 'ok' | 'error';
  message?: string;
}
