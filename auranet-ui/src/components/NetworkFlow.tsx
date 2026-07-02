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
import { Play, Pause, RefreshCw, Plus, ShieldCheck, Cpu, Database, WifiOff } from 'lucide-react';
import { SystemNode } from '../types';
import { INITIAL_NODES } from '../data';

// Custom Central Node component
const CentralNodeComponent = ({ data }: any) => {
  return (
    <div className="relative flex items-center justify-center">
      {/* Ripple Rings */}
      <div className="absolute inset-0 h-20 w-20 bg-indigo-500/20 rounded-full animate-ping pointer-events-none" />
      <div className="absolute -inset-4 h-24 w-24 border-2 border-indigo-400/40 rounded-full pointer-events-none" />
      
      {/* Node Body */}
      <div className="h-16 w-16 bg-[#4d41df] text-white rounded-full flex flex-col items-center justify-center border-4 border-indigo-300 shadow-xl z-10 select-none">
        <Database size={20} className="text-white animate-pulse" />
        <span className="font-display font-extrabold text-[9px] mt-0.5 tracking-tight uppercase">Hub</span>
      </div>
      
      {/* Central Handle */}
      <Handle type="source" position={Position.Bottom} className="opacity-0" />
      <Handle type="target" position={Position.Top} className="opacity-0" />
    </div>
  );
};

// Custom Satellite Node Component
const SatelliteNodeComponent = ({ data }: any) => {
  const { label, type, status, cpu } = data;
  
  const getStatusColor = () => {
    if (status === 'offline') return 'bg-red-700 border-red-500 shadow-red-700/30';
    if (status === 'warning') return 'bg-amber-600 border-amber-500 shadow-amber-600/30';
    return 'bg-cyan-700 border-cyan-500 shadow-cyan-700/30'; // Darker cyan (was #00ced1)
  };

  return (
    <div className="flex flex-col items-center group">
      {/* Node Core */}
      <div className={`h-12 w-12 rounded-full ${getStatusColor()} border-3 flex items-center justify-center shadow-lg transition-transform duration-200 group-hover:scale-110 z-10`}>
        {status === 'offline' ? (
          <WifiOff size={16} className="text-white" />
        ) : type === 'sensor' ? (
          <Cpu size={16} className="text-white animate-pulse" />
        ) : (
          <div className="h-4 w-4 bg-white/40 rounded-full animate-ping pointer-events-none absolute" />
        )}
      </div>

      {/* Label Box (Only on hover, or compact text) */}
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
    centralNode: CentralNodeComponent,
    satelliteNode: SatelliteNodeComponent,
  }), []);

  // Set up React Flow elements from systemNodes
  const getInitialNodes = useCallback(() => {
    return systemNodes.map((node) => {
      // Position calculation for a circular/radial layout
      let x = 300;
      let y = 300;

      if (node.id === 'central-hub') {
        x = 300;
        y = 300;
      } else {
        // Arrange outer nodes in a circle around center (300, 300)
        const outerNodes = systemNodes.filter(n => n.id !== 'central-hub');
        const index = outerNodes.findIndex(n => n.id === node.id);
        const total = outerNodes.length;
        const angle = (index * 2 * Math.PI) / total - Math.PI / 2; // offset to top-aligned start
        const radius = 220; // Radius of topology star
        
        x = 300 + radius * Math.cos(angle);
        y = 300 + radius * Math.sin(angle);
      }

      return {
        id: node.id,
        type: node.id === 'central-hub' ? 'centralNode' : 'satelliteNode',
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

  const getInitialEdges = useCallback(() => {
    const edges: Edge[] = [];
    systemNodes.forEach((node) => {
      if (node.id !== 'central-hub') {
        const isOffline = node.status === 'offline';
        const isWarning = node.status === 'warning';
        
        edges.push({
          id: `edge-${node.id}`,
          source: 'central-hub',
          target: node.id,
          type: 'straight',
          animated: !isOffline,
          style: { 
            stroke: isOffline 
              ? '#991b1b' 
              : isWarning 
                ? '#b45309' 
                : '#475569',
            strokeWidth: isOffline ? 1.5 : 2.5,
            opacity: isOffline ? 0.4 : 0.85
          },
        });
      }
    });
    return edges;
  }, [systemNodes]);

  const [nodes, setNodes, onNodesChange] = useNodesState(getInitialNodes());
  const [edges, setEdges, onEdgesChange] = useEdgesState(getInitialEdges());

  // Update flow elements when our parent state changes
  // Inside NetworkFlow.tsx component
  useEffect(() => {
    const fetchTopology = async () => {
      try {
        const response = await fetch('/api/topology');
        const data = await response.json();
        
        if (data.nodes && data.edges) {
          setNodes(data.nodes);
          setEdges(data.edges);
          // Also update parent state so other views have the nodes
          setSystemNodes(data.nodes);
        }
      } catch (error) {
        console.error("Failed to fetch topology:", error);
      }
    };

    fetchTopology();
  }, []);

  // When node is clicked in React Flow
  const onNodeClick = useCallback((event: React.MouseEvent, flowNode: Node) => {
    const originalNode = systemNodes.find(n => n.id === flowNode.id);
    if (originalNode) {
      onNodeSelect(originalNode);
    }
  }, [systemNodes, onNodeSelect]);

  // Handle adding a new node to the system
  const handleAddNewNode = () => {
    const labels = ['Nordic Compute', 'Oceania Beacon', 'Canada Sensor', 'S.E. Asia Gateway'];
    const regions = ['Norway (Oslo)', 'Australia (Sydney)', 'Canada (Montreal)', 'Singapore (Jurong)'];
    const types: ('sensor' | 'gateway' | 'compute')[] = ['sensor', 'gateway', 'compute'];
    
    const randomIndex = Math.floor(Math.random() * labels.length);
    const id = `node-${Date.now()}`;
    
    const newNode: SystemNode = {
      id,
      label: labels[randomIndex],
      type: types[Math.floor(Math.random() * types.length)],
      status: 'active',
      latency: Math.floor(Math.random() * 45) + 5,
      region: regions[randomIndex],
      ip: `192.168.${Math.floor(Math.random() * 5) + 5}.${Math.floor(Math.random() * 254) + 1}`,
      cpu: Math.floor(Math.random() * 40) + 10,
      memory: Math.floor(Math.random() * 50) + 20,
      connections: ['central-hub'],
    };

    setSystemNodes(prev => [...prev, newNode]);
    onNodeSelect(newNode);
  };

  // Simulated node state pulsing
  const [pulseActive, setPulseActive] = useState(true);
  useEffect(() => {
    if (!pulseActive) return;

    const interval = setInterval(() => {
      setSystemNodes((prev) => 
        prev.map((node) => {
          if (node.status === 'offline') return node;
          
          // Random slight fluctuation in CPU & Latency to make the dashboard feel real
          const cpuDelta = Math.floor(Math.random() * 7) - 3;
          const latencyDelta = Math.floor(Math.random() * 5) - 2;

          return {
            ...node,
            cpu: Math.max(5, Math.min(99, node.cpu + cpuDelta)),
            latency: Math.max(1, Math.min(250, node.latency + latencyDelta)),
          };
        })
      );
    }, 4000);

    return () => clearInterval(interval);
  }, [pulseActive, setSystemNodes]);

  // Average Latency of active nodes
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
            System Network Topology
          </span>
          <div className="flex items-center gap-2 mt-1">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-[#e0fbfc] text-[#006e70]">
              <span className="h-2 w-2 rounded-full bg-[#00ced1] animate-pulse" />
              Active Nodes: {systemNodes.filter(n => n.status !== 'offline').length}/{systemNodes.length}
            </span>
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-indigo-50 text-indigo-700">
              <ShieldCheck size={12} />
              Status: Stable
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
            title={pulseActive ? "Pause simulated network fluctuations" : "Resume simulated network fluctuations"}
            id="btn-toggle-pulse"
          >
            {pulseActive ? <Pause size={14} /> : <Play size={14} />}
            <span>{pulseActive ? 'Live Sync' : 'Paused'}</span>
          </button>

          <button
            onClick={handleAddNewNode}
            className="p-2 bg-[#4d41df] hover:bg-indigo-600 text-white rounded-lg border border-indigo-500 shadow-sm transition-all text-xs font-semibold flex items-center gap-1.5 hover:scale-[1.02]"
            id="btn-add-node"
          >
            <Plus size={14} />
            <span>Add Node</span>
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
          id="react-flow-instance"
        >
          <Background color="#cbd5e1" gap={16} size={1} />
          <Controls showInteractive={false} position="bottom-right" />
        </ReactFlow>

        {/* Latency Floating Badge - bottom left */}
        <div 
          className="absolute bottom-4 left-4 bg-white/95 backdrop-blur-xs border border-brand-border rounded-xl p-3 shadow-lg select-none z-30"
          id="floating-latency-badge"
        >
          <span className="font-mono text-[9px] font-bold text-slate-400 tracking-wider uppercase block">
            Average Latency
          </span>
          <span className="font-display font-extrabold text-xl text-brand-primary block leading-none mt-1">
            {avgLatency}ms
          </span>
        </div>
      </div>

      {/* Selected Node Details Tray (Interactive expansion) */}
      <AnimatePresence>
        {selectedNode && (
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 30 }}
            className="mt-4 bg-[#f8f9fa] border border-brand-border rounded-xl p-3 flex flex-wrap items-center justify-between gap-3 relative"
            id="selected-node-tray"
          >
            <div className="flex items-center gap-3">
              <div className={`h-8 w-8 rounded-full flex items-center justify-center text-white ${
                selectedNode.status === 'offline' 
                  ? 'bg-red-500' 
                  : selectedNode.status === 'warning' 
                    ? 'bg-amber-500' 
                    : 'bg-[#4d41df]'
              }`}>
                {selectedNode.type === 'central' ? <Database size={14} /> : <Cpu size={14} />}
              </div>
              <div>
                <h4 className="font-sans font-bold text-sm text-slate-800">{selectedNode.label}</h4>
                <p className="font-mono text-[10px] text-slate-500">IP: {selectedNode.ip} | Region: {selectedNode.region}</p>
              </div>
            </div>

            <div className="flex gap-4 items-center">
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
              
              {/* Actions on Node */}
              {selectedNode.id !== 'central-hub' && (
                <div className="flex items-center gap-1.5 border-l border-slate-200 pl-3">
                  <button
                    onClick={() => {
                      setSystemNodes(prev => prev.map(n => {
                        if (n.id === selectedNode.id) {
                          const nextStatus = n.status === 'active' ? 'warning' : n.status === 'warning' ? 'offline' : 'active';
                          const latency = nextStatus === 'offline' ? 320 : nextStatus === 'warning' ? 95 : 15;
                          const cpu = nextStatus === 'offline' ? 0 : nextStatus === 'warning' ? 94 : 35;
                          const memory = nextStatus === 'offline' ? 0 : nextStatus === 'warning' ? 88 : 45;
                          const updated = { ...n, status: nextStatus, latency, cpu, memory };
                          onNodeSelect(updated);
                          return updated;
                        }
                        return n;
                      }));
                    }}
                    className="px-2 py-1 text-[10px] font-mono font-bold bg-white hover:bg-slate-100 border border-slate-200 rounded text-slate-700"
                    id="btn-toggle-node-state"
                  >
                    Toggle State
                  </button>
                  <button
                    onClick={() => {
                      setSystemNodes(prev => prev.filter(n => n.id !== selectedNode.id));
                      onNodeSelect(INITIAL_NODES[0]); // Reset to central hub
                    }}
                    className="px-2 py-1 text-[10px] font-mono font-bold bg-red-50 hover:bg-red-100 border border-red-200 rounded text-red-600"
                    id="btn-delete-node"
                  >
                    Remove
                  </button>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
