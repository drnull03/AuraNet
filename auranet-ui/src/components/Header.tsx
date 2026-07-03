/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { Bell, Settings, Search, Menu, Moon, Sun, AlertTriangle, CheckCircle, ShieldAlert } from 'lucide-react';
import { ActiveView, SystemAlert } from '../types';

interface HeaderProps {
  activeView: ActiveView;
  activeSubTab: string;
  setActiveSubTab: (tab: string) => void;
  isCollapsed: boolean;
  setIsCollapsed: (collapsed: boolean) => void;
  alerts: SystemAlert[];
  unreadAlertsCount: number;
  onMarkAlertsRead: () => void;
  onProfileClick: () => void;
}

export default function Header({
  activeView,
  activeSubTab,
  setActiveSubTab,
  isCollapsed,
  setIsCollapsed,
  alerts,
  unreadAlertsCount,
  onMarkAlertsRead,
  onProfileClick,
}: HeaderProps) {
  
  const getBreadcrumbTitle = () => {
    switch (activeView) {
      case 'main': return 'System Workload Visualizer';
      case 'stress': return 'Mesh Stress Test Controller';
      case 'statistics': return 'Analytical Topology Statistics';
      case 'attack': return 'Cybersecurity Threat Attack Simulator';
      case 'workload': return 'Distributed Workload Balancer';
      default: return 'System Workload Visualizer';
    }
  };

  return (
    <header 
      className="bg-slate-50 border-b border-slate-200 h-[72px] px-6 flex items-center justify-between sticky top-0 z-40 select-none shadow-xs"
      id="main-app-header"
    >
      <div className="flex items-center gap-6">
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="lg:hidden p-1.5 hover:bg-slate-200 rounded text-slate-500 hover:text-slate-800 transition-colors"
        >
          <Menu size={20} />
        </button>

        <div className="flex items-center gap-2">
          <h1 className="font-display font-extrabold text-2xl tracking-tight text-[#4d41df]">
            {getBreadcrumbTitle()}
          </h1>
        </div>
      </div>

      <div className="flex items-center gap-4">
        {/* Notifications Alert Bell (Persistent) */}
        <div className="relative group" onMouseEnter={onMarkAlertsRead}>
          <button 
            className="p-2 hover:bg-slate-200 rounded-full text-slate-600 hover:text-[#4d41df] transition-all relative"
            id="btn-bell-notifications"
          >
            <Bell size={20} />
            {unreadAlertsCount > 0 && (
              <span className="absolute top-1.5 right-1.5 h-4 w-4 bg-red-500 rounded-full text-[10px] text-white flex items-center justify-center font-bold font-mono animate-bounce shadow-sm">
                {unreadAlertsCount}
              </span>
            )}
          </button>
          
          {/* Notifications Dropdown (Preserves History) */}
          <div className="absolute right-0 mt-2 w-80 bg-white border border-brand-border rounded-xl shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50 p-4">
            <div className="flex items-center justify-between pb-2 border-b border-slate-100 mb-2">
              <span className="font-display font-bold text-sm text-slate-800">Global Threat History</span>
              <span className="font-mono text-xs text-indigo-500 font-semibold bg-indigo-50 px-2 rounded-md">
                {alerts.length} Events Logged
              </span>
            </div>
            
            <div className="space-y-2 max-h-[320px] overflow-y-auto custom-scrollbar pr-1">
              {alerts.length > 0 ? (
                alerts.map(alert => (
                  <div key={alert.id} className={`flex items-start gap-2.5 p-2 rounded-lg border ${
                    alert.type === 'critical' ? 'bg-red-50 border-red-100' :
                    alert.type === 'success' ? 'bg-emerald-50 border-emerald-100' :
                    'bg-amber-50 border-amber-100'
                  }`}>
                    <div className={`p-1.5 rounded-full mt-0.5 flex-shrink-0 ${
                      alert.type === 'critical' ? 'bg-red-100 text-red-600' :
                      alert.type === 'success' ? 'bg-emerald-100 text-emerald-600' :
                      'bg-amber-100 text-amber-600'
                    }`}>
                      {alert.type === 'critical' ? <AlertTriangle size={14} /> :
                       alert.type === 'success' ? <CheckCircle size={14} /> :
                       <ShieldAlert size={14} />}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2">
                        <p className={`text-xs font-bold truncate ${
                          alert.type === 'critical' ? 'text-red-800' :
                          alert.type === 'success' ? 'text-emerald-800' :
                          'text-amber-800'
                        }`}>{alert.title}</p>
                        <span className="text-[9px] text-slate-400 font-mono flex-shrink-0">
                          {alert.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                        </span>
                      </div>
                      <p className={`text-[10px] mt-0.5 leading-snug ${
                        alert.type === 'critical' ? 'text-red-600' :
                        alert.type === 'success' ? 'text-emerald-600' :
                        'text-amber-600'
                      }`}>{alert.message}</p>
                    </div>
                  </div>
                ))
              ) : (
                <div className="py-6 text-center">
                  <ShieldAlert size={24} className="mx-auto text-emerald-400 mb-2 opacity-50" />
                  <p className="text-xs text-slate-500 font-medium">All systems operating within normal parameters.</p>
                </div>
              )}
            </div>
          </div>
        </div>

        <button 
          onClick={() => alert("Settings configuration panel is active. All security logs synced.")}
          className="p-2 hover:bg-slate-200 rounded-full text-slate-600 hover:text-indigo-600 transition-colors"
          title="System Settings"
        >
          <Settings size={20} />
        </button>
      </div>
    </header>
  );
}