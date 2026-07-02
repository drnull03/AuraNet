/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useEffect } from 'react';
import { ShieldAlert, ShieldCheck, Play, Skull, RefreshCw, Radio, Terminal, AlertCircle } from 'lucide-react';
import { SystemNode } from '../types';

interface AttackViewProps {
  systemNodes: SystemNode[];
  setSystemNodes: React.Dispatch<React.SetStateAction<SystemNode[]>>;
}

interface SimulatedAttack {
  id: string;
  nodeId: string;
  nodeLabel: string;
  type: 'ddos' | 'mitm' | 'intrusion';
  status: 'active' | 'mitigated';
  timestamp: string;
}

export default function AttackView({ systemNodes, setSystemNodes }: AttackViewProps) {
  const [selectedNodeId, setSelectedNodeId] = useState<string>(systemNodes[0]?.id || '');
  const [attackType, setAttackType] = useState<'ddos' | 'mitm' | 'intrusion'>('ddos');
  const [activeAttacks, setActiveAttacks] = useState<SimulatedAttack[]>([]);
  const [attackLogs, setAttackLogs] = useState<{ id: string; time: string; msg: string; type: 'info' | 'warn' | 'error' | 'success' }[]>([
    { id: '1', time: new Date().toLocaleTimeString(), msg: 'Intrusion Detection System (IDS) monitoring on 12 nodes. All clean.', type: 'success' }
  ]);

  const addLog = (msg: string, type: 'info' | 'warn' | 'error' | 'success' = 'info') => {
    setAttackLogs(prev => [
      { id: Date.now().toString(), time: new Date().toLocaleTimeString(), msg, type },
      ...prev.slice(0, 19)
    ]);
  };

  const handleLaunchAttack = () => {
    const node = systemNodes.find(n => n.id === selectedNodeId);
    if (!node) return;

    // Check if node is already being attacked
    if (activeAttacks.some(a => a.nodeId === node.id && a.status === 'active')) {
      addLog(`Cannot launch attack! Node ${node.label} is already under active exploit.`, 'error');
      return;
    }

    const newAttack: SimulatedAttack = {
      id: `attack-${Date.now()}`,
      nodeId: node.id,
      nodeLabel: node.label,
      type: attackType,
      status: 'active',
      timestamp: new Date().toLocaleTimeString(),
    };

    setActiveAttacks(prev => [newAttack, ...prev]);
    addLog(`!!! MALICIOUS EXPLOIT INITIATED !!! Target: ${node.label} (${node.ip})`, 'error');

    // Trigger state changes in the parent component
    setSystemNodes(prevNodes =>
      prevNodes.map(n => {
        if (n.id === node.id) {
          if (attackType === 'ddos') {
            return {
              ...n,
              status: 'offline',
              cpu: 100,
              memory: 98,
              latency: 480,
            };
          } else if (attackType === 'mitm') {
            return {
              ...n,
              status: 'warning',
              cpu: 75,
              memory: 88,
              latency: 220,
            };
          } else {
            return {
              ...n,
              status: 'warning',
              cpu: 95,
              memory: 55,
              latency: 140,
            };
          }
        }
        return n;
      })
    );

    // Stream logs for the attack
    setTimeout(() => {
      if (attackType === 'ddos') {
        addLog(`[SECURITY CRITICAL] Large UDP flood detected on ${node.label}. Ingress limit saturated.`, 'error');
      } else if (attackType === 'mitm') {
        addLog(`[ALERT] BGP route pollution flagged on adjacent route of ${node.label}. Handshake intercept.`, 'warn');
      } else {
        addLog(`[ALERT] Unauthorized SSH login attempt succeeded on root of ${node.label}. Root shell active.`, 'error');
      }
    }, 1000);
  };

  const handleMitigateAttack = (attackId: string) => {
    const attack = activeAttacks.find(a => a.id === attackId);
    if (!attack) return;

    addLog(`Deploying digital countermeasures and neural firewall onto ${attack.nodeLabel}...`, 'info');

    // Mitigate
    setSystemNodes(prevNodes =>
      prevNodes.map(n => {
        if (n.id === attack.nodeId) {
          return {
            ...n,
            status: 'active',
            cpu: Math.floor(Math.random() * 20) + 30, // Normal range
            memory: Math.floor(Math.random() * 20) + 40,
            latency: n.id === 'central-hub' ? 1.2 : Math.floor(Math.random() * 30) + 15,
          };
        }
        return n;
      })
    );

    setActiveAttacks(prev =>
      prev.map(a => (a.id === attackId ? { ...a, status: 'mitigated' } : a))
    );

    addLog(`Neural Firewall deployed. Malicious exploit purged from ${attack.nodeLabel}. Normal operations restored.`, 'success');
  };

  const handleMitigateAll = () => {
    const activeOnes = activeAttacks.filter(a => a.status === 'active');
    if (activeOnes.length === 0) return;

    addLog(`Global cluster purge command broadcasted to all endpoints...`, 'info');

    setSystemNodes(prevNodes =>
      prevNodes.map(n => {
        // Reset any attacked nodes to active normal
        const isAttacked = activeOnes.some(a => a.nodeId === n.id);
        if (isAttacked) {
          return {
            ...n,
            status: 'active',
            cpu: Math.floor(Math.random() * 20) + 30,
            memory: Math.floor(Math.random() * 20) + 40,
            latency: n.id === 'central-hub' ? 1.2 : Math.floor(Math.random() * 30) + 15,
          };
        }
        return n;
      })
    );

    setActiveAttacks(prev => prev.map(a => ({ ...a, status: 'mitigated' })));
    addLog(`All malicious threats purged globally. Zero active incident traces remaining.`, 'success');
  };

  const activeCount = activeAttacks.filter(a => a.status === 'active').length;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6" id="attack-view-root">
      {/* Configuration Column */}
      <div className="lg:col-span-1 bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex flex-col justify-between h-fit">
        <div>
          <div className="flex items-center gap-2 mb-4">
            <div className="p-2 bg-red-50 rounded-lg text-red-600">
              <Skull size={20} className="animate-pulse" />
            </div>
            <h2 className="font-display font-extrabold text-lg text-slate-900">Simulate Threat Vector</h2>
          </div>

          <div className="space-y-4">
            {/* Target Selector */}
            <div>
              <label className="block text-xs font-semibold text-slate-600 uppercase tracking-wider mb-2">Target Vulnerability Node</label>
              <select
                value={selectedNodeId}
                onChange={(e) => setSelectedNodeId(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 px-3 py-2.5 rounded-lg text-sm text-slate-800 font-medium focus:outline-none focus:ring-2 focus:ring-red-500"
              >
                {systemNodes.map((n) => (
                  <option key={n.id} value={n.id}>
                    {n.label} ({n.ip})
                  </option>
                ))}
              </select>
            </div>

            {/* Attack Types */}
            <div>
              <label className="block text-xs font-semibold text-slate-600 uppercase tracking-wider mb-2">Select Exploit payload</label>
              <div className="space-y-2">
                {[
                  { id: 'ddos', label: 'Distributed Denial of Service (DDoS)', desc: 'UDP flood saturating bandwidth, taking node offline', color: 'border-red-200 hover:bg-red-50/20' },
                  { id: 'mitm', label: 'BGP Route Hijacking (MitM)', desc: 'Inject false routing tables, snooping connection packets', color: 'border-amber-200 hover:bg-amber-50/20' },
                  { id: 'intrusion', label: 'Intrusion / Credentials Breach', desc: 'Symmetric key theft triggering high unauthorized CPU computing', color: 'border-rose-200 hover:bg-rose-50/20' },
                ].map((item) => (
                  <button
                    key={item.id}
                    onClick={() => setAttackType(item.id as any)}
                    className={`w-full p-3 border rounded-xl text-left transition-all flex flex-col ${
                      attackType === item.id
                        ? 'border-red-600 bg-red-50/30 text-red-950 shadow-xs ring-1 ring-red-500/20'
                        : 'border-slate-200 hover:bg-slate-50 text-slate-700'
                    }`}
                  >
                    <span className="text-xs font-bold">{item.label}</span>
                    <span className="text-[10px] text-slate-500 mt-1 leading-normal">{item.desc}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        <div className="mt-6 pt-4 border-t border-slate-100">
          <button
            onClick={handleLaunchAttack}
            className="w-full py-3 rounded-lg text-sm font-semibold flex items-center justify-center gap-2 bg-red-600 text-white hover:bg-red-700 shadow-sm shadow-red-600/10 transition-all"
          >
            <Play size={16} />
            <span>Launch Simulated Attack</span>
          </button>
        </div>
      </div>

      {/* Logging & Live Threat Monitor column */}
      <div className="lg:col-span-2 space-y-6 flex flex-col justify-between">
        
        {/* Threat Alert Panel */}
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex-1">
          
          {/* Active Alert Banner */}
          {activeCount > 0 ? (
            <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-4 animate-pulse flex items-start gap-3">
              <AlertCircle className="text-red-600 h-5 w-5 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <h4 className="text-xs font-bold text-red-800 uppercase tracking-wider">Active Exploits Detected: {activeCount}</h4>
                <p className="text-[11px] text-red-600 mt-1">
                  Intrusion shields report packet anomalies. System nodes have initiated defensive latency overrides.
                </p>
                <button
                  onClick={handleMitigateAll}
                  className="mt-3 text-xs font-bold px-3 py-1.5 bg-red-600 text-white hover:bg-red-700 rounded-lg flex items-center gap-1.5 transition-all"
                >
                  <ShieldCheck size={14} /> Deploy Global Neural Purge
                </button>
              </div>
            </div>
          ) : (
            <div className="bg-emerald-50 border border-emerald-100 text-emerald-800 rounded-xl p-4 mb-4 flex items-center gap-3">
              <ShieldCheck className="text-emerald-600 h-5 w-5" />
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider">Mesh Integrity: SECURE</h4>
                <p className="text-[11px] text-emerald-600 mt-0.5">IDS reports 0 abnormal telemetry signatures. Routing maps standard.</p>
              </div>
            </div>
          )}

          {/* Active Incident List */}
          <h3 className="font-display font-extrabold text-xs text-slate-500 uppercase tracking-wider mb-3">Threat Incident Journal</h3>
          {activeAttacks.length === 0 ? (
            <div className="text-center py-8 border-2 border-dashed border-slate-100 rounded-xl text-slate-400 text-xs">
              No historical simulated threats recorded.
            </div>
          ) : (
            <div className="space-y-2 max-h-[160px] overflow-y-auto pr-1">
              {activeAttacks.map((a) => (
                <div key={a.id} className={`flex items-center justify-between p-3 border rounded-xl ${
                  a.status === 'active' ? 'bg-red-50/30 border-red-100' : 'bg-slate-50/50 border-slate-100'
                }`}>
                  <div className="flex items-center gap-3">
                    <div className={`h-2.5 w-2.5 rounded-full ${a.status === 'active' ? 'bg-red-500 animate-ping' : 'bg-emerald-500'}`} />
                    <div>
                      <p className="text-xs font-bold text-slate-800">{a.nodeLabel}</p>
                      <p className="text-[10px] text-slate-500 font-mono font-medium">
                        {a.type.toUpperCase()} @ {a.timestamp}
                      </p>
                    </div>
                  </div>
                  {a.status === 'active' ? (
                    <button
                      onClick={() => handleMitigateAttack(a.id)}
                      className="text-xs font-bold px-2.5 py-1.5 bg-indigo-600 text-white hover:bg-indigo-700 rounded-lg flex items-center gap-1 transition-all"
                    >
                      <ShieldCheck size={13} /> Resolve Threat
                    </button>
                  ) : (
                    <span className="text-xs font-mono font-bold text-emerald-600 uppercase bg-emerald-50 px-2.5 py-1 rounded-full">
                      Purged
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Security Terminal Logs */}
        <div className="bg-slate-950 text-emerald-400 font-mono text-xs rounded-xl p-5 border border-slate-900 shadow-xl flex flex-col h-[200px]">
          <div className="flex items-center justify-between border-b border-slate-900 pb-2 mb-2 select-none text-slate-500">
            <span className="text-[10px] font-bold tracking-widest uppercase flex items-center gap-1.5">
              <Terminal size={12} className="text-emerald-500" /> Intrusion Defense System (IDS) Terminal
            </span>
            <span className="text-[9px] font-mono select-none">root@project-alpha-ids:~#</span>
          </div>
          <div className="flex-1 overflow-y-auto space-y-1.5 pr-2 select-text text-[11px] leading-relaxed">
            {attackLogs.map((log) => (
              <div key={log.id} className="flex items-start gap-2">
                <span className="text-slate-600 flex-shrink-0 select-none">[{log.time}]</span>
                <span className={`${
                  log.type === 'error' ? 'text-red-500' : log.type === 'warn' ? 'text-amber-400' : log.type === 'success' ? 'text-emerald-400' : 'text-slate-400'
                }`}>
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
