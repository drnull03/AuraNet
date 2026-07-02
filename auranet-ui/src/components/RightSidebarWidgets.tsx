/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState, useEffect } from 'react';
import { Sun, CloudRain, Clock, User, ArrowRight, CheckCircle2, AlertCircle } from 'lucide-react';
import { CommitLog } from '../types';
import { USER_PROFILE } from '../data';

interface RightSidebarWidgetsProps {
  commitLogs: CommitLog[];
  onViewLogs: () => void;
}

export default function RightSidebarWidgets({
  commitLogs,
  onViewLogs,
}: RightSidebarWidgetsProps) {
  const [time, setTime] = useState(new Date());
  const [tempUnit, setTempUnit] = useState<'C' | 'F'>('C');
  const [temp, setTemp] = useState(30);

  // Live ticking clock
  useEffect(() => {
    const timer = setInterval(() => {
      setTime(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const formatTime = () => {
    // Let's get the hours, minutes, and AM/PM
    let hours = time.getHours();
    const minutes = time.getMinutes().toString().padStart(2, '0');
    const ampm = hours >= 12 ? 'PM' : 'AM';
    hours = hours % 12;
    hours = hours ? hours : 12; // the hour '0' should be '12'
    const hoursStr = hours.toString().padStart(2, '0');
    return {
      hm: `${hoursStr}:${minutes}`,
      ampm
    };
  };

  const toggleTemperature = () => {
    if (tempUnit === 'C') {
      setTemp(Math.round((30 * 9) / 5 + 32));
      setTempUnit('F');
    } else {
      setTemp(30);
      setTempUnit('C');
    }
  };

  const { hm, ampm } = formatTime();

  return (
    <div className="space-y-6" id="right-sidebar-widgets-container">
      {/* Time & Weather Grid */}
      <div className="grid grid-cols-2 gap-4">
        {/* Time Card */}
        <div 
          className="bg-indigo-50 border border-indigo-100 rounded-2xl p-5 flex flex-col justify-center items-center shadow-sm relative overflow-hidden select-none group hover:border-indigo-200 transition-all"
          id="time-utc-widget"
        >
          <span className="font-mono text-[9px] font-bold text-indigo-400 tracking-wider uppercase block">
            System Time
          </span>
          <div className="flex items-baseline gap-1 mt-1">
            <span className="font-display font-black text-3xl text-brand-primary leading-none tracking-tight">
              {hm}
            </span>
            <span className="font-mono text-[10px] font-bold text-indigo-500 uppercase">
              {ampm}
            </span>
          </div>
          <span className="font-mono text-[9px] text-indigo-400/80 mt-1 flex items-center gap-1">
            <Clock size={10} /> UTC / Local
          </span>
        </div>

        {/* Weather Card */}
        <button 
          onClick={toggleTemperature}
          className="bg-white border border-brand-border rounded-2xl p-5 flex flex-col justify-center items-center shadow-sm select-none group hover:border-amber-200 hover:bg-amber-50/10 transition-all text-center"
          id="weather-widget"
          title="Toggle Celsius/Fahrenheit"
        >
          <span className="font-mono text-[9px] font-bold text-slate-400 tracking-wider uppercase block">
            Node Temp
          </span>
          <div className="flex items-center gap-2 mt-1">
            <Sun className="h-6 w-6 text-amber-500 animate-spin-slow group-hover:scale-110 transition-transform" style={{ animationDuration: '20s' }} />
            <span className="font-display font-black text-3xl text-brand-text leading-none">
              {temp}°{tempUnit}
            </span>
          </div>
          <span className="font-mono text-[9px] text-slate-400 mt-1">
            Optimal State
          </span>
        </button>
      </div>

      {/* Recent Commits Widget */}
      <div className="bg-white border border-brand-border rounded-2xl shadow-sm p-5" id="recent-commits-card">
        <span className="font-mono text-xs font-bold text-slate-400 tracking-wider uppercase block select-none mb-4">
          Recent Commits
        </span>

        {/* Commit Log list */}
        <div className="relative border-l border-slate-100 pl-4 space-y-5" id="commit-timeline">
          {commitLogs.slice(0, 3).map((commit) => {
            const isPerformance = commit.category === 'performance';
            const isSecurity = commit.category === 'security';
            const isInfra = commit.category === 'infra';
            
            return (
              <div key={commit.id} className="relative group/commit" id={`commit-item-${commit.id}`}>
                {/* Timeline Dot */}
                <div className={`absolute -left-[21px] top-0.5 h-2.5 w-2.5 rounded-full border-2 border-white transition-all duration-200 group-hover/commit:scale-125 ${
                  isSecurity 
                    ? 'bg-red-500' 
                    : isPerformance 
                      ? 'bg-amber-500' 
                      : isInfra 
                        ? 'bg-cyan-500' 
                        : 'bg-brand-primary'
                }`} />

                {/* Content */}
                <div className="space-y-1 select-none">
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="font-sans font-bold text-slate-800 flex items-center gap-1">
                      {commit.author}
                      {commit.author === USER_PROFILE.name && (
                        <span className="px-1 py-0.2 bg-indigo-50 text-indigo-600 rounded text-[8px]">You</span>
                      )}
                    </span>
                    <span className="font-mono text-slate-400">{commit.timeAgo}</span>
                  </div>
                  
                  <p className="text-xs text-slate-600 leading-relaxed font-sans font-medium line-clamp-3">
                    {commit.message}
                  </p>
                  
                  {commit.nodeId && (
                    <span className="inline-block font-mono text-[9px] text-brand-primary-light font-bold uppercase mt-1">
                      Target: {commit.nodeId}
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* View Logs Button */}
        <button
          onClick={onViewLogs}
          className="w-full mt-5 bg-[#00696b] hover:bg-[#005254] text-white py-2.5 px-4 rounded-xl text-xs font-bold uppercase tracking-wider flex items-center justify-center gap-1.5 transition-all hover:scale-[1.01] shadow-xs cursor-pointer"
          id="btn-view-all-logs"
        >
          <span>View All Logs</span>
          <ArrowRight size={14} />
        </button>
      </div>
    </div>
  );
}
