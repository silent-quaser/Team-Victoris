'use client';

import React from 'react';
import { mockRiskAssessments } from '@/data/mock-data';
import { ShieldAlert, Info } from 'lucide-react';

export default function RiskPage() {
  const getBadgeColor = (level: string) => {
    switch (level) {
      case 'critical': return 'bg-red-100 text-red-700 border-red-200';
      case 'high': return 'bg-orange-100 text-orange-700 border-orange-200';
      case 'medium': return 'bg-amber-100 text-amber-700 border-amber-200';
      case 'low': return 'bg-green-100 text-green-700 border-green-200';
      default: return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  // Helper for matrix mapping
  const getMatrixCell = (prob: number, imp: number) => {
    const x = Math.min(Math.floor(imp * 4), 3); // 0 to 3
    const y = Math.min(Math.floor(prob * 4), 3); // 0 to 3
    return { x, y };
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Risk & Uncertainty</h1>
          <p className="text-slate-500">Asset risk assessment and uncertainty quantification</p>
        </div>
      </div>

      {/* Key Insight Card */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-5 flex items-start gap-4">
        <ShieldAlert className="w-6 h-6 text-blue-600 shrink-0 mt-0.5" />
        <div>
          <h3 className="font-semibold text-blue-900 mb-1">Key Insight</h3>
          <p className="text-blue-800 text-sm">
            <strong>Transformer T3</strong> has the highest uncertainty (62%). Resolving this uncertainty has the highest value of information (0.87).
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Risk Matrix Visualization */}
        <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm">
          <h3 className="font-semibold text-slate-800 mb-4">Risk Matrix</h3>
          
          <div className="flex">
            {/* Y-Axis Label */}
            <div className="flex flex-col justify-center items-center pr-4">
              <div className="transform -rotate-90 text-xs font-medium text-slate-500 whitespace-nowrap">Probability</div>
            </div>
            
            <div className="flex-1">
              {/* 4x4 Grid */}
              <div className="grid grid-cols-4 grid-rows-4 gap-1 aspect-square bg-slate-100 p-1 rounded-md">
                {/* We map top-left (high prob, low impact) to bottom-right (low prob, high impact).
                    Standard matrix: Y is Prob (High top), X is Impact (High right). */}
                {Array.from({ length: 4 }).map((_, r) => (
                  Array.from({ length: 4 }).map((_, c) => {
                    const row = 3 - r; // 3=High, 0=Low
                    const col = c;     // 0=Low, 3=High
                    // Determine cell color
                    let cellClass = 'bg-green-100'; // Low
                    if (row + col >= 3) cellClass = 'bg-amber-100'; // Med
                    if (row + col >= 4) cellClass = 'bg-orange-100'; // High
                    if (row + col >= 5) cellClass = 'bg-red-200'; // Critical

                    // Find assessments in this cell
                    const items = mockRiskAssessments.filter(a => {
                      const { x, y } = getMatrixCell(a.probability, a.impact_score);
                      return x === col && y === row;
                    });

                    return (
                      <div key={`${r}-${c}`} className={`${cellClass} rounded flex items-center justify-center relative p-1`}>
                        {items.length > 0 && (
                          <div className="flex flex-wrap gap-1 justify-center">
                            {items.map(item => (
                              <div key={item.id} title={item.asset_name} className="w-4 h-4 rounded-full bg-slate-800 text-white flex items-center justify-center text-[8px] font-bold shadow cursor-pointer">
                                {item.asset_name.substring(0,2)}
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    );
                  })
                ))}
              </div>
              {/* X-Axis Label */}
              <div className="text-center pt-3 text-xs font-medium text-slate-500">
                Impact
              </div>
            </div>
          </div>
          <div className="mt-4 flex gap-4 text-xs text-slate-500 justify-center">
             <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-sm bg-green-100 border border-green-200"></span> Low</span>
             <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-sm bg-amber-100 border border-amber-200"></span> Medium</span>
             <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-sm bg-orange-100 border border-orange-200"></span> High</span>
             <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-sm bg-red-200 border border-red-300"></span> Critical</span>
          </div>
        </div>

        {/* Uncertainty Breakdown */}
        <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm">
          <h3 className="font-semibold text-slate-800 mb-4 flex items-center gap-2">
            <Info className="w-5 h-5 text-slate-400" />
            Uncertainty Breakdown
          </h3>
          
          <div className="space-y-6">
            {mockRiskAssessments.map(assessment => (
              <div key={assessment.id}>
                <div className="flex justify-between text-sm mb-1.5">
                  <span className="font-medium text-slate-700">{assessment.asset_name}</span>
                  <span className="text-slate-500">{(assessment.uncertainty * 100).toFixed(0)}%</span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full ${assessment.uncertainty > 0.5 ? 'bg-indigo-500' : 'bg-slate-300'}`} 
                    style={{ width: `${assessment.uncertainty * 100}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-8 p-4 bg-slate-50 rounded-lg border border-slate-100">
            <h4 className="text-sm font-semibold text-slate-700 mb-2">Decision Making Impact</h4>
            <p className="text-sm text-slate-600">
              High uncertainty on critical assets (like T3) drastically changes the optimal recovery path. Dispatching crews to confirm status before committing heavy resources is currently recommended.
            </p>
          </div>
        </div>
      </div>

      {/* Risk Register Table */}
      <div className="bg-white border border-slate-200 rounded-lg shadow-sm overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-200">
          <h3 className="font-semibold text-slate-800">Risk Register</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="bg-slate-50 text-slate-600 text-xs uppercase border-b border-slate-200">
              <tr>
                <th className="px-5 py-3 font-medium">Asset</th>
                <th className="px-5 py-3 font-medium">Risk Level</th>
                <th className="px-5 py-3 font-medium">Probability</th>
                <th className="px-5 py-3 font-medium">Impact Score</th>
                <th className="px-5 py-3 font-medium">Uncertainty</th>
                <th className="px-5 py-3 font-medium">Mitigation</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {mockRiskAssessments.map((risk) => (
                <tr key={risk.id} className="hover:bg-slate-50 transition-colors">
                  <td className="px-5 py-3 text-slate-800 font-medium">{risk.asset_name}</td>
                  <td className="px-5 py-3">
                    <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium border ${getBadgeColor(risk.risk_level)} capitalize`}>
                      {risk.risk_level}
                    </span>
                  </td>
                  <td className="px-5 py-3 text-slate-600">{(risk.probability * 100).toFixed(0)}%</td>
                  <td className="px-5 py-3 text-slate-600">{risk.impact_score.toFixed(2)}</td>
                  <td className="px-5 py-3 text-slate-600">{(risk.uncertainty * 100).toFixed(0)}%</td>
                  <td className="px-5 py-3 text-slate-600 truncate max-w-xs" title={risk.mitigation}>{risk.mitigation}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
