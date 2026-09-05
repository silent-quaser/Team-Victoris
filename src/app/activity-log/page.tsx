'use client';

import React, { useState } from 'react';
import { useGridStore } from '@/store/grid-store';
import { Filter, Search, ChevronDown, ChevronUp, AlertCircle, Info, CheckCircle, AlertTriangle } from 'lucide-react';

type FilterType = 'all' | 'action' | 'alert' | 'system' | 'operator';

export default function ActivityLogPage() {
  const activityLog = useGridStore((s) => s.activityLog);
  const [filter, setFilter] = useState<FilterType>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const baseFilteredLogs = filter === 'all' 
    ? activityLog 
    : activityLog.filter(log => log.type === filter);
    
  const filteredLogs = searchQuery.trim() === ''
    ? baseFilteredLogs
    : baseFilteredLogs.filter(log => 
        log.message.toLowerCase().includes(searchQuery.toLowerCase()) || 
        (log.user && log.user.toLowerCase().includes(searchQuery.toLowerCase()))
      );

  const counts = {
    all: activityLog.length,
    action: activityLog.filter(l => l.type === 'action').length,
    alert: activityLog.filter(l => l.type === 'alert').length,
    system: activityLog.filter(l => l.type === 'system').length,
    operator: activityLog.filter(l => l.type === 'operator').length,
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'error': return <AlertCircle className="w-4 h-4 text-red-500" />;
      case 'warning': return <AlertTriangle className="w-4 h-4 text-amber-500" />;
      case 'success': return <CheckCircle className="w-4 h-4 text-emerald-500" />;
      case 'info':
      default: return <Info className="w-4 h-4 text-blue-500" />;
    }
  };

  const getTypeBadgeClass = (type: string) => {
    switch (type) {
      case 'alert': return 'bg-red-50 text-red-700 border-red-100';
      case 'action': return 'bg-blue-50 text-blue-700 border-blue-100';
      case 'system': return 'bg-slate-100 text-slate-700 border-slate-200';
      case 'operator': return 'bg-indigo-50 text-indigo-700 border-indigo-100';
      default: return 'bg-gray-50 text-gray-700 border-gray-200';
    }
  };

  return (
    <div className="flex flex-col gap-6 max-w-5xl mx-auto h-[calc(100vh-6rem)]">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Activity Log</h1>
        <p className="text-slate-500">System events, operator actions, and alerts</p>
      </div>

      <div className="flex flex-col flex-1 bg-white border border-slate-200 rounded-lg overflow-hidden">
        {/* Filter Bar */}
        <div className="p-4 border-b border-slate-200 flex items-center justify-between bg-slate-50/50">
          <div className="flex items-center gap-2 overflow-x-auto">
            {(['all', 'action', 'alert', 'system', 'operator'] as FilterType[]).map((type) => (
              <button
                key={type}
                onClick={() => setFilter(type)}
                className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors whitespace-nowrap flex items-center gap-2 ${
                  filter === type 
                    ? 'bg-white text-slate-900 shadow-sm border border-slate-200' 
                    : 'text-slate-600 hover:bg-slate-100 border border-transparent'
                }`}
              >
                <span className="capitalize">{type}</span>
                <span className={`text-xs px-1.5 py-0.5 rounded-full ${filter === type ? 'bg-slate-100 text-slate-700' : 'bg-slate-200/50 text-slate-500'}`}>
                  {counts[type]}
                </span>
              </button>
            ))}
          </div>
          <div className="relative hidden md:block">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input 
              type="text" 
              placeholder="Search logs..." 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 pr-4 py-1.5 text-sm border border-slate-200 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent w-48 lg:w-64"
            />
          </div>
        </div>

        {/* Log List */}
        <div className="flex-1 overflow-y-auto p-0">
          {filteredLogs.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-slate-500 py-12">
              <Filter className="w-8 h-8 mb-2 opacity-20" />
              {searchQuery.trim() !== '' ? (
                <p>No logs matched <span className="font-semibold text-slate-600">"{searchQuery}"</span>. Try a different keyword.</p>
              ) : (
                <p>No log entries found for this filter.</p>
              )}
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {filteredLogs.map((log) => {
                const isExpanded = expandedId === log.id;
                
                return (
                  <div 
                    key={log.id} 
                    className={`hover:bg-slate-50 transition-colors ${isExpanded ? 'bg-slate-50' : ''}`}
                  >
                    <div 
                      className="p-4 flex items-start gap-4 cursor-pointer"
                      onClick={() => setExpandedId(isExpanded ? null : log.id)}
                    >
                      <div className="min-w-[80px] text-xs text-slate-500 font-mono mt-1">
                        {new Date(log.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                      </div>
                      
                      <div className="flex items-start gap-3 flex-1">
                        <div className="mt-1 flex-shrink-0">
                          {getSeverityIcon(log.severity)}
                        </div>
                        
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1 flex-wrap">
                            <span className={`text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded border ${getTypeBadgeClass(log.type)}`}>
                              {log.type}
                            </span>
                            {log.user && (
                              <span className="text-xs text-slate-500 font-medium">
                                by {log.user}
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-slate-900 font-medium line-clamp-2">{log.message}</p>
                        </div>
                      </div>

                      {log.details && (
                        <div className="flex-shrink-0 ml-4 text-slate-400">
                          {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                        </div>
                      )}
                    </div>

                    {isExpanded && log.details && (
                      <div className="pl-[116px] pr-4 pb-4">
                        <div className="bg-white border border-slate-200 rounded p-3 text-xs text-slate-600 font-mono overflow-x-auto">
                          {log.details}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
