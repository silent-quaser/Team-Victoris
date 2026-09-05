import {
  Bus, Line, Transformer, DER, Fault, Scenario, CriticalService,
  RecoveryAction, Recommendation, ImpactAnalysis, RestorationProgress,
  GridState, Crew, Resource, ActivityEntry, RiskAssessment, WhatIfScenario
} from '@/types';

// ============================================================
// IEEE 33-Bus Test System — Mock Topology
// ============================================================

export const mockBuses: Bus[] = [
  // Substation
  { id: 'bus-1', number: 1, name: 'Substation', status: 'healthy', voltage_kv: 12.66, load_mw: 0, has_der: false, is_critical: false, latitude: 13.006700, longitude: 80.220600, x: 50, y: 300, feeder: 'main' },
  // Main Feeder F1 (buses 2–18)
  { id: 'bus-2', number: 2, name: 'Bus 2', status: 'healthy', voltage_kv: 12.62, load_mw: 0.1, has_der: false, is_critical: false, latitude: 13.007645, longitude: 80.221197, x: 150, y: 300, feeder: 'F1' },
  { id: 'bus-3', number: 3, name: 'Bus 3', status: 'healthy', voltage_kv: 12.58, load_mw: 0.09, has_der: false, is_critical: true, critical_facility: 'Apollo Hospital Guindy', latitude: 13.008617, longitude: 80.221977, x: 250, y: 300, feeder: 'F1' },
  { id: 'bus-4', number: 4, name: 'Bus 4', status: 'healthy', voltage_kv: 12.54, load_mw: 0.12, has_der: false, is_critical: false, latitude: 13.009413, longitude: 80.223429, x: 350, y: 300, feeder: 'F1' },
  { id: 'bus-5', number: 5, name: 'Bus 5', status: 'healthy', voltage_kv: 12.50, load_mw: 0.06, has_der: false, is_critical: false, latitude: 13.010588, longitude: 80.224411, x: 450, y: 300, feeder: 'F1' },
  { id: 'bus-6', number: 6, name: 'Bus 6', status: 'healthy', voltage_kv: 12.46, load_mw: 0.06, has_der: true, is_critical: false, latitude: 13.011423, longitude: 80.225071, x: 550, y: 300, feeder: 'F1' },
  { id: 'bus-7', number: 7, name: 'Bus 7', status: 'failed', voltage_kv: 0, load_mw: 0, has_der: false, is_critical: true, critical_facility: 'MIOT International', latitude: 13.012345, longitude: 80.225864, x: 650, y: 300, feeder: 'F1' },
  { id: 'bus-8', number: 8, name: 'Bus 8', status: 'failed', voltage_kv: 0, load_mw: 0, has_der: false, is_critical: false, latitude: 13.012879, longitude: 80.226944, x: 750, y: 300, feeder: 'F1' },
  { id: 'bus-9', number: 9, name: 'Bus 9', status: 'failed', voltage_kv: 0, load_mw: 0, has_der: false, is_critical: false, latitude: 13.014382, longitude: 80.227815, x: 850, y: 300, feeder: 'F1' },
  { id: 'bus-10', number: 10, name: 'Bus 10', status: 'failed', voltage_kv: 0, load_mw: 0, has_der: false, is_critical: true, critical_facility: 'Fortis Malar Hospital', latitude: 13.015405, longitude: 80.228400, x: 950, y: 300, feeder: 'F1' },
  { id: 'bus-11', number: 11, name: 'Bus 11', status: 'failed', voltage_kv: 0, load_mw: 0, has_der: false, is_critical: false, latitude: 13.016238, longitude: 80.229306, x: 1050, y: 300, feeder: 'F1' },
  { id: 'bus-12', number: 12, name: 'Bus 12', status: 'failed', voltage_kv: 0, load_mw: 0, has_der: false, is_critical: false, latitude: 13.017199, longitude: 80.230088, x: 1150, y: 300, feeder: 'F1' },
  { id: 'bus-13', number: 13, name: 'Bus 13', status: 'failed', voltage_kv: 0, load_mw: 0, has_der: true, is_critical: false, latitude: 13.018308, longitude: 80.231394, x: 1250, y: 300, feeder: 'F1' },
  { id: 'bus-14', number: 14, name: 'Bus 14', status: 'failed', voltage_kv: 0, load_mw: 0, has_der: false, is_critical: true, critical_facility: 'BSNL Exchange Guindy', latitude: 13.019930, longitude: 80.232253, x: 1350, y: 300, feeder: 'F1' },
  { id: 'bus-15', number: 15, name: 'Bus 15', status: 'failed', voltage_kv: 0, load_mw: 0, has_der: false, is_critical: false, latitude: 13.020758, longitude: 80.233391, x: 1450, y: 300, feeder: 'F1' },
  { id: 'bus-16', number: 16, name: 'Bus 16', status: 'failed', voltage_kv: 0, load_mw: 0, has_der: false, is_critical: false, latitude: 13.021675, longitude: 80.233955, x: 1550, y: 300, feeder: 'F1' },
  { id: 'bus-17', number: 17, name: 'Bus 17', status: 'failed', voltage_kv: 0, load_mw: 0, has_der: false, is_critical: false, latitude: 13.022659, longitude: 80.235373, x: 1650, y: 300, feeder: 'F1' },
  { id: 'bus-18', number: 18, name: 'Bus 18', status: 'failed', voltage_kv: 0, load_mw: 0, has_der: false, is_critical: true, critical_facility: 'Airtel Network Hub', latitude: 13.023532, longitude: 80.236325, x: 1750, y: 300, feeder: 'F1' },
  // Branch from Bus 2 (buses 19–22)
  { id: 'bus-19', number: 19, name: 'Bus 19', status: 'healthy', voltage_kv: 12.60, load_mw: 0.09, has_der: false, is_critical: false, latitude: 13.006771, longitude: 80.222324, x: 150, y: 150, feeder: 'F2' },
  { id: 'bus-20', number: 20, name: 'Bus 20', status: 'healthy', voltage_kv: 12.58, load_mw: 0.09, has_der: false, is_critical: false, latitude: 13.005436, longitude: 80.223355, x: 250, y: 150, feeder: 'F2' },
  { id: 'bus-21', number: 21, name: 'Bus 21', status: 'healthy', voltage_kv: 12.56, load_mw: 0.09, has_der: false, is_critical: true, critical_facility: 'Guindy Water Station', latitude: 13.004877, longitude: 80.224280, x: 350, y: 150, feeder: 'F2' },
  { id: 'bus-22', number: 22, name: 'Bus 22', status: 'healthy', voltage_kv: 12.54, load_mw: 0.09, has_der: true, is_critical: false, latitude: 13.004019, longitude: 80.225073, x: 450, y: 150, feeder: 'F2' },
  // Branch from Bus 3 (buses 23–25)
  { id: 'bus-23', number: 23, name: 'Bus 23', status: 'healthy', voltage_kv: 12.56, load_mw: 0.09, has_der: false, is_critical: false, latitude: 13.007953, longitude: 80.220929, x: 250, y: 450, feeder: 'F3' },
  { id: 'bus-24', number: 24, name: 'Bus 24', status: 'healthy', voltage_kv: 12.54, load_mw: 0.42, has_der: false, is_critical: true, critical_facility: 'Metro Water Treatment', latitude: 13.006991, longitude: 80.220479, x: 350, y: 450, feeder: 'F3' },
  { id: 'bus-25', number: 25, name: 'Bus 25', status: 'healthy', voltage_kv: 12.52, load_mw: 0.42, has_der: false, is_critical: false, latitude: 13.005902, longitude: 80.218941, x: 450, y: 450, feeder: 'F3' },
  // Branch from Bus 6 (buses 26–33)
  { id: 'bus-26', number: 26, name: 'Bus 26', status: 'failed', voltage_kv: 0, load_mw: 0, has_der: false, is_critical: false, latitude: 13.012221, longitude: 80.224090, x: 550, y: 450, feeder: 'F4' },
  { id: 'bus-27', number: 27, name: 'Bus 27', status: 'failed', voltage_kv: 0, load_mw: 0, has_der: false, is_critical: true, critical_facility: 'Guindy Fire Station', latitude: 13.012964, longitude: 80.223098, x: 650, y: 450, feeder: 'F4' },
  { id: 'bus-28', number: 28, name: 'Bus 28', status: 'failed', voltage_kv: 0, load_mw: 0, has_der: false, is_critical: false, latitude: 13.013828, longitude: 80.222193, x: 750, y: 450, feeder: 'F4' },
  { id: 'bus-29', number: 29, name: 'Bus 29', status: 'failed', voltage_kv: 0, load_mw: 0, has_der: false, is_critical: false, latitude: 13.014859, longitude: 80.220783, x: 850, y: 450, feeder: 'F4' },
  { id: 'bus-30', number: 30, name: 'Bus 30', status: 'failed', voltage_kv: 0, load_mw: 0, has_der: false, is_critical: true, critical_facility: 'Police Headquarters', latitude: 13.016454, longitude: 80.220058, x: 950, y: 450, feeder: 'F4' },
  { id: 'bus-31', number: 31, name: 'Bus 31', status: 'failed', voltage_kv: 0, load_mw: 0, has_der: false, is_critical: false, latitude: 13.018102, longitude: 80.219099, x: 1050, y: 450, feeder: 'F4' },
  { id: 'bus-32', number: 32, name: 'Bus 32', status: 'failed', voltage_kv: 0, load_mw: 0, has_der: false, is_critical: false, latitude: 13.018945, longitude: 80.217892, x: 1150, y: 450, feeder: 'F4' },
  { id: 'bus-33', number: 33, name: 'Bus 33', status: 'failed', voltage_kv: 0, load_mw: 0, has_der: true, is_critical: true, critical_facility: 'Guindy Metro Station', latitude: 13.020360, longitude: 80.216584, x: 1250, y: 450, feeder: 'F4' },
];

export const mockLines: Line[] = [
  // Main feeder
  { id: 'L1-2', from_bus: 'bus-1', to_bus: 'bus-2', status: 'healthy', type: 'feeder', length_km: 0.5, capacity_mw: 5, current_flow_mw: 3.2 },
  { id: 'L2-3', from_bus: 'bus-2', to_bus: 'bus-3', status: 'healthy', type: 'feeder', length_km: 0.6, capacity_mw: 5, current_flow_mw: 2.8 },
  { id: 'L3-4', from_bus: 'bus-3', to_bus: 'bus-4', status: 'healthy', type: 'feeder', length_km: 0.4, capacity_mw: 5, current_flow_mw: 2.4 },
  { id: 'L4-5', from_bus: 'bus-4', to_bus: 'bus-5', status: 'healthy', type: 'feeder', length_km: 0.7, capacity_mw: 5, current_flow_mw: 2.0 },
  { id: 'L5-6', from_bus: 'bus-5', to_bus: 'bus-6', status: 'healthy', type: 'feeder', length_km: 0.5, capacity_mw: 5, current_flow_mw: 1.6 },
  { id: 'L6-7', from_bus: 'bus-6', to_bus: 'bus-7', status: 'failed', type: 'feeder', length_km: 0.8, capacity_mw: 5, current_flow_mw: 0 },
  { id: 'L7-8', from_bus: 'bus-7', to_bus: 'bus-8', status: 'failed', type: 'feeder', length_km: 0.5, capacity_mw: 5, current_flow_mw: 0 },
  { id: 'L8-9', from_bus: 'bus-8', to_bus: 'bus-9', status: 'failed', type: 'feeder', length_km: 0.6, capacity_mw: 5, current_flow_mw: 0 },
  { id: 'L9-10', from_bus: 'bus-9', to_bus: 'bus-10', status: 'failed', type: 'feeder', length_km: 0.4, capacity_mw: 5, current_flow_mw: 0 },
  { id: 'L10-11', from_bus: 'bus-10', to_bus: 'bus-11', status: 'failed', type: 'feeder', length_km: 0.5, capacity_mw: 5, current_flow_mw: 0 },
  { id: 'L11-12', from_bus: 'bus-11', to_bus: 'bus-12', status: 'failed', type: 'feeder', length_km: 0.6, capacity_mw: 5, current_flow_mw: 0 },
  { id: 'L12-13', from_bus: 'bus-12', to_bus: 'bus-13', status: 'failed', type: 'feeder', length_km: 0.7, capacity_mw: 5, current_flow_mw: 0 },
  { id: 'L13-14', from_bus: 'bus-13', to_bus: 'bus-14', status: 'failed', type: 'feeder', length_km: 0.5, capacity_mw: 3, current_flow_mw: 0 },
  { id: 'L14-15', from_bus: 'bus-14', to_bus: 'bus-15', status: 'failed', type: 'feeder', length_km: 0.4, capacity_mw: 3, current_flow_mw: 0 },
  { id: 'L15-16', from_bus: 'bus-15', to_bus: 'bus-16', status: 'failed', type: 'feeder', length_km: 0.6, capacity_mw: 3, current_flow_mw: 0 },
  { id: 'L16-17', from_bus: 'bus-16', to_bus: 'bus-17', status: 'failed', type: 'feeder', length_km: 0.5, capacity_mw: 3, current_flow_mw: 0 },
  { id: 'L17-18', from_bus: 'bus-17', to_bus: 'bus-18', status: 'failed', type: 'feeder', length_km: 0.3, capacity_mw: 3, current_flow_mw: 0 },
  // Branch F2 from bus-2
  { id: 'L2-19', from_bus: 'bus-2', to_bus: 'bus-19', status: 'healthy', type: 'lateral', length_km: 0.3, capacity_mw: 2, current_flow_mw: 0.8 },
  { id: 'L19-20', from_bus: 'bus-19', to_bus: 'bus-20', status: 'healthy', type: 'lateral', length_km: 0.4, capacity_mw: 2, current_flow_mw: 0.6 },
  { id: 'L20-21', from_bus: 'bus-20', to_bus: 'bus-21', status: 'healthy', type: 'lateral', length_km: 0.3, capacity_mw: 2, current_flow_mw: 0.4 },
  { id: 'L21-22', from_bus: 'bus-21', to_bus: 'bus-22', status: 'healthy', type: 'lateral', length_km: 0.5, capacity_mw: 2, current_flow_mw: 0.2 },
  // Branch F3 from bus-3
  { id: 'L3-23', from_bus: 'bus-3', to_bus: 'bus-23', status: 'healthy', type: 'lateral', length_km: 0.4, capacity_mw: 2, current_flow_mw: 1.0 },
  { id: 'L23-24', from_bus: 'bus-23', to_bus: 'bus-24', status: 'healthy', type: 'lateral', length_km: 0.3, capacity_mw: 2, current_flow_mw: 0.8 },
  { id: 'L24-25', from_bus: 'bus-24', to_bus: 'bus-25', status: 'healthy', type: 'lateral', length_km: 0.5, capacity_mw: 2, current_flow_mw: 0.4 },
  // Branch F4 from bus-6
  { id: 'L25-26', from_bus: 'bus-25', to_bus: 'bus-26', status: 'failed', type: 'lateral', length_km: 0.6, capacity_mw: 2, current_flow_mw: 0 },
  { id: 'L26-27', from_bus: 'bus-26', to_bus: 'bus-27', status: 'failed', type: 'lateral', length_km: 0.4, capacity_mw: 2, current_flow_mw: 0 },
  { id: 'L27-28', from_bus: 'bus-27', to_bus: 'bus-28', status: 'failed', type: 'lateral', length_km: 0.3, capacity_mw: 2, current_flow_mw: 0 },
  { id: 'L28-29', from_bus: 'bus-28', to_bus: 'bus-29', status: 'failed', type: 'lateral', length_km: 0.5, capacity_mw: 2, current_flow_mw: 0 },
  { id: 'L29-30', from_bus: 'bus-29', to_bus: 'bus-30', status: 'failed', type: 'lateral', length_km: 0.6, capacity_mw: 2, current_flow_mw: 0 },
  { id: 'L30-31', from_bus: 'bus-30', to_bus: 'bus-31', status: 'failed', type: 'lateral', length_km: 0.4, capacity_mw: 2, current_flow_mw: 0 },
  { id: 'L31-32', from_bus: 'bus-31', to_bus: 'bus-32', status: 'failed', type: 'lateral', length_km: 0.3, capacity_mw: 2, current_flow_mw: 0 },
  { id: 'L32-33', from_bus: 'bus-32', to_bus: 'bus-33', status: 'failed', type: 'lateral', length_km: 0.5, capacity_mw: 2, current_flow_mw: 0 },
];

export const mockTransformers: Transformer[] = [
  { id: 'T1', name: 'Transformer T1', bus_id: 'bus-1', status: 'healthy', rating_mva: 10, load_pct: 65, tap_position: 3 },
  { id: 'T2', name: 'Transformer T2', bus_id: 'bus-6', status: 'healthy', rating_mva: 5, load_pct: 42, tap_position: 2 },
  { id: 'T3', name: 'Transformer T3', bus_id: 'bus-7', status: 'uncertain', rating_mva: 5, load_pct: 0, tap_position: 0 },
  { id: 'T4', name: 'Transformer T4', bus_id: 'bus-13', status: 'failed', rating_mva: 3, load_pct: 0, tap_position: 0 },
];

export const mockDERs: DER[] = [
  { id: 'DER-1', bus_id: 'bus-6', type: 'solar', capacity_mw: 1.5, current_output_mw: 0.8, status: 'healthy' },
  { id: 'DER-2', bus_id: 'bus-22', type: 'battery', capacity_mw: 0.5, current_output_mw: 0.3, status: 'healthy' },
  { id: 'DER-3', bus_id: 'bus-13', type: 'diesel', capacity_mw: 2.0, current_output_mw: 0, status: 'failed' },
  { id: 'DER-4', bus_id: 'bus-33', type: 'wind', capacity_mw: 1.0, current_output_mw: 0, status: 'failed' },
];

export const mockFaults: Fault[] = [
  { id: 'fault-1', asset_id: 'L6-7', asset_name: 'Line L6-7', asset_type: 'line', status: 'failed', confidence_pct: 100, detected_at: '2024-11-27T14:18:00Z', description: 'Conductor down due to wind damage' },
  { id: 'fault-2', asset_id: 'T3', asset_name: 'Transformer T3', asset_type: 'transformer', status: 'uncertain', confidence_pct: 62, detected_at: '2024-11-27T14:22:00Z', description: 'Possible insulation failure — sensor data ambiguous' },
  { id: 'fault-3', asset_id: 'L12-13', asset_name: 'Line L12-13', asset_type: 'line', status: 'failed', confidence_pct: 98, detected_at: '2024-11-27T14:25:00Z', description: 'Tree contact caused phase-to-ground fault' },
  { id: 'fault-4', asset_id: 'L25-26', asset_name: 'Line L25-26', asset_type: 'line', status: 'failed', confidence_pct: 95, detected_at: '2024-11-27T14:30:00Z', description: 'Pole damage from debris impact' },
];

export const mockScenario: Scenario = {
  id: 'scenario-1',
  name: 'Severe Storm Event',
  description: 'Multi-fault event caused by severe storm with high winds and heavy rain',
  started_at: '2024-11-27T14:15:00Z',
  weather: { wind_kmh: 78, rain: 'Heavy', temperature_c: 12 },
  faults: mockFaults,
  is_active: true,
};

export const mockServices: CriticalService[] = [
  { id: 'svc-1', name: 'Apollo Hospital Guindy', type: 'hospital', status: 'offline', load_mw: 2.4, priority: 1, bus_id: 'bus-3', backup_available: true, estimated_restore: '2024-11-27T18:00:00Z' },
  { id: 'svc-2', name: 'Metro Water Treatment', type: 'water', status: 'offline', load_mw: 1.8, priority: 2, bus_id: 'bus-24', backup_available: false },
  { id: 'svc-3', name: 'BSNL Exchange Guindy', type: 'telecom', status: 'degraded', load_mw: 0.6, priority: 3, bus_id: 'bus-14', backup_available: true },
  { id: 'svc-4', name: 'Guindy Fire Station', type: 'emergency', status: 'online', load_mw: 0.8, priority: 1, bus_id: 'bus-27', backup_available: true },
  { id: 'svc-5', name: 'Velachery Residential Zone', type: 'residential', status: 'partially_supplied', load_mw: 3.2, priority: 4, bus_id: 'bus-8', backup_available: false },
  { id: 'svc-6', name: 'Phoenix Marketcity Mall', type: 'commercial', status: 'partially_supplied', load_mw: 1.6, priority: 5, bus_id: 'bus-11', backup_available: false },
  { id: 'svc-7', name: 'Guindy Industrial Estate', type: 'industrial', status: 'online', load_mw: 2.1, priority: 6, bus_id: 'bus-4', backup_available: true },
  { id: 'svc-8', name: 'MIOT International', type: 'hospital', status: 'offline', load_mw: 3.5, priority: 1, bus_id: 'bus-7', backup_available: true },
  { id: 'svc-9', name: 'Police Headquarters', type: 'emergency', status: 'online', load_mw: 1.2, priority: 1, bus_id: 'bus-30', backup_available: true }
];

export const mockRecommendation: Recommendation = {
  id: 'rec-1',
  action: {
    id: 'action-1',
    name: 'Inspect Transformer T3',
    description: 'Dispatch crew to inspect Transformer T3 at Bus 7',
    type: 'inspect',
    target_asset_id: 'T3',
    priority: 'high',
    estimated_duration_min: 45,
    crew_required: 1,
    decision_value: 0.87,
  },
  uncertainty_pct: 62,
  critical_impact: 'high',
  explanation: 'T3 has high uncertainty and affects Hospital, Water Plant and downstream loads. Inspection can reduce decision risk and may change the optimal recovery sequence.',
  label: 'VALUE OF INFORMATION',
  alternatives: [
    { id: 'action-2', name: 'Reconfigure Feeder F2', description: 'Switch feeder F2 to alternate supply path', type: 'reconfigure', target_asset_id: 'L6-7', priority: 'high', estimated_duration_min: 30, crew_required: 1, decision_value: 0.72 },
    { id: 'action-3', name: 'Island Hospital Microgrid', description: 'Activate hospital microgrid with local DER', type: 'island', target_asset_id: 'bus-9', priority: 'high', estimated_duration_min: 20, crew_required: 1, decision_value: 0.65 },
    { id: 'action-4', name: 'Repair Line L12-13', description: 'Deploy crew to repair faulted line L12-13', type: 'repair', target_asset_id: 'L12-13', priority: 'medium', estimated_duration_min: 120, crew_required: 2, decision_value: 0.51 },
  ],
};

export const mockImpact: ImpactAnalysis = {
  services: mockServices,
  total_load_mw: 12.5,
  recoverable_load_pct: 72,
  customers_affected: 4520,
  buses_out: 12,
  critical_facilities_offline: 3,
};

export const mockRestoration: RestorationProgress = {
  current_stage: 'next_action',
  pct_complete: 28,
  stages: [
    { id: 'initial_state', label: 'Initial State', status: 'completed', timestamp: '2024-11-27T14:15:00Z' },
    { id: 'fault_detection', label: 'Fault Detection', status: 'completed', timestamp: '2024-11-27T14:18:00Z' },
    { id: 'impact_assessment', label: 'Impact Assessment', status: 'completed', timestamp: '2024-11-27T14:35:00Z' },
    { id: 'next_action', label: 'Next Action', status: 'active' },
    { id: 'execute_action', label: 'Execute Action', status: 'pending' },
    { id: 're_evaluate', label: 'Re-evaluate', status: 'pending' },
  ],
};

export const mockCrews: Crew[] = [
  { id: 'crew-1', name: 'Alpha Team', status: 'available', members: 4, specialization: 'Line Repair', location: 'Depot A' },
  { id: 'crew-2', name: 'Beta Team', status: 'deployed', current_task: 'Patrolling Feeder F1', members: 3, specialization: 'Switching', location: 'Bus 5 Area' },
  { id: 'crew-3', name: 'Gamma Team', status: 'en_route', current_task: 'Responding to L25-26', members: 4, specialization: 'Line Repair', location: 'En route' },
  { id: 'crew-4', name: 'Delta Team', status: 'off_duty', members: 3, specialization: 'Transformer', location: 'Off-site' },
];

export const mockResources: Resource[] = [
  { id: 'res-1', type: 'crew', name: 'Field Crews', quantity: 4, available: 2, unit: 'teams' },
  { id: 'res-2', type: 'equipment', name: 'Mobile Generators', quantity: 3, available: 2, unit: 'units' },
  { id: 'res-3', type: 'equipment', name: 'Bucket Trucks', quantity: 5, available: 3, unit: 'vehicles' },
  { id: 'res-4', type: 'material', name: 'Conductor (ACSR)', quantity: 2000, available: 1500, unit: 'meters' },
  { id: 'res-5', type: 'material', name: 'Poles (Wood)', quantity: 20, available: 15, unit: 'units' },
  { id: 'res-6', type: 'equipment', name: 'Fault Locators', quantity: 4, available: 3, unit: 'devices' },
];

export const mockActivityLog: ActivityEntry[] = [
  { id: 'log-1', timestamp: '2024-11-27T14:15:00Z', type: 'alert', severity: 'error', message: 'Severe storm warning issued for service territory', user: 'System' },
  { id: 'log-2', timestamp: '2024-11-27T14:18:00Z', type: 'alert', severity: 'error', message: 'Fault detected on Line L6-7 — conductor down', user: 'SCADA' },
  { id: 'log-3', timestamp: '2024-11-27T14:22:00Z', type: 'alert', severity: 'warning', message: 'Transformer T3 reporting anomalous readings — status uncertain', user: 'SCADA' },
  { id: 'log-4', timestamp: '2024-11-27T14:25:00Z', type: 'alert', severity: 'error', message: 'Fault detected on Line L12-13 — tree contact', user: 'SCADA' },
  { id: 'log-5', timestamp: '2024-11-27T14:28:00Z', type: 'system', severity: 'info', message: 'Impact assessment initiated for Scenario: Severe Storm Event', user: 'GridGuard' },
  { id: 'log-6', timestamp: '2024-11-27T14:30:00Z', type: 'alert', severity: 'error', message: 'Fault detected on Line L25-26 — pole damage', user: 'SCADA' },
  { id: 'log-7', timestamp: '2024-11-27T14:32:00Z', type: 'operator', severity: 'info', message: 'Beta Team dispatched to patrol Feeder F1', user: 'Operator Sharma' },
  { id: 'log-8', timestamp: '2024-11-27T14:35:00Z', type: 'system', severity: 'success', message: 'Impact assessment complete — 4,520 customers affected, 3 critical facilities offline', user: 'GridGuard' },
  { id: 'log-9', timestamp: '2024-11-27T14:38:00Z', type: 'system', severity: 'info', message: 'Recovery recommendation generated: Inspect Transformer T3 (VOI = 0.87)', user: 'GridGuard' },
  { id: 'log-10', timestamp: '2024-11-27T14:40:00Z', type: 'operator', severity: 'info', message: 'Gamma Team dispatched to respond to L25-26 fault', user: 'Operator Sharma' },
];

export const mockRiskAssessments: RiskAssessment[] = [
  { id: 'risk-1', asset_id: 'T3', asset_name: 'Transformer T3', risk_level: 'critical', probability: 0.62, impact_score: 0.91, uncertainty: 0.62, mitigation: 'Inspect to resolve uncertainty before committing recovery resources' },
  { id: 'risk-2', asset_id: 'L6-7', asset_name: 'Line L6-7', risk_level: 'high', probability: 1.0, impact_score: 0.85, uncertainty: 0.0, mitigation: 'Repair after T3 status is confirmed' },
  { id: 'risk-3', asset_id: 'L12-13', asset_name: 'Line L12-13', risk_level: 'high', probability: 0.98, impact_score: 0.72, uncertainty: 0.02, mitigation: 'Schedule repair crew after priority faults' },
  { id: 'risk-4', asset_id: 'L25-26', asset_name: 'Line L25-26', risk_level: 'medium', probability: 0.95, impact_score: 0.55, uncertainty: 0.05, mitigation: 'Gamma Team en route' },
  { id: 'risk-5', asset_id: 'bus-9', asset_name: 'Hospital Bus', risk_level: 'critical', probability: 0.88, impact_score: 0.95, uncertainty: 0.38, mitigation: 'Consider microgrid islanding as contingency' },
];

export const mockWhatIfScenarios: WhatIfScenario[] = [
  {
    id: 'whatif-1',
    name: 'T3 Confirmed Failed',
    description: 'What if Transformer T3 is confirmed as failed?',
    base_scenario_id: 'scenario-1',
    modifications: [
      { asset_id: 'T3', field: 'status', original_value: 'uncertain', new_value: 'failed' },
    ],
    results: { load_restored_pct: 58, customers_restored: 2620, time_to_restore_min: 240, risk_score: 0.72 },
  },
  {
    id: 'whatif-2',
    name: 'T3 Confirmed Healthy',
    description: 'What if Transformer T3 is actually healthy?',
    base_scenario_id: 'scenario-1',
    modifications: [
      { asset_id: 'T3', field: 'status', original_value: 'uncertain', new_value: 'healthy' },
    ],
    results: { load_restored_pct: 85, customers_restored: 3842, time_to_restore_min: 120, risk_score: 0.31 },
  },
  {
    id: 'whatif-3',
    name: 'Hospital Microgrid Active',
    description: 'What if hospital microgrid is islanded with local DER?',
    base_scenario_id: 'scenario-1',
    modifications: [
      { asset_id: 'bus-9', field: 'der_active', original_value: 'false', new_value: 'true' },
    ],
    results: { load_restored_pct: 74, customers_restored: 4520, time_to_restore_min: 180, risk_score: 0.45 },
  },
];

// ============================================================
// Assembled initial grid state
// ============================================================

export const initialGridState: GridState = {
  buses: mockBuses,
  lines: mockLines,
  transformers: mockTransformers,
  ders: mockDERs,
  scenario: mockScenario,
  impact: mockImpact,
  recommendation: mockRecommendation,
  restoration: mockRestoration,
  services: mockServices,
  timestamp: '2024-11-27T14:40:00Z',
};
