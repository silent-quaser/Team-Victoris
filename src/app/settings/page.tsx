'use client';

import React from 'react';
import { Settings, Sliders, Monitor, Zap, Info, ShieldAlert } from 'lucide-react';
import { useGridStore } from '@/store/grid-store';

export default function SettingsPage() {
  const settings = useGridStore((s) => s.settings);
  const updateSettings = useGridStore((s) => s.updateSettings);

  return (
    <div className="flex flex-col gap-6 max-w-4xl mx-auto pb-10">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Settings</h1>
        <p className="text-slate-500">Application configuration and preferences</p>
      </div>

      <div className="grid grid-cols-1 gap-6">
        {/* General Section */}
        <section className="bg-white border border-slate-200 rounded-lg overflow-hidden shadow-sm">
          <div className="p-4 border-b border-slate-100 bg-slate-50 flex items-center gap-2">
            <Sliders className="w-5 h-5 text-slate-600" />
            <h2 className="text-lg font-semibold text-slate-800">General</h2>
          </div>
          <div className="p-6 flex flex-col gap-5">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-2 md:gap-4 items-center">
              <label className="text-sm font-medium text-slate-700">Operator Name</label>
              <div className="md:col-span-2">
                <input 
                  type="text" 
                  value="Operator Chen" 
                  disabled
                  className="w-full md:w-2/3 px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-md text-slate-500 cursor-not-allowed"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-2 md:gap-4 items-center">
              <label className="text-sm font-medium text-slate-700">Operator Role</label>
              <div className="md:col-span-2">
                <input 
                  type="text" 
                  value="Senior Grid Operator" 
                  disabled
                  className="w-full md:w-2/3 px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-md text-slate-500 cursor-not-allowed"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-2 md:gap-4 items-center pt-4 border-t border-slate-100">
              <label className="text-sm font-medium text-slate-700">Simulation Mode</label>
              <div className="md:col-span-2">
                <select 
                  value={settings.simulationMode}
                  onChange={(e) => updateSettings({ simulationMode: e.target.value as any })}
                  className="w-full md:w-1/2 px-3 py-2 text-sm bg-white border border-slate-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="local">Local Simulation</option>
                  <option value="connected">Connected (Live)</option>
                  <option value="historical">Historical Playback</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-2 md:gap-4 items-center">
              <label className="text-sm font-medium text-slate-700">Auto-refresh interval</label>
              <div className="md:col-span-2 flex items-center gap-2">
                <input 
                  type="number" 
                  defaultValue={30}
                  className="w-24 px-3 py-2 text-sm bg-white border border-slate-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
                <span className="text-sm text-slate-500">seconds</span>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-2 md:gap-4 items-center">
              <label className="text-sm font-medium text-slate-700">Desktop Notifications</label>
              <div className="md:col-span-2">
                <label className="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" className="sr-only peer" defaultChecked />
                  <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  <span className="ml-3 text-sm font-medium text-slate-600">Enabled</span>
                </label>
              </div>
            </div>
          </div>
        </section>

        {/* Display Section */}
        <section className="bg-white border border-slate-200 rounded-lg overflow-hidden shadow-sm">
          <div className="p-4 border-b border-slate-100 bg-slate-50 flex items-center gap-2">
            <Monitor className="w-5 h-5 text-slate-600" />
            <h2 className="text-lg font-semibold text-slate-800">Display</h2>
          </div>
          <div className="p-6 flex flex-col gap-5">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-2 md:gap-4 items-center">
              <label className="text-sm font-medium text-slate-700">Theme</label>
              <div className="md:col-span-2">
                <div className="inline-flex items-center px-3 py-1.5 bg-slate-100 border border-slate-200 rounded text-sm text-slate-600 cursor-not-allowed">
                  Light Theme Only
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-2 md:gap-4 items-center">
              <label className="text-sm font-medium text-slate-700">Grid visualization</label>
              <div className="md:col-span-2">
                <select 
                  value={settings.gridVisualization}
                  onChange={(e) => updateSettings({ gridVisualization: e.target.value as any })}
                  className="w-full md:w-1/2 px-3 py-2 text-sm bg-white border border-slate-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="network">Network Map View</option>
                  <option value="geo">Geospatial View</option>
                  <option value="list">List View</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-2 md:gap-4 items-center">
              <label className="text-sm font-medium text-slate-700">Show bus labels</label>
              <div className="md:col-span-2">
                <label className="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" className="sr-only peer" defaultChecked />
                  <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  <span className="ml-3 text-sm font-medium text-slate-600">Yes</span>
                </label>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-2 md:gap-4 items-center">
              <label className="text-sm font-medium text-slate-700">Show edge labels</label>
              <div className="md:col-span-2">
                <label className="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" className="sr-only peer" />
                  <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  <span className="ml-3 text-sm font-medium text-slate-600">No</span>
                </label>
              </div>
            </div>
          </div>
        </section>

        {/* Simulation Section */}
        <section className="bg-white border border-slate-200 rounded-lg overflow-hidden shadow-sm">
          <div className="p-4 border-b border-slate-100 bg-amber-50/50 flex items-center gap-2">
            <Zap className="w-5 h-5 text-amber-600" />
            <h2 className="text-lg font-semibold text-slate-800">Simulation Configuration</h2>
          </div>
          <div className="p-6 flex flex-col gap-5">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-2 md:gap-4 items-center">
              <label className="text-sm font-medium text-slate-700">Time step</label>
              <div className="md:col-span-2">
                <select defaultValue="5" className="w-full md:w-1/3 px-3 py-2 text-sm bg-white border border-slate-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                  <option value="1">1 minute</option>
                  <option value="5">5 minutes</option>
                  <option value="15">15 minutes</option>
                  <option value="60">1 hour</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-2 md:gap-4 items-center">
              <label className="text-sm font-medium text-slate-700">Active Scenario</label>
              <div className="md:col-span-2 flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-red-500" />
                <span className="text-sm font-medium text-slate-900">Severe Storm Event</span>
                <span className="text-xs bg-slate-100 text-slate-500 px-2 py-0.5 rounded ml-2">Read-only in active sim</span>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-2 md:gap-4 items-center">
              <label className="text-sm font-medium text-slate-700">Auto-run recovery optimizer</label>
              <div className="md:col-span-2">
                <label className="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" className="sr-only peer" defaultChecked />
                  <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  <span className="ml-3 text-sm font-medium text-slate-600">Yes</span>
                </label>
              </div>
            </div>
          </div>
        </section>

        {/* About Section */}
        <section className="bg-slate-50 border border-slate-200 rounded-lg p-6">
          <div className="flex items-start gap-4">
            <Info className="w-5 h-5 text-slate-400 flex-shrink-0 mt-0.5" />
            <div className="flex flex-col gap-1">
              <h3 className="text-sm font-semibold text-slate-900">GridGuard System</h3>
              <p className="text-sm text-slate-600">Version 0.1.0-alpha (Frontend Build)</p>
              <p className="text-xs text-slate-500 font-mono mt-2">API Endpoint: localhost:3000 (Mocked Data Mode)</p>
              <p className="text-xs text-slate-500 font-mono">Environment: Development</p>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
