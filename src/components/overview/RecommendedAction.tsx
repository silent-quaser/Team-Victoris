'use client';

import { useGridStore } from '@/store/grid-store';

export default function RecommendedAction() {
  const recommendation = useGridStore((s) => s.gridState.recommendation);
  const confirmAction = useGridStore((s) => s.confirmAction);

  const impactColors: Record<string, string> = {
    high: 'text-red-600',
    medium: 'text-amber-600',
    low: 'text-green-600',
  };

  return (
    <div className="bg-white border border-slate-200 rounded-lg p-4 border-l-4 border-l-blue-600">
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
          <div className="text-[10px] uppercase text-slate-400 mb-0.5">
            Uncertainty
          </div>
          <div className="text-sm font-semibold text-amber-600">
            {recommendation.uncertainty_pct}%
          </div>
        </div>
        <div>
          <div className="text-[10px] uppercase text-slate-400 mb-0.5">
            Critical Impact
          </div>
          <div
            className={`text-sm font-semibold capitalize ${
              impactColors[recommendation.critical_impact] ?? 'text-slate-700'
            }`}
          >
            {recommendation.critical_impact}
          </div>
        </div>
        <div>
          <div className="text-[10px] uppercase text-slate-400 mb-0.5">
            Decision Value
          </div>
          <div className="text-sm font-bold text-blue-600">
            {recommendation.action.decision_value}
          </div>
        </div>
      </div>

      {/* Label tag */}
      <span className="text-[10px] uppercase bg-blue-50 text-blue-600 px-2 py-0.5 rounded inline-block font-medium mb-2">
        {recommendation.label}
      </span>

      {/* Explanation */}
      <p className="text-sm text-slate-600 leading-relaxed mb-4">
        {recommendation.explanation}
      </p>

      {/* Action buttons */}
      <div className="flex items-center gap-2 mb-4">
        <button
          onClick={() => confirmAction(recommendation.action.id)}
          className="bg-blue-600 text-white text-sm px-4 py-1.5 rounded-md hover:bg-blue-700 transition-colors"
        >
          Confirm Action
        </button>
        <button className="border border-slate-300 text-slate-700 text-sm px-4 py-1.5 rounded-md hover:bg-slate-50 transition-colors">
          Simulate
        </button>
        <button className="text-slate-500 text-sm px-3 py-1.5 hover:text-slate-700 transition-colors">
          More
        </button>
      </div>

      {/* Alternative actions */}
      <div>
        <div className="text-xs font-medium text-slate-500 mb-1">
          Alternative Actions
        </div>
        <div className="divide-y divide-slate-100">
          {recommendation.alternatives.map((alt) => (
            <div
              key={alt.id}
              className="flex items-center justify-between py-1.5 text-sm hover:bg-slate-50 px-1 rounded cursor-pointer transition-colors"
            >
              <span className="text-slate-700">{alt.name}</span>
              <span className="text-slate-500 font-medium">
                {alt.decision_value}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
