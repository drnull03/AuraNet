/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { Sliders, Plus, Play, RefreshCw, Layers, Cpu, Database, Network } from 'lucide-react';
import { SystemNode } from '../types';

interface WorkloadViewProps {
  systemNodes: SystemNode[];
  setSystemNodes: React.Dispatch<React.SetStateAction<SystemNode[]>>;
}

interface WorkloadRule {
  id: string;
  nodeId: string;
  nodeLabel: string;
  intensity: number;
  pollingMs: number;
  active: boolean;
}

export default function WorkloadView({ systemNodes, setSystemNodes }: WorkloadViewProps) {
  const [selectedNodeId, setSelectedNodeId] = useState<string>(systemNodes[0]?.id || '');
  const [intensity, setIntensity] = useState<number>(2.5); // Multiplier
  const [pollingMs, setPollingMs] = useState<number>(500);
  const [activeRules, setActiveRules] = useState<WorkloadRule[]>([]);
  const [workloadLogs, setWorkloadLogs] = useState<{ id: string; time: string; msg: string; type: 'info' | 'success' }[]>([
    { id: '1', time: new Date().toLocaleTimeString(), msg: 'Workload manager loaded. Initializing scheduling threads...', type: 'info' }
  ]);

  const addLog = (msg: string, type: 'info' | 'success' = 'info') => {
    setWorkloadLogs(prev => [
      { id: Date.now().toString(), time: new Date().toLocaleTimeString(), msg, type },
      ...prev.slice(0, 19)
    ]);
  };

  const handleAddRule = () => {
    const node = systemNodes.find(n => n.id === selectedNodeId);
    if (!node) return;

    // Check if duplicate rule exists
    if (activeRules.some(r => r.nodeId === node.id && r.active)) {
      addLog(`Workload schedule already active on ${node.label}. Scaling existing multiplier...`, 'info');
      setActiveRules(prev =>
        prev.map(r => (r.nodeId === node.id ? { ...r, intensity, pollingMs } : r))
      );
    } else {
      const newRule: WorkloadRule = {
        id: `rule-${Date.now()}`,
        nodeId: node.id,
        nodeLabel: node.label,
        intensity,
        pollingMs,
        active: true,
      };
      setActiveRules(prev => [newRule, ...prev]);
      addLog(`Successfully registered workload schedule for ${node.label}.`, 'success');
    }

    // Apply multiplier to node's CPU, Memory, and Latency
    setSystemNodes(prevNodes =>
      prevNodes.map(n => {
        if (n.id === node.id) {
          // Compute multiplied metrics
          const multiplier = intensity;
          const baselineCpu = 35;
          const baselineMemory = 40;
          const baselineLatency = n.id === 'central-hub' ? 1.2 : 20;

          const updatedCpu = Math.min(98, Math.round(baselineCpu * multiplier));
          const updatedMemory = Math.min(98, Math.round(baselineMemory * multiplier));
          const updatedLatency = Math.min(400, Math.round(baselineLatency * multiplier));

          const updatedStatus = updatedCpu > 85 || updatedMemory > 85 ? 'warning' : 'active';

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

    addLog(`Rescheduling thread: ${node.label} metrics elevated (Multiplier: ${intensity}x, Polling: ${pollingMs}ms).`, 'success');
  };

  const handleRemoveRule = (ruleId: string) => {
    const rule = activeRules.find(r => r.id === ruleId);
    if (!rule) return;

    setActiveRules(prev => prev.filter(r => r.id !== ruleId));
    addLog(`Halted workload schedule on ${rule.nodeLabel}. Restoring base metrics...`, 'info');

    // Restore node to standard normal parameters
    setSystemNodes(prevNodes =>
      prevNodes.map(n => {
        if (n.id === rule.nodeId) {
          return {
            ...n,
            status: 'active',
            cpu: Math.floor(Math.random() * 20) + 35,
            memory: Math.floor(Math.random() * 25) + 40,
            latency: n.id === 'central-hub' ? 1.2 : Math.floor(Math.random() * 30) + 15,
          };
        }
        return n;
      })
    );

    addLog(`Baseline traffic configuration successfully restored on ${rule.nodeLabel}.`, 'success');
  };

  const handleResetAll = () => {
    setActiveRules([]);
    addLog(`Clearing all scheduling overrides. Restoring entire cluster to 1.0x baseline traffic...`, 'info');

    setSystemNodes(prevNodes =>
      prevNodes.map(n => ({
        ...n,
        status: n.id === 'node-af' ? 'offline' : 'active',
        cpu: n.id === 'node-af' ? 0 : Math.floor(Math.random() * 20) + 35,
        memory: n.id === 'node-af' ? 0 : Math.floor(Math.random() * 25) + 40,
        latency: n.id === 'central-hub' ? 1.2 : n.id === 'node-af' ? 320 : Math.floor(Math.random() * 30) + 15,
      }))
    );

    addLog(`All system traffic levels normalized to standard baseline. Override arrays empty.`, 'success');
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6" id="workload-view-root">
      {/* Workload Injection Configuration Panel */}
      <div className="lg:col-span-1 bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex flex-col justify-between h-fit">
        <div>
          <div className="flex items-center gap-2 mb-4">
            <div className="p-2 bg-indigo-50 rounded-lg text-indigo-600">
              <Sliders size={20} />
            </div>
            <h2 className="font-display font-extrabold text-lg text-slate-900">Inject Workload</h2>
          </div>

          <div className="space-y-4">
            {/* Target Select */}
            <div>
              <label className="block text-xs font-semibold text-slate-600 uppercase tracking-wider mb-2">Target Node Endpoint</label>
              <select
                value={selectedNodeId}
                onChange={(e) => setSelectedNodeId(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 px-3 py-2.5 rounded-lg text-sm text-slate-800 font-medium focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                {systemNodes.map((n) => (
                  <option key={n.id} value={n.id}>
                    {n.label} ({n.ip})
                  </option>
                ))}
              </select>
            </div>

            {/* Workload Multiplier Slider */}
            <div>
              <div className="flex justify-between text-xs font-semibold text-slate-600 uppercase tracking-wider mb-2">
                <span>Traffic Multiplier</span>
                <span className="text-indigo-600 font-mono font-bold">{intensity.toFixed(1)}x</span>
              </div>
              <input
                type="range"
                min="1.0"
                max="4.0"
                step="0.5"
                value={intensity}
                onChange={(e) => setIntensity(parseFloat(e.target.value))}
                className="w-full accent-indigo-600 cursor-pointer h-1.5 bg-slate-100 rounded-lg"
              />
              <div className="flex justify-between text-[9px] text-slate-400 font-bold uppercase mt-1">
                <span>Baseline (1x)</span>
                <span>Peak (2x)</span>
                <span>Critical (4x)</span>
              </div>
            </div>

            {/* Polling Cadence Selector */}
            <div>
              <label className="block text-xs font-semibold text-slate-600 uppercase tracking-wider mb-2">Telemetry Cadence</label>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { id: 100, label: 'Fast', desc: '100ms' },
                  { id: 500, label: 'Standard', desc: '500ms' },
                  { id: 2000, label: 'Eco', desc: '2000ms' },
                ].map((item) => (
                  <button
                    key={item.id}
                    onClick={() => setPollingMs(item.id)}
                    className={`p-2.5 border rounded-lg text-center transition-all ${
                      pollingMs === item.id
                        ? 'border-indigo-600 bg-indigo-50/40 text-indigo-950 font-semibold'
                        : 'border-slate-200 text-slate-700 hover:bg-slate-50'
                    }`}
                  >
                    <span className="text-xs block">{item.label}</span>
                    <span className="text-[9px] text-slate-500 block font-mono mt-0.5">{item.desc}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Action button */}
        <div className="mt-6 pt-4 border-t border-slate-100 space-y-2">
          <button
            onClick={handleAddRule}
            className="w-full py-3 rounded-lg text-sm font-semibold flex items-center justify-center gap-2 bg-indigo-600 text-white hover:bg-indigo-700 shadow-sm shadow-indigo-600/10 transition-all"
          >
            <Plus size={16} />
            <span>Apply Workload Scale</span>
          </button>

          {activeRules.length > 0 && (
            <button
              onClick={handleResetAll}
              className="w-full py-2 border border-slate-200 text-slate-600 hover:bg-slate-50 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors"
            >
              <RefreshCw size={13} />
              <span>Reset baseline (1.0x)</span>
            </button>
          )}
        </div>
      </div>

      {/* Active Workload Rules and Stream */}
      <div className="lg:col-span-2 space-y-6 flex flex-col justify-between">
        {/* Active Overrides Panel */}
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex-1">
          <h3 className="font-display font-extrabold text-xs text-slate-500 uppercase tracking-wider mb-4 flex items-center gap-2 border-b border-slate-100 pb-3">
            <Layers size={14} className="text-indigo-600" />
            Active Scaling Schedules ({activeRules.length})
          </h3>

          {activeRules.length === 0 ? (
            <div className="text-center py-10 border-2 border-dashed border-slate-100 rounded-xl text-slate-400 text-xs">
              All 12 nodes running standard 1.0x baseline traffic.
            </div>
          ) : (
            <div className="space-y-2 max-h-[160px] overflow-y-auto">
              {activeRules.map((r) => (
                <div key={r.id} className="flex items-center justify-between p-3 bg-indigo-50/20 border border-indigo-100 rounded-xl">
                  <div className="flex items-center gap-3">
                    <div className="h-2 w-2 bg-indigo-600 rounded-full animate-pulse" />
                    <div>
                      <p className="text-xs font-bold text-slate-800">{r.nodeLabel}</p>
                      <p className="text-[10px] text-slate-500 font-mono">
                        Multiplier: {r.intensity.toFixed(1)}x | Cadence: {r.pollingMs}ms
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => handleRemoveRule(r.id)}
                    className="text-xs font-semibold px-2.5 py-1.5 rounded-lg bg-white border border-slate-200 text-slate-600 hover:bg-slate-50 hover:border-slate-300 transition-all"
                  >
                    Halt Override
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Schedule Logs Stream */}
        <div className="bg-slate-950 text-indigo-300 font-mono text-xs rounded-xl p-5 border border-slate-900 shadow-xl flex flex-col h-[200px]">
          <div className="flex items-center justify-between border-b border-slate-900 pb-2 mb-2 select-none">
            <span className="text-[10px] font-bold tracking-widest uppercase text-slate-400">Scheduler Log Console</span>
            <div className="flex gap-1.5">
              <span className="w-2 h-2 rounded-full bg-slate-800" />
              <span className="w-2 h-2 rounded-full bg-slate-800" />
              <span className="w-2 h-2 rounded-full bg-indigo-500/80" />
            </div>
          </div>
          <div className="flex-1 overflow-y-auto space-y-1.5 pr-2 select-text text-[11px] leading-relaxed">
            {workloadLogs.map((log) => (
              <div key={log.id} className="flex items-start gap-2">
                <span className="text-slate-600 flex-shrink-0 select-none">[{log.time}]</span>
                <span className={log.type === 'success' ? 'text-emerald-400' : 'text-slate-400'}>
                  {log.msg}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
