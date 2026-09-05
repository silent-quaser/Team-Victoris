'use client';

import { useState } from 'react';
import { useGridStore } from '@/store/grid-store';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import type { ServiceStatus } from '@/types';

const tabs = ['Services', 'Load', 'Customers'] as const;
type Tab = (typeof tabs)[number];

const statusStyles: Record<ServiceStatus, string> = {
  online: 'bg-emerald-50 text-emerald-700',
  offline: 'bg-red-50 text-red-700',
  degraded: 'bg-amber-50 text-amber-700',
  partially_supplied: 'bg-blue-50 text-blue-700',
};

const statusLabel: Record<ServiceStatus, string> = {
  online: 'Online',
  offline: 'Offline',
  degraded: 'Degraded',
  partially_supplied: 'Partial',
};

export default function ImpactAnalysis() {
  const [activeTab, setActiveTab] = useState<Tab>('Services');
  const services = useGridStore((s) => s.gridState.services);
  const impact = useGridStore((s) => s.gridState.impact);

  const loadData = services.map((s) => ({
    name: s.name,
    load: s.load_mw,
  }));

  const onlineCount = services.filter((s) => s.status === 'online').length;
  const offlineCount = services.filter((s) => s.status === 'offline').length;
  const degradedCount = services.filter(
    (s) => s.status === 'degraded' || s.status === 'partially_supplied'
  ).length;

  return (
    <div className="bg-white border border-slate-200 rounded-lg p-4">
      {/* Tabs */}
      <div className="flex gap-4 border-b border-slate-100 mb-3">
        {tabs.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`pb-2 text-sm font-medium transition-colors ${
              activeTab === tab
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-slate-500 hover:text-slate-700'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Services tab */}
      {activeTab === 'Services' && (
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-100">
              <th className="text-left py-1.5 text-xs font-medium text-slate-500">
                Service
              </th>
              <th className="text-left py-1.5 text-xs font-medium text-slate-500">
                Status
              </th>
              <th className="text-right py-1.5 text-xs font-medium text-slate-500">
                Load (MW)
              </th>
            </tr>
          </thead>
          <tbody>
            {services.map((svc) => (
              <tr key={svc.id} className="border-b border-slate-50">
                <td className="py-1.5 text-slate-700">{svc.name}</td>
                <td className="py-1.5">
                  <span
                    className={`inline-block text-xs px-2 py-0.5 rounded font-medium ${
                      statusStyles[svc.status]
                    }`}
                  >
                    {statusLabel[svc.status]}
                  </span>
                </td>
                <td className="py-1.5 text-right text-slate-700">
                  {svc.load_mw.toFixed(1)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {/* Load tab */}
      {activeTab === 'Load' && (
        <div className="h-52">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={loadData} margin={{ top: 8, right: 8, bottom: 0, left: -16 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis
                dataKey="name"
                tick={{ fontSize: 10, fill: '#64748b' }}
                axisLine={{ stroke: '#e2e8f0' }}
                tickLine={false}
              />
              <YAxis
                tick={{ fontSize: 10, fill: '#64748b' }}
                axisLine={{ stroke: '#e2e8f0' }}
                tickLine={false}
                unit=" MW"
              />
              <Tooltip
                contentStyle={{
                  fontSize: 12,
                  borderRadius: 8,
                  border: '1px solid #e2e8f0',
                }}
              />
              <Bar dataKey="load" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Customers tab */}
      {activeTab === 'Customers' && (
        <div className="space-y-3">
          <div className="flex items-baseline justify-between">
            <span className="text-sm text-slate-500">Total Affected</span>
            <span className="text-xl font-semibold text-slate-900">
              {impact.customers_affected.toLocaleString()}
            </span>
          </div>
          <div className="flex items-baseline justify-between">
            <span className="text-sm text-slate-500">Total Load (MW)</span>
            <span className="text-lg font-semibold text-slate-900">
              {impact.total_load_mw}
            </span>
          </div>
          <div className="flex items-baseline justify-between">
            <span className="text-sm text-slate-500">Recoverable</span>
            <span className="text-lg font-semibold text-green-600">
              {impact.recoverable_load_pct}%
            </span>
          </div>
          <div className="border-t border-slate-100 pt-3 grid grid-cols-3 gap-2 text-center">
            <div>
              <div className="text-lg font-semibold text-emerald-600">
                {onlineCount}
              </div>
              <div className="text-[10px] text-slate-500">Online</div>
            </div>
            <div>
              <div className="text-lg font-semibold text-red-600">
                {offlineCount}
              </div>
              <div className="text-[10px] text-slate-500">Offline</div>
            </div>
            <div>
              <div className="text-lg font-semibold text-amber-600">
                {degradedCount}
              </div>
              <div className="text-[10px] text-slate-500">Degraded</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
