'use client';

import { useGridStore } from '@/store/grid-store';

export default function RestorationProgress() {
  const restoration = useGridStore((s) => s.gridState.restoration);

  const dotStyles: Record<string, string> = {
    completed: 'bg-green-500',
    active: 'bg-blue-500 ring-4 ring-blue-100 animate-pulse',
    pending: 'bg-slate-300',
  };

  const labelStyles: Record<string, string> = {
    completed: 'text-green-600',
    active: 'text-blue-600 font-medium',
    pending: 'text-slate-400',
  };

  const lineStyles: Record<string, string> = {
    completed: 'bg-green-500',
    active: 'bg-blue-500',
    pending: 'bg-slate-200',
  };

  return (
    <div className="bg-white border border-slate-200 rounded-lg p-4">
      {/* Progress header */}
      <div className="mb-3">
        <div className="text-3xl font-bold text-slate-900">
          {restoration.pct_complete}%
        </div>
        <div className="text-xs text-slate-500 mt-0.5">
          Restoration Progress
        </div>
      </div>

      {/* Progress bar */}
      <div className="h-2 bg-slate-100 rounded-full mb-5">
        <div
          className="h-2 bg-blue-600 rounded-full transition-all duration-500"
          style={{ width: `${restoration.pct_complete}%` }}
        />
      </div>

      {/* Timeline stepper */}
      <div className="flex items-start">
        {restoration.stages.map((stage, idx) => (
          <div
            key={stage.id}
            className="flex items-start flex-1"
          >
            {/* Dot + Line segment */}
            <div className="flex flex-col items-center w-full">
              <div className="flex items-center w-full">
                {/* Left line */}
                {idx > 0 && (
                  <div
                    className={`h-0.5 flex-1 ${lineStyles[stage.status]}`}
                  />
                )}

                {/* Dot */}
                <div
                  className={`w-3 h-3 rounded-full shrink-0 ${dotStyles[stage.status]}`}
                />

                {/* Right line */}
                {idx < restoration.stages.length - 1 && (
                  <div
                    className={`h-0.5 flex-1 ${
                      lineStyles[restoration.stages[idx + 1].status]
                    }`}
                  />
                )}
              </div>

              {/* Label */}
              <div
                className={`text-[9px] mt-1.5 text-center leading-tight ${labelStyles[stage.status]}`}
              >
                {stage.label}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
