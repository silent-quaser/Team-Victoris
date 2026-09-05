'use client';

import React from 'react';
import { AlertCircle, ZapOff, CheckCircle2, Building, Radio, Heart, Droplets } from 'lucide-react';

export default function DependencyMapPage() {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Dependency Map</h1>
          <p className="text-slate-500">Infrastructure dependencies and cascading failure analysis</p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6">
        {/* Cascading Failures Summary */}
        <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm">
          <h3 className="font-semibold text-slate-800 mb-4 flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-red-500" />
            Cascading Failures Detected
          </h3>
          <div className="space-y-3">
            <div className="p-3 bg-red-50 border border-red-100 rounded-md flex items-start gap-3">
              <ZapOff className="w-5 h-5 text-red-500 mt-0.5 shrink-0" />
              <div>
                <p className="text-sm font-medium text-red-800">
                  L6-7 failure <span className="mx-1 text-red-400">→</span> 12 buses de-energized <span className="mx-1 text-red-400">→</span> Hospital offline, Water Plant offline
                </p>
                <p className="text-xs text-red-600 mt-1">Primary feeder interruption causing downstream critical facility loss.</p>
              </div>
            </div>
            <div className="p-3 bg-amber-50 border border-amber-100 rounded-md flex items-start gap-3">
              <ZapOff className="w-5 h-5 text-amber-500 mt-0.5 shrink-0" />
              <div>
                <p className="text-sm font-medium text-amber-800">
                  L25-26 failure <span className="mx-1 text-amber-400">→</span> 8 buses de-energized <span className="mx-1 text-amber-400">→</span> Telecom Tower offline
                </p>
                <p className="text-xs text-amber-600 mt-1">Lateral feeder interruption affecting communication infrastructure.</p>
              </div>
            </div>
          </div>
        </div>

        {/* Hierarchical Dependency Visualization */}
        <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm overflow-x-auto">
          <h3 className="font-semibold text-slate-800 mb-6">Dependency Chain</h3>
          
          <div className="pl-2 space-y-2 font-mono text-sm whitespace-nowrap min-w-max">
            {/* Root */}
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-green-500" />
              <span className="font-semibold text-slate-800">Substation (Bus 1)</span>
              <span className="text-xs px-2 py-0.5 bg-green-100 text-green-700 rounded-full ml-2">Energized</span>
            </div>

            {/* Feeder 1 */}
            <div className="pl-8 border-l-2 border-slate-200 ml-2 relative">
              <div className="absolute w-6 border-t-2 border-slate-200 top-3 left-0"></div>
              <div className="flex items-center gap-2 pt-1 pb-2">
                <CheckCircle2 className="w-4 h-4 text-green-500" />
                <span className="font-medium text-slate-700">Feeder F1</span>
              </div>
              
              <div className="pl-8 border-l-2 border-slate-200 ml-2">
                {/* Healthy buses F1 */}
                <div className="relative">
                  <div className="absolute w-6 border-t-2 border-slate-200 top-3 left-0"></div>
                  <div className="flex items-center gap-2 pt-1 pb-2">
                    <CheckCircle2 className="w-4 h-4 text-green-500" />
                    <span className="text-slate-600">Bus 2-6</span>
                  </div>
                </div>

                {/* Failed buses F1 */}
                <div className="relative">
                  <div className="absolute w-6 border-t-2 border-red-200 top-3 left-0"></div>
                  <div className="flex flex-col gap-2 pt-1 pb-2">
                    <div className="flex items-center gap-2">
                      <ZapOff className="w-4 h-4 text-red-500" />
                      <span className="text-red-600 font-medium">L6-7 Failure</span>
                    </div>
                    
                    <div className="pl-6 flex flex-col gap-1.5 border-l-2 border-red-100 ml-2">
                      <div className="flex items-center gap-2 text-slate-500">
                        <span className="text-red-500">↳</span> Bus 7-18 (De-energized)
                      </div>
                      <div className="flex items-center gap-2 text-slate-700 ml-4 bg-red-50 px-2 py-1 rounded border border-red-100">
                        <Heart className="w-4 h-4 text-red-600" />
                        Hospital (Bus 9) - Offline
                      </div>
                      <div className="flex items-center gap-2 text-slate-700 ml-4 bg-red-50 px-2 py-1 rounded border border-red-100">
                        <Droplets className="w-4 h-4 text-red-600" />
                        Water Plant (Bus 13) - Offline
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Feeder 2 */}
            <div className="pl-8 border-l-2 border-slate-200 ml-2 relative">
              <div className="absolute w-6 border-t-2 border-slate-200 top-3 left-0"></div>
              <div className="flex items-center gap-2 pt-1 pb-2">
                <CheckCircle2 className="w-4 h-4 text-green-500" />
                <span className="font-medium text-slate-700">Feeder F2</span>
              </div>
              <div className="pl-8 ml-2 relative">
                <div className="absolute w-6 border-t-2 border-slate-200 top-3 left-0"></div>
                <div className="flex items-center gap-2 pt-1 pb-2">
                  <CheckCircle2 className="w-4 h-4 text-green-500" />
                  <span className="text-slate-600">Bus 19-22</span>
                </div>
              </div>
            </div>

            {/* Feeder 3 */}
            <div className="pl-8 border-l-2 border-slate-200 ml-2 relative">
              <div className="absolute w-6 border-t-2 border-slate-200 top-3 left-0"></div>
              <div className="flex items-center gap-2 pt-1 pb-2">
                <CheckCircle2 className="w-4 h-4 text-green-500" />
                <span className="font-medium text-slate-700">Feeder F3</span>
              </div>
              <div className="pl-8 ml-2 relative">
                <div className="absolute w-6 border-t-2 border-slate-200 top-3 left-0"></div>
                <div className="flex items-center gap-2 pt-1 pb-2">
                  <CheckCircle2 className="w-4 h-4 text-green-500" />
                  <span className="text-slate-600">Bus 23-25</span>
                </div>
              </div>
            </div>

            {/* Feeder 4 (Branch from Bus 6 conceptually, but simplified) */}
            <div className="pl-8 border-l-2 border-transparent ml-2 relative">
              <div className="absolute w-6 border-t-2 border-slate-200 top-3 left-0"></div>
              <div className="flex items-center gap-2 pt-1 pb-2">
                <CheckCircle2 className="w-4 h-4 text-green-500" />
                <span className="font-medium text-slate-700">Feeder F4 (via Bus 6)</span>
              </div>
              <div className="pl-8 border-l-2 border-transparent ml-2">
                <div className="relative">
                  <div className="absolute w-6 border-t-2 border-amber-200 top-3 left-0"></div>
                  <div className="flex flex-col gap-2 pt-1 pb-2">
                    <div className="flex items-center gap-2">
                      <ZapOff className="w-4 h-4 text-amber-500" />
                      <span className="text-amber-600 font-medium">L25-26 Failure</span>
                    </div>
                    
                    <div className="pl-6 flex flex-col gap-1.5 ml-2">
                      <div className="flex items-center gap-2 text-slate-500">
                        <span className="text-amber-500">↳</span> Bus 26-33 (De-energized)
                      </div>
                      <div className="flex items-center gap-2 text-slate-700 ml-4 bg-amber-50 px-2 py-1 rounded border border-amber-100">
                        <Radio className="w-4 h-4 text-amber-600" />
                        Telecom Tower (Bus 29) - Degraded
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

          </div>
        </div>
      </div>
    </div>
  );
}
