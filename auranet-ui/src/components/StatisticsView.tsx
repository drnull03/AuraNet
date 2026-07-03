/**
* @license
* SPDX-License-Identifier: Apache-2.0
*/
import React, { useState, useEffect } from 'react';
import { Cpu, HardDrive, MemoryStick, Server, Activity, Database } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { SystemNode, MetricData } from '../types';

interface StatisticsViewProps {
    systemNodes: SystemNode[];
    metrics: MetricData;
}

interface SystemStats {
    cpu: { model: string; cores: number; usagePercent: number };
    ram: { totalGB: string; usedGB: string; freeGB: string; usagePercent: number };
    disk: { filesystem: string; size: string; used: string; available: string; usePercent: number; mountedOn: string }[];
    inodes: { filesystem: string; inodes: string; used: string; available: string; usePercent: number; mountedOn: string }[];
}

export default function StatisticsView({ systemNodes, metrics }: StatisticsViewProps) {
    const [stats, setStats] = useState<SystemStats | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchStats = async () => {
            try {
                const res = await fetch('/api/system-stats');
                const data = await res.json();
                setStats(data);
            } catch (err) {
                console.error("Failed to fetch system stats", err);
            } finally {
                setLoading(false);
            }
        };

        fetchStats();
        // Auto-refresh telemetry every 5 seconds
        const interval = setInterval(fetchStats, 5000); 
        return () => clearInterval(interval);
    }, []);

    if (loading || !stats) {
        return (
            <div className="flex items-center justify-center h-full text-slate-400 font-mono text-sm animate-pulse">
                Initializing system telemetry probes...
            </div>
        );
    }

    // Filter out virtual filesystems for cleaner charts
    const physicalDisks = stats.disk.filter(d => 
        !d.filesystem.includes('tmpfs') && 
        !d.filesystem.includes('devtmpfs') && 
        !d.filesystem.includes('overlay') && 
        d.mountedOn !== '/dev' &&
        !d.mountedOn.startsWith('/snap/')
    );
    
    const physicalInodes = stats.inodes.filter(d => 
        !d.filesystem.includes('tmpfs') && 
        !d.filesystem.includes('devtmpfs') && 
        !d.filesystem.includes('overlay') && 
        d.mountedOn !== '/dev' &&
        !d.mountedOn.startsWith('/snap/')
    );

    // Map data for the comparison chart
    const chartData = physicalDisks.map(d => {
        const inodeData = physicalInodes.find(i => i.mountedOn === d.mountedOn);
        return {
            name: d.mountedOn,
            'Disk %': d.usePercent,
            'Inode %': inodeData ? inodeData.usePercent : 0
        };
    });

    return (
        <div className="space-y-6 p-2" id="system-stats-root">
            {/* Header */}
            <div className="flex items-center gap-3 mb-2">
                <div className="p-2 bg-indigo-100 rounded-lg text-indigo-600">
                    <Activity size={24} />
                </div>
                <div>
                    <h2 className="font-display font-extrabold text-2xl text-slate-900">Host System Telemetry</h2>
                    <p className="text-xs text-slate-500 font-mono">Real-time hardware resource monitoring (Auto-refresh: 5s)</p>
                </div>
            </div>

            {/* Top Metrics: CPU & RAM */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* CPU Card */}
                <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm flex flex-col justify-between">
                    <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-orange-100 rounded-lg text-orange-600">
                                <Cpu size={20} />
                            </div>
                            <div>
                                <h3 className="font-display font-bold text-lg text-slate-900">Processor (CPU)</h3>
                                <p className="text-[10px] font-mono text-slate-500 truncate max-w-[200px]" title={stats.cpu.model}>{stats.cpu.model}</p>
                            </div>
                        </div>
                        <span className="text-xs font-bold font-mono bg-slate-100 px-2 py-1 rounded-md text-slate-600">{stats.cpu.cores} Cores</span>
                    </div>
                    <div className="flex items-center gap-6">
                        <div className="relative w-24 h-24 flex-shrink-0">
                            <svg className="w-full h-full transform -rotate-90">
                                <circle cx="48" cy="48" r="40" strokeWidth="8" stroke="#e2e8f0" fill="transparent" />
                                <circle 
                                    cx="48" cy="48" r="40" strokeWidth="8" 
                                    stroke={stats.cpu.usagePercent > 80 ? '#ef4444' : stats.cpu.usagePercent > 50 ? '#f59e0b' : '#10b981'} 
                                    fill="transparent" 
                                    strokeDasharray={2 * Math.PI * 40} 
                                    strokeDashoffset={2 * Math.PI * 40 * (1 - stats.cpu.usagePercent / 100)} 
                                    className="transition-all duration-1000" 
                                />
                            </svg>
                            <span className="absolute inset-0 flex items-center justify-center font-mono font-bold text-xl text-slate-800">
                                {stats.cpu.usagePercent}%
                            </span>
                        </div>
                        <div className="flex-1 space-y-2">
                            <div>
                                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Global Load</span>
                                <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden mt-1">
                                    <div 
                                        className={`h-full rounded-full transition-all duration-1000 ${stats.cpu.usagePercent > 80 ? 'bg-red-500' : stats.cpu.usagePercent > 50 ? 'bg-amber-500' : 'bg-emerald-500'}`} 
                                        style={{ width: `${stats.cpu.usagePercent}%` }} 
                                    />
                                </div>
                            </div>
                            <p className="text-xs text-slate-500 leading-relaxed">
                                Average utilization across all {stats.cpu.cores} logical threads.
                            </p>
                        </div>
                    </div>
                </div>

                {/* RAM Card */}
                <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm flex flex-col justify-between">
                    <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-blue-100 rounded-lg text-blue-600">
                                <MemoryStick size={20} />
                            </div>
                            <div>
                                <h3 className="font-display font-bold text-lg text-slate-900">Memory (RAM)</h3>
                                <p className="text-[10px] font-mono text-slate-500">System Physical Memory</p>
                            </div>
                        </div>
                        <span className="text-xs font-bold font-mono bg-slate-100 px-2 py-1 rounded-md text-slate-600">{stats.ram.totalGB} GB</span>
                    </div>
                    <div className="flex items-center gap-6">
                        <div className="relative w-24 h-24 flex-shrink-0">
                            <svg className="w-full h-full transform -rotate-90">
                                <circle cx="48" cy="48" r="40" strokeWidth="8" stroke="#e2e8f0" fill="transparent" />
                                <circle 
                                    cx="48" cy="48" r="40" strokeWidth="8" 
                                    stroke={stats.ram.usagePercent > 80 ? '#ef4444' : stats.ram.usagePercent > 50 ? '#f59e0b' : '#10b981'} 
                                    fill="transparent" 
                                    strokeDasharray={2 * Math.PI * 40} 
                                    strokeDashoffset={2 * Math.PI * 40 * (1 - stats.ram.usagePercent / 100)} 
                                    className="transition-all duration-1000" 
                                />
                            </svg>
                            <span className="absolute inset-0 flex items-center justify-center font-mono font-bold text-xl text-slate-800">
                                {stats.ram.usagePercent}%
                            </span>
                        </div>
                        <div className="flex-1 space-y-3">
                            <div className="flex justify-between text-xs">
                                <span className="text-slate-500">Used</span>
                                <span className="font-mono font-bold text-slate-800">{stats.ram.usedGB} GB</span>
                            </div>
                            <div className="flex justify-between text-xs">
                                <span className="text-slate-500">Available</span>
                                <span className="font-mono font-bold text-slate-800">{stats.ram.freeGB} GB</span>
                            </div>
                            <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                                <div 
                                    className={`h-full rounded-full transition-all duration-1000 ${stats.ram.usagePercent > 80 ? 'bg-red-500' : stats.ram.usagePercent > 50 ? 'bg-amber-500' : 'bg-emerald-500'}`} 
                                    style={{ width: `${stats.ram.usagePercent}%` }} 
                                />
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Charts Section */}
            <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
                <div className="flex items-center gap-2 mb-4 border-b border-slate-100 pb-3">
                    <Database size={16} className="text-indigo-600" />
                    <h3 className="font-display font-bold text-sm text-slate-900 uppercase tracking-wider">Storage & Inode Utilization</h3>
                </div>
                <div className="h-[250px] w-full mt-2">
                    {chartData.length > 0 ? (
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 5 }}>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                                <XAxis dataKey="name" tick={{ fill: '#64748b', fontSize: 11, fontFamily: 'JetBrains Mono' }} />
                                <YAxis tick={{ fill: '#94a3b8', fontSize: 10, fontFamily: 'JetBrains Mono' }} domain={[0, 100]} unit="%" />
                                <Tooltip 
                                    contentStyle={{ backgroundColor: '#0f172a', borderRadius: '8px', border: 'none', color: '#f8fafc', fontFamily: 'JetBrains Mono', fontSize: '11px' }}
                                    cursor={{ fill: 'rgba(0,0,0,0.05)' }}
                                />
                                <Bar dataKey="Disk %" fill="#4d41df" radius={[4, 4, 0, 0]} barSize={20} />
                                <Bar dataKey="Inode %" fill="#0891b2" radius={[4, 4, 0, 0]} barSize={20} />
                            </BarChart>
                        </ResponsiveContainer>
                    ) : (
                        <div className="flex items-center justify-center h-full text-slate-400 text-sm">No physical storage partitions detected.</div>
                    )}
                </div>
            </div>

            {/* Tables Section: Disk & Inodes */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Disk Table */}
                <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm overflow-hidden">
                    <div className="flex items-center gap-2 mb-4 border-b border-slate-100 pb-3">
                        <HardDrive size={16} className="text-indigo-600" />
                        <h3 className="font-display font-bold text-sm text-slate-900 uppercase tracking-wider">Disk Space Allocation</h3>
                    </div>
                    <div className="overflow-x-auto max-h-[300px] overflow-y-auto custom-scrollbar">
                        <table className="w-full text-left border-collapse text-xs">
                            <thead className="sticky top-0 bg-white z-10">
                                <tr className="border-b border-slate-200 text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider">
                                    <th className="py-2 px-2">Filesystem</th>
                                    <th className="py-2 px-2">Size</th>
                                    <th className="py-2 px-2">Used</th>
                                    <th className="py-2 px-2">Avail</th>
                                    <th className="py-2 px-2">Use%</th>
                                    <th className="py-2 px-2">Mount</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-50 text-slate-700 font-mono">
                                {stats.disk.map((d, idx) => (
                                    <tr key={idx} className="hover:bg-slate-50/50 transition-colors">
                                        <td className="py-2 px-2 truncate max-w-[100px]" title={d.filesystem}>{d.filesystem}</td>
                                        <td className="py-2 px-2">{d.size}</td>
                                        <td className="py-2 px-2">{d.used}</td>
                                        <td className="py-2 px-2">{d.available}</td>
                                        <td className="py-2 px-2">
                                            <span className={`px-1.5 py-0.5 rounded font-bold ${
                                                d.usePercent > 80 ? 'bg-red-100 text-red-700' : 
                                                d.usePercent > 50 ? 'bg-amber-100 text-amber-700' : 
                                                'bg-emerald-100 text-emerald-700'
                                            }`}>
                                                {d.usePercent}%
                                            </span>
                                        </td>
                                        <td className="py-2 px-2 font-bold text-slate-800">{d.mountedOn}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* Inodes Table */}
                <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm overflow-hidden">
                    <div className="flex items-center gap-2 mb-4 border-b border-slate-100 pb-3">
                        <Server size={16} className="text-indigo-600" />
                        <h3 className="font-display font-bold text-sm text-slate-900 uppercase tracking-wider">Inode Utilization</h3>
                    </div>
                    <div className="overflow-x-auto max-h-[300px] overflow-y-auto custom-scrollbar">
                        <table className="w-full text-left border-collapse text-xs">
                            <thead className="sticky top-0 bg-white z-10">
                                <tr className="border-b border-slate-200 text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider">
                                    <th className="py-2 px-2">Filesystem</th>
                                    <th className="py-2 px-2">Inodes</th>
                                    <th className="py-2 px-2">Used</th>
                                    <th className="py-2 px-2">Free</th>
                                    <th className="py-2 px-2">Use%</th>
                                    <th className="py-2 px-2">Mount</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-50 text-slate-700 font-mono">
                                {stats.inodes.map((d, idx) => (
                                    <tr key={idx} className="hover:bg-slate-50/50 transition-colors">
                                        <td className="py-2 px-2 truncate max-w-[100px]" title={d.filesystem}>{d.filesystem}</td>
                                        <td className="py-2 px-2">{d.inodes}</td>
                                        <td className="py-2 px-2">{d.used}</td>
                                        <td className="py-2 px-2">{d.available}</td>
                                        <td className="py-2 px-2">
                                            <span className={`px-1.5 py-0.5 rounded font-bold ${
                                                d.usePercent > 80 ? 'bg-red-100 text-red-700' : 
                                                d.usePercent > 50 ? 'bg-amber-100 text-amber-700' : 
                                                'bg-emerald-100 text-emerald-700'
                                            }`}>
                                                {d.usePercent}%
                                            </span>
                                        </td>
                                        <td className="py-2 px-2 font-bold text-slate-800">{d.mountedOn}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    );
}