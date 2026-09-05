'use client';

import React from 'react';
import { mockCrews, mockResources } from '@/data/mock-data';
import { Users, Truck, Wrench, Shield, CheckCircle, Clock, MapPin, Package } from 'lucide-react';

export default function ResourcesPage() {
  const crewStats = {
    available: mockCrews.filter(c => c.status === 'available').length,
    deployed: mockCrews.filter(c => c.status === 'deployed').length,
    enRoute: mockCrews.filter(c => c.status === 'en_route').length,
    offDuty: mockCrews.filter(c => c.status === 'off_duty').length,
  };

  const getStatusColor = (status: string) => {
    switch(status) {
      case 'available': return 'bg-green-50 text-green-700 border-green-200';
      case 'deployed': return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'en_route': return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'off_duty': return 'bg-slate-100 text-slate-700 border-slate-200';
      default: return 'bg-slate-50 text-slate-700 border-slate-200';
    }
  };

  return (
    <div className="flex flex-col gap-6 max-w-7xl mx-auto">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Resources</h1>
        <p className="text-sm text-slate-500 mt-1">Crew management and equipment inventory</p>
      </div>

      <div className="grid grid-cols-4 gap-4">
        <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm">
          <p className="text-sm font-medium text-slate-500 mb-1">Available Crews</p>
          <div className="flex items-end justify-between">
            <span className="text-2xl font-bold text-slate-900">{crewStats.available}</span>
            <div className="p-2 bg-green-50 text-green-600 rounded-lg"><CheckCircle size={18} /></div>
          </div>
        </div>
        <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm">
          <p className="text-sm font-medium text-slate-500 mb-1">Deployed</p>
          <div className="flex items-end justify-between">
            <span className="text-2xl font-bold text-slate-900">{crewStats.deployed}</span>
            <div className="p-2 bg-blue-50 text-blue-600 rounded-lg"><Wrench size={18} /></div>
          </div>
        </div>
        <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm">
          <p className="text-sm font-medium text-slate-500 mb-1">En Route</p>
          <div className="flex items-end justify-between">
            <span className="text-2xl font-bold text-slate-900">{crewStats.enRoute}</span>
            <div className="p-2 bg-amber-50 text-amber-600 rounded-lg"><Truck size={18} /></div>
          </div>
        </div>
        <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm">
          <p className="text-sm font-medium text-slate-500 mb-1">Off Duty</p>
          <div className="flex items-end justify-between">
            <span className="text-2xl font-bold text-slate-900">{crewStats.offDuty}</span>
            <div className="p-2 bg-slate-100 text-slate-600 rounded-lg"><Clock size={18} /></div>
          </div>
        </div>
      </div>

      <div className="space-y-4">
        <h2 className="text-lg font-semibold text-slate-900">Crew Status</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
          {mockCrews.map(crew => (
            <div key={crew.id} className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm">
              <div className="flex justify-between items-start mb-3">
                <h3 className="font-semibold text-slate-900">{crew.name}</h3>
                <span className={`text-xs px-2 py-0.5 rounded-full border font-medium capitalize ${getStatusColor(crew.status)}`}>
                  {crew.status.replace('_', ' ')}
                </span>
              </div>
              
              <div className="space-y-2 mb-4">
                <div className="flex items-center text-sm text-slate-600">
                  <Users size={14} className="mr-2 text-slate-400" />
                  {crew.members} members
                </div>
                <div className="flex items-center text-sm text-slate-600">
                  <Shield size={14} className="mr-2 text-slate-400" />
                  {crew.specialization}
                </div>
                <div className="flex items-center text-sm text-slate-600">
                  <MapPin size={14} className="mr-2 text-slate-400" />
                  {crew.location || 'Unknown'}
                </div>
              </div>

              {crew.current_task && (
                <div className="mt-auto pt-3 border-t border-slate-100">
                  <p className="text-xs font-medium text-slate-500 mb-1">Current Task</p>
                  <p className="text-sm text-slate-800 line-clamp-2">{crew.current_task}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="space-y-4 mt-2">
        <h2 className="text-lg font-semibold text-slate-900">Equipment & Materials Inventory</h2>
        <div className="bg-white border border-slate-200 rounded-lg shadow-sm overflow-hidden">
          <table className="w-full text-left">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="py-3 px-4 text-xs font-semibold text-slate-500 uppercase">Resource Name</th>
                <th className="py-3 px-4 text-xs font-semibold text-slate-500 uppercase">Type</th>
                <th className="py-3 px-4 text-xs font-semibold text-slate-500 uppercase">Total Qty</th>
                <th className="py-3 px-4 text-xs font-semibold text-slate-500 uppercase">Available</th>
                <th className="py-3 px-4 text-xs font-semibold text-slate-500 uppercase">Unit</th>
                <th className="py-3 px-4 text-xs font-semibold text-slate-500 uppercase w-48">Availability</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {mockResources.map(res => {
                const availPct = (res.available / res.quantity) * 100;
                return (
                  <tr key={res.id} className="hover:bg-slate-50">
                    <td className="py-3 px-4 text-sm font-medium text-slate-900 flex items-center gap-2">
                      <Package size={16} className="text-slate-400" />
                      {res.name}
                    </td>
                    <td className="py-3 px-4 text-sm text-slate-600 capitalize">{res.type}</td>
                    <td className="py-3 px-4 text-sm text-slate-600">{res.quantity.toLocaleString()}</td>
                    <td className="py-3 px-4 text-sm font-medium text-slate-900">{res.available.toLocaleString()}</td>
                    <td className="py-3 px-4 text-sm text-slate-600">{res.unit}</td>
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
                          <div 
                            className={`h-full rounded-full ${availPct > 50 ? 'bg-green-500' : availPct > 20 ? 'bg-amber-500' : 'bg-red-500'}`} 
                            style={{ width: `${availPct}%` }}
                          ></div>
                        </div>
                        <span className="text-xs font-medium text-slate-500 w-8">{Math.round(availPct)}%</span>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
