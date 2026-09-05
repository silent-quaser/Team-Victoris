'use client';

import React from 'react';
import { X, Activity, AlertCircle, Zap, ShieldAlert, Cpu } from 'lucide-react';
import { useGridStore } from '@/store/grid-store';
import { AssetStatus } from '@/types';

const StatusBadge = ({ status }: { status: AssetStatus }) => {
  const styles = {
    healthy: 'bg-green-100 text-green-800 border-green-200',
    failed: 'bg-red-100 text-red-800 border-red-200',
    uncertain: 'bg-amber-100 text-amber-800 border-amber-200',
    selected: 'bg-blue-100 text-blue-800 border-blue-200',
  };

  const labels = {
    healthy: 'Healthy',
    failed: 'Failed',
    uncertain: 'Uncertain State',
    selected: 'Selected',
  };

  return (
    <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border ${styles[status] || styles.healthy}`}>
      {labels[status] || status}
    </span>
  );
};

export default function AssetDrawer() {
  const { selectedAssetId, assetDrawerOpen, closeAssetDrawer, gridState } = useGridStore();

  if (!assetDrawerOpen || !selectedAssetId) return null;

  // Find the selected asset
  const bus = gridState.buses.find(b => b.id === selectedAssetId);
  const line = gridState.lines.find(l => l.id === selectedAssetId);
  const transformer = gridState.transformers.find(t => t.id === selectedAssetId);
  
  const assetType = bus ? 'Bus' : line ? 'Line' : transformer ? 'Transformer' : 'Unknown Asset';
  const asset = bus || line || transformer;
  
  if (!asset) return null;

  const isT3 = asset.id === 'T3';

  return (
    <>
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-slate-900/20 backdrop-blur-[1px] z-40 transition-opacity"
        onClick={closeAssetDrawer}
      />
      
      {/* Drawer */}
      <div className="fixed inset-y-0 right-0 w-96 bg-white shadow-2xl z-50 transform transition-transform duration-300 ease-in-out border-l border-slate-200 flex flex-col">
        {/* Header */}
        <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50">
          <div>
            <h2 className="text-lg font-bold text-slate-900">
              {assetType === 'Transformer' ? transformer?.name : assetType === 'Bus' ? `Bus ${bus?.number}` : line?.id}
            </h2>
            <div className="text-xs text-slate-500 font-medium">{assetType}</div>
          </div>
          <button 
            onClick={closeAssetDrawer}
            className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-200 rounded-md transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-5 space-y-6">
          {/* Status Section */}
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-slate-600">Current Status</span>
            <StatusBadge status={asset.status} />
          </div>

          {/* Special warning for T3 */}
          {isT3 && asset.status === 'uncertain' && (
            <div className="bg-amber-50 border border-amber-200 rounded-md p-3 flex items-start space-x-3">
              <ShieldAlert className="text-amber-500 mt-0.5 shrink-0" size={18} />
              <div>
                <h4 className="text-sm font-semibold text-amber-800">Unconfirmed Fault</h4>
                <p className="text-xs text-amber-700 mt-1">
                  Protection relays triggered, but DGA sensors show conflicting data. Physical inspection recommended.
                </p>
              </div>
            </div>
          )}

          {isT3 && asset.status === 'failed' && (
            <div className="bg-red-50 border border-red-200 rounded-md p-3 flex items-start space-x-3">
              <AlertCircle className="text-red-500 mt-0.5 shrink-0" size={18} />
              <div>
                <h4 className="text-sm font-semibold text-red-800">Confirmed Failure</h4>
                <p className="text-xs text-red-700 mt-1">
                  Field crew inspection confirmed internal insulation failure. Asset must be isolated.
                </p>
              </div>
            </div>
          )}

          {/* Properties Table */}
          <div>
            <h3 className="text-sm font-semibold text-slate-900 mb-3 flex items-center">
              <Activity size={16} className="mr-2 text-slate-400" />
              Operating Metrics
            </h3>
            
            <div className="bg-slate-50 rounded-lg border border-slate-200 overflow-hidden">
              <table className="w-full text-sm">
                <tbody className="divide-y divide-slate-200">
                  
                  {/* Bus Properties */}
                  {bus && (
                    <>
                      <tr>
                        <td className="px-4 py-2.5 text-slate-500 font-medium w-1/2">Voltage</td>
                        <td className="px-4 py-2.5 text-slate-900 font-semibold">{bus.voltage_kv} kV</td>
                      </tr>
                      <tr>
                        <td className="px-4 py-2.5 text-slate-500 font-medium">Load</td>
                        <td className="px-4 py-2.5 text-slate-900 font-semibold">{bus.load_mw} MW</td>
                      </tr>
                      {bus.feeder && (
                        <tr>
                          <td className="px-4 py-2.5 text-slate-500 font-medium">Feeder</td>
                          <td className="px-4 py-2.5 text-slate-900 font-semibold">{bus.feeder}</td>
                        </tr>
                      )}
                      {bus.is_critical && (
                        <tr>
                          <td className="px-4 py-2.5 text-slate-500 font-medium">Critical Facility</td>
                          <td className="px-4 py-2.5 text-blue-700 font-semibold">{bus.critical_facility}</td>
                        </tr>
                      )}
                    </>
                  )}

                  {/* Line Properties */}
                  {line && (
                    <>
                      <tr>
                        <td className="px-4 py-2.5 text-slate-500 font-medium w-1/2">Connections</td>
                        <td className="px-4 py-2.5 text-slate-900 font-semibold">Bus {line.from_bus} → Bus {line.to_bus}</td>
                      </tr>
                      <tr>
                        <td className="px-4 py-2.5 text-slate-500 font-medium">Type</td>
                        <td className="px-4 py-2.5 text-slate-900 font-semibold capitalize">{line.type}</td>
                      </tr>
                      <tr>
                        <td className="px-4 py-2.5 text-slate-500 font-medium">Length</td>
                        <td className="px-4 py-2.5 text-slate-900 font-semibold">{line.length_km} km</td>
                      </tr>
                      <tr>
                        <td className="px-4 py-2.5 text-slate-500 font-medium">Current Flow</td>
                        <td className="px-4 py-2.5 text-slate-900 font-semibold">
                          {line.current_flow_mw} / {line.capacity_mw} MW
                          <div className="w-full bg-slate-200 rounded-full h-1.5 mt-1.5">
                            <div 
                              className={`h-1.5 rounded-full ${line.current_flow_mw > line.capacity_mw * 0.9 ? 'bg-red-500' : 'bg-blue-500'}`}
                              style={{ width: `${Math.min(100, (line.current_flow_mw / line.capacity_mw) * 100)}%` }}
                            ></div>
                          </div>
                        </td>
                      </tr>
                    </>
                  )}

                  {/* Transformer Properties */}
                  {transformer && (
                    <>
                      <tr>
                        <td className="px-4 py-2.5 text-slate-500 font-medium w-1/2">Rating</td>
                        <td className="px-4 py-2.5 text-slate-900 font-semibold">{transformer.rating_mva} MVA</td>
                      </tr>
                      <tr>
                        <td className="px-4 py-2.5 text-slate-500 font-medium">Load Level</td>
                        <td className="px-4 py-2.5 text-slate-900 font-semibold">
                          {transformer.load_pct}%
                          <div className="w-full bg-slate-200 rounded-full h-1.5 mt-1.5">
                            <div 
                              className={`h-1.5 rounded-full ${transformer.load_pct > 90 ? 'bg-amber-500' : 'bg-blue-500'}`}
                              style={{ width: `${transformer.load_pct}%` }}
                            ></div>
                          </div>
                        </td>
                      </tr>
                      <tr>
                        <td className="px-4 py-2.5 text-slate-500 font-medium">Tap Position</td>
                        <td className="px-4 py-2.5 text-slate-900 font-semibold">{transformer.tap_position}</td>
                      </tr>
                    </>
                  )}
                </tbody>
              </table>
            </div>
          </div>
          
          {bus && bus.has_der && (
            <div>
              <h3 className="text-sm font-semibold text-slate-900 mb-3 flex items-center">
                <Zap size={16} className="mr-2 text-green-500" />
                Local DER Assets
              </h3>
              <div className="bg-green-50 border border-green-200 rounded-md p-3">
                <p className="text-xs text-green-800">
                  This node has connected Distributed Energy Resources capable of supporting microgrid formation.
                </p>
              </div>
            </div>
          )}

        </div>
        
        {/* Footer Actions */}
        <div className="p-4 border-t border-slate-200 bg-slate-50 flex space-x-3">
          <button 
            onClick={() => {
              useGridStore.getState().addLog(`Triggered automated isolation sequence for ${assetType} ${asset.id}`, 'warning');
              closeAssetDrawer();
            }}
            className="flex-1 bg-white border border-red-300 text-red-700 py-2 rounded-md text-sm font-medium hover:bg-red-50 transition-colors shadow-sm"
          >
            Isolate Asset
          </button>
          <button 
            onClick={() => {
              useGridStore.getState().addLog(`Dispatched Field Crew to ${assetType} ${asset.id}`, 'success');
              closeAssetDrawer();
            }}
            className="flex-1 bg-blue-600 text-white py-2 rounded-md text-sm font-medium hover:bg-blue-700 transition-colors shadow-sm"
          >
            Dispatch Crew
          </button>
        </div>
      </div>
    </>
  );
}
