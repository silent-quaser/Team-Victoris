'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useGridStore } from '@/store/grid-store';
import {
  Shield,
  LayoutDashboard,
  Network,
  CloudLightning,
  Route,
  Users,
  GitBranch,
  Share2,
  Building2,
  TriangleAlert,
  Database,
  FileText,
  Settings,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
}

const operationsItems: NavItem[] = [
  { label: 'Overview', href: '/', icon: LayoutDashboard },
  { label: 'Grid Model', href: '/grid-model', icon: Network },
  { label: 'Scenarios', href: '/scenarios', icon: CloudLightning },
  { label: 'Recovery Planner', href: '/recovery-planner', icon: Route },
  { label: 'Resources', href: '/resources', icon: Users },
];

const analysisItems: NavItem[] = [
  { label: 'What-If Analysis', href: '/what-if', icon: GitBranch },
  { label: 'Dependency Map', href: '/dependency-map', icon: Share2 },
  { label: 'Critical Services', href: '/critical-services', icon: Building2 },
  { label: 'Risk & Uncertainty', href: '/risk', icon: TriangleAlert },
];

const systemItems: NavItem[] = [
  { label: 'Data & Models', href: '/data-models', icon: Database },
  { label: 'Activity Log', href: '/activity-log', icon: FileText },
  { label: 'Settings', href: '/settings', icon: Settings },
];

function NavSection({ label, items }: { label: string; items: NavItem[] }) {
  const pathname = usePathname();

  return (
    <div>
      <div className="text-[10px] uppercase tracking-wider text-slate-400 mb-1 mt-4 px-3">
        {label}
      </div>
      <nav className="flex flex-col gap-0.5">
        {items.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`
                flex items-center gap-2.5 px-3 py-1.5 text-[13px] rounded-md
                border-l-2 transition-colors
                ${
                  isActive
                    ? 'border-blue-600 bg-blue-50 text-blue-700 font-medium'
                    : 'border-transparent text-slate-600 hover:bg-slate-50'
                }
              `}
            >
              <Icon size={16} />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>
    </div>
  );
}

function SidebarStatus() {
  const settings = useGridStore(s => s.settings);
  const modeLabel = settings.simulationMode === 'local' ? 'Local Simulation' 
    : settings.simulationMode === 'connected' ? 'Live SCADA' : 'Historical Playback';
  const modeColor = settings.simulationMode === 'local' ? 'bg-green-500' 
    : settings.simulationMode === 'connected' ? 'bg-blue-500' : 'bg-amber-500';
  const modeDesc = settings.simulationMode === 'local' ? 'IEEE 33-Bus mock data' 
    : settings.simulationMode === 'connected' ? 'Connected to SCADA feed' : 'Playback: 2024-11-27';

  return (
    <div className="border-t border-slate-200 px-3 py-3">
      <div className="text-[10px] uppercase tracking-wider text-slate-400 mb-2">{modeLabel}</div>
      <div className="flex items-center gap-2 mb-1">
        <span className={`w-1.5 h-1.5 rounded-full ${modeColor}`} />
        <span className="text-[11px] text-slate-500">{modeDesc}</span>
      </div>
    </div>
  );
}

export default function Sidebar() {
  return (
    <aside className="fixed left-0 top-0 w-56 h-screen bg-white border-r border-slate-200 flex flex-col z-30">
      {/* Brand */}
      <div className="px-4 py-3 flex items-center gap-2">
        <Shield size={20} className="text-blue-600" />
        <div>
          <div className="font-bold text-sm tracking-wider text-slate-800">
            GRIDGUARD
          </div>
          <div className="text-[10px] text-slate-400">
            Impact-Aware Grid Recovery
          </div>
        </div>
      </div>

      {/* Navigation */}
      <div className="flex-1 overflow-y-auto px-1">
        <NavSection label="Operations" items={operationsItems} />
        <NavSection label="Analysis" items={analysisItems} />
        <NavSection label="System" items={systemItems} />
      </div>

      <SidebarStatus />
    </aside>
  );
}
