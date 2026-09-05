'use client';

import { CloudLightning } from 'lucide-react';
import { useGridStore } from '@/store/grid-store';

const statusBadge: Record<string, string> = {
  failed: 'bg-red-50 text-red-700',
  uncertain: 'bg-amber-50 text-amber-700',
};

export default function CurrentScenario() {
  const scenario = useGridStore((s) => s.gridState.scenario);

  const started = new Date(scenario.started_at).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });

  return (
    <div className="bg-white border border-slate-200 rounded-lg p-4">
      {/* Header */}
      <div className="flex items-center gap-2 mb-3">
        <CloudLightning className="h-4 w-4 text-slate-500" />
        <h3 className="text-sm font-semibold text-slate-900">
          Current Scenario
        </h3>
      </div>

      <p className="text-sm font-bold text-slate-900 mb-3">{scenario.name}</p>

      {/* Details */}
      <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm mb-4">
        <span className="text-slate-500">Started</span>
        <span className="text-slate-700">{started}</span>

        <span className="text-slate-500">Wind</span>
        <span className="text-slate-700">
          {scenario.weather.wind_kmh} km/h
        </span>

        <span className="text-slate-500">Rain</span>
        <span className="text-slate-700">{scenario.weather.rain}</span>

        <span className="text-slate-500">Temperature</span>
        <span className="text-slate-700">
          {scenario.weather.temperature_c}°C
        </span>
      </div>

      {/* Fault table */}
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-100">
            <th className="text-left py-1.5 text-xs font-medium text-slate-500">
              Asset
            </th>
            <th className="text-left py-1.5 text-xs font-medium text-slate-500">
              Status
            </th>
            <th className="text-right py-1.5 text-xs font-medium text-slate-500">
              Confidence
            </th>
          </tr>
        </thead>
        <tbody>
          {scenario.faults.map((fault) => (
            <tr key={fault.id} className="border-b border-slate-50">
              <td className="py-1.5 text-slate-700">{fault.asset_name}</td>
              <td className="py-1.5">
                <span
                  className={`inline-block text-xs px-2 py-0.5 rounded font-medium capitalize ${
                    statusBadge[fault.status] ?? ''
                  }`}
                >
                  {fault.status}
                </span>
              </td>
              <td className="py-1.5 text-right text-slate-700">
                {fault.confidence_pct}%
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
