'use client';

import { create } from 'zustand';
import {
  GridState, Bus, Line, Transformer, Fault, Recommendation,
  RestorationProgress, ActivityEntry, CriticalService
} from '@/types';
import {
  initialGridState, mockActivityLog, mockFaults, mockRecommendation,
  mockRestoration, mockServices
} from '@/data/mock-data';

interface GridStore {
  // State
  gridState: GridState;
  activityLog: ActivityEntry[];
  selectedAssetId: string | null;
  assetDrawerOpen: boolean;
  currentPage: string;
  t3Inspected: boolean;

  // Actions
  setCurrentPage: (page: string) => void;
  selectAsset: (assetId: string | null) => void;
  closeAssetDrawer: () => void;
  confirmAction: (actionId: string) => void;
  inspectT3: () => void;
  islandHospital: () => void;
  addLog: (message: string, severity?: 'info' | 'warning' | 'error' | 'success') => void;
}

export const useGridStore = create<GridStore>((set, get) => ({
  gridState: initialGridState,
  activityLog: [...mockActivityLog],
  selectedAssetId: null,
  assetDrawerOpen: false,
  currentPage: 'overview',
  t3Inspected: false,

  setCurrentPage: (page: string) => set({ currentPage: page }),

  selectAsset: (assetId: string | null) =>
    set({ selectedAssetId: assetId, assetDrawerOpen: assetId !== null }),

  closeAssetDrawer: () =>
    set({ selectedAssetId: null, assetDrawerOpen: false }),

  addLog: (message: string, severity: 'info' | 'warning' | 'error' | 'success' = 'info') => {
    const newLogEntry: ActivityEntry = {
      id: `log-${Date.now()}`,
      timestamp: new Date().toISOString(),
      type: 'operator',
      severity,
      message,
      user: 'Operator Sharma',
    };
    set(state => ({ activityLog: [newLogEntry, ...state.activityLog] }));
  },

  confirmAction: (actionId: string) => {
    if (actionId === 'action-1') {
      get().inspectT3();
    } else if (actionId === 'action-5') {
      get().islandHospital();
    }
  },

  islandHospital: () => {
    const state = get();
    
    const updatedServices = state.gridState.services.map(s => 
      s.name === 'Hospital' ? { ...s, status: 'online' as const } : s
    );

    const updatedBuses = state.gridState.buses.map(b => 
      b.id === 'bus-9' ? { ...b, status: 'healthy' as const } : b
    );

    const newLogEntry: ActivityEntry = {
      id: `log-${Date.now()}`,
      timestamp: new Date().toISOString(),
      type: 'action',
      severity: 'success',
      message: 'Hospital Microgrid successfully islanded. Critical load restored.',
      user: 'Operator Sharma',
    };

    set({
      gridState: {
        ...state.gridState,
        buses: updatedBuses,
        services: updatedServices,
        restoration: {
          ...state.gridState.restoration,
          pct_complete: 65,
        }
      },
      activityLog: [newLogEntry, ...state.activityLog],
    });
  },

  inspectT3: () => {
    const state = get();
    if (state.t3Inspected) return;

    // T3 inspection reveals it is FAILED
    const updatedTransformers: Transformer[] = state.gridState.transformers.map(t =>
      t.id === 'T3' ? { ...t, status: 'failed' as const } : t
    );

    // Update faults: T3 is now confirmed failed
    const updatedFaults: Fault[] = state.gridState.scenario.faults.map(f =>
      f.asset_id === 'T3'
        ? { ...f, status: 'failed' as const, confidence_pct: 100 }
        : f
    );

    // New recommendation after T3 is confirmed failed
    const newRecommendation: Recommendation = {
      id: 'rec-2',
      action: {
        id: 'action-5',
        name: 'Island Hospital Microgrid',
        description: 'Activate hospital microgrid with local DER to restore critical load',
        type: 'island',
        target_asset_id: 'bus-9',
        priority: 'critical',
        estimated_duration_min: 20,
        crew_required: 1,
        decision_value: 0.92,
      },
      uncertainty_pct: 8,
      critical_impact: 'high',
      explanation:
        'With T3 confirmed failed, the optimal path is to island the Hospital microgrid using local DER while scheduling T3 replacement. This restores the highest-priority critical service immediately.',
      label: 'OPTIMAL RECOVERY',
      alternatives: [
        { id: 'action-2', name: 'Reconfigure Feeder F2', description: 'Switch feeder F2 to alternate supply path', type: 'reconfigure', target_asset_id: 'L6-7', priority: 'high', estimated_duration_min: 30, crew_required: 1, decision_value: 0.78 },
        { id: 'action-6', name: 'Replace Transformer T3', description: 'Deploy mobile transformer to Bus 7', type: 'repair', target_asset_id: 'T3', priority: 'high', estimated_duration_min: 180, crew_required: 2, decision_value: 0.65 },
        { id: 'action-4', name: 'Repair Line L12-13', description: 'Deploy crew to repair faulted line L12-13', type: 'repair', target_asset_id: 'L12-13', priority: 'medium', estimated_duration_min: 120, crew_required: 2, decision_value: 0.51 },
      ],
    };

    // Updated restoration progress
    const newRestoration: RestorationProgress = {
      current_stage: 'execute_action',
      pct_complete: 45,
      stages: [
        { id: 'initial_state', label: 'Initial State', status: 'completed', timestamp: '2024-11-27T14:15:00Z' },
        { id: 'fault_detection', label: 'Fault Detection', status: 'completed', timestamp: '2024-11-27T14:18:00Z' },
        { id: 'impact_assessment', label: 'Impact Assessment', status: 'completed', timestamp: '2024-11-27T14:35:00Z' },
        { id: 'next_action', label: 'Next Action', status: 'completed', timestamp: '2024-11-27T14:42:00Z' },
        { id: 'execute_action', label: 'Execute Action', status: 'active' },
        { id: 're_evaluate', label: 'Re-evaluate', status: 'pending' },
      ],
    };

    // Update services — Hospital still offline but Telecom Tower now fully offline
    const updatedServices: CriticalService[] = state.gridState.services.map(s =>
      s.name === 'Telecom Tower' ? { ...s, status: 'offline' as const } : s
    );

    // New activity log entry
    const newLogEntry: ActivityEntry = {
      id: `log-${state.activityLog.length + 1}`,
      timestamp: new Date().toISOString(),
      type: 'action',
      severity: 'warning',
      message: 'Transformer T3 inspection complete — CONFIRMED FAILED. Insulation failure detected.',
      user: 'Operator Sharma',
    };

    const newLogEntry2: ActivityEntry = {
      id: `log-${state.activityLog.length + 2}`,
      timestamp: new Date().toISOString(),
      type: 'system',
      severity: 'info',
      message: 'Recovery plan updated. New recommendation: Island Hospital Microgrid (VOI = 0.92)',
      user: 'GridGuard',
    };

    set({
      t3Inspected: true,
      gridState: {
        ...state.gridState,
        transformers: updatedTransformers,
        scenario: {
          ...state.gridState.scenario,
          faults: updatedFaults,
        },
        recommendation: newRecommendation,
        restoration: newRestoration,
        services: updatedServices,
        impact: {
          ...state.gridState.impact,
          services: updatedServices,
          critical_facilities_offline: 3,
        },
      },
      activityLog: [newLogEntry2, newLogEntry, ...state.activityLog],
    });
  },
}));
