'use client';

import { useState } from 'react';
import { useGridStore } from '@/store/grid-store';
import { Clock, Users, ChevronDown, ChevronUp, Info } from 'lucide-react';

export default function RecommendedAction() {
  const recommendation = useGridStore((s) => s.gridState.recommendation);
  const confirmAction = useGridStore((s) => s.confirmAction);
  const simulateAction = useGridStore((s) => s.simulateAction);
  const [showDetails, setShowDetails] = useState(false);

  const impactColors: Record<string, string> = {
    high: 'text-red-600',
    medium: 'text-amber-600',
    low: 'text-green-600',
  };

  if (!recommendation) {
    return (
      <div className="bg-white border border-green-200 rounded-lg p-6 border-l-4 border-l-green-600 flex flex-col items-center justify-center h-full min-h-[200px]">
        <div className="w-12 h-12 bg-green-100 text-green-600 rounded-full flex items-center justify-center mb-3">
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path></svg>
        </div>
        <h3 className="text-xl font-bold text-green-700 mb-1">Restoration Complete</h3>
        <p className="text-sm text-green-600 text-center">All critical facilities and downstream loads have been successfully restored.</p>
      </div>
    );
  }

  return (
    <div className="bg-white border border-slate-200 rounded-lg p-4 border-l-4 border-l-blue-600 flex flex-col h-full">
      {/* Header row */}
      <div className="flex items-center justify-between mb-2">
        <span className="text-[10px] uppercase tracking-wider text-slate-400 font-medium">
          Recommended Next Action
        </span>
        <span className="text-[10px] bg-red-50 text-red-600 px-2 py-0.5 rounded font-medium uppercase">
          High Priority
        </span>
      </div>

      {/* Action name */}
      <h3 className="text-lg font-semibold text-slate-900 mb-3">
        {recommendation.action.name}
      </h3>

      {/* Metrics row */}
      <div className="grid grid-cols-3 gap-3 mb-3">
        <div>
          <div className="text-[10px] uppercase text-slate-400 mb-0.5">Uncertainty</div>
          <div className="text-sm font-semibold text-amber-600">{recommendation.uncertainty_pct}%</div>
        </div>
        <div>
          <div className="text-[10px] uppercase text-slate-400 mb-0.5">Critical Impact</div>
          <div className={`text-sm font-semibold capitalize ${impactColors[recommendation.critical_impact] ?? 'text-slate-700'}`}>
            {recommendation.critical_impact}
          </div>
        </div>
        <div>
          <div className="text-[10px] uppercase text-slate-400 mb-0.5">Decision Value</div>
          <div className="text-sm font-bold text-blue-600">{recommendation.action.decision_value}</div>
        </div>
      </div>

      {/* Label tag */}
      <span className="text-[10px] uppercase bg-blue-50 text-blue-600 px-2 py-0.5 rounded inline-block font-medium mb-2">
        {recommendation.label}
      </span>

      {/* Explanation */}
      <p className="text-sm text-slate-600 leading-relaxed mb-4">{recommendation.explanation}</p>

      {/* Action buttons */}
      <div className="flex items-center gap-2 mb-3">
        <button
          onClick={() => confirmAction(recommendation.action.id)}
          className="bg-blue-600 text-white text-sm px-4 py-1.5 rounded-md hover:bg-blue-700 transition-colors"
        >
          Confirm Action
        </button>
        <button
          onClick={() => simulateAction(recommendation.action.id, recommendation.action.name)}
          className="border border-slate-300 text-slate-700 text-sm px-4 py-1.5 rounded-md hover:bg-slate-50 transition-colors"
        >
          Simulate
        </button>
        <button
          onClick={() => setShowDetails(v => !v)}
          className="flex items-center gap-1 text-slate-500 text-sm px-3 py-1.5 hover:text-blue-600 hover:bg-blue-50 rounded-md transition-colors"
        >
          More {showDetails ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
        </button>
      </div>

      {/* More details panel */}
      {showDetails && (
        <div className="mb-3 p-3 bg-slate-50 rounded-lg border border-slate-200 text-sm space-y-2">
          <div className="font-medium text-slate-700 flex items-center gap-1.5 mb-2">
            <Info className="w-4 h-4 text-blue-500" /> Action Details
          </div>
          <p className="text-slate-600">{recommendation.action.description}</p>
          <div className="flex gap-4 pt-1">
            <div className="flex items-center gap-1.5 text-slate-600">
              <Clock className="w-3.5 h-3.5 text-slate-400" />
              Est. Duration: <span className="font-medium text-slate-800">{recommendation.action.estimated_duration_min} min</span>
            </div>
            <div className="flex items-center gap-1.5 text-slate-600">
              <Users className="w-3.5 h-3.5 text-slate-400" />
              Crew Required: <span className="font-medium text-slate-800">{recommendation.action.crew_required}</span>
            </div>
          </div>
          <div className="text-[11px] text-slate-500">
            Action Type: <span className="font-medium uppercase">{recommendation.action.type}</span> · Target: <span className="font-medium">{recommendation.action.target_asset_id}</span>
          </div>
        </div>
      )}

      {/* Alternative actions */}
      <div>
        <div className="text-xs font-medium text-slate-500 mb-1">Alternative Actions</div>
        <div className="divide-y divide-slate-100">
          {recommendation.alternatives.map((alt) => (
            <div
              key={alt.id}
              className="flex items-center justify-between py-1.5 text-sm hover:bg-slate-50 px-1 rounded cursor-pointer transition-colors"
              onClick={() => simulateAction(alt.id, alt.name)}
              title="Click to simulate this alternative"
            >
              <span className="text-slate-700">{alt.name}</span>
              <span className="text-slate-500 font-medium">{alt.decision_value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}


