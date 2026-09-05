'use client';

import React, { useMemo, useEffect, useState } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
  Position,
  Handle,
  Panel,
  MarkerType
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { useGridStore } from '@/store/grid-store';
import { AssetStatus, Bus, Line, Transformer } from '@/types';
import { Building2, Hospital, Radio, Map as MapIcon, List, Network, Zap } from 'lucide-react';

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
  const statusColor = statusColors[bus.status];
  const colorClass = getStatusColorClass(bus.status);

  let Icon = null;
  if (bus.is_critical && bus.critical_facility) {
    if (bus.critical_facility.toLowerCase().includes('hospital')) Icon = Hospital;
    else if (bus.critical_facility.toLowerCase().includes('telecom')) Icon = Radio;
    else Icon = Building2;
  }

  return (
    <div 
      className={`relative flex items-center justify-center transition-all ${isSubstation ? 'w-10 h-10 rounded-md' : 'w-8 h-8 rounded-full'} ${selected || bus.status === 'selected' ? 'ring-4 ring-blue-300' : 'border border-slate-300'} shadow-sm bg-white cursor-pointer hover:shadow-md`}
      onClick={() => data.onSelect(bus.id)}
    >
      <Handle type="target" position={Position.Left} className="!opacity-0" />
      
      <div className={`absolute inset-0 opacity-10 rounded-full ${colorClass}`}></div>
      
      <span className="text-xs font-semibold text-slate-700 z-10">{bus.number}</span>
      
      {/* Status indicator dot */}
      <div className={`absolute -top-1 -right-1 w-3 h-3 rounded-full border border-white ${colorClass}`} />
      
      {/* Icons */}
      {Icon && (
        <div className="absolute -bottom-4 left-1/2 transform -translate-x-1/2 bg-white p-0.5 rounded shadow border border-slate-200 z-20">
          <Icon size={12} className={bus.status === 'failed' ? 'text-red-500' : 'text-slate-600'} />
        </div>
      )}
      
      {bus.has_der && (
        <div className="absolute -top-4 left-1/2 transform -translate-x-1/2 bg-green-50 p-0.5 rounded shadow border border-green-200 z-20 text-green-600">
          <Zap size={10} />
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
      className={`relative flex flex-col items-center justify-center cursor-pointer ${selected || t.status === 'selected' ? 'ring-4 ring-blue-300 rounded-full' : ''}`}
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
      
      <div className="mt-1 text-[10px] font-bold text-slate-600 bg-white px-1 rounded border border-slate-200 shadow-sm">{t.name}</div>
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
    // Generate nodes and edges from store data
    const newNodes: Node[] = [];
    const newEdges: Edge[] = [];

    // Scale down the mock data x,y coordinates
    const scale = 0.4;
    
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
      // Find connected bus to position transformer near it
      const bus = gridState.buses.find(b => b.id === t.bus_id);
      if (bus) {
        newNodes.push({
          id: t.id,
          type: 'transformer',
          position: { x: (bus.x * scale) + 40, y: (bus.y * scale) - 50 },
          data: { 
            transformer: { ...t, status: selectedAssetId === t.id ? 'selected' : t.status }, 
            onSelect: selectAsset 
          },
        });
        
        // Add pseudo-edge for transformer to bus
        newEdges.push({
          id: `e-${t.id}-${bus.id}`,
          source: bus.id,
          target: t.id,
          style: { stroke: '#94a3b8', strokeWidth: 1, strokeDasharray: '4 4' },
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
          strokeWidth: line.type === 'feeder' ? 3 : 2,
          strokeDasharray: isFailed ? '5 5' : isUncertain ? '2 2' : 'none',
        },
        animated: isUncertain,
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

  return (
    <div className="bg-white border border-slate-200 rounded-lg flex flex-col h-[420px] overflow-hidden shadow-sm">
      {/* Header Tabs */}
      <div className="flex border-b border-slate-200 bg-slate-50 px-4 h-11 items-center justify-between">
        <div className="flex space-x-1">
          <button 
            onClick={() => setActiveTab('network')}
            className={`flex items-center px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${activeTab === 'network' ? 'bg-white text-blue-700 shadow-sm border border-slate-200' : 'text-slate-600 hover:bg-slate-200'}`}
          >
            <Network size={16} className="mr-1.5" />
            Network
          </button>
          <button 
            onClick={() => setActiveTab('geo')}
            className={`flex items-center px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${activeTab === 'geo' ? 'bg-white text-blue-700 shadow-sm border border-slate-200' : 'text-slate-600 hover:bg-slate-200'}`}
          >
            <MapIcon size={16} className="mr-1.5" />
            Geographic
          </button>
          <button 
            onClick={() => setActiveTab('list')}
            className={`flex items-center px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${activeTab === 'list' ? 'bg-white text-blue-700 shadow-sm border border-slate-200' : 'text-slate-600 hover:bg-slate-200'}`}
          >
            <List size={16} className="mr-1.5" />
            List
          </button>
        </div>
        
        <div className="flex items-center text-xs text-slate-500 space-x-4">
          <div className="flex items-center"><div className="w-2 h-2 rounded-full bg-green-500 mr-1"></div> Healthy</div>
          <div className="flex items-center"><div className="w-2 h-2 rounded-full bg-amber-500 mr-1"></div> Uncertain</div>
          <div className="flex items-center"><div className="w-2 h-2 rounded-full bg-red-500 mr-1"></div> Failed</div>
        </div>
      </div>

      {/* Content Area */}
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
            attributionPosition="bottom-right"
          >
            <Background color="#e2e8f0" gap={16} size={1} />
            <Controls className="bg-white border border-slate-200 shadow-sm rounded-md" />
          </ReactFlow>
        )}
        
        {activeTab === 'geo' && (
          <div className="absolute inset-0 flex items-center justify-center bg-slate-50">
            <div className="text-center">
              <MapIcon size={48} className="mx-auto text-slate-300 mb-3" />
              <h3 className="text-sm font-medium text-slate-600">Geographic View Not Configured</h3>
              <p className="text-xs text-slate-400 mt-1">GIS integration requires API key setup.</p>
            </div>
          </div>
        )}
        
        {activeTab === 'list' && (
          <div className="absolute inset-0 flex items-center justify-center bg-slate-50">
            <div className="text-center">
              <List size={48} className="mx-auto text-slate-300 mb-3" />
              <h3 className="text-sm font-medium text-slate-600">Asset List View</h3>
              <p className="text-xs text-slate-400 mt-1">Select an asset from the Network view.</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
