/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, PieChart, Pie, Cell } from 'recharts';
import { SystemNode, MetricData } from '../types';
import MetricCards from './MetricCards';
import ActivityChart from './ActivityChart';
import { TrendingUp, BarChart2, PieChart as PieIcon, Activity } from 'lucide-react';

interface StatisticsViewProps {
  systemNodes: SystemNode[];
  metrics: MetricData;
}

export default function StatisticsView({ systemNodes, metrics }: StatisticsViewProps) {
  // 1. Prepare Bar Chart Data for CPU/Memory across all nodes
  const barChartData = useMemo(() => {
    return systemNodes.map(node => ({
      name: node.label.replace(' Gateway', '').replace(' Sensor', '').replace(' Compute', '').replace(' Node', ''),
      cpu: node.cpu,
      memory: node.memory,
    }));
  }, [systemNodes]);

  // 2. Prepare Pie Chart Data for status distribution
  const pieChartData = useMemo(() => {
    const activeCount = systemNodes.filter(n => n.status === 'active').length;
    const warningCount = systemNodes.filter(n => n.status === 'warning').length;
    const offlineCount = systemNodes.filter(n => n.status === 'offline').length;

    return [
      { name: 'Active', value: activeCount, color: '#0ea5e9' },
      { name: 'Warning', value: warningCount, color: '#f59e0b' },
      { name: 'Offline', value: offlineCount, color: '#ef4444' },
    ].filter(item => item.value > 0);
  }, [systemNodes]);

  return (
    <div className="space-y-6" id="statistics-view-root">
      {/* Dynamic Metric summary cards at top of statistics view */}
      <MetricCards metrics={metrics} />

      {/* Main Graphs Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left side: CPU/Memory Node load comparison */}
        <div className="lg:col-span-2 bg-white border border-slate-200 rounded-2xl p-5 shadow-sm">
          <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-4 select-none">
            <div>
              <span className="font-mono text-[10px] font-bold text-slate-400 tracking-widest uppercase block">Node Resources comparison</span>
              <h3 className="font-display font-extrabold text-base text-slate-900 block mt-0.5">CPU & Memory Loads (%)</h3>
            </div>
            <div className="flex items-center gap-3 text-xs">
              <span className="flex items-center gap-1 font-semibold text-slate-600">
                <span className="h-2.5 w-2.5 rounded-xs bg-[#4d41df]" /> CPU
              </span>
              <span className="flex items-center gap-1 font-semibold text-slate-600">
                <span className="h-2.5 w-2.5 rounded-xs bg-[#0891b2]" /> Memory
              </span>
            </div>
          </div>

          <div className="h-[280px] w-full mt-2">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={barChartData} margin={{ top: 10, right: 10, left: -20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis 
                  dataKey="name" 
                  tickLine={false}
                  axisLine={false}
                  tick={{ fill: '#64748b', fontSize: 9, fontFamily: 'JetBrains Mono', fontWeight: 600 }}
                />
                <YAxis 
                  tickLine={false}
                  axisLine={false}
                  tick={{ fill: '#94a3b8', fontSize: 10, fontFamily: 'JetBrains Mono' }}
                  domain={[0, 100]}
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#0f172a', 
                    borderRadius: '8px', 
                    border: 'none',
                    color: '#f8fafc',
                    fontFamily: 'JetBrains Mono',
                    fontSize: '11px'
                  }}
                />
                <Bar dataKey="cpu" fill="#4d41df" radius={[4, 4, 0, 0]} barSize={12} />
                <Bar dataKey="memory" fill="#0891b2" radius={[4, 4, 0, 0]} barSize={12} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Right side: Status breakdown & Activity line */}
        <div className="lg:col-span-1 space-y-6">
          {/* Status Pie Chart */}
          <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm flex flex-col justify-between">
            <div className="pb-3 border-b border-slate-100 select-none">
              <span className="font-mono text-[10px] font-bold text-slate-400 tracking-widest uppercase block">Global Health</span>
              <h3 className="font-display font-extrabold text-base text-slate-900 block mt-0.5">Endpoint Health Ratio</h3>
            </div>

            <div className="flex items-center justify-between mt-4">
              {/* Pie Graph */}
              <div className="h-[120px] w-[120px] relative">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={pieChartData}
                      cx="50%"
                      cy="50%"
                      innerRadius={35}
                      outerRadius={50}
                      paddingAngle={3}
                      dataKey="value"
                    >
                      {pieChartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
                <div className="absolute inset-0 flex flex-col items-center justify-center select-none pointer-events-none">
                  <span className="font-mono font-extrabold text-lg text-slate-800">{systemNodes.length}</span>
                  <span className="text-[8px] font-bold text-slate-400 uppercase">Nodes</span>
                </div>
              </div>

              {/* Legend with precise numbers */}
              <div className="flex-1 pl-4 space-y-2 select-none">
                {pieChartData.map((item, index) => (
                  <div key={index} className="flex items-center justify-between text-xs">
                    <span className="flex items-center gap-2 text-slate-600 font-semibold">
                      <span className="h-2 w-2 rounded-full" style={{ backgroundColor: item.color }} />
                      {item.name}
                    </span>
                    <span className="font-mono font-bold text-slate-800">{item.value}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <ActivityChart />
        </div>
      </div>
    </div>
  );
}
