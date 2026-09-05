'use client';

import React from 'react';
import { useGridStore } from '@/store/grid-store';
import { mockWhatIfScenarios } from '@/data/mock-data';
import { Plus, ArrowRight, Play } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export default function WhatIfPage() {
  const chartData = mockWhatIfScenarios.map(s => ({
    name: s.name,
    loadRestored: s.results?.load_restored_pct || 0,
    riskScore: (s.results?.risk_score || 0) * 100,
  }));

  const getRiskColor = (score: number) => {
    if (score < 0.4) return 'text-green-600 bg-green-50';
    if (score < 0.7) return 'text-amber-600 bg-amber-50';
    return 'text-red-600 bg-red-50';
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">What-If Analysis</h1>
          <p className="text-slate-500">Compare scenario outcomes and evaluate decision alternatives</p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium transition-colors">
          <Plus className="w-4 h-4" />
          Create New Scenario
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {mockWhatIfScenarios.map((scenario) => (
          <div key={scenario.id} className="bg-white border border-slate-200 rounded-lg p-5 flex flex-col shadow-sm">
            <h3 className="font-semibold text-lg text-slate-800">{scenario.name}</h3>
            <p className="text-sm text-slate-500 mt-1 mb-4">{scenario.description}</p>
            
            <div className="mb-4 flex-1">
              <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Modifications</h4>
              <div className="space-y-2">
                {scenario.modifications.map((mod, idx) => (
                  <div key={idx} className="flex items-center text-sm bg-slate-50 p-2 rounded border border-slate-100">
                    <span className="font-medium text-slate-700 w-16">{mod.asset_id}</span>
                    <span className="text-slate-400 mx-2">{mod.field}:</span>
                    <span className="line-through text-slate-400">{mod.original_value}</span>
                    <ArrowRight className="w-3 h-3 mx-2 text-slate-400" />
                    <span className="font-medium text-blue-600">{mod.new_value}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="border-t border-slate-100 pt-4 mb-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-xs text-slate-500 mb-1">Load Restored</div>
                  <div className="text-lg font-semibold text-slate-800">{scenario.results?.load_restored_pct}%</div>
                </div>
                <div>
                  <div className="text-xs text-slate-500 mb-1">Risk Score</div>
                  <div className={`inline-flex px-2 py-0.5 rounded text-sm font-medium ${getRiskColor(scenario.results?.risk_score || 0)}`}>
                    {(scenario.results?.risk_score || 0).toFixed(2)}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-slate-500 mb-1">Time to Restore</div>
                  <div className="text-sm font-medium text-slate-800">{scenario.results?.time_to_restore_min} min</div>
                </div>
                <div>
                  <div className="text-xs text-slate-500 mb-1">Customers</div>
                  <div className="text-sm font-medium text-slate-800">{scenario.results?.customers_restored}</div>
                </div>
              </div>
            </div>

            <button className="w-full flex items-center justify-center gap-2 py-2 border border-blue-200 text-blue-700 rounded-md hover:bg-blue-50 transition-colors text-sm font-medium">
              <Play className="w-4 h-4" />
              Run Simulation
            </button>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm">
          <h3 className="font-semibold text-slate-800 mb-4">Scenario Comparison</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="bg-slate-50 text-slate-600 text-xs uppercase border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3 font-medium">Metric</th>
                  {mockWhatIfScenarios.map(s => (
                    <th key={s.id} className="px-4 py-3 font-medium">{s.name}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                <tr>
                  <td className="px-4 py-3 font-medium text-slate-700">Load Restored (%)</td>
                  {mockWhatIfScenarios.map(s => (
                    <td key={s.id} className="px-4 py-3 text-slate-600">{s.results?.load_restored_pct}</td>
                  ))}
                </tr>
                <tr>
                  <td className="px-4 py-3 font-medium text-slate-700">Customers Restored</td>
                  {mockWhatIfScenarios.map(s => (
                    <td key={s.id} className="px-4 py-3 text-slate-600">{s.results?.customers_restored}</td>
                  ))}
                </tr>
                <tr>
                  <td className="px-4 py-3 font-medium text-slate-700">Time to Restore (min)</td>
                  {mockWhatIfScenarios.map(s => (
                    <td key={s.id} className="px-4 py-3 text-slate-600">{s.results?.time_to_restore_min}</td>
                  ))}
                </tr>
                <tr>
                  <td className="px-4 py-3 font-medium text-slate-700">Risk Score</td>
                  {mockWhatIfScenarios.map(s => (
                    <td key={s.id} className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${getRiskColor(s.results?.risk_score || 0)}`}>
                        {s.results?.risk_score}
                      </span>
                    </td>
                  ))}
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm">
          <h3 className="font-semibold text-slate-800 mb-4">Key Metrics Comparison</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="name" tick={{ fontSize: 12, fill: '#64748b' }} axisLine={false} tickLine={false} />
                <YAxis yAxisId="left" tick={{ fontSize: 12, fill: '#64748b' }} axisLine={false} tickLine={false} />
                <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 12, fill: '#64748b' }} axisLine={false} tickLine={false} />
                <Tooltip 
                  contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0', boxShadow: '0 1px 2px 0 rgb(0 0 0 / 0.05)' }}
                />
                <Legend iconType="circle" wrapperStyle={{ fontSize: '12px' }} />
                <Bar yAxisId="left" dataKey="loadRestored" name="Load Restored %" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                <Bar yAxisId="right" dataKey="riskScore" name="Risk Score (x100)" fill="#f59e0b" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
