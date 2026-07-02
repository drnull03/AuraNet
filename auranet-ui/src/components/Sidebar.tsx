/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { 
  LayoutDashboard, 
  Activity,
  BarChart3,
  ShieldAlert,
  Sliders,
  LogOut, 
  ChevronLeft,
  ChevronRight,
  Hexagon
} from 'lucide-react';
import { ActiveView } from '../types';

interface SidebarProps {
  activeView: ActiveView;
  setActiveView: (view: ActiveView) => void;
  isCollapsed: boolean;
  setIsCollapsed: (collapsed: boolean) => void;
  onExport: () => void;
}

export default function Sidebar({
  activeView,
  setActiveView,
  isCollapsed,
  setIsCollapsed,
  onExport,
}: SidebarProps) {
  const menuItems = [
    { id: 'main' as ActiveView, label: 'Main', icon: LayoutDashboard },
    { id: 'stress' as ActiveView, label: 'Stress Tests', icon: Activity },
    { id: 'statistics' as ActiveView, label: 'Statistics', icon: BarChart3 },
    { id: 'attack' as ActiveView, label: 'Launch Simulated Attack', icon: ShieldAlert },
    { id: 'workload' as ActiveView, label: 'Add Workload', icon: Sliders },
  ];

  return (
    <div 
      className={`relative h-screen bg-brand-primary text-white flex flex-col justify-between transition-all duration-300 ease-in-out border-r border-indigo-700/30 ${
        isCollapsed ? 'w-[72px]' : 'w-[240px]'
      }`}
      id="sidebar-container"
    >
      {/* Sidebar Header */}
      <div>
        <div className="flex items-center justify-between p-4 border-b border-indigo-500/30">
          <div className="flex items-center gap-3 overflow-hidden">
            <div className="p-2 bg-indigo-600/50 rounded-lg flex-shrink-0">
              <Hexagon className="h-6 w-6 text-[#06b6d4] animate-pulse" />
            </div>
            {!isCollapsed && (
              <div className="flex flex-col select-none">
                <span className="font-display font-bold text-lg tracking-tight leading-none text-white">
                  Project Alpha
                </span>
                <span className="font-mono text-[10px] text-indigo-200 mt-1 uppercase tracking-wider">
                  Graduation 2024
                </span>
              </div>
            )}
          </div>
          
          <button 
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="p-1 hover:bg-indigo-600/40 rounded text-indigo-200 hover:text-white transition-colors"
            title={isCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
            id="sidebar-toggle-btn"
          >
            {isCollapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
          </button>
        </div>

        {/* Navigation Items */}
        <nav className="p-3 space-y-1.5 mt-4" id="sidebar-nav">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeView === item.id;
            return (
              <button
                key={item.id}
                id={`sidebar-link-${item.id}`}
                onClick={() => setActiveView(item.id)}
                className={`w-full flex items-center gap-3 px-3 py-3 rounded-lg text-sm font-medium transition-all duration-200 group relative ${
                  isActive 
                    ? 'bg-indigo-900/60 text-white shadow-inner font-semibold border-l-4 border-[#06b6d4] pl-2' 
                    : 'text-indigo-100 hover:bg-indigo-600/30 hover:text-white'
                }`}
              >
                <Icon 
                  size={20} 
                  className={`flex-shrink-0 transition-transform duration-200 group-hover:scale-110 ${
                    isActive ? 'text-[#06b6d4]' : 'text-indigo-200 group-hover:text-white'
                  }`} 
                />
                
                {!isCollapsed && (
                  <span className="truncate">{item.label}</span>
                )}

                {/* Collapsed Tooltip */}
                {isCollapsed && (
                  <div className="absolute left-16 bg-indigo-950 text-white text-xs py-1.5 px-3 rounded shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50 whitespace-nowrap">
                    {item.label}
                  </div>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Footer Controls */}
      <div className="p-3 border-t border-indigo-500/30 space-y-2">
        <button
          onClick={() => alert("Sign out successful! This resets dashboard simulated session.")}
          id="btn-sign-out"
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-medium text-indigo-200 hover:bg-red-950/40 hover:text-red-200 transition-all duration-200 group"
          title="Sign Out Session"
        >
          <LogOut size={16} className="flex-shrink-0 group-hover:translate-x-1 transition-transform text-indigo-300" />
          {!isCollapsed && <span>Sign Out</span>}
        </button>
      </div>
    </div>
  );
}
