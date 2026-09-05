'use client';

import React from 'react';
import { useGridStore } from '@/store/grid-store';
import { Heart, Droplets, Radio, Siren, Home, Building, Factory, Clock, Battery, BatteryWarning } from 'lucide-react';

export default function CriticalServicesPage() {
  const services = useGridStore(s => s.gridState.services);
  
  // Sort by priority (ascending, 1 is highest)
  const sortedServices = [...services].sort((a, b) => a.priority - b.priority);

  const getIcon = (type: string) => {
    switch (type) {
      case 'hospital': return <Heart className="w-5 h-5 text-rose-500" />;
      case 'water': return <Droplets className="w-5 h-5 text-blue-500" />;
      case 'telecom': return <Radio className="w-5 h-5 text-purple-500" />;
      case 'emergency': return <Siren className="w-5 h-5 text-amber-500" />;
      case 'residential': return <Home className="w-5 h-5 text-slate-500" />;
      case 'commercial': return <Building className="w-5 h-5 text-indigo-500" />;
      case 'industrial': return <Factory className="w-5 h-5 text-orange-500" />;
      default: return <Building className="w-5 h-5 text-slate-500" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'online': return <span className="bg-green-100 text-green-700 px-2.5 py-0.5 rounded-full text-xs font-medium border border-green-200">Online</span>;
      case 'offline': return <span className="bg-red-100 text-red-700 px-2.5 py-0.5 rounded-full text-xs font-medium border border-red-200">Offline</span>;
      case 'degraded': return <span className="bg-amber-100 text-amber-700 px-2.5 py-0.5 rounded-full text-xs font-medium border border-amber-200">Degraded</span>;
      case 'partially_supplied': return <span className="bg-blue-100 text-blue-700 px-2.5 py-0.5 rounded-full text-xs font-medium border border-blue-200">Partial</span>;
      default: return null;
    }
  };

  const statusCounts = services.reduce((acc, svc) => {
    acc[svc.status] = (acc[svc.status] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Critical Services</h1>
          <p className="text-slate-500">Priority-ranked critical infrastructure status and restoration tracking</p>
        </div>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white border border-slate-200 p-4 rounded-lg shadow-sm flex flex-col items-center justify-center">
          <div className="text-2xl font-semibold text-slate-800">{statusCounts['online'] || 0}</div>
          <div className="text-sm font-medium text-green-600">Online</div>
        </div>
        <div className="bg-white border border-slate-200 p-4 rounded-lg shadow-sm flex flex-col items-center justify-center">
          <div className="text-2xl font-semibold text-slate-800">{statusCounts['offline'] || 0}</div>
          <div className="text-sm font-medium text-red-600">Offline</div>
        </div>
        <div className="bg-white border border-slate-200 p-4 rounded-lg shadow-sm flex flex-col items-center justify-center">
          <div className="text-2xl font-semibold text-slate-800">{statusCounts['degraded'] || 0}</div>
          <div className="text-sm font-medium text-amber-600">Degraded</div>
        </div>
        <div className="bg-white border border-slate-200 p-4 rounded-lg shadow-sm flex flex-col items-center justify-center">
          <div className="text-2xl font-semibold text-slate-800">{statusCounts['partially_supplied'] || 0}</div>
          <div className="text-sm font-medium text-blue-600">Partial</div>
        </div>
      </div>

      {/* Cards List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {sortedServices.map((service) => (
          <div key={service.id} className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm relative">
            <div className="absolute top-4 right-4">{getStatusBadge(service.status)}</div>
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-slate-50 rounded-lg border border-slate-100">
                {getIcon(service.type)}
              </div>
              <div>
                <h3 className="font-semibold text-slate-800 leading-tight">{service.name}</h3>
                <div className="text-xs text-slate-500 uppercase tracking-wide">Priority {service.priority}</div>
              </div>
            </div>
            
            <div className="space-y-3 mb-4">
              <div className="flex justify-between items-center text-sm border-b border-slate-50 pb-2">
                <span className="text-slate-500">Location</span>
                <span className="font-medium text-slate-700">{service.bus_id}</span>
              </div>
              <div className="flex justify-between items-center text-sm border-b border-slate-50 pb-2">
                <span className="text-slate-500">Load Profile</span>
                <span className="font-medium text-slate-700">{service.load_mw} MW</span>
              </div>
              <div className="flex justify-between items-center text-sm border-b border-slate-50 pb-2">
                <span className="text-slate-500">Backup Power</span>
                {service.backup_available ? (
                  <span className="flex items-center gap-1 font-medium text-green-600">
                    <Battery className="w-4 h-4" /> Available
                  </span>
                ) : (
                  <span className="flex items-center gap-1 font-medium text-red-600">
                    <BatteryWarning className="w-4 h-4" /> None
                  </span>
                )}
              </div>
            </div>

            {service.status !== 'online' && (
              <div className="bg-slate-50 rounded-md p-3 flex items-center gap-2 border border-slate-100">
                <Clock className="w-4 h-4 text-slate-400" />
                <div>
                  <div className="text-xs text-slate-500">Est. Restoration</div>
                  <div className="text-sm font-medium text-slate-700">
                    {service.estimated_restore ? new Date(service.estimated_restore).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : 'TBD'}
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Priority Matrix Table */}
      <div className="bg-white border border-slate-200 rounded-lg shadow-sm overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-200">
          <h3 className="font-semibold text-slate-800">Service Priority Matrix</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="bg-slate-50 text-slate-600 text-xs uppercase border-b border-slate-200">
              <tr>
                <th className="px-5 py-3 font-medium">Priority</th>
                <th className="px-5 py-3 font-medium">Service</th>
                <th className="px-5 py-3 font-medium">Type</th>
                <th className="px-5 py-3 font-medium">Location</th>
                <th className="px-5 py-3 font-medium">Status</th>
                <th className="px-5 py-3 font-medium">Load (MW)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {sortedServices.map(svc => (
                <tr key={svc.id} className="hover:bg-slate-50 transition-colors">
                  <td className="px-5 py-3 text-slate-700 font-medium">#{svc.priority}</td>
                  <td className="px-5 py-3 text-slate-800 font-medium flex items-center gap-2">
                    {getIcon(svc.type)}
                    {svc.name}
                  </td>
                  <td className="px-5 py-3 text-slate-500 capitalize">{svc.type}</td>
                  <td className="px-5 py-3 text-slate-600">{svc.bus_id}</td>
                  <td className="px-5 py-3">{getStatusBadge(svc.status)}</td>
                  <td className="px-5 py-3 text-slate-600">{svc.load_mw.toFixed(1)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
