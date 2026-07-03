/**
* @license
* SPDX-License-Identifier: Apache-2.0
*/
import React, { useState } from 'react';
import { Activity, Cpu, Database } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from 'recharts';
import { SystemNode } from '../types';

interface StressViewProps {
systemNodes: SystemNode[];
setSystemNodes: React.Dispatch<React.SetStateAction<SystemNode[]>>;
}

export default function StressView({ systemNodes, setSystemNodes }: StressViewProps) {
const [testReports, setTestReports] = useState<any[]>([]);
const [loadingReports, setLoadingReports] = useState(false);

const fetchReports = async () => {
    setLoadingReports(true);
    try {
        const res = await fetch('/api/stress-tests');
        const data = await res.json();
        setTestReports(data);
    } catch (err) {
        console.error("Failed to fetch stress test reports:", err);
    } finally {
        setLoadingReports(false);
    }
};

// Prepare data for charts
const requestsData = testReports.map(r => ({
    name: r.name,
    'HTTP Requests': r.metrics.httpReqs || 0,
    'Iterations': r.metrics.iterations || 0
}));

const durationData = testReports.map(r => ({
    name: r.name,
    'Avg Duration (ms)': r.metrics.avgDuration ? parseFloat(r.metrics.avgDuration.toFixed(2)) : 0,
    'p95 Duration (ms)': r.metrics.p95Duration ? parseFloat(r.metrics.p95Duration.toFixed(2)) : 0
}));

const checksData = testReports.map(r => ({
    name: r.name,
    'Success %': r.metrics.checksSuccessRate || 0,
    'Failed %': r.metrics.checksFailedRate || 0
}));

const networkData = testReports.map(r => ({
    name: r.name,
    'Received (kB)': r.metrics.dataReceived || 0,
    'Sent (kB)': r.metrics.dataSent || 0
}));

return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6" id="stress-view-root">
        {/* Control Panel */}
        <div className="lg:col-span-1 bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex flex-col justify-between h-fit">
            <div>
                <div className="flex items-center gap-2 mb-4">
                    <div className="p-2 bg-rose-50 rounded-lg text-rose-600">
                        <Activity size={20} className="animate-pulse" />
                    </div>
                    <h2 className="font-display font-extrabold text-lg text-slate-900">Stress Test Analytics</h2>
                </div>
                <div className="space-y-4">
                    <p className="text-xs text-slate-500 leading-relaxed">
                        Analyze historical k6 stress test reports. The system will parse all text files in the <code className="bg-slate-100 px-1 rounded">stress_tests</code> directory and generate statistical charts.
                    </p>
                    
                    <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-2">
                        <h4 className="text-xs font-bold text-slate-600 uppercase tracking-wider">Detected Reports</h4>
                        {testReports.length > 0 ? (
                            <ul className="space-y-1">
                                {testReports.map((r, idx) => (
                                    <li key={idx} className="flex items-center gap-2 text-xs text-slate-700">
                                        <div className="h-1.5 w-1.5 rounded-full bg-indigo-500" />
                                        {r.name}
                                    </li>
                                ))}
                            </ul>
                        ) : (
                            <p className="text-xs text-slate-400 italic">No reports loaded yet.</p>
                        )}
                    </div>
                </div>
            </div>

            {/* Action button */}
            <div className="mt-6 pt-4 border-t border-slate-100 space-y-2">
                <button
                    onClick={fetchReports}
                    disabled={loadingReports}
                    className={`w-full py-3 rounded-lg text-sm font-semibold flex items-center justify-center gap-2 transition-all ${
                        loadingReports
                            ? 'bg-slate-100 text-slate-400 cursor-not-allowed'
                            : 'bg-indigo-600 text-white hover:bg-indigo-700 shadow-sm shadow-indigo-600/10'
                    }`}
                >
                    <Activity size={16} className={loadingReports ? 'animate-spin' : ''} />
                    <span>{loadingReports ? 'Analyzing Reports...' : 'Analyze Stress Test Reports'}</span>
                </button>
            </div>
        </div>

        {/* Analytics Dashboard */}
        <div className="lg:col-span-2 space-y-6 flex flex-col">
            <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex-1">
                <h3 className="font-display font-extrabold text-sm text-slate-900 uppercase tracking-wider mb-4 flex items-center gap-2 border-b border-slate-100 pb-3">
                    <Activity size={16} className="text-indigo-600" />
                    Performance Metrics Dashboard
                </h3>
                
                {testReports.length === 0 ? (
                    <div className="text-center py-16 text-slate-400 flex flex-col items-center gap-3">
                        <Database size={32} className="opacity-50" />
                        <p className="text-sm">No stress test reports found.</p>
                        <p className="text-xs">Click "Analyze Stress Test Reports" to load data from the <code className="bg-slate-100 px-1 rounded">stress_tests</code> directory.</p>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {/* Chart 1: HTTP Requests & Iterations */}
                        <div className="border border-slate-100 rounded-xl p-4 bg-slate-50/50">
                            <h4 className="text-xs font-bold text-slate-500 uppercase mb-3 tracking-wider">HTTP Requests & Iterations</h4>
                            <ResponsiveContainer width="100%" height={200}>
                                <BarChart data={requestsData}>
                                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                                    <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#64748b' }} />
                                    <YAxis tick={{ fontSize: 10, fill: '#64748b' }} />
                                    <Tooltip contentStyle={{ fontSize: '11px', borderRadius: '8px' }} />
                                    <Legend wrapperStyle={{ fontSize: '10px' }} />
                                    <Bar dataKey="HTTP Requests" fill="#4d41df" radius={[4, 4, 0, 0]} />
                                    <Bar dataKey="Iterations" fill="#0891b2" radius={[4, 4, 0, 0]} />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>

                        {/* Chart 2: Response Times */}
                        <div className="border border-slate-100 rounded-xl p-4 bg-slate-50/50">
                            <h4 className="text-xs font-bold text-slate-500 uppercase mb-3 tracking-wider">Response Times (ms)</h4>
                            <ResponsiveContainer width="100%" height={200}>
                                <BarChart data={durationData}>
                                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                                    <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#64748b' }} />
                                    <YAxis tick={{ fontSize: 10, fill: '#64748b' }} />
                                    <Tooltip contentStyle={{ fontSize: '11px', borderRadius: '8px' }} />
                                    <Legend wrapperStyle={{ fontSize: '10px' }} />
                                    <Bar dataKey="Avg Duration (ms)" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                                    <Bar dataKey="p95 Duration (ms)" fill="#ef4444" radius={[4, 4, 0, 0]} />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>

                        {/* Chart 3: Check Success Rate */}
                        <div className="border border-slate-100 rounded-xl p-4 bg-slate-50/50">
                            <h4 className="text-xs font-bold text-slate-500 uppercase mb-3 tracking-wider">Check Success Rate (%)</h4>
                            <ResponsiveContainer width="100%" height={200}>
                                <BarChart data={checksData}>
                                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                                    <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#64748b' }} />
                                    <YAxis tick={{ fontSize: 10, fill: '#64748b' }} domain={[0, 100]} />
                                    <Tooltip contentStyle={{ fontSize: '11px', borderRadius: '8px' }} />
                                    <Legend wrapperStyle={{ fontSize: '10px' }} />
                                    <Bar dataKey="Success %" stackId="a" fill="#10b981" />
                                    <Bar dataKey="Failed %" stackId="a" fill="#ef4444" />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>

                        {/* Chart 4: Network Traffic */}
                        <div className="border border-slate-100 rounded-xl p-4 bg-slate-50/50">
                            <h4 className="text-xs font-bold text-slate-500 uppercase mb-3 tracking-wider">Network Traffic (kB)</h4>
                            <ResponsiveContainer width="100%" height={200}>
                                <BarChart data={networkData}>
                                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                                    <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#64748b' }} />
                                    <YAxis tick={{ fontSize: 10, fill: '#64748b' }} />
                                    <Tooltip contentStyle={{ fontSize: '11px', borderRadius: '8px' }} />
                                    <Legend wrapperStyle={{ fontSize: '10px' }} />
                                    <Bar dataKey="Received (kB)" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                                    <Bar dataKey="Sent (kB)" fill="#06b6d4" radius={[4, 4, 0, 0]} />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    </div>
                )}
            </div>

            {/* Parsed Metrics Summary Terminal */}
            <div className="bg-slate-950 text-slate-300 font-mono text-xs rounded-xl p-5 border border-slate-800 shadow-xl flex flex-col h-[250px]">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2 mb-2 select-none">
                    <span className="text-slate-400 text-[10px] font-bold tracking-widest uppercase flex items-center gap-1.5">
                        <Cpu size={12} className="text-indigo-400" /> Parsed Metrics Summary
                    </span>
                    <span className="text-[9px] font-mono select-none text-slate-500">root@stress-analytics:~#</span>
                </div>
                <div className="flex-1 overflow-y-auto space-y-3 pr-2 select-text text-[11px] leading-relaxed custom-scrollbar">
                    {testReports.length === 0 ? (
                        <span className="text-slate-500 italic">Waiting for analysis...</span>
                    ) : (
                        testReports.map((report, idx) => (
                            <div key={idx} className="border-b border-slate-800 pb-2 mb-2 last:border-0">
                                <div className="text-indigo-400 font-bold mb-1.5 flex items-center gap-2">
                                    <div className="h-1.5 w-1.5 rounded-full bg-indigo-400 animate-pulse" />
                                    {report.name}
                                </div>
                                <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-slate-400">
                                    <span>Run Time: <span className="text-slate-200">{report.metrics.runTime || 'N/A'}</span></span>
                                    <span>Max VUs: <span className="text-slate-200">{report.metrics.vusMax || 'N/A'}</span></span>
                                    <span>HTTP Reqs: <span className="text-slate-200">{report.metrics.httpReqs || 0}</span></span>
                                    <span>Iterations: <span className="text-slate-200">{report.metrics.iterations || 0}</span></span>
                                    <span>Avg Duration: <span className="text-slate-200">{report.metrics.avgDuration ? report.metrics.avgDuration.toFixed(2) : 0} ms</span></span>
                                    <span>p95 Duration: <span className="text-slate-200">{report.metrics.p95Duration ? report.metrics.p95Duration.toFixed(2) : 0} ms</span></span>
                                    <span>Success Rate: <span className="text-emerald-400">{report.metrics.checksSuccessRate ? report.metrics.checksSuccessRate.toFixed(2) : 0}%</span></span>
                                    <span>Failed Rate: <span className="text-red-400">{report.metrics.checksFailedRate ? report.metrics.checksFailedRate.toFixed(2) : 0}%</span></span>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>
        </div>
    </div>
);
}