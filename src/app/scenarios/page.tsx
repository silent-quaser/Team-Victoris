'use client';

import React from 'react';
import { mockScenario, mockFaults } from '@/data/mock-data';
import { CloudRain, Wind, AlertTriangle, AlertCircle, Clock, Search, Map } from 'lucide-react';

export default function ScenariosPage() {
  const pastScenarios = [
    { id: 'scen-2', name: 'Winter Storm Oak', date: '2023-12-14', impact: 'High', faults: 7, status: 'Resolved' },
    { id: 'scen-3', name: 'Heatwave Load Shed', date: '2023-08-22', impact: 'Medium', faults: 3, status: 'Resolved' },
    { id: 'scen-4', name: 'Substation B Failure', date: '2023-04-10', impact: 'Critical', faults: 1, status: 'Resolved' }
  ];

  return (
    <div className="flex flex-col gap-6 max-w-7xl mx-auto">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Scenarios</h1>
        <p className="text-sm text-slate-500 mt-1">Storm event scenarios and fault analysis</p>
      </div>

      <div className="bg-white border border-slate-200 rounded-lg shadow-sm overflow-hidden">
        <div className="p-5 border-b border-slate-200 flex justify-between items-start bg-slate-50/50">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="flex h-2 w-2 rounded-full bg-red-500"></span>
              <h2 className="text-lg font-semibold text-slate-900">Active Scenario: {mockScenario.name}</h2>
            </div>
            <p className="text-sm text-slate-600">{mockScenario.description}</p>
            <div className="flex items-center gap-4 mt-3 text-xs text-slate-500 font-medium">
              <span className="flex items-center gap-1"><Clock size={14} /> Started: {new Date(mockScenario.started_at).toLocaleString()}</span>
              <span className="flex items-center gap-1"><Map size={14} /> System-wide impact</span>
            </div>
          </div>
          <div className="flex gap-4">
            <div className="flex flex-col items-center bg-white border border-slate-200 rounded-lg p-3 min-w-[80px]">
              <Wind size={20} className="text-blue-500 mb-1" />
              <span className="text-xs font-semibold text-slate-600">Wind</span>
              <span className="text-sm font-bold text-slate-900">{mockScenario.weather.wind_kmh} km/h</span>
            </div>
            <div className="flex flex-col items-center bg-white border border-slate-200 rounded-lg p-3 min-w-[80px]">
              <CloudRain size={20} className="text-blue-500 mb-1" />
              <span className="text-xs font-semibold text-slate-600">Rain</span>
              <span className="text-sm font-bold text-slate-900">{mockScenario.weather.rain}</span>
            </div>
          </div>
        </div>
        
        <div className="p-5">
          <h3 className="text-sm font-semibold text-slate-900 mb-3">Active Faults</h3>
          <div className="border border-slate-200 rounded-lg overflow-hidden">
            <table className="w-full text-left">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="py-2.5 px-4 text-xs font-semibold text-slate-500 uppercase">Asset</th>
                  <th className="py-2.5 px-4 text-xs font-semibold text-slate-500 uppercase">Type</th>
                  <th className="py-2.5 px-4 text-xs font-semibold text-slate-500 uppercase">Status</th>
                  <th className="py-2.5 px-4 text-xs font-semibold text-slate-500 uppercase">Confidence</th>
                  <th className="py-2.5 px-4 text-xs font-semibold text-slate-500 uppercase">Time Detected</th>
                  <th className="py-2.5 px-4 text-xs font-semibold text-slate-500 uppercase">Description</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {mockFaults.map(fault => (
                  <tr key={fault.id} className="hover:bg-slate-50">
                    <td className="py-3 px-4 text-sm font-medium text-slate-900">{fault.asset_name}</td>
                    <td className="py-3 px-4 text-sm text-slate-600 capitalize">{fault.asset_type}</td>
                    <td className="py-3 px-4 text-sm">
                      {fault.status === 'failed' ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-red-50 text-red-700 border border-red-200"><AlertTriangle size={12} /> Failed</span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200"><AlertCircle size={12} /> Uncertain</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-sm">
                      <div className="flex items-center gap-2">
                        <div className="h-1.5 w-16 bg-slate-100 rounded-full overflow-hidden">
                          <div className={`h-full rounded-full ${fault.confidence_pct > 90 ? 'bg-red-500' : 'bg-amber-500'}`} style={{ width: `${fault.confidence_pct}%` }}></div>
                        </div>
                        <span className="text-xs font-medium text-slate-600">{fault.confidence_pct}%</span>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-sm text-slate-600">{new Date(fault.detected_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</td>
                    <td className="py-3 px-4 text-sm text-slate-600">{fault.description}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-lg shadow-sm p-5">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Scenario History</h3>
        <div className="border border-slate-200 rounded-lg overflow-hidden">
          <table className="w-full text-left">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="py-2.5 px-4 text-xs font-semibold text-slate-500 uppercase">Scenario Name</th>
                <th className="py-2.5 px-4 text-xs font-semibold text-slate-500 uppercase">Date</th>
                <th className="py-2.5 px-4 text-xs font-semibold text-slate-500 uppercase">Impact Level</th>
                <th className="py-2.5 px-4 text-xs font-semibold text-slate-500 uppercase">Faults</th>
                <th className="py-2.5 px-4 text-xs font-semibold text-slate-500 uppercase">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {pastScenarios.map(scen => (
                <tr key={scen.id} className="hover:bg-slate-50">
                  <td className="py-3 px-4 text-sm font-medium text-slate-900">{scen.name}</td>
                  <td className="py-3 px-4 text-sm text-slate-600">{scen.date}</td>
                  <td className="py-3 px-4 text-sm text-slate-600">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                      scen.impact === 'Critical' ? 'bg-red-50 text-red-700' :
                      scen.impact === 'High' ? 'bg-amber-50 text-amber-700' :
                      'bg-yellow-50 text-yellow-700'
                    }`}>
                      {scen.impact}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-sm text-slate-600">{scen.faults}</td>
                  <td className="py-3 px-4 text-sm text-slate-600">
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-700">{scen.status}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
