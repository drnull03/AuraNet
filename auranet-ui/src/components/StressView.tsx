/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Activity, Play, Square, RefreshCw, AlertTriangle, Cpu, Database, Network } from 'lucide-react';
import { SystemNode } from '../types';

interface StressViewProps {
  systemNodes: SystemNode[];
  setSystemNodes: React.Dispatch<React.SetStateAction<SystemNode[]>>;
}

export default function StressView({ systemNodes, setSystemNodes }: StressViewProps) {
  const [selectedNodeId, setSelectedNodeId] = useState<string>(systemNodes[0]?.id || '');
  const [testType, setTestType] = useState<'cpu' | 'memory' | 'latency' | 'extreme'>('cpu');
  const [intensity, setIntensity] = useState<number>(85);
  const [runningTests, setRunningTests] = useState<{ [nodeId: string]: { type: string; intensity: number; intervalId: any } }>({});
  const [logStream, setLogStream] = useState<{ id: string; timestamp: string; message: string; type: 'info' | 'warn' | 'success' }[]>([
    { id: '1', timestamp: new Date().toLocaleTimeString(), message: 'Stress controller initialized. Connected to 12 endpoints.', type: 'info' }
  ]);

  const addLog = (message: string, type: 'info' | 'warn' | 'success' = 'info') => {
    setLogStream((prev) => [
      { id: Date.now().toString(), timestamp: new Date().toLocaleTimeString(), message, type },
      ...prev.slice(0, 19),
    ]);
  };

  const getSelectedNode = () => systemNodes.find(n => n.id === selectedNodeId);

  // Handle triggering stress test on the selected node
  const handleStartTest = () => {
    const node = getSelectedNode();
    if (!node) return;

    if (runningTests[node.id]) {
      addLog(`Test already running on ${node.label}!`, 'warn');
      return;
    }

    addLog(`Initiating [${testType.toUpperCase()}] stress test on ${node.label} at ${intensity}% workload level...`, 'warn');

    // Store original values before test
    const originalCpu = node.cpu;
    const originalMemory = node.memory;
    const originalLatency = node.latency;
    const originalStatus = node.status;

    // Set up active interval to simulate fluctuating highly active workloads
    const intervalId = setInterval(() => {
      setSystemNodes((prevNodes) =>
        prevNodes.map((n) => {
          if (n.id === node.id) {
            // Apply heavy metrics based on type
            let updatedCpu = n.cpu;
            let updatedMemory = n.memory;
            let updatedLatency = n.latency;
            let updatedStatus = n.status;

            const variation = Math.floor(Math.random() * 8) - 4; // +-4% fluctuation

            if (testType === 'cpu') {
              updatedCpu = Math.min(100, Math.max(90, intensity + variation));
              updatedStatus = updatedCpu > 90 ? 'warning' : 'active';
            } else if (testType === 'memory') {
              updatedMemory = Math.min(100, Math.max(88, intensity + variation));
              updatedStatus = updatedMemory > 90 ? 'warning' : 'active';
            } else if (testType === 'latency') {
              updatedLatency = Math.min(450, Math.max(250, 300 + variation * 10));
              updatedStatus = 'warning';
            } else if (testType === 'extreme') {
              updatedCpu = Math.min(100, Math.max(95, intensity + variation));
              updatedMemory = Math.min(100, Math.max(92, intensity + variation));
              updatedLatency = Math.min(500, Math.max(350, 380 + variation * 15));
              updatedStatus = 'offline';
            }

            return {
              ...n,
              cpu: updatedCpu,
              memory: updatedMemory,
              latency: updatedLatency,
              status: updatedStatus,
            };
          }
          return n;
        })
      );

      // Periodically append to logs
      const messages = [
        `System telemetry thread reported high load thresholds on ${node.label}.`,
        `Cluster coordinator alert: CPU/Memory spike detected.`,
        `Ping monitor reported latency fluctuation on ${node.label}.`,
      ];
      const randomMsg = messages[Math.floor(Math.random() * messages.length)];
      addLog(`[ALERT] ${node.label}: ${randomMsg}`, 'warn');
    }, 2000);

    setRunningTests((prev) => ({
      ...prev,
      [node.id]: { type: testType, intensity, intervalId },
    }));

    // Trigger immediate update
    setSystemNodes((prevNodes) =>
      prevNodes.map((n) => {
        if (n.id === node.id) {
          return {
            ...n,
            status: testType === 'extreme' ? 'offline' : 'warning',
            cpu: testType === 'cpu' || testType === 'extreme' ? intensity : n.cpu,
            memory: testType === 'memory' || testType === 'extreme' ? intensity : n.memory,
            latency: testType === 'latency' || testType === 'extreme' ? 350 : n.latency,
          };
        }
        return n;
      })
    );

    addLog(`Test successfully launched on ${node.label}. Telemetry stream open.`, 'success');
  };

  // Stop stress test on selected node
  const handleStopTest = (nodeId: string) => {
    const test = runningTests[nodeId];
    if (!test) return;

    clearInterval(test.intervalId);

    const targetNode = systemNodes.find(n => n.id === nodeId);
    if (targetNode) {
      addLog(`Terminating stress test on ${targetNode.label}. Normalizing telemetry parameters...`, 'info');
    }

    // Restore node to standard normal parameters
    setSystemNodes((prevNodes) =>
      prevNodes.map((n) => {
        if (n.id === nodeId) {
          // Determine realistic restored parameters
          return {
            ...n,
            status: 'active',
            cpu: Math.floor(Math.random() * 20) + 35, // 35-55%
            memory: Math.floor(Math.random() * 25) + 40, // 40-65%
            latency: n.id === 'central-hub' ? 1.2 : Math.floor(Math.random() * 30) + 15,
          };
        }
        return n;
      })
    );

    setRunningTests((prev) => {
      const copy = { ...prev };
      delete copy[nodeId];
      return copy;
    });

    if (targetNode) {
      addLog(`Telemetry on ${targetNode.label} recovered to baseline successfully.`, 'success');
    }
  };

  const handleStopAll = () => {
    Object.keys(runningTests).forEach((nodeId) => {
      handleStopTest(nodeId);
    });
    addLog(`All active mesh stress tests halted. Global cluster safety protocols active.`, 'success');
  };

  // Cleanup intervals on unmount
  useEffect(() => {
    return () => {
      const active = runningTests as { [nodeId: string]: { type: string; intensity: number; intervalId: any } };
      Object.values(active).forEach((t) => {
        clearInterval(t.intervalId);
      });
    };
  }, [runningTests]);

  const selectedNode = getSelectedNode();

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6" id="stress-view-root">
      {/* Test Setup Panel */}
      <div className="lg:col-span-1 bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex flex-col justify-between h-fit">
        <div>
          <div className="flex items-center gap-2 mb-4">
            <div className="p-2 bg-rose-50 rounded-lg text-rose-600">
              <Activity size={20} className="animate-pulse" />
            </div>
            <h2 className="font-display font-extrabold text-lg text-slate-900">Configure Stress Test</h2>
          </div>

          <div className="space-y-4">
            {/* Target Node Selection */}
            <div>
              <label className="block text-xs font-semibold text-slate-600 uppercase tracking-wider mb-2">Target Node Endpoint</label>
              <select
                value={selectedNodeId}
                onChange={(e) => setSelectedNodeId(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 px-3 py-2.5 rounded-lg text-sm text-slate-800 font-medium focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                {systemNodes.map((n) => (
                  <option key={n.id} value={n.id}>
                    {n.label} ({n.ip}) - {n.status.toUpperCase()}
                  </option>
                ))}
              </select>
            </div>

            {/* Test Vector Profile */}
            <div>
              <label className="block text-xs font-semibold text-slate-600 uppercase tracking-wider mb-2">Stress Vector Profile</label>
              <div className="grid grid-cols-2 gap-2">
                {[
                  { id: 'cpu', label: 'CPU Flooding', desc: 'Simulate full thread utilization', icon: Cpu, color: 'text-orange-500' },
                  { id: 'memory', label: 'Memory Leak', desc: 'Saturate active RAM segments', icon: Database, color: 'text-amber-500' },
                  { id: 'latency', label: 'Ping Flood', desc: 'Generate artificial lag latency', icon: Network, color: 'text-indigo-500' },
                  { id: 'extreme', label: 'Extreme Spike', desc: 'Simulate complete host failure', icon: AlertTriangle, color: 'text-red-500' },
                ].map((item) => {
                  const Icon = item.icon;
                  return (
                    <button
                      key={item.id}
                      onClick={() => setTestType(item.id as any)}
                      className={`p-3 border rounded-xl flex flex-col text-left transition-all ${
                        testType === item.id
                          ? 'border-indigo-600 bg-indigo-50/40 text-indigo-950 shadow-xs'
                          : 'border-slate-200 hover:bg-slate-50 text-slate-700'
                      }`}
                    >
                      <Icon size={18} className={`mb-1.5 ${item.color}`} />
                      <span className="text-xs font-bold font-sans">{item.label}</span>
                      <span className="text-[9px] text-slate-500 mt-0.5 leading-tight">{item.desc}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Load Intensity */}
            {testType !== 'latency' && (
              <div>
                <div className="flex justify-between text-xs font-semibold text-slate-600 uppercase tracking-wider mb-2">
                  <span>Load Intensity</span>
                  <span className="text-indigo-600 font-mono">{intensity}%</span>
                </div>
                <input
                  type="range"
                  min="50"
                  max="100"
                  value={intensity}
                  onChange={(e) => setIntensity(Number(e.target.value))}
                  className="w-full accent-indigo-600 cursor-pointer h-1.5 bg-slate-100 rounded-lg"
                />
              </div>
            )}
          </div>
        </div>

        {/* Start / Stop Buttons */}
        <div className="mt-6 pt-4 border-t border-slate-100 space-y-2">
          <button
            onClick={handleStartTest}
            disabled={!!runningTests[selectedNodeId]}
            className={`w-full py-3 rounded-lg text-sm font-semibold flex items-center justify-center gap-2 transition-all ${
              runningTests[selectedNodeId]
                ? 'bg-slate-100 text-slate-400 cursor-not-allowed'
                : 'bg-indigo-600 text-white hover:bg-indigo-700 shadow-sm shadow-indigo-600/10'
            }`}
          >
            <Play size={16} />
            <span>Launch Stress Test</span>
          </button>

          {Object.keys(runningTests).length > 0 && (
            <button
              onClick={handleStopAll}
              className="w-full py-2.5 rounded-lg text-xs font-semibold border border-red-200 text-red-600 hover:bg-red-50 transition-all flex items-center justify-center gap-2"
            >
              <Square size={14} />
              <span>Halt All Stress Tests</span>
            </button>
          )}
        </div>
      </div>

      {/* Target Metrics Monitor & Active Threads */}
      <div className="lg:col-span-2 space-y-6 flex flex-col justify-between">
        {/* Selected Node Real-time Telemetry Monitor */}
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex-1">
          <h3 className="font-display font-extrabold text-sm text-slate-900 uppercase tracking-wider mb-4 flex items-center gap-2 border-b border-slate-100 pb-3">
            <Activity size={16} className="text-indigo-600" />
            Live Endpoint Analyzer: <span className="text-indigo-600">{selectedNode?.label}</span>
          </h3>

          {selectedNode ? (
            <div className="grid grid-cols-3 gap-4">
              {/* CPU Ring */}
              <div className="bg-slate-50 rounded-xl p-4 border border-slate-100 flex flex-col items-center justify-center">
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2">CPU Utilization</span>
                <div className="relative flex items-center justify-center">
                  <svg className="w-20 h-20 transform -rotate-90">
                    <circle cx="40" cy="40" r="32" strokeWidth="6" stroke="#e2e8f0" fill="transparent" />
                    <circle
                      cx="40" cy="40" r="32" strokeWidth="6"
                      stroke={selectedNode.cpu > 80 ? '#f43f5e' : selectedNode.cpu > 60 ? '#f59e0b' : '#10b981'}
                      fill="transparent"
                      strokeDasharray={2 * Math.PI * 32}
                      strokeDashoffset={2 * Math.PI * 32 * (1 - selectedNode.cpu / 100)}
                      className="transition-all duration-500"
                    />
                  </svg>
                  <span className="absolute font-mono font-bold text-base text-slate-800">{selectedNode.cpu}%</span>
                </div>
              </div>

              {/* Memory Ring */}
              <div className="bg-slate-50 rounded-xl p-4 border border-slate-100 flex flex-col items-center justify-center">
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2">Memory Load</span>
                <div className="relative flex items-center justify-center">
                  <svg className="w-20 h-20 transform -rotate-90">
                    <circle cx="40" cy="40" r="32" strokeWidth="6" stroke="#e2e8f0" fill="transparent" />
                    <circle
                      cx="40" cy="40" r="32" strokeWidth="6"
                      stroke={selectedNode.memory > 80 ? '#f43f5e' : selectedNode.memory > 60 ? '#f59e0b' : '#10b981'}
                      fill="transparent"
                      strokeDasharray={2 * Math.PI * 32}
                      strokeDashoffset={2 * Math.PI * 32 * (1 - selectedNode.memory / 100)}
                      className="transition-all duration-500"
                    />
                  </svg>
                  <span className="absolute font-mono font-bold text-base text-slate-800">{selectedNode.memory}%</span>
                </div>
              </div>

              {/* Latency Indicator */}
              <div className="bg-slate-50 rounded-xl p-4 border border-slate-100 flex flex-col items-center justify-center">
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1 text-center">Network Latency</span>
                <span className={`font-mono font-bold text-2xl mt-2 ${
                  selectedNode.latency > 150 ? 'text-rose-600' : selectedNode.latency > 50 ? 'text-amber-600' : 'text-emerald-600'
                }`}>
                  {selectedNode.latency} <span className="text-xs">ms</span>
                </span>
                <span className="text-[9px] text-slate-400 font-semibold uppercase mt-2 tracking-wider">
                  {selectedNode.status === 'offline' ? 'Timeout Error' : 'Stable Stream'}
                </span>
              </div>
            </div>
          ) : (
            <p className="text-slate-400 text-sm py-8 text-center">Please select a valid node endpoint.</p>
          )}

          {/* Active Stress Tests list */}
          <div className="mt-6">
            <span className="text-xs font-bold text-slate-600 uppercase tracking-wider block mb-3">Active Test Threads</span>
            {Object.keys(runningTests).length === 0 ? (
              <div className="text-center py-6 border-2 border-dashed border-slate-100 rounded-xl text-slate-400 text-xs font-medium">
                No stress tests currently active in the cluster.
              </div>
            ) : (
            <div className="space-y-2 max-h-[140px] overflow-y-auto">
                {Object.entries(runningTests as { [nodeId: string]: { type: string; intensity: number; intervalId: any } }).map(([nodeId, test]) => {
                  const node = systemNodes.find(n => n.id === nodeId);
                  if (!node) return null;
                  return (
                    <div key={nodeId} className="flex items-center justify-between p-3 bg-red-50/50 border border-red-100 rounded-xl">
                      <div className="flex items-center gap-3">
                        <div className="h-2 w-2 bg-rose-600 rounded-full animate-ping" />
                        <div>
                          <p className="text-xs font-bold text-slate-800">{node.label}</p>
                          <p className="text-[10px] text-red-600 font-mono font-bold uppercase">
                            Vector: {test.type} ({test.intensity}%)
                          </p>
                        </div>
                      </div>
                      <button
                        onClick={() => handleStopTest(nodeId)}
                        className="text-xs font-semibold px-2.5 py-1.5 rounded-md bg-white border border-red-200 text-red-600 hover:bg-red-50 transition-colors"
                      >
                        Stop Test
                      </button>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Real-time Stress Log Terminal */}
        <div className="bg-slate-950 text-slate-300 font-mono text-xs rounded-xl p-5 border border-slate-800 shadow-xl flex flex-col h-[200px]">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2 mb-2 select-none">
            <span className="text-slate-400 text-[10px] font-bold tracking-widest uppercase">Telemetry System Logs Stream</span>
            <div className="flex gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-red-500/80" />
              <span className="w-2.5 h-2.5 rounded-full bg-yellow-500/80" />
              <span className="w-2.5 h-2.5 rounded-full bg-green-500/80" />
            </div>
          </div>
          <div className="flex-1 overflow-y-auto space-y-1.5 pr-2 select-text text-[11px] leading-relaxed">
            {logStream.map((log) => (
              <div key={log.id} className="flex items-start gap-2">
                <span className="text-slate-600 flex-shrink-0 select-none">[{log.timestamp}]</span>
                <span className={`${
                  log.type === 'warn' ? 'text-amber-400' : log.type === 'success' ? 'text-emerald-400' : 'text-slate-400'
                }`}>
                  {log.message}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
