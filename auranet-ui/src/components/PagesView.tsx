/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { 
  Server, 
  Activity, 
  AlertTriangle, 
  CheckCircle2, 
  RefreshCw, 
  Cpu, 
  Network, 
  Search,
  ExternalLink,
  Sliders,
  Trash2
} from 'lucide-react';
import { SystemNode } from '../types';

interface PagesViewProps {
  systemNodes: SystemNode[];
  setSystemNodes: React.Dispatch<React.SetStateAction<SystemNode[]>>;
  onNodeSelect: (node: SystemNode) => void;
}

export default function PagesView({
  systemNodes,
  setSystemNodes,
  onNodeSelect,
}: PagesViewProps) {
  const [search, setSearch] = useState('');
  const [filterType, setFilterType] = useState<string>('all');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [pingingNodeId, setPingingNodeId] = useState<string | null>(null);

  // Search and filter logic
  const filteredNodes = systemNodes.filter((node) => {
    const matchesSearch = 
      node.label.toLowerCase().includes(search.toLowerCase()) ||
      node.ip.includes(search) ||
      node.region.toLowerCase().includes(search.toLowerCase());
    
    const matchesType = filterType === 'all' || node.type === filterType;
    const matchesStatus = filterStatus === 'all' || node.status === filterStatus;

    return matchesSearch && matchesType && matchesStatus;
  });

  const handlePingNode = (nodeId: string) => {
    setPingingNodeId(nodeId);
    setTimeout(() => {
      setPingingNodeId(null);
      // Slower random success notification
      alert(`ICMP Ping packet successfully replied from Node ID: ${nodeId}. Status verified.`);
    }, 1200);
  };

  const handleRebootNode = (nodeId: string) => {
    if (!confirm(`Are you sure you want to reboot node ${nodeId}? This will temporarily disrupt active connections.`)) return;

    // Simulate node reboot
    setSystemNodes((prev) => 
      prev.map((n) => {
        if (n.id === nodeId) {
          return {
            ...n,
            status: 'offline',
            cpu: 0,
            memory: 0,
            latency: 999,
          };
        }
        return n;
      })
    );

    alert(`Reboot command issued. Node ${nodeId} is power cycling (Offline). It will re-synchronize in a moment.`);

    // Automatically recover node after 5 seconds
    setTimeout(() => {
      setSystemNodes((prev) => 
        prev.map((n) => {
          if (n.id === nodeId) {
            return {
              ...n,
              status: 'active',
              cpu: 34,
              memory: 45,
              latency: 18,
            };
          }
          return n;
        })
      );
    }, 5000);
  };

  const handleDeleteNode = (nodeId: string) => {
    if (!confirm(`Confirm removal of node ${nodeId} from Project Alpha registry?`)) return;
    setSystemNodes((prev) => prev.filter((n) => n.id !== nodeId));
  };

  return (
    <div className="bg-white border border-brand-border rounded-2xl shadow-sm p-6 space-y-6" id="nodes-inventory-panel">
      {/* Table Title / Statistics Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-brand-border">
        <div>
          <span className="font-mono text-xs font-bold text-slate-400 tracking-wider uppercase block select-none">
            Network Operations Center
          </span>
          <h3 className="font-display font-extrabold text-xl text-brand-text block mt-0.5">
            Registered Node Inventory & Telemetry Directory
          </h3>
        </div>

        {/* Global overview boxes */}
        <div className="flex items-center gap-3 select-none">
          <div className="px-3 py-2 bg-slate-50 border border-slate-100 rounded-xl text-center">
            <span className="font-mono text-[9px] text-slate-400 block uppercase font-bold">Total Rings</span>
            <span className="text-sm font-bold text-slate-700">{systemNodes.length} Nodes</span>
          </div>
          <div className="px-3 py-2 bg-green-50 border border-green-100 rounded-xl text-center">
            <span className="font-mono text-[9px] text-green-600 block uppercase font-bold">Healthy</span>
            <span className="text-sm font-bold text-green-700">
              {systemNodes.filter(n => n.status === 'active').length} Active
            </span>
          </div>
          <div className="px-3 py-2 bg-amber-50 border border-amber-100 rounded-xl text-center">
            <span className="font-mono text-[9px] text-amber-600 block uppercase font-bold">Alerting</span>
            <span className="text-sm font-bold text-amber-700">
              {systemNodes.filter(n => n.status !== 'active').length} Non-nominal
            </span>
          </div>
        </div>
      </div>

      {/* Query Filter Toolbar */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4" id="inventory-toolbar">
        {/* Search Input */}
        <div className="relative md:col-span-2">
          <Search size={16} className="absolute left-3 top-3 text-slate-400" />
          <input
            type="text"
            placeholder="Search nodes by name, IP, or geographic region..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-slate-50 border border-brand-border rounded-xl text-xs font-semibold focus:outline-hidden focus:bg-white focus:border-brand-primary focus:ring-2 focus:ring-indigo-100 transition-all"
            id="node-search-field"
          />
        </div>

        {/* Filter Type */}
        <div className="space-y-1">
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="w-full px-3 py-2 bg-slate-50 border border-brand-border rounded-xl text-xs font-semibold text-slate-700 focus:outline-hidden focus:bg-white cursor-pointer"
            id="node-type-filter"
          >
            <option value="all">All Types (Central/Sensor/Gateway/Compute)</option>
            <option value="central">Central Core Nodes</option>
            <option value="gateway">BGP Edge Gateways</option>
            <option value="compute">Distributed Compute Nodes</option>
            <option value="sensor">Telemetry Edge Sensors</option>
          </select>
        </div>

        {/* Filter Status */}
        <div className="space-y-1">
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="w-full px-3 py-2 bg-slate-50 border border-brand-border rounded-xl text-xs font-semibold text-slate-700 focus:outline-hidden focus:bg-white cursor-pointer"
            id="node-status-filter"
          >
            <option value="all">All Statuses (Active/Warning/Offline)</option>
            <option value="active">Active / Healthy State</option>
            <option value="warning">Warning / Peak Congestion State</option>
            <option value="offline">Offline / Timeout Failure State</option>
          </select>
        </div>
      </div>

      {/* Table Container */}
      <div className="border border-slate-100 rounded-xl overflow-hidden shadow-xs">
        <table className="w-full text-left border-collapse" id="nodes-inventory-table">
          <thead>
            <tr className="bg-slate-50 border-b border-brand-border font-mono text-[10px] text-slate-400 font-extrabold uppercase tracking-wider select-none">
              <th className="py-3 px-4">Node Profile</th>
              <th className="py-3 px-4">Type</th>
              <th className="py-3 px-4">Registry IP</th>
              <th className="py-3 px-4">Latency</th>
              <th className="py-3 px-4">CPU & Memory Usage</th>
              <th className="py-3 px-4">Status</th>
              <th className="py-3 px-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 text-xs font-sans font-semibold text-slate-700">
            {filteredNodes.length > 0 ? (
              filteredNodes.map((node) => {
                const isOffline = node.status === 'offline';
                const isWarning = node.status === 'warning';
                
                return (
                  <tr 
                    key={node.id} 
                    className="hover:bg-slate-50/40 transition-colors"
                    id={`table-row-${node.id}`}
                  >
                    {/* Node Profile */}
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-lg ${
                          isOffline ? 'bg-red-50 text-red-600' : isWarning ? 'bg-amber-50 text-amber-600' : 'bg-indigo-50 text-[#4d41df]'
                        }`}>
                          <Server size={16} />
                        </div>
                        <div>
                          <button
                            onClick={() => onNodeSelect(node)}
                            className="font-display font-bold text-slate-800 hover:text-brand-primary block text-left transition-colors cursor-pointer"
                          >
                            {node.label}
                          </button>
                          <span className="font-mono text-[9px] text-slate-400 block mt-0.5">{node.region}</span>
                        </div>
                      </div>
                    </td>

                    {/* Type */}
                    <td className="py-3 px-4">
                      <span className="font-mono font-bold uppercase text-[9px] text-slate-500 bg-slate-100 px-2 py-0.5 rounded-sm">
                        {node.type}
                      </span>
                    </td>

                    {/* Registry IP */}
                    <td className="py-3 px-4 font-mono font-medium text-slate-500">
                      {node.ip}
                    </td>

                    {/* Latency */}
                    <td className="py-3 px-4 font-mono">
                      <span className={`font-bold ${
                        isOffline ? 'text-red-500 animate-pulse' : isWarning ? 'text-amber-500' : 'text-[#00ced1]'
                      }`}>
                        {node.latency}ms
                      </span>
                    </td>

                    {/* CPU & Memory bars */}
                    <td className="py-3 px-4 max-w-[160px] select-none">
                      <div className="space-y-1.5">
                        {/* CPU */}
                        <div className="flex items-center justify-between text-[9px]">
                          <span className="font-mono text-slate-400">CPU</span>
                          <span className="font-mono font-bold text-slate-600">{node.cpu}%</span>
                        </div>
                        <div className="w-full bg-slate-100 h-1 rounded-full overflow-hidden">
                          <div 
                            style={{ width: `${node.cpu}%` }} 
                            className={`h-full rounded-full ${isOffline ? 'bg-slate-300' : isWarning ? 'bg-amber-500 animate-pulse' : 'bg-brand-primary'}`} 
                          />
                        </div>

                        {/* Memory */}
                        <div className="flex items-center justify-between text-[9px] pt-0.5">
                          <span className="font-mono text-slate-400">MEM</span>
                          <span className="font-mono font-bold text-slate-600">{node.memory}%</span>
                        </div>
                        <div className="w-full bg-slate-100 h-1 rounded-full overflow-hidden">
                          <div 
                            style={{ width: `${node.memory}%` }} 
                            className={`h-full rounded-full ${isOffline ? 'bg-slate-300' : isWarning ? 'bg-amber-400' : 'bg-cyan-500'}`} 
                          />
                        </div>
                      </div>
                    </td>

                    {/* Status Pill */}
                    <td className="py-3 px-4 select-none">
                      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-bold ${
                        isOffline 
                          ? 'bg-red-50 text-red-700' 
                          : isWarning 
                            ? 'bg-amber-50 text-amber-700' 
                            : 'bg-[#e0fbfc] text-[#006e70]'
                      }`}>
                        <span className={`h-1.5 w-1.5 rounded-full ${isOffline ? 'bg-red-500' : isWarning ? 'bg-amber-500' : 'bg-[#00ced1]'}`} />
                        {node.status.toUpperCase()}
                      </span>
                    </td>

                    {/* Actions dropdown/buttons */}
                    <td className="py-3 px-4 text-right">
                      <div className="flex items-center justify-end gap-1.5 select-none">
                        <button
                          onClick={() => handlePingNode(node.id)}
                          disabled={pingingNodeId === node.id}
                          className="px-2 py-1 bg-white hover:bg-slate-50 border border-slate-200 rounded-md text-[10px] font-mono font-bold text-slate-600 transition-colors disabled:opacity-50"
                          id={`btn-table-ping-${node.id}`}
                          title="Ping node via ICMP packet"
                        >
                          {pingingNodeId === node.id ? 'Pinging...' : 'Ping'}
                        </button>
                        <button
                          onClick={() => handleRebootNode(node.id)}
                          className="px-2 py-1 bg-white hover:bg-amber-50 border border-slate-200 hover:border-amber-200 rounded-md text-[10px] font-mono font-bold text-amber-600 transition-colors"
                          id={`btn-table-reboot-${node.id}`}
                          title="Power cycle node"
                        >
                          Reboot
                        </button>
                        {node.id !== 'central-hub' && (
                          <button
                            onClick={() => handleDeleteNode(node.id)}
                            className="p-1.5 bg-red-50 hover:bg-red-100 text-red-600 rounded-md transition-colors"
                            id={`btn-table-delete-${node.id}`}
                            title="De-register node from cluster"
                          >
                            <Trash2 size={12} />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })
            ) : (
              <tr>
                <td colSpan={7} className="py-8 px-4 text-center text-slate-400 font-medium">
                  No active system nodes matched your filter query.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
