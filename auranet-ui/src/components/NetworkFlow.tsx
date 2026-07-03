/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { 
  ReactFlow, 
  Background, 
  Controls, 
  useNodesState, 
  useEdgesState, 
  MarkerType,
  Handle,
  Position,
  Node,
  Edge
} from '@xyflow/react';
import { motion, AnimatePresence } from 'motion/react';
import { Play, Pause, Plus, ShieldCheck, Cpu, Database, WifiOff, AlertTriangle } from 'lucide-react';
import { SystemNode } from '../types';
import { INITIAL_NODES } from '../data';

// Custom Satellite Node Component
const SatelliteNodeComponent = ({ data }: any) => {
  const { label, type, status } = data;
  
  const getStatusColor = () => {
    if (status === 'offline') return 'bg-red-700 border-red-500 shadow-red-700/30';
    if (status === 'warning') return 'bg-amber-600 border-amber-500 shadow-amber-600/30';
    return 'bg-cyan-700 border-cyan-500 shadow-cyan-700/30'; // Dark cyan
  };

  return (
    <div className="flex flex-col items-center group">
      {/* Node Core */}
      <div className={`h-12 w-12 rounded-full ${getStatusColor()} border-3 flex items-center justify-center shadow-lg transition-transform duration-200 group-hover:scale-110 z-10`}>
        {status === 'offline' ? (
          <WifiOff size={16} className="text-white" />
        ) : type === 'sensor' || type === 'gateway' ? (
          <Cpu size={16} className="text-white animate-pulse" />
        ) : (
          <Database size={16} className="text-white" />
        )}
      </div>

      {/* Label Box */}
      <div className="mt-1.5 bg-white/90 backdrop-blur-xs border border-brand-border px-2 py-0.5 rounded-md text-[10px] font-mono font-bold text-slate-800 shadow-xs whitespace-nowrap z-20">
        {label}
      </div>

      {/* Explicitly pin the handles 24px from the top (center of the 48px circle) */}
      <Handle 
        type="target" 
        position={Position.Left} 
        className="opacity-0" 
        style={{ top: '24px' }} 
      />
      <Handle 
        type="source" 
        position={Position.Right} 
        className="opacity-0" 
        style={{ top: '24px' }} 
      />
    </div>
  );
};

interface NetworkFlowProps {
  systemNodes: SystemNode[];
  setSystemNodes: React.Dispatch<React.SetStateAction<SystemNode[]>>;
  onNodeSelect: (node: SystemNode) => void;
  selectedNode: SystemNode | null;
}

export default function NetworkFlow({
  systemNodes,
  setSystemNodes,
  onNodeSelect,
  selectedNode,
}: NetworkFlowProps) {
  // Define custom node types
  const nodeTypes = useMemo(() => ({
    satelliteNode: SatelliteNodeComponent,
  }), []);

  const [isAuraNetHealthy, setIsAuraNetHealthy] = useState<boolean>(false);

  // Dynamically position nodes based on their role to create a left-to-right flow
  const getInitialNodes = useCallback(() => {
    // Keep track of how many nodes are in each column to stack them vertically
    const tierCounts: Record<number, number> = { 0: 0, 1: 0, 2: 0, 3: 0 };

    return systemNodes.map((node) => {
      let tier = 2; // Default to middle
      const lbl = node.label.toLowerCase();
      
      // Basic heuristics to auto-layout the naive.conf map
      if (lbl.includes('ui') || lbl.includes('frontend')) tier = 0;
      else if (lbl.includes('gateway')) tier = 1;
      else if (lbl.includes('service') || lbl.includes('backend')) tier = 2;
      else if (lbl.includes('db') || lbl.includes('finance')) tier = 3;

      const x = 100 + (tier * 250); // 250px horizontal gap between columns
      const y = 150 + (tierCounts[tier] * 150); // 150px vertical gap between stacked nodes
      tierCounts[tier]++;

      return {
        id: node.id,
        type: 'satelliteNode', 
        position: { x, y },
        data: { 
          label: node.label, 
          type: node.type, 
          status: node.status,
          cpu: node.cpu
        },
      } as Node;
    });
  }, [systemNodes]);

  // Dynamically draw edges based on the connections array
  const getInitialEdges = useCallback(() => {
    const edges: Edge[] = [];
    systemNodes.forEach((node) => {
      if (!node.connections) return;
      
      node.connections.forEach(targetId => {
        const targetNode = systemNodes.find(n => n.id === targetId);
        const isOffline = targetNode?.status === 'offline' || node.status === 'offline';
        const isWarning = targetNode?.status === 'warning' || node.status === 'warning';
        
        edges.push({
          id: `edge-${node.id}-${targetId}`,
          source: node.id,
          target: targetId,
          type: 'straight', // Force straight lines
          animated: !isOffline,
          style: { 
            stroke: isOffline ? '#991b1b' : isWarning ? '#b45309' : '#475569',
            strokeWidth: isOffline ? 1.5 : 2.5,
            opacity: isOffline ? 0.6 : 0.95
          },
          markerEnd: {
            type: MarkerType.ArrowClosed,
            width: 20, // Large, visible arrows
            height: 20,
            color: isOffline ? '#991b1b' : isWarning ? '#b45309' : '#475569'
          }
        });
      });
    });
    return edges;
  }, [systemNodes]);

  const [nodes, setNodes, onNodesChange] = useNodesState(getInitialNodes());
  const [edges, setEdges, onEdgesChange] = useEdgesState(getInitialEdges());

  // Cluster Sync Effect
  useEffect(() => {
    const fetchTopology = async () => {
      try {
        const response = await fetch('/api/topology');
        const data = await response.json();
        
        if (data.systemNodes) {
          setSystemNodes(data.systemNodes); 
          setIsAuraNetHealthy(data.auranetHealth);
        }
      } catch (error) {
        console.error("Failed to fetch cluster topology:", error);
      }
    };

    fetchTopology();
    // Poll the backend every 5 seconds to keep UI synced with live K8s cluster
    const interval = setInterval(fetchTopology, 5000); 
    return () => clearInterval(interval);
  }, [setSystemNodes]);

  // Keep React Flow visualizer in sync when systemNodes change
  useEffect(() => {
    setNodes(getInitialNodes());
    setEdges(getInitialEdges());
  }, [systemNodes, getInitialNodes, getInitialEdges, setNodes, setEdges]);

  const onNodeClick = useCallback((event: React.MouseEvent, flowNode: Node) => {
    const originalNode = systemNodes.find(n => n.id === flowNode.id);
    if (originalNode) {
      onNodeSelect(originalNode);
    }
  }, [systemNodes, onNodeSelect]);

  const [pulseActive, setPulseActive] = useState(true);

  // Active node logic
  const activeNodes = systemNodes.filter(n => n.status !== 'offline');
  const avgLatency = Math.round(
    activeNodes.reduce((acc, curr) => acc + curr.latency, 0) / (activeNodes.length || 1)
  );

  return (
    <div className="bg-white border border-brand-border rounded-2xl shadow-sm p-5 flex flex-col h-[640px]" id="network-topology-card">
      
      {/* Card Header controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-brand-border mb-4">
        <div>
          <span className="font-mono text-xs font-bold text-slate-400 tracking-wider uppercase block select-none">
            Live Cluster Topology
          </span>
          <div className="flex items-center gap-2 mt-1">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-[#e0fbfc] text-[#006e70]">
              <span className="h-2 w-2 rounded-full bg-[#00ced1] animate-pulse" />
              Active Pods: {activeNodes.length}/{systemNodes.length}
            </span>
            
            {/* Live AuraNet Health Badge */}
            <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold text-white shadow-sm transition-colors ${
              isAuraNetHealthy ? 'bg-emerald-500' : 'bg-red-600 animate-pulse'
            }`}>
              {isAuraNetHealthy ? <ShieldCheck size={14} /> : <AlertTriangle size={14} />}
              AuraNet: {isAuraNetHealthy ? 'Active & Protecting' : 'Offline / Unreachable'}
            </span>
          </div>
        </div>

        {/* Toolbar buttons */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setPulseActive(!pulseActive)}
            className={`p-2 rounded-lg border transition-all text-xs font-semibold flex items-center gap-1.5 ${
              pulseActive 
                ? 'bg-[#e3dfff] text-brand-primary border-indigo-200 hover:bg-indigo-100' 
                : 'bg-slate-50 text-slate-500 border-slate-200 hover:bg-slate-100'
            }`}
          >
            {pulseActive ? <Pause size={14} /> : <Play size={14} />}
            <span>{pulseActive ? 'Polling Cluster' : 'Paused'}</span>
          </button>
        </div>
      </div>

      {/* Main flow layout */}
      <div className="flex-1 min-h-[400px] border border-slate-100 rounded-xl relative overflow-hidden bg-slate-50/50">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={onNodeClick}
          fitView
          fitViewOptions={{ padding: 0.15 }}
          zoomOnScroll={false}
          panOnDrag={true}
          preventScrolling={true}
        >
          <Background color="#cbd5e1" gap={16} size={1} />
          <Controls showInteractive={false} position="bottom-right" />
        </ReactFlow>

        {/* Latency Floating Badge */}
        <div className="absolute bottom-4 left-4 bg-white/95 backdrop-blur-xs border border-brand-border rounded-xl p-3 shadow-lg select-none z-30">
          <span className="font-mono text-[9px] font-bold text-slate-400 tracking-wider uppercase block">
            Average Latency
          </span>
          <span className="font-display font-extrabold text-xl text-brand-primary block leading-none mt-1">
            {avgLatency}ms
          </span>
        </div>
      </div>

      {/* Selected Node Details Tray */}
      <AnimatePresence>
        {selectedNode && (
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 30 }}
            className="mt-4 bg-[#f8f9fa] border border-brand-border rounded-xl p-3 flex flex-wrap items-center justify-between gap-3 relative"
          >
            <div className="flex items-center gap-3">
              <div className={`h-8 w-8 rounded-full flex items-center justify-center text-white ${
                selectedNode.status === 'offline' 
                  ? 'bg-red-500' 
                  : selectedNode.status === 'warning' 
                    ? 'bg-amber-500' 
                    : 'bg-[#4d41df]'
              }`}>
                {selectedNode.type === 'compute' ? <Database size={14} /> : <Cpu size={14} />}
              </div>
              <div>
                <h4 className="font-sans font-bold text-sm text-slate-800">{selectedNode.label}</h4>
                <p className="font-mono text-[10px] text-slate-500">IP: {selectedNode.ip} | Region: {selectedNode.region}</p>
              </div>
            </div>

            <div className="flex gap-4 items-center pr-4">
              <div className="text-center font-mono select-none">
                <span className="text-[9px] text-slate-400 block uppercase font-bold">CPU Usage</span>
                <span className="text-xs font-bold text-slate-700">{selectedNode.cpu}%</span>
              </div>
              <div className="text-center font-mono select-none">
                <span className="text-[9px] text-slate-400 block uppercase font-bold">Memory</span>
                <span className="text-xs font-bold text-slate-700">{selectedNode.memory}%</span>
              </div>
              <div className="text-center font-mono select-none">
                <span className="text-[9px] text-slate-400 block uppercase font-bold">Latency</span>
                <span className={`text-xs font-bold ${
                  selectedNode.latency > 150 ? 'text-red-500' : 'text-[#00ced1]'
                }`}>{selectedNode.latency}ms</span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}