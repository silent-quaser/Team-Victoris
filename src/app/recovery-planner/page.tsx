'use client';

import React from 'react';
import { mockCrews, mockImpact } from '@/data/mock-data';
import { CheckCircle2, Clock, MapPin, Truck, AlertCircle, Wrench, Shield } from 'lucide-react';

const recoverySteps = [
  { id: 1, action: 'Inspect Transformer T3', time: 45, team: 'Alpha Team', status: 'in-progress' },
  { id: 2, action: 'Island Hospital Microgrid', time: 20, team: 'Beta Team', status: 'pending' },
  { id: 3, action: 'Repair Line L25-26', time: 90, team: 'Gamma Team', status: 'pending' },
  { id: 4, action: 'Repair Line L6-7', time: 120, team: 'Alpha Team', status: 'pending' },
  { id: 5, action: 'Repair Line L12-13', time: 120, team: 'Gamma Team', status: 'pending' },
  { id: 6, action: 'Restore Transformer T3', time: 180, team: 'Delta Team', status: 'pending' }
];

export default function RecoveryPlannerPage() {
  const totalMinutes = recoverySteps.reduce((acc, step) => acc + step.time, 0);
  const totalHours = (totalMinutes / 60).toFixed(1);

  return (
    <div className="flex flex-col gap-6 max-w-7xl mx-auto">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Recovery Planner</h1>
        <p className="text-sm text-slate-500 mt-1">Optimized recovery sequence and crew assignment</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white border border-slate-200 rounded-lg shadow-sm p-5">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold text-slate-900">Recovery Sequence</h2>
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium bg-blue-50 text-blue-700 px-2.5 py-1 rounded-full border border-blue-200">
                  Total Time: ~{totalHours} hrs
                </span>
                <span className="text-xs font-medium bg-slate-100 text-slate-700 px-2.5 py-1 rounded-full border border-slate-200">
                  6 Tasks
                </span>
              </div>
            </div>

            <div className="relative pl-6 border-l-2 border-slate-200 ml-4 space-y-8">
              {recoverySteps.map((step, idx) => (
                <div key={step.id} className="relative">
                  <div className={`absolute -left-[35px] w-6 h-6 rounded-full border-2 flex items-center justify-center bg-white ${
                    step.status === 'completed' ? 'border-green-500 text-green-500' :
                    step.status === 'in-progress' ? 'border-blue-500 text-blue-500' :
                    'border-slate-300 text-slate-400'
                  }`}>
                    {step.status === 'completed' ? <CheckCircle2 size={14} /> : 
                     step.status === 'in-progress' ? <Clock size={14} /> : 
                     <span className="text-xs font-bold">{step.id}</span>}
                  </div>
                  
                  <div className={`bg-white border rounded-lg p-4 shadow-sm ${
                    step.status === 'in-progress' ? 'border-blue-200 bg-blue-50/30' : 'border-slate-200'
                  }`}>
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="font-semibold text-slate-900">{step.action}</h3>
                      <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                        step.status === 'completed' ? 'bg-green-100 text-green-700' :
                        step.status === 'in-progress' ? 'bg-blue-100 text-blue-700' :
                        'bg-slate-100 text-slate-600'
                      }`}>
                        {step.status === 'completed' ? 'Completed' : 
                         step.status === 'in-progress' ? 'In Progress' : 'Pending'}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 text-xs text-slate-500 mt-3">
                      <div className="flex items-center gap-1">
                        <Clock size={14} />
                        {step.time} min
                      </div>
                      <div className="flex items-center gap-1">
                        <Wrench size={14} />
                        {step.team}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="bg-white border border-slate-200 rounded-lg shadow-sm p-5">
            <h3 className="text-base font-semibold text-slate-900 mb-4">Recovery Metrics</h3>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-slate-600">Load Restored</span>
                  <span className="font-semibold text-slate-900">{mockImpact.recoverable_load_pct}%</span>
                </div>
                <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                  <div className="h-full bg-blue-500 rounded-full" style={{ width: `${mockImpact.recoverable_load_pct}%` }}></div>
                </div>
                <p className="text-xs text-slate-500 mt-1">{mockImpact.total_load_mw * (mockImpact.recoverable_load_pct/100)} MW / {mockImpact.total_load_mw} MW</p>
              </div>
              <div className="pt-3 border-t border-slate-100">
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-slate-600">Customers Restored</span>
                  <span className="font-semibold text-slate-900">0 / {mockImpact.customers_affected}</span>
                </div>
              </div>
              <div className="pt-3 border-t border-slate-100">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-600">Estimated Full Restoration</span>
                  <span className="font-semibold text-slate-900">{totalHours} hours</span>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white border border-slate-200 rounded-lg shadow-sm p-5">
            <h3 className="text-base font-semibold text-slate-900 mb-4">Crew Assignments</h3>
            <div className="space-y-3">
              {mockCrews.map(crew => (
                <div key={crew.id} className="border border-slate-100 bg-slate-50/50 rounded-lg p-3">
                  <div className="flex justify-between items-start mb-1">
                    <h4 className="text-sm font-semibold text-slate-900">{crew.name}</h4>
                    <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${
                      crew.status === 'available' ? 'bg-green-100 text-green-700' :
                      crew.status === 'deployed' ? 'bg-blue-100 text-blue-700' :
                      crew.status === 'en_route' ? 'bg-amber-100 text-amber-700' :
                      'bg-slate-200 text-slate-700'
                    }`}>
                      {crew.status.replace('_', ' ')}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mb-2">{crew.specialization} ({crew.members} members)</p>
                  <div className="text-xs text-slate-700 bg-white border border-slate-200 rounded px-2 py-1.5 flex items-start gap-1.5">
                    <MapPin size={14} className="text-slate-400 mt-0.5 flex-shrink-0" />
                    <span>{crew.current_task || crew.location || 'On Standby'}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
