'use client';

import React from 'react';
import { Database, Activity, HardDrive, CheckCircle2, Clock, Zap, Map, Wifi, Loader2 } from 'lucide-react';

export default function DataModelsPage() {
  return (
    <div className="flex flex-col gap-6 max-w-7xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Data & Models</h1>
        <p className="text-slate-500">Data sources, model configurations, and system integrations</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Data Sources Section */}
        <section className="flex flex-col gap-4">
          <h2 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
            <Database className="w-5 h-5 text-blue-600" />
            Data Sources
          </h2>
          
          <div className="bg-white border border-slate-200 rounded-lg p-4 flex flex-col gap-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 last:border-0 last:pb-0">
              <div className="flex items-center gap-3">
                <div className="w-2 h-2 rounded-full bg-emerald-500"></div>
                <div>
                  <h3 className="font-medium text-slate-900">SCADA System</h3>
                  <p className="text-xs text-slate-500">2,450 data points</p>
                </div>
              </div>
              <div className="text-right">
                <span className="text-xs font-medium text-emerald-600 bg-emerald-50 px-2 py-1 rounded-full">Connected</span>
                <p className="text-xs text-slate-400 mt-1 flex items-center gap-1 justify-end"><Clock className="w-3 h-3" /> 14:40</p>
              </div>
            </div>

            <div className="flex items-center justify-between pb-3 border-b border-slate-100 last:border-0 last:pb-0">
              <div className="flex items-center gap-3">
                <div className="w-2 h-2 rounded-full bg-emerald-500"></div>
                <div>
                  <h3 className="font-medium text-slate-900">Weather Service</h3>
                  <p className="text-xs text-slate-500">Regional forecast</p>
                </div>
              </div>
              <div className="text-right">
                <span className="text-xs font-medium text-emerald-600 bg-emerald-50 px-2 py-1 rounded-full">Connected</span>
                <p className="text-xs text-slate-400 mt-1 flex items-center gap-1 justify-end"><Clock className="w-3 h-3" /> 14:35</p>
              </div>
            </div>

            <div className="flex items-center justify-between pb-3 border-b border-slate-100 last:border-0 last:pb-0">
              <div className="flex items-center gap-3">
                <div className="w-2 h-2 rounded-full bg-emerald-500"></div>
                <div>
                  <h3 className="font-medium text-slate-900">GIS Database</h3>
                  <p className="text-xs text-slate-500">Asset locations</p>
                </div>
              </div>
              <div className="text-right">
                <span className="text-xs font-medium text-emerald-600 bg-emerald-50 px-2 py-1 rounded-full">Connected</span>
                <p className="text-xs text-slate-400 mt-1 flex items-center gap-1 justify-end"><Clock className="w-3 h-3" /> 14:00</p>
              </div>
            </div>

            <div className="flex items-center justify-between pb-3 border-b border-slate-100 last:border-0 last:pb-0">
              <div className="flex items-center gap-3">
                <div className="w-2 h-2 rounded-full bg-emerald-500"></div>
                <div>
                  <h3 className="font-medium text-slate-900">AMI Metering</h3>
                  <p className="text-xs text-slate-500">Customer meters</p>
                </div>
              </div>
              <div className="text-right">
                <span className="text-xs font-medium text-emerald-600 bg-emerald-50 px-2 py-1 rounded-full">Connected</span>
                <p className="text-xs text-slate-400 mt-1 flex items-center gap-1 justify-end"><Clock className="w-3 h-3" /> 14:38</p>
              </div>
            </div>
          </div>
        </section>

        {/* Models Section */}
        <section className="flex flex-col gap-4">
          <h2 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
            <Zap className="w-5 h-5 text-indigo-600" />
            Models
          </h2>
          
          <div className="bg-white border border-slate-200 rounded-lg p-4 flex flex-col gap-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 last:border-0 last:pb-0">
              <div>
                <h3 className="font-medium text-slate-900">Power Flow Model <span className="text-xs text-slate-400 font-normal ml-1">v2.3.1</span></h3>
                <p className="text-xs text-slate-500 mt-1 flex items-center gap-1"><Clock className="w-3 h-3" /> Run: 14:35</p>
              </div>
              <div>
                <span className="inline-flex items-center gap-1 text-xs font-medium text-blue-700 bg-blue-50 px-2.5 py-1 rounded-full">
                  <CheckCircle2 className="w-3 h-3" />
                  Ready
                </span>
              </div>
            </div>

            <div className="flex items-center justify-between pb-3 border-b border-slate-100 last:border-0 last:pb-0">
              <div>
                <h3 className="font-medium text-slate-900">Fault Probability Model <span className="text-xs text-slate-400 font-normal ml-1">v1.8.0</span></h3>
                <p className="text-xs text-slate-500 mt-1 flex items-center gap-1"><Clock className="w-3 h-3" /> Run: 14:22</p>
              </div>
              <div>
                <span className="inline-flex items-center gap-1 text-xs font-medium text-blue-700 bg-blue-50 px-2.5 py-1 rounded-full">
                  <CheckCircle2 className="w-3 h-3" />
                  Ready
                </span>
              </div>
            </div>

            <div className="flex items-center justify-between pb-3 border-b border-slate-100 last:border-0 last:pb-0">
              <div>
                <h3 className="font-medium text-slate-900">Recovery Optimizer <span className="text-xs text-slate-400 font-normal ml-1">v3.1.2</span></h3>
                <p className="text-xs text-slate-500 mt-1 flex items-center gap-1"><Clock className="w-3 h-3" /> Started: 14:38</p>
              </div>
              <div>
                <span className="inline-flex items-center gap-1 text-xs font-medium text-amber-700 bg-amber-50 px-2.5 py-1 rounded-full">
                  <Loader2 className="w-3 h-3 animate-spin" />
                  Running
                </span>
              </div>
            </div>

            <div className="flex items-center justify-between pb-3 border-b border-slate-100 last:border-0 last:pb-0">
              <div>
                <h3 className="font-medium text-slate-900">Impact Estimator <span className="text-xs text-slate-400 font-normal ml-1">v2.0.4</span></h3>
                <p className="text-xs text-slate-500 mt-1 flex items-center gap-1"><Clock className="w-3 h-3" /> Run: 14:35</p>
              </div>
              <div>
                <span className="inline-flex items-center gap-1 text-xs font-medium text-blue-700 bg-blue-50 px-2.5 py-1 rounded-full">
                  <CheckCircle2 className="w-3 h-3" />
                  Ready
                </span>
              </div>
            </div>
          </div>
        </section>
      </div>

      {/* System Health Section */}
      <section className="flex flex-col gap-4 mt-2">
        <h2 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
          <Activity className="w-5 h-5 text-slate-600" />
          System Health
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white border border-slate-200 rounded-lg p-4 flex flex-col justify-between">
            <h3 className="text-sm font-medium text-slate-500 mb-2">CPU Usage</h3>
            <div className="flex items-end justify-between mb-2">
              <span className="text-2xl font-bold text-slate-800">34%</span>
            </div>
            <div className="w-full bg-slate-100 rounded-full h-2">
              <div className="bg-blue-500 h-2 rounded-full" style={{ width: '34%' }}></div>
            </div>
          </div>
          
          <div className="bg-white border border-slate-200 rounded-lg p-4 flex flex-col justify-between">
            <h3 className="text-sm font-medium text-slate-500 mb-2">Memory Usage</h3>
            <div className="flex items-end justify-between mb-2">
              <span className="text-2xl font-bold text-slate-800">2.1 <span className="text-sm font-normal text-slate-500">GB</span></span>
              <span className="text-xs text-slate-500">8 GB Total</span>
            </div>
            <div className="w-full bg-slate-100 rounded-full h-2">
              <div className="bg-indigo-500 h-2 rounded-full" style={{ width: '26%' }}></div>
            </div>
          </div>

          <div className="bg-white border border-slate-200 rounded-lg p-4 flex flex-col justify-center items-center text-center">
            <h3 className="text-sm font-medium text-slate-500 mb-2">API Latency</h3>
            <div className="flex items-center gap-2 text-2xl font-bold text-slate-800">
              <Wifi className="w-5 h-5 text-emerald-500" />
              45<span className="text-sm font-normal text-slate-500">ms</span>
            </div>
          </div>

          <div className="bg-white border border-slate-200 rounded-lg p-4 flex flex-col justify-center items-center text-center">
            <h3 className="text-sm font-medium text-slate-500 mb-2">Database Status</h3>
            <div className="flex items-center gap-2 text-xl font-bold text-emerald-600 bg-emerald-50 px-4 py-2 rounded-lg">
              <HardDrive className="w-5 h-5" />
              Healthy
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
