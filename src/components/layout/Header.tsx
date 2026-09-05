'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Search, Bell, AlertTriangle, CheckCircle, Info } from 'lucide-react';
import { useGridStore } from '@/store/grid-store';

export default function Header() {
  const router = useRouter();
  const [showNotifications, setShowNotifications] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const activityLog = useGridStore(s => s.activityLog);
  const { gridState, selectAsset, setCurrentPage } = useGridStore();
  const unreadCount = 3; // mock unread count
  const [currentTime, setCurrentTime] = useState<string>('');

  const handleSearch = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && searchQuery.trim()) {
      const query = searchQuery.toLowerCase().trim();
      
      // Page navigation
      if (query.includes('setting')) {
        setCurrentPage('settings');
        router.push('/settings');
        setSearchQuery('');
        return;
      }
      if (query.includes('activity') || query.includes('log')) {
        setCurrentPage('activity-log');
        router.push('/activity-log');
        setSearchQuery('');
        return;
      }
      if (query.includes('overview') || query.includes('home')) {
        setCurrentPage('overview');
        router.push('/');
        setSearchQuery('');
        return;
      }

      // Asset search
      const foundAsset = 
        gridState.buses.find(b => b.id.toLowerCase() === query || b.name.toLowerCase().includes(query)) ||
        gridState.transformers.find(t => t.id.toLowerCase() === query || t.name.toLowerCase().includes(query)) ||
        gridState.lines.find(l => l.id.toLowerCase() === query);
      
      if (foundAsset) {
        selectAsset(foundAsset.id);
        setCurrentPage('overview');
        router.push('/');
        setSearchQuery('');
        return;
      }
      
      // Default to Activity Log search if no match
      setCurrentPage('activity-log');
      router.push('/activity-log');
    }
  };

  useEffect(() => {
    // Update time every minute
    const updateTime = () => {
      const now = new Date();
      // Format: DD MMM YYYY · HH:MM IST
      const options: Intl.DateTimeFormatOptions = { 
        day: '2-digit', month: 'short', year: 'numeric',
        hour: '2-digit', minute: '2-digit', hour12: true,
        timeZone: 'Asia/Kolkata'
      };
      setCurrentTime(now.toLocaleString('en-IN', options).replace(',', ' ·') + ' IST');
    };
    
    updateTime();
    const interval = setInterval(updateTime, 60000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="h-12 bg-white border-b border-slate-200 px-4 flex items-center justify-between relative shadow-sm">
      {/* Left: Search */}
      <div className="relative">
        <Search
          size={14}
          className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400"
        />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyDown={handleSearch}
          placeholder="Search grid assets, faults, or locations..."
          className="h-8 w-64 pl-8 pr-3 text-sm bg-slate-50 border border-slate-200 rounded-md
                     placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 transition-all focus:w-80"
        />
      </div>

      {/* Right */}
      <div className="flex items-center gap-4">
        {/* Simulation status */}
        <div className="flex items-center gap-1.5 bg-emerald-50 text-emerald-700 border border-emerald-200 px-2.5 py-1 rounded-md shadow-sm">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-xs font-bold tracking-wide">SYSTEM LIVE</span>
        </div>

        {/* Date/time */}
        <span className="text-sm font-medium text-slate-600 tracking-tight">{currentTime}</span>

        {/* Notification bell */}
        <div className="relative">
          <button 
            onClick={() => setShowNotifications(!showNotifications)}
            className="relative text-slate-500 hover:text-slate-700 transition-colors p-1"
          >
            <Bell size={18} />
            <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-red-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center">
              {unreadCount}
            </span>
          </button>
          
          {/* Notifications Dropdown */}
          {showNotifications && (
            <div className="absolute top-10 right-0 w-80 bg-white border border-slate-200 shadow-xl rounded-lg z-50 overflow-hidden">
              <div className="bg-slate-50 px-4 py-2 border-b border-slate-200 flex justify-between items-center">
                <span className="text-sm font-semibold text-slate-700">Notifications</span>
                <button 
                  onClick={() => setShowNotifications(false)}
                  className="text-xs text-blue-600 hover:underline"
                >
                  Mark all as read
                </button>
              </div>
              <div className="max-h-64 overflow-y-auto">
                {activityLog.slice(0, 5).map(log => (
                  <div key={log.id} className="p-3 border-b border-slate-100 hover:bg-slate-50 flex gap-3">
                    <div className="shrink-0 mt-0.5">
                      {log.severity === 'error' ? <AlertTriangle size={14} className="text-red-500" /> :
                       log.severity === 'warning' ? <AlertTriangle size={14} className="text-amber-500" /> :
                       log.severity === 'success' ? <CheckCircle size={14} className="text-green-500" /> :
                       <Info size={14} className="text-blue-500" />}
                    </div>
                    <div>
                      <p className="text-xs text-slate-700 font-medium leading-snug">{log.message}</p>
                      <span className="text-[10px] text-slate-400 mt-1 block">
                        {new Date(log.timestamp).toLocaleTimeString()} · {log.user}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
              <div className="bg-slate-50 p-2 text-center border-t border-slate-200">
                <button className="text-xs text-slate-500 hover:text-slate-700 font-medium">View all activity</button>
              </div>
            </div>
          )}
        </div>

        {/* Operator avatar */}
        <div className="flex items-center gap-2 border-l border-slate-200 pl-4 ml-1">
          <div className="w-7 h-7 rounded-full bg-orange-600 text-white text-xs font-bold flex items-center justify-center shadow-sm">
            RS
          </div>
          <span className="text-sm font-semibold text-slate-700">Operator Sharma</span>
        </div>
      </div>
    </header>
  );
}
