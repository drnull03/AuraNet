/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

const data = [
  { name: '1', value: 42 },
  { name: '2', value: 50 },
  { name: '3', value: 38 },
  { name: '4', value: 70 },
  { name: '5', value: 55 },
  { name: '6', value: 82 },
  { name: '7', value: 60 },
  { name: '8', value: 91 },
  { name: '9', value: 74 },
];

export default function ActivityChart() {
  return (
    <div className="bg-white border border-brand-border rounded-2xl shadow-sm p-5 select-none" id="user-activity-card">
      <div className="flex items-center justify-between pb-4 border-b border-brand-border mb-4">
        <div>
          <span className="font-mono text-xs font-bold text-slate-400 tracking-wider uppercase block">
            User Activity
          </span>
          <span className="font-display font-extrabold text-lg text-brand-text block mt-0.5">
            Active Workloads
          </span>
        </div>
        <div className="flex items-center gap-1.5 font-mono text-[10px] text-[#006e70] bg-[#e0fbfc] px-2.5 py-1 rounded-full font-bold">
          <span className="h-1.5 w-1.5 bg-[#00ced1] rounded-full animate-ping" />
          Realtime Peak: 91%
        </div>
      </div>

      {/* Recharts Area Chart */}
      <div className="h-[180px] w-full mt-2">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={data}
            margin={{ top: 10, right: 5, left: -25, bottom: 0 }}
          >
            <defs>
              <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#4d41df" stopOpacity={0.25}/>
                <stop offset="95%" stopColor="#4d41df" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
            <XAxis 
              dataKey="name" 
              axisLine={false} 
              tickLine={false}
              tick={{ fill: '#94a3b8', fontSize: 10, fontFamily: 'JetBrains Mono', fontWeight: 600 }}
            />
            <YAxis 
              axisLine={false} 
              tickLine={false} 
              tick={{ fill: '#94a3b8', fontSize: 10, fontFamily: 'JetBrains Mono' }}
            />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: '#ffffff', 
                borderRadius: '8px', 
                border: '1px solid #e2e8f0',
                boxShadow: '0 4px 12px rgba(0, 0, 0, 0.05)',
                fontFamily: 'JetBrains Mono',
                fontSize: '11px'
              }} 
            />
            <Area 
              type="monotone" 
              dataKey="value" 
              stroke="#4d41df" 
              strokeWidth={3} 
              fillOpacity={1} 
              fill="url(#colorValue)" 
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
