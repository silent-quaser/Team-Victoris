'use client';

import { useGridStore } from '@/store/grid-store';

interface MetricCard {
  value: string | number;
  label: string;
  accent: string;
}

const accentColors: Record<string, string> = {
  red: 'border-l-red-500',
  amber: 'border-l-amber-500',
  blue: 'border-l-blue-500',
  green: 'border-l-green-500',
};

export default function MetricCards() {
  const impact = useGridStore((s) => s.gridState.impact);

  const cards: MetricCard[] = [
    {
      value: impact.buses_out,
      label: 'Buses Out of Service',
      accent: 'red',
    },
    {
      value: impact.customers_affected.toLocaleString(),
      label: 'Customers Affected',
      accent: 'red',
    },
    {
      value: impact.critical_facilities_offline,
      label: 'Critical Facilities Offline',
      accent: 'amber',
    },
    {
      value: '2 crews',
      label: 'Recovery Resources',
      accent: 'blue',
    },
    {
      value: `${impact.recoverable_load_pct}%`,
      label: 'Estimated Recoverable Load',
      accent: 'green',
    },
  ];

  return (
    <div className="grid grid-cols-5 gap-3">
      {cards.map((card) => (
        <div
          key={card.label}
          className={`bg-white border border-slate-200 rounded-lg p-3 border-l-2 ${accentColors[card.accent]}`}
        >
          <div className="text-2xl font-semibold text-slate-900">
            {card.value}
          </div>
          <div className="text-xs text-slate-500 mt-0.5">{card.label}</div>
        </div>
      ))}
    </div>
  );
}
