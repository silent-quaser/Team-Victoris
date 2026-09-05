'use client';

import React, { useEffect, useState } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
  Position,
  Handle,
  MarkerType
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { useGridStore } from '@/store/grid-store';
import { AssetStatus, Bus, Line, Transformer } from '@/types';
import { Building2, Hospital, Radio, Map as MapIcon, List, Network, Zap } from 'lucide-react';
import DynamicGeoMap from './DynamicGeoMap';

const statusColors: Record<AssetStatus, string> = {
  healthy: '#22c55e',
  failed: '#ef4444',
  uncertain: '#f59e0b',
  selected: '#3b82f6',
};

const getStatusColorClass = (status: AssetStatus) => {
  switch (status) {
    case 'healthy': return 'bg-green-500';
    case 'failed': return 'bg-red-500';
    case 'uncertain': return 'bg-amber-500';
    case 'selected': return 'bg-blue-500';
    default: return 'bg-slate-500';
  }
};

const BusNode = ({ data, selected }: { data: any, selected?: boolean }) => {
  const bus = data.bus as Bus;
  const isSubstation = bus.number === 1;
  const colorClass = getStatusColorClass(bus.status);

  let Icon = null;
  if (bus.is_critical && bus.critical_facility) {
    if (bus.critical_facility.toLowerCase().includes('hospital')) Icon = Hospital;
    else if (bus.critical_facility.toLowerCase().includes('telecom') || bus.critical_facility.toLowerCase().includes('exchange')) Icon = Radio;
    else Icon = Building2;
  }

  return (
    <div 
      className={`relative flex items-center justify-center transition-all ${isSubstation ? 'w-10 h-10 rounded-md' : 'w-8 h-8 rounded-full'} ${selected || bus.status === 'selected' ? 'ring-4 ring-blue-300 scale-110' : 'border border-slate-300'} shadow-sm bg-white cursor-pointer hover:shadow-md hover:scale-110`}
      onClick={() => data.onSelect(bus.id)}
    >
      <Handle type="target" position={Position.Left} className="!opacity-0" />
      <div className={`absolute inset-0 opacity-10 rounded-full ${colorClass}`}></div>
      <span className="text-xs font-semibold text-slate-700 z-10">{bus.number}</span>
      <div className={`absolute -top-1 -right-1 w-3 h-3 rounded-full border border-white ${colorClass}`} />
      
      {Icon && (
        <div className="absolute -bottom-5 left-1/2 transform -translate-x-1/2 bg-white p-1 rounded shadow border border-slate-200 z-20">
          <Icon size={14} className={bus.status === 'failed' ? 'text-red-500' : 'text-slate-600'} />
        </div>
      )}
      
      {bus.has_der && (
        <div className="absolute -top-5 left-1/2 transform -translate-x-1/2 bg-green-50 p-1 rounded shadow border border-green-200 z-20 text-green-600">
          <Zap size={12} fill="currentColor" />
        </div>
      )}
      
      <Handle type="source" position={Position.Right} className="!opacity-0" />
      <Handle type="source" position={Position.Top} className="!opacity-0" />
      <Handle type="source" position={Position.Bottom} className="!opacity-0" />
    </div>
  );
};

const TransformerNode = ({ data, selected }: { data: any, selected?: boolean }) => {
  const t = data.transformer as Transformer;
  const colorClass = getStatusColorClass(t.status);
  
  return (
    <div 
      className={`relative flex flex-col items-center justify-center cursor-pointer transition-all ${selected || t.status === 'selected' ? 'ring-4 ring-blue-300 rounded-full scale-110' : 'hover:scale-110'}`}
      onClick={() => data.onSelect(t.id)}
      title={t.name}
    >
      <Handle type="target" position={Position.Left} className="!opacity-0" />
      <div className="relative w-8 h-10 flex flex-col items-center justify-center -space-y-3">
        <div className={`w-6 h-6 rounded-full border-2 ${t.status === 'failed' ? 'border-red-500' : t.status === 'uncertain' ? 'border-amber-500' : 'border-slate-500'} bg-white z-10 flex items-center justify-center`}>
          <div className={`w-2 h-2 rounded-full ${colorClass}`} />
        </div>
        <div className={`w-6 h-6 rounded-full border-2 ${t.status === 'failed' ? 'border-red-500' : t.status === 'uncertain' ? 'border-amber-500' : 'border-slate-500'} bg-white z-0`}></div>
      </div>
      <div className="mt-1 text-[10px] font-bold text-slate-600 bg-white px-1 rounded border border-slate-200 shadow-sm whitespace-nowrap">{t.name}</div>
      <Handle type="source" position={Position.Right} className="!opacity-0" />
    </div>
  );
};

const nodeTypes = {
  bus: BusNode,
  transformer: TransformerNode,
};

export default function GridVisualization() {
  const { gridState, selectAsset, selectedAssetId } = useGridStore();
  const [activeTab, setActiveTab] = useState<'network' | 'geo' | 'list'>('network');
  
  const [nodes, setNodes, onNodesChange] = useNodesState([] as Node[]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([] as Edge[]);

  useEffect(() => {
    const newNodes: Node[] = [];
    const newEdges: Edge[] = [];
    const scale = 0.45; // slightly larger scale for better spacing
    
    gridState.buses.forEach(bus => {
      newNodes.push({
        id: bus.id,
        type: 'bus',
        position: { x: bus.x * scale, y: bus.y * scale },
        data: { 
          bus: { ...bus, status: selectedAssetId === bus.id ? 'selected' : bus.status }, 
          onSelect: selectAsset 
        },
      });
    });
    
    gridState.transformers.forEach(t => {
      const bus = gridState.buses.find(b => b.id === t.bus_id);
      if (bus) {
        newNodes.push({
          id: t.id,
          type: 'transformer',
          position: { x: (bus.x * scale) + 40, y: (bus.y * scale) - 55 },
          data: { 
            transformer: { ...t, status: selectedAssetId === t.id ? 'selected' : t.status }, 
            onSelect: selectAsset 
          },
        });
        
        newEdges.push({
          id: `e-${t.id}-${bus.id}`,
          source: bus.id,
          target: t.id,
          style: { stroke: '#94a3b8', strokeWidth: 1.5, strokeDasharray: '4 4' },
          animated: false,
        });
      }
    });

    gridState.lines.forEach(line => {
      const isFailed = line.status === 'failed';
      const isUncertain = line.status === 'uncertain';
      const isSelected = selectedAssetId === line.id;
      
      let strokeColor = statusColors.healthy;
      if (isSelected) strokeColor = statusColors.selected;
      else if (isFailed) strokeColor = statusColors.failed;
      else if (isUncertain) strokeColor = statusColors.uncertain;
      
      newEdges.push({
        id: line.id,
        source: line.from_bus,
        target: line.to_bus,
        type: 'default',
        style: { 
          stroke: strokeColor, 
          strokeWidth: isSelected ? 4 : (line.type === 'feeder' ? 3 : 2),
          strokeDasharray: isFailed ? '5 5' : isUncertain ? '2 2' : 'none',
          transition: 'all 0.3s ease',
        },
        animated: isUncertain || isFailed, // animate failed and uncertain lines for emphasis
        markerEnd: {
          type: MarkerType.ArrowClosed,
          width: 15,
          height: 15,
          color: strokeColor,
        },
      });
    });

    setNodes(newNodes);
    setEdges(newEdges);
  }, [gridState.buses, gridState.lines, gridState.transformers, selectedAssetId, selectAsset, setNodes, setEdges]);

  // Combined asset list for the List View
  const allAssets = [
    ...gridState.buses.map(b => ({ id: b.id, name: b.name, type: 'Bus', status: b.status, detail: `${b.load_mw} MW` })),
    ...gridState.transformers.map(t => ({ id: t.id, name: t.name, type: 'Transformer', status: t.status, detail: `${t.rating_mva} MVA` })),
    ...gridState.lines.map(l => ({ id: l.id, name: l.id, type: 'Line', status: l.status, detail: `${l.capacity_mw} MW Cap` }))
  ];

  return (
    <div className="bg-white border border-slate-200 rounded-lg flex flex-col h-[480px] overflow-hidden shadow-sm">
      <div className="flex border-b border-slate-200 bg-slate-50 px-4 h-12 items-center justify-between z-10">
        <div className="flex space-x-2 bg-slate-200/50 p-1 rounded-lg">
          <button 
            onClick={() => setActiveTab('network')}
            className={`flex items-center px-4 py-1.5 text-sm font-medium rounded-md transition-all ${activeTab === 'network' ? 'bg-white text-blue-700 shadow-sm' : 'text-slate-600 hover:text-slate-900'}`}
          >
            <Network size={16} className="mr-2" />
            Network
          </button>
          <button 
            onClick={() => setActiveTab('geo')}
            className={`flex items-center px-4 py-1.5 text-sm font-medium rounded-md transition-all ${activeTab === 'geo' ? 'bg-white text-blue-700 shadow-sm' : 'text-slate-600 hover:text-slate-900'}`}
          >
            <MapIcon size={16} className="mr-2" />
            Geographic
          </button>
          <button 
            onClick={() => setActiveTab('list')}
            className={`flex items-center px-4 py-1.5 text-sm font-medium rounded-md transition-all ${activeTab === 'list' ? 'bg-white text-blue-700 shadow-sm' : 'text-slate-600 hover:text-slate-900'}`}
          >
            <List size={16} className="mr-2" />
            List
          </button>
        </div>
        
        <div className="flex items-center text-xs text-slate-600 font-medium space-x-5 bg-white px-3 py-1.5 rounded-full border border-slate-200">
          <div className="flex items-center"><div className="w-2.5 h-2.5 rounded-full bg-green-500 mr-1.5 shadow-sm"></div> Healthy</div>
          <div className="flex items-center"><div className="w-2.5 h-2.5 rounded-full bg-amber-500 mr-1.5 shadow-sm"></div> Uncertain</div>
          <div className="flex items-center"><div className="w-2.5 h-2.5 rounded-full bg-red-500 mr-1.5 shadow-sm animate-pulse"></div> Failed</div>
        </div>
      </div>

      <div className="flex-1 relative bg-[#f8fafc]">
        {activeTab === 'network' && (
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            nodeTypes={nodeTypes}
            fitView
            fitViewOptions={{ padding: 0.2 }}
            minZoom={0.2}
            maxZoom={2}
          >
            <Background color="#cbd5e1" gap={20} size={2} />
            <Controls className="bg-white border border-slate-200 shadow-sm rounded-md" />
            <MiniMap 
              className="border border-slate-200 shadow-sm rounded-lg overflow-hidden bg-white/80 backdrop-blur"
              nodeColor={(n) => n.type === 'transformer' ? '#94a3b8' : '#3b82f6'}
              maskColor="rgba(241, 245, 249, 0.7)"
            />
          </ReactFlow>
        )}
        
        {activeTab === 'geo' && (
          <div className="absolute inset-0 z-0">
            <DynamicGeoMap />
          </div>
        )}
        
        {activeTab === 'list' && (
          <div className="absolute inset-0 overflow-y-auto bg-white">
            <table className="w-full text-sm text-left">
              <thead className="bg-slate-50 text-slate-600 sticky top-0 shadow-sm z-10 border-b border-slate-200">
                <tr>
                  <th className="px-6 py-3 font-semibold">Asset ID</th>
                  <th className="px-6 py-3 font-semibold">Type</th>
                  <th className="px-6 py-3 font-semibold">Status</th>
                  <th className="px-6 py-3 font-semibold">Details</th>
                  <th className="px-6 py-3 font-semibold">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {allAssets.map(asset => (
                  <tr 
                    key={asset.id} 
                    className={`hover:bg-blue-50 transition-colors cursor-pointer ${selectedAssetId === asset.id ? 'bg-blue-50' : ''}`}
                    onClick={() => selectAsset(asset.id)}
                  >
                    <td className="px-6 py-3 font-medium text-slate-800">{asset.name}</td>
                    <td className="px-6 py-3 text-slate-500">
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-700 border border-slate-200">
                        {asset.type}
                      </span>
                    </td>
                    <td className="px-6 py-3">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium text-white ${getStatusColorClass(asset.status)}`}>
                        {asset.status.toUpperCase()}
                      </span>
                    </td>
                    <td className="px-6 py-3 text-slate-600">{asset.detail}</td>
                    <td className="px-6 py-3">
                      <button className="text-blue-600 hover:text-blue-800 text-xs font-medium hover:underline">
                        View Details
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
