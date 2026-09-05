'use client';

import { Search, Bell } from 'lucide-react';

export default function Header() {
  return (
    <header className="h-12 bg-white border-b border-slate-200 px-4 flex items-center justify-between">
      {/* Left: Search */}
      <div className="relative">
        <Search
          size={14}
          className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400"
        />
        <input
          type="text"
          placeholder="Search assets, faults, actions..."
          className="h-8 w-64 pl-8 pr-3 text-sm bg-slate-50 border border-slate-200 rounded-md
                     placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>

      {/* Right */}
      <div className="flex items-center gap-4">
        {/* Simulation status */}
        <div className="flex items-center gap-1.5 bg-emerald-50 text-emerald-700 border border-emerald-200 px-2.5 py-1 rounded-md">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
          <span className="text-xs font-medium">Simulation Active</span>
        </div>

        {/* Date/time */}
        <span className="text-sm text-slate-500">Nov 27, 2024 · 14:40</span>

        {/* Notification bell */}
        <button className="relative text-slate-500 hover:text-slate-700 transition-colors">
          <Bell size={18} />
          <span className="absolute -top-1 -right-1.5 w-4 h-4 bg-red-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center">
            3
          </span>
        </button>

        {/* Operator avatar */}
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-full bg-slate-700 text-white text-xs font-medium flex items-center justify-center">
            OC
          </div>
          <span className="text-sm text-slate-600">Operator Chen</span>
        </div>
      </div>
    </header>
  );
}
