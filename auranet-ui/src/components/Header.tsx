/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { Bell, Settings, Search, Menu, Moon, Sun, AlertTriangle } from 'lucide-react';
import { ActiveView } from '../types';
import { USER_PROFILE } from '../data';

interface HeaderProps {
  activeView: ActiveView;
  activeSubTab: string;
  setActiveSubTab: (tab: string) => void;
  isCollapsed: boolean;
  setIsCollapsed: (collapsed: boolean) => void;
  nodeAlertCount: number;
  onProfileClick: () => void;
}

export default function Header({
  activeView,
  activeSubTab,
  setActiveSubTab,
  isCollapsed,
  setIsCollapsed,
  nodeAlertCount,
  onProfileClick,
}: HeaderProps) {
  const tabs = ['Overview', 'Network', 'Analytics'];

  const getBreadcrumbTitle = () => {
    switch (activeView) {
      case 'main':
        return 'System Workload Visualizer';
      case 'stress':
        return 'Mesh Stress Test Controller';
      case 'statistics':
        return 'Analytical Topology Statistics';
      case 'attack':
        return 'Cybersecurity Threat Attack Simulator';
      case 'workload':
        return 'Distributed Workload Balancer';
      default:
        return 'System Workload Visualizer';
    }
  };

  return (
    <header 
      className="bg-slate-50 border-b border-slate-200 h-[72px] px-6 flex items-center justify-between sticky top-0 z-40 select-none shadow-xs"
      id="main-app-header"
    >
      {/* Left section: Hamburger (mobile/tablet) + Title + Subtabs */}
      <div className="flex items-center gap-6">
        {/* Toggle Sidebar for smaller viewports if requested */}
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="lg:hidden p-1.5 hover:bg-slate-200 rounded text-slate-500 hover:text-slate-800 transition-colors"
          id="header-mobile-menu-btn"
        >
          <Menu size={20} />
        </button>

        <div className="flex items-center gap-2">
          <h1 
            className="font-display font-extrabold text-2xl tracking-tight text-[#4d41df]"
            id="header-breadcrumb-title"
          >
            {getBreadcrumbTitle()}
          </h1>
        </div>
      </div>

      {/* Right section: Global Actions */}
      <div className="flex items-center gap-4">
        {/* Notifications Alert Bell */}
        <div className="relative group">
          <button 
            className="p-2 hover:bg-slate-200 rounded-full text-slate-600 hover:text-[#4d41df] transition-all relative"
            id="btn-bell-notifications"
          >
            <Bell size={20} />
            {nodeAlertCount > 0 && (
              <span className="absolute top-1.5 right-1.5 h-4 w-4 bg-red-500 rounded-full text-[10px] text-white flex items-center justify-center font-bold font-mono animate-bounce">
                {nodeAlertCount}
              </span>
            )}
          </button>
          
          {/* Notifications Dropdown (Interactive hover preview) */}
          <div className="absolute right-0 mt-2 w-80 bg-white border border-brand-border rounded-xl shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50 p-4">
            <div className="flex items-center justify-between pb-2 border-b border-slate-100 mb-2">
              <span className="font-display font-bold text-sm text-slate-800">System Alerts</span>
              <span className="font-mono text-xs text-red-500 font-semibold flex items-center gap-1">
                <AlertTriangle size={12} /> {nodeAlertCount} Critical
              </span>
            </div>
            <div className="space-y-2.5 max-h-60 overflow-y-auto">
              {nodeAlertCount > 0 ? (
                <div className="flex items-start gap-2.5 p-2 bg-red-50 rounded-lg border border-red-100">
                  <div className="p-1 bg-red-100 rounded-full text-red-600 mt-0.5">
                    <AlertTriangle size={14} />
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-red-800">Africa South Node Offline</p>
                    <p className="text-[10px] text-red-600 mt-0.5">Latency is 320ms+ (timeout). Connection severed.</p>
                  </div>
                </div>
              ) : (
                <p className="text-xs text-slate-500 text-center py-2">All systems operating within normal parameters.</p>
              )}
              <div className="flex items-start gap-2.5 p-2 bg-amber-50 rounded-lg border border-amber-100">
                <div className="p-1 bg-amber-100 rounded-full text-amber-600 mt-0.5">
                  <AlertTriangle size={14} />
                </div>
                <div>
                  <p className="text-xs font-semibold text-amber-800">Asia South Node Warning</p>
                  <p className="text-[10px] text-amber-600 mt-0.5">CPU utilization spike (94%). High memory consumption.</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Settings shortcut */}
        <button 
          onClick={() => alert("Settings configuration panel is active. All security logs synced.")}
          className="p-2 hover:bg-slate-200 rounded-full text-slate-600 hover:text-indigo-600 transition-colors"
          title="System Settings"
          id="btn-quick-settings"
        >
          <Settings size={20} />
        </button>
      </div>
    </header>
  );
}
