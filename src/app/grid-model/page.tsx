'use client';

import React, { useState } from 'react';
import { mockBuses, mockLines, mockTransformers, mockDERs } from '@/data/mock-data';
import { Activity, Grid, AlertTriangle, CheckCircle, HelpCircle } from 'lucide-react';

type Tab = 'buses' | 'lines' | 'transformers' | 'der';

const getStatusBadge = (status: string) => {
  switch (status) {
    case 'healthy':
      return <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-green-50 text-green-700 border border-green-200"><CheckCircle size={12} /> Healthy</span>;
    case 'failed':
      return <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-red-50 text-red-700 border border-red-200"><AlertTriangle size={12} /> Failed</span>;
    case 'uncertain':
      return <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200"><HelpCircle size={12} /> Uncertain</span>;
    default:
      return <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-slate-50 text-slate-700 border border-slate-200">{status}</span>;
  }
};

export default function GridModelPage() {
  const [activeTab, setActiveTab] = useState<Tab>('buses');
  const [sortKey, setSortKey] = useState<string>('number');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

  const handleSort = (key: string) => {
    if (sortKey === key) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortOrder('asc');
    }
  };

  const sortedBuses = [...mockBuses].sort((a, b) => {
    const valA = a[sortKey as keyof typeof a] ?? '';
    const valB = b[sortKey as keyof typeof b] ?? '';
    if (valA < valB) return sortOrder === 'asc' ? -1 : 1;
    if (valA > valB) return sortOrder === 'asc' ? 1 : -1;
    return 0;
  });

  const sortedLines = [...mockLines].sort((a, b) => {
    const valA = a[sortKey as keyof typeof a] ?? '';
    const valB = b[sortKey as keyof typeof b] ?? '';
    if (valA < valB) return sortOrder === 'asc' ? -1 : 1;
    if (valA > valB) return sortOrder === 'asc' ? 1 : -1;
    return 0;
  });

  const sortedTransformers = [...mockTransformers].sort((a, b) => {
    const valA = a[sortKey as keyof typeof a];
    const valB = b[sortKey as keyof typeof b];
    if (valA < valB) return sortOrder === 'asc' ? -1 : 1;
    if (valA > valB) return sortOrder === 'asc' ? 1 : -1;
    return 0;
  });

  const sortedDERs = [...mockDERs].sort((a, b) => {
    const valA = a[sortKey as keyof typeof a];
    const valB = b[sortKey as keyof typeof b];
    if (valA < valB) return sortOrder === 'asc' ? -1 : 1;
    if (valA > valB) return sortOrder === 'asc' ? 1 : -1;
    return 0;
  });

  return (
    <div className="flex flex-col gap-6 max-w-7xl mx-auto">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Grid Model</h1>
        <p className="text-sm text-slate-500 mt-1">IEEE 33-bus distribution network topology and asset inventory</p>
      </div>

      <div className="grid grid-cols-4 gap-4">
        <div className="bg-white border border-slate-200 rounded-lg p-4 flex items-center justify-between shadow-sm">
          <div>
            <p className="text-sm font-medium text-slate-500">Total Buses</p>
            <p className="text-2xl font-bold text-slate-900">{mockBuses.length}</p>
          </div>
          <div className="p-3 bg-blue-50 text-blue-600 rounded-lg"><Grid size={20} /></div>
        </div>
        <div className="bg-white border border-slate-200 rounded-lg p-4 flex items-center justify-between shadow-sm">
          <div>
            <p className="text-sm font-medium text-slate-500">Total Lines</p>
            <p className="text-2xl font-bold text-slate-900">{mockLines.length}</p>
          </div>
          <div className="p-3 bg-indigo-50 text-indigo-600 rounded-lg"><Activity size={20} /></div>
        </div>
        <div className="bg-white border border-slate-200 rounded-lg p-4 flex items-center justify-between shadow-sm">
          <div>
            <p className="text-sm font-medium text-slate-500">Transformers</p>
            <p className="text-2xl font-bold text-slate-900">{mockTransformers.length}</p>
          </div>
          <div className="p-3 bg-amber-50 text-amber-600 rounded-lg"><Activity size={20} /></div>
        </div>
        <div className="bg-white border border-slate-200 rounded-lg p-4 flex items-center justify-between shadow-sm">
          <div>
            <p className="text-sm font-medium text-slate-500">DER Units</p>
            <p className="text-2xl font-bold text-slate-900">{mockDERs.length}</p>
          </div>
          <div className="p-3 bg-green-50 text-green-600 rounded-lg"><Activity size={20} /></div>
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-lg shadow-sm overflow-hidden flex flex-col min-h-[500px]">
        <div className="border-b border-slate-200 px-2 flex">
          {(['buses', 'lines', 'transformers', 'der'] as Tab[]).map((tab) => (
            <button
              key={tab}
              onClick={() => { setActiveTab(tab); setSortKey('id'); }}
              className={`px-4 py-3 text-sm font-medium capitalize border-b-2 transition-colors ${activeTab === tab ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'}`}
            >
              {tab}
            </button>
          ))}
        </div>
        
        <div className="p-4 flex-1 overflow-auto">
          <table className="w-full text-left border-collapse min-w-max">
            <thead>
              {activeTab === 'buses' && (
                <tr className="border-b border-slate-200">
                  <th className="py-3 px-4 text-xs font-semibold text-slate-500 uppercase cursor-pointer hover:bg-slate-50" onClick={() => handleSort('number')}>Bus #</th>
                  <th className="py-3 px-4 text-xs font-semibold text-slate-500 uppercase cursor-pointer hover:bg-slate-50" onClick={() => handleSort('name')}>Name</th>
                  <th className="py-3 px-4 text-xs font-semibold text-slate-500 uppercase cursor-pointer hover:bg-slate-50" onClick={() => handleSort('status')}>Status</th>
                  <th className="py-3 px-4 text-xs font-semibold text-slate-500 uppercase cursor-pointer hover:bg-slate-50" onClick={() => handleSort('voltage_kv')}>Voltage (kV)</th>
                  <th className="py-3 px-4 text-xs font-semibold text-slate-500 uppercase cursor-pointer hover:bg-slate-50" onClick={() => handleSort('load_mw')}>Load (MW)</th>
                  <th className="py-3 px-4 text-xs font-semibold text-slate-500 uppercase cursor-pointer hover:bg-slate-50" onClick={() => handleSort('feeder')}>Feeder</th>
                  <th className="py-3 px-4 text-xs font-semibold text-slate-500 uppercase">Critical Facility</th>
                  <th className="py-3 px-4 text-xs font-semibold text-slate-500 uppercase">DER</th>
                </tr>
              )}
              {activeTab === 'lines' && (
                <tr className="border-b border-slate-200">
                  <th className="py-3 px-4 text-xs font-semibold text-slate-500 uppercase cursor-pointer hover:bg-slate-50" onClick={() => handleSort('id')}>Line ID</th>
                  <th className="py-3 px-4 text-xs font-semibold text-slate-500 uppercase cursor-pointer hover:bg-slate-50" onClick={() => handleSort('from_bus')}>From</th>
                  <th className="py-3 px-4 text-xs font-semibold text-slate-500 uppercase cursor-pointer hover:bg-slate-50" onClick={() => handleSort('to_bus')}>To</th>
                  <th className="py-3 px-4 text-xs font-semibold text-slate-500 uppercase cursor-pointer hover:bg-slate-50" onClick={() => handleSort('status')}>Status</th>
                  <th className="py-3 px-4 text-xs font-semibold text-slate-500 uppercase cursor-pointer hover:bg-slate-50" onClick={() => handleSort('type')}>Type</th>
                  <th className="py-3 px-4 text-xs font-semibold text-slate-500 uppercase cursor-pointer hover:bg-slate-50" onClick={() => handleSort('length_km')}>Length (km)</th>
                  <th className="py-3 px-4 text-xs font-semibold text-slate-500 uppercase cursor-pointer hover:bg-slate-50" onClick={() => handleSort('capacity_mw')}>Capacity (MW)</th>
                  <th className="py-3 px-4 text-xs font-semibold text-slate-500 uppercase cursor-pointer hover:bg-slate-50" onClick={() => handleSort('current_flow_mw')}>Flow (MW)</th>
                </tr>
              )}
              {activeTab === 'transformers' && (
                <tr className="border-b border-slate-200">
                  <th className="py-3 px-4 text-xs font-semibold text-slate-500 uppercase cursor-pointer hover:bg-slate-50" onClick={() => handleSort('id')}>ID</th>
                  <th className="py-3 px-4 text-xs font-semibold text-slate-500 uppercase cursor-pointer hover:bg-slate-50" onClick={() => handleSort('name')}>Name</th>
                  <th className="py-3 px-4 text-xs font-semibold text-slate-500 uppercase cursor-pointer hover:bg-slate-50" onClick={() => handleSort('bus_id')}>Bus</th>
                  <th className="py-3 px-4 text-xs font-semibold text-slate-500 uppercase cursor-pointer hover:bg-slate-50" onClick={() => handleSort('status')}>Status</th>
                  <th className="py-3 px-4 text-xs font-semibold text-slate-500 uppercase cursor-pointer hover:bg-slate-50" onClick={() => handleSort('rating_mva')}>Rating (MVA)</th>
                  <th className="py-3 px-4 text-xs font-semibold text-slate-500 uppercase cursor-pointer hover:bg-slate-50" onClick={() => handleSort('load_pct')}>Load (%)</th>
                  <th className="py-3 px-4 text-xs font-semibold text-slate-500 uppercase cursor-pointer hover:bg-slate-50" onClick={() => handleSort('tap_position')}>Tap Pos</th>
                </tr>
              )}
              {activeTab === 'der' && (
                <tr className="border-b border-slate-200">
                  <th className="py-3 px-4 text-xs font-semibold text-slate-500 uppercase cursor-pointer hover:bg-slate-50" onClick={() => handleSort('id')}>ID</th>
                  <th className="py-3 px-4 text-xs font-semibold text-slate-500 uppercase cursor-pointer hover:bg-slate-50" onClick={() => handleSort('bus_id')}>Bus</th>
                  <th className="py-3 px-4 text-xs font-semibold text-slate-500 uppercase cursor-pointer hover:bg-slate-50" onClick={() => handleSort('type')}>Type</th>
                  <th className="py-3 px-4 text-xs font-semibold text-slate-500 uppercase cursor-pointer hover:bg-slate-50" onClick={() => handleSort('status')}>Status</th>
                  <th className="py-3 px-4 text-xs font-semibold text-slate-500 uppercase cursor-pointer hover:bg-slate-50" onClick={() => handleSort('capacity_mw')}>Capacity (MW)</th>
                  <th className="py-3 px-4 text-xs font-semibold text-slate-500 uppercase cursor-pointer hover:bg-slate-50" onClick={() => handleSort('current_output_mw')}>Output (MW)</th>
                </tr>
              )}
            </thead>
            <tbody className="divide-y divide-slate-100">
              {activeTab === 'buses' && sortedBuses.map((bus) => (
                <tr key={bus.id} className="hover:bg-slate-50">
                  <td className="py-2.5 px-4 text-sm text-slate-900 font-medium">{bus.number}</td>
                  <td className="py-2.5 px-4 text-sm text-slate-700">{bus.name}</td>
                  <td className="py-2.5 px-4 text-sm">{getStatusBadge(bus.status)}</td>
                  <td className="py-2.5 px-4 text-sm text-slate-700">{bus.voltage_kv.toFixed(2)}</td>
                  <td className="py-2.5 px-4 text-sm text-slate-700">{bus.load_mw.toFixed(2)}</td>
                  <td className="py-2.5 px-4 text-sm text-slate-700">{bus.feeder || '-'}</td>
                  <td className="py-2.5 px-4 text-sm text-slate-700">{bus.is_critical ? <span className="text-amber-600 font-medium">{bus.critical_facility}</span> : '-'}</td>
                  <td className="py-2.5 px-4 text-sm text-slate-700">{bus.has_der ? 'Yes' : 'No'}</td>
                </tr>
              ))}
              {activeTab === 'lines' && sortedLines.map((line) => (
                <tr key={line.id} className="hover:bg-slate-50">
                  <td className="py-2.5 px-4 text-sm text-slate-900 font-medium">{line.id}</td>
                  <td className="py-2.5 px-4 text-sm text-slate-700">{line.from_bus}</td>
                  <td className="py-2.5 px-4 text-sm text-slate-700">{line.to_bus}</td>
                  <td className="py-2.5 px-4 text-sm">{getStatusBadge(line.status)}</td>
                  <td className="py-2.5 px-4 text-sm text-slate-700 capitalize">{line.type}</td>
                  <td className="py-2.5 px-4 text-sm text-slate-700">{line.length_km.toFixed(1)}</td>
                  <td className="py-2.5 px-4 text-sm text-slate-700">{line.capacity_mw.toFixed(1)}</td>
                  <td className="py-2.5 px-4 text-sm text-slate-700">{line.current_flow_mw.toFixed(1)}</td>
                </tr>
              ))}
              {activeTab === 'transformers' && sortedTransformers.map((t) => (
                <tr key={t.id} className="hover:bg-slate-50">
                  <td className="py-2.5 px-4 text-sm text-slate-900 font-medium">{t.id}</td>
                  <td className="py-2.5 px-4 text-sm text-slate-700">{t.name}</td>
                  <td className="py-2.5 px-4 text-sm text-slate-700">{t.bus_id}</td>
                  <td className="py-2.5 px-4 text-sm">{getStatusBadge(t.status)}</td>
                  <td className="py-2.5 px-4 text-sm text-slate-700">{t.rating_mva}</td>
                  <td className="py-2.5 px-4 text-sm text-slate-700">{t.load_pct}%</td>
                  <td className="py-2.5 px-4 text-sm text-slate-700">{t.tap_position}</td>
                </tr>
              ))}
              {activeTab === 'der' && sortedDERs.map((der) => (
                <tr key={der.id} className="hover:bg-slate-50">
                  <td className="py-2.5 px-4 text-sm text-slate-900 font-medium">{der.id}</td>
                  <td className="py-2.5 px-4 text-sm text-slate-700">{der.bus_id}</td>
                  <td className="py-2.5 px-4 text-sm text-slate-700 capitalize">{der.type}</td>
                  <td className="py-2.5 px-4 text-sm">{getStatusBadge(der.status)}</td>
                  <td className="py-2.5 px-4 text-sm text-slate-700">{der.capacity_mw.toFixed(2)}</td>
                  <td className="py-2.5 px-4 text-sm text-slate-700">{der.current_output_mw.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
