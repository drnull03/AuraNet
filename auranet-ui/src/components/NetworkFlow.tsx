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
import { Play, Pause, Plus, ShieldCheck, Cpu, Database, WifiOff, AlertTriangle, Layers, Server } from 'lucide-react';
import { SystemNode, K8sNode, AuraNode } from '../types';

// Custom Central Node component
const CentralNodeComponent = ({ data }: any) => {
  return (
    <div className="relative flex items-center justify-center">
      <div className="absolute inset-0 h-20 w-20 bg-indigo-500/20 rounded-full animate-ping pointer-events-none" />
      <div className="absolute -inset-4 h-24 w-24 border-2 border-indigo-400/40 rounded-full pointer-events-none" />
      <div className="h-16 w-16 bg-[#4d41df] text-white rounded-full flex flex-col items-center justify-center border-4 border-indigo-300 shadow-xl z-10 select-none">
        <Database size={20} className="text-white animate-pulse" />
        <span className="font-display font-extrabold text-[9px] mt-0.5 tracking-tight uppercase">Hub</span>
      </div>
      <Handle type="source" position={Position.Right} className="opacity-0" style={{ top: '32px' }} />
      <Handle type="target" position={Position.Left} className="opacity-0" style={{ top: '32px' }} />
    </div>
  );
};

// Custom Satellite Node Component
const SatelliteNodeComponent = ({ data }: any) => {
  const { label, type, status, isPhysicalNode, isAuraNet } = data;
  
  const getStatusColor = () => {
    if (status === 'offline') return 'bg-red-700 border-red-500 shadow-red-700/30';
    if (status === 'warning') return 'bg-amber-600 border-amber-500 shadow-amber-600/30';
    return 'bg-cyan-700 border-cyan-500 shadow-cyan-700/30';
  };

  return (
    <div className="flex flex-col items-center group">
      {/* Node Core */}
      <div className={`relative h-12 w-12 rounded-full ${getStatusColor()} border-3 flex items-center justify-center shadow-lg transition-transform duration-200 group-hover:scale-110 z-10 ${isPhysicalNode ? 'rounded-lg' : 'rounded-full'}`}>
        {status === 'offline' ? (
          <WifiOff size={16} className="text-white" />
        ) : isAuraNet ? (
          <ShieldCheck size={16} className="text-white" />
        ) : isPhysicalNode ? (
          <Server size={16} className="text-white" />
        ) : type === 'sensor' || type === 'gateway' ? (
          <Cpu size={16} className="text-white animate-pulse" />
        ) : (
          <Database size={16} className="text-white" />
        )}

        {isAuraNet && status === 'active' && (
          <div className="absolute -top-1 -right-1 h-3.5 w-3.5 bg-emerald-400 rounded-full border-2 border-white animate-pulse shadow-sm" title="AuraNet Component Active" />
        )}
      </div>

      {/* Label Box */}
      <div className="mt-1.5 bg-white/90 backdrop-blur-xs border border-brand-border px-2 py-0.5 rounded-md text-[10px] font-mono font-bold text-slate-800 shadow-xs whitespace-nowrap z-20 flex flex-col items-center">
        <span>{label}</span>
        {isPhysicalNode && <span className="text-[8px] text-slate-500 font-normal">Hardware Node</span>}
      </div>

      {/* Place handles perfectly in the center of the 48x48 icon (top: 24px) */}
      <Handle type="target" position={Position.Top} className="opacity-0" style={{ left: '50%', top: '24px', transform: 'translate(-50%, -50%)' }} />
      <Handle type="source" position={Position.Bottom} className="opacity-0" style={{ left: '50%', top: '24px', transform: 'translate(-50%, -50%)' }} />
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
  const nodeTypes = useMemo(() => ({
    centralNode: CentralNodeComponent,
    satelliteNode: SatelliteNodeComponent,
  }), []);

  const [isAuraNetHealthy, setIsAuraNetHealthy] = useState<boolean>(false);
  const [pulseActive, setPulseActive] = useState(true);
  
  // Real Kubernetes Node State
  const [k8sNodes, setK8sNodes] = useState<K8sNode[]>([]);
  const [auranetNodes, setAuraNetNodes] = useState<AuraNode[]>([]);
  
  // View Mode State
  const [viewMode, setViewMode] = useState<'workloads' | 'nodes' | 'auranet'>('workloads');

  // Set up React Flow elements based on View Mode
  const getInitialNodes = useCallback(() => {
    if (viewMode === 'workloads') {
      const tierCounts: Record<number, number> = { 0: 0, 1: 0, 2: 0, 3: 0 };
      return systemNodes.map((node) => {
        let tier = 2; // Default to middle
        const lbl = node.label.toLowerCase();
        
        if (lbl.includes('ui') || lbl.includes('frontend')) tier = 0;
        else if (lbl.includes('gateway')) tier = 1;
        else if (lbl.includes('service') || lbl.includes('backend')) tier = 2;
        else if (lbl.includes('db') || lbl.includes('finance')) tier = 3;

        const x = 100 + (tier * 250); 
        const y = 150 + (tierCounts[tier] * 150); 
        tierCounts[tier]++;

        return {
          id: node.id,
          type: node.id === 'central-hub' ? 'centralNode' : 'satelliteNode',
          position: { x, y },
          data: { label: node.label, type: node.type, status: node.status, cpu: node.cpu, isPhysicalNode: false },
        } as Node;
      });
    } else if (viewMode === 'nodes') {
      // NODE VIEW: Map directly from `kubectl get nodes` fetch
      return k8sNodes.map((node, index) => {
        return {
          id: `k8s-${node.id}`,
          type: 'satelliteNode',
          // Staggered horizontal layout for actual nodes
          position: { x: 200 + (index * 220), y: 250 + (index % 2 === 0 ? -50 : 50) },
          data: { label: node.name, type: 'compute', status: node.status, cpu: node.cpu, isPhysicalNode: true },
        } as Node;
      });
    } else {
      // AURANET VIEW: Map directly from `kubectl get pods -n auranet-namespace`
      const controllers = auranetNodes.filter(n => n.name.includes('controller'));
      const ztcs = auranetNodes.filter(n => n.name.includes('ztc'));
      const autoheals = auranetNodes.filter(n => n.name.includes('autoheal'));
      const engines = auranetNodes.filter(n => n.name.includes('engine'));
      const runtimes = auranetNodes.filter(n => n.name.includes('runtime'));
      const others = auranetNodes.filter(n => !n.name.includes('controller') && !n.name.includes('ztc') && !n.name.includes('autoheal') && !n.name.includes('engine') && !n.name.includes('runtime'));
      
      const nodes: Node[] = [];
      
      controllers.forEach((c, idx) => nodes.push({
        id: `aura-${c.id}`, type: 'satelliteNode', position: { x: 400 + (idx * 200), y: 50 },
        data: { label: c.name, type: 'compute', status: c.status, cpu: c.cpu, isPhysicalNode: false, isAuraNet: true }
      }));

      ztcs.forEach((z, idx) => nodes.push({
        id: `aura-${z.id}`, type: 'satelliteNode', position: { x: 250 + (idx * 200), y: 200 },
        data: { label: z.name, type: 'compute', status: z.status, cpu: z.cpu, isPhysicalNode: false, isAuraNet: true }
      }));

      autoheals.forEach((a, idx) => nodes.push({
        id: `aura-${a.id}`, type: 'satelliteNode', position: { x: 600 + (idx * 200), y: 200 },
        data: { label: a.name, type: 'compute', status: a.status, cpu: a.cpu, isPhysicalNode: false, isAuraNet: true }
      }));

      engines.forEach((e, idx) => nodes.push({
        id: `aura-${e.id}`, type: 'satelliteNode', position: { x: 100 + (idx * 250), y: 350 },
        data: { label: e.name, type: 'compute', status: e.status, cpu: e.cpu, isPhysicalNode: false, isAuraNet: true }
      }));

      runtimes.forEach((r, idx) => nodes.push({
        id: `aura-${r.id}`, type: 'satelliteNode', position: { x: 650 + (idx * 250), y: 350 },
        data: { label: r.name, type: 'compute', status: r.status, cpu: r.cpu, isPhysicalNode: false, isAuraNet: true }
      }));

      others.forEach((o, idx) => nodes.push({
        id: `aura-${o.id}`, type: 'satelliteNode', position: { x: 850 + (idx * 200), y: 50 },
        data: { label: o.name, type: 'compute', status: o.status, cpu: o.cpu, isPhysicalNode: false, isAuraNet: true }
      }));
      
      return nodes;
    }
  }, [systemNodes, k8sNodes, auranetNodes, viewMode]);

  const getInitialEdges = useCallback(() => {
    const edges: Edge[] = [];
    if (viewMode === 'workloads') {
      systemNodes.forEach((node) => {
        if (!node.connections) return;
        node.connections.forEach(targetId => {
          const targetNode = systemNodes.find(n => n.id === targetId);
          if (!targetNode) return;
          const isOffline = targetNode.status === 'offline' || node.status === 'offline';
          const isWarning = targetNode.status === 'warning' || node.status === 'warning';
          
          edges.push({
            id: `edge-${node.id}-${targetId}`,
            source: node.id,
            target: targetId,
            type: 'straight',
            animated: !isOffline,
            style: { 
              stroke: isOffline ? '#991b1b' : isWarning ? '#b45309' : '#475569',
              strokeWidth: isOffline ? 1.5 : 2.5,
              opacity: isOffline ? 0.6 : 0.95
            },
            markerEnd: { type: MarkerType.ArrowClosed, width: 20, height: 20, color: isOffline ? '#991b1b' : isWarning ? '#b45309' : '#475569' }
          });
        });
      });
    } else if (viewMode === 'auranet') {
      const controllers = auranetNodes.filter(n => n.name.includes('controller'));
      const engines = auranetNodes.filter(n => n.name.includes('engine'));
      const ztcs = auranetNodes.filter(n => n.name.includes('ztc'));
      const autoheals = auranetNodes.filter(n => n.name.includes('autoheal'));
      const runtimes = auranetNodes.filter(n => n.name.includes('runtime'));
      
      // 1. engine -> controller
      engines.forEach(engine => {
        controllers.forEach(controller => {
          edges.push({
            id: `edge-eng-ctrl-${engine.id}-${controller.id}`,
            source: `aura-${engine.id}`,
            target: `aura-${controller.id}`,
            type: 'straight',
            animated: true,
            style: { stroke: '#10b981', strokeWidth: 2, opacity: 0.8 },
            markerEnd: { type: MarkerType.ArrowClosed, width: 20, height: 20, color: '#10b981' }
          });
        });
      });

      // 2. ztc <-> autoheal (Two-headed connection)
      ztcs.forEach(ztc => {
        autoheals.forEach(autoheal => {
          edges.push({
            id: `edge-ztc-auto-${ztc.id}-${autoheal.id}`,
            source: `aura-${ztc.id}`,
            target: `aura-${autoheal.id}`,
            type: 'straight',
            animated: true,
            style: { stroke: '#0ea5e9', strokeWidth: 2, opacity: 0.8 },
            markerStart: { type: MarkerType.ArrowClosed, width: 20, height: 20, color: '#0ea5e9' },
            markerEnd: { type: MarkerType.ArrowClosed, width: 20, height: 20, color: '#0ea5e9' }
          });
        });
      });

      // 3. engine -> ztc
      engines.forEach(engine => {
        ztcs.forEach(ztc => {
          edges.push({
            id: `edge-eng-ztc-${engine.id}-${ztc.id}`,
            source: `aura-${engine.id}`,
            target: `aura-${ztc.id}`,
            type: 'straight',
            animated: true,
            style: { stroke: '#f59e0b', strokeWidth: 2, opacity: 0.8 },
            markerEnd: { type: MarkerType.ArrowClosed, width: 20, height: 20, color: '#f59e0b' }
          });
        });
      });

      // 4. runtime -> ztc
      runtimes.forEach(runtime => {
        ztcs.forEach(ztc => {
          edges.push({
            id: `edge-rt-ztc-${runtime.id}-${ztc.id}`,
            source: `aura-${runtime.id}`,
            target: `aura-${ztc.id}`,
            type: 'straight',
            animated: true,
            style: { stroke: '#8b5cf6', strokeWidth: 2, opacity: 0.8 },
            markerEnd: { type: MarkerType.ArrowClosed, width: 20, height: 20, color: '#8b5cf6' }
          });
        });
      });
    }
    return edges;
  }, [systemNodes, auranetNodes, viewMode]);

  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  // Force redraw when toggling between Workloads and Nodes
  useEffect(() => {
    setNodes(getInitialNodes());
    setEdges(getInitialEdges());
  }, [viewMode]); 

  // Smart Merge for Live Data Polling
  useEffect(() => {
    const freshNodes = getInitialNodes();
    
    setNodes((currentNodes) => {
      // Prevent merging mismatching view states during rapid transitions
      const isK8s = viewMode === 'nodes';
      const isAura = viewMode === 'auranet';

      if (currentNodes.length > 0) {
        const firstId = currentNodes[0].id;
        if ((firstId.startsWith('k8s-') && !isK8s) || 
            (firstId.startsWith('aura-') && !isAura) ||
            (!firstId.startsWith('k8s-') && !firstId.startsWith('aura-') && (isK8s || isAura))) {
          return freshNodes; 
        }
      }
      
      return freshNodes.map(freshNode => {
        const existingNode = currentNodes.find(n => n.id === freshNode.id);
        if (existingNode) {
          return { ...freshNode, position: existingNode.position };
        }
        return freshNode;
      });
    });

    setEdges(getInitialEdges());
  }, [systemNodes, k8sNodes, auranetNodes, getInitialNodes, getInitialEdges, setNodes, setEdges, viewMode]);

  // Cluster Sync Effect
  useEffect(() => {
    const fetchTopology = async () => {
      if (!pulseActive) return;
      try {
        const response = await fetch('/api/topology');
        const data = await response.json();
        
        if (data.systemNodes) {
          setSystemNodes(data.systemNodes); 
          setIsAuraNetHealthy(data.auranetHealth);
        }
        if (data.k8sNodes) {
          setK8sNodes(data.k8sNodes);
        }
        if (data.auranetNodes) {
          setAuraNetNodes(data.auranetNodes);
        }
      } catch (error) {
        console.error("Failed to fetch topology:", error);
      }
    };

    fetchTopology();
    const interval = setInterval(fetchTopology, 5000); 
    return () => clearInterval(interval);
  }, [setSystemNodes, pulseActive]);

  // Handle Node Clicks based on current view
  const onNodeClick = useCallback((event: React.MouseEvent, flowNode: Node) => {
    if (viewMode === 'workloads') {
      const originalNode = systemNodes.find(n => n.id === flowNode.id);
      if (originalNode) onNodeSelect(originalNode);
    } else if (viewMode === 'nodes') {
      // In Node View, inject the k8sNode info into a mocked SystemNode struct so the UI tray populates
      const cleanId = flowNode.id.replace('k8s-', '');
      const k8sNode = k8sNodes.find(n => n.id === cleanId);
      
      if (k8sNode) {
        onNodeSelect({
          id: flowNode.id,
          label: k8sNode.name,
          type: 'compute',
          status: k8sNode.status,
          latency: k8sNode.status === 'offline' ? 999 : 10,
          region: 'Kubernetes Cluster',
          ip: k8sNode.ip,
          cpu: k8sNode.cpu,
          memory: k8sNode.memory,
          connections: []
        });
      }
    } else if (viewMode === 'auranet') {
      const cleanId = flowNode.id.replace('aura-', '');
      const aNode = auranetNodes.find(n => n.id === cleanId);
      
      if (aNode) {
        onNodeSelect({
          id: flowNode.id,
          label: aNode.name,
          type: 'compute',
          status: aNode.status,
          latency: aNode.status === 'offline' ? 999 : 5,
          region: 'AuraNet Namespace',
          ip: aNode.ip,
          cpu: aNode.cpu,
          memory: aNode.memory,
          connections: []
        });
      }
    }
  }, [systemNodes, k8sNodes, auranetNodes, onNodeSelect, viewMode]);

  const handleAddNewNode = () => {
    const labels = ['Nordic Compute', 'Oceania Beacon', 'Canada Sensor', 'S.E. Asia Gateway'];
    const regions = ['Norway (Oslo)', 'Australia (Sydney)', 'Canada (Montreal)', 'Singapore (Jurong)'];
    const types: ('sensor' | 'gateway' | 'compute')[] = ['sensor', 'gateway', 'compute'];
    const IPs = ['192.168.10.1', '192.168.10.2', '192.168.10.3'];
    
    const randomIndex = Math.floor(Math.random() * labels.length);
    const id = `node-${Date.now()}`;
    
    const newNode: SystemNode = {
      id,
      label: labels[randomIndex],
      type: types[Math.floor(Math.random() * types.length)],
      status: 'active',
      latency: Math.floor(Math.random() * 45) + 5,
      region: regions[randomIndex],
      ip: IPs[Math.floor(Math.random() * IPs.length)],
      cpu: Math.floor(Math.random() * 40) + 10,
      memory: Math.floor(Math.random() * 50) + 20,
      connections: [],
    };

    setSystemNodes(prev => [...prev, newNode]);
  };

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
            <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold text-white shadow-sm transition-colors ${
              isAuraNetHealthy ? 'bg-emerald-500' : 'bg-red-600 animate-pulse'
            }`}>
              {isAuraNetHealthy ? <ShieldCheck size={14} /> : <AlertTriangle size={14} />}
              AuraNet: {isAuraNetHealthy ? 'Active & Protecting' : 'Offline / Unreachable'}
            </span>
          </div>
        </div>

        {/* Toolbar buttons */}
        <div className="flex items-center gap-3">
          
          {/* VIEW TOGGLE */}
          <div className="flex items-center bg-slate-100 p-0.5 rounded-lg border border-slate-200">
            <button
              onClick={() => setViewMode('workloads')}
              className={`px-3 py-1.5 text-xs font-mono font-bold uppercase rounded-md transition-all flex items-center gap-1.5 ${
                viewMode === 'workloads' ? 'bg-white text-indigo-700 shadow-xs' : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              <Layers size={14} /> Workloads
            </button>
            <button
              onClick={() => setViewMode('nodes')}
              className={`px-3 py-1.5 text-xs font-mono font-bold uppercase rounded-md transition-all flex items-center gap-1.5 ${
                viewMode === 'nodes' ? 'bg-white text-indigo-700 shadow-xs' : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              <Server size={14} /> Nodes
            </button>
            <button
              onClick={() => setViewMode('auranet')}
              className={`px-3 py-1.5 text-xs font-mono font-bold uppercase rounded-md transition-all flex items-center gap-1.5 ${
                viewMode === 'auranet' ? 'bg-white text-emerald-600 shadow-xs' : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              <ShieldCheck size={14} /> AuraNet
            </button>
          </div>

          <div className="h-6 w-px bg-slate-200 mx-1" />

          <button
            onClick={() => setPulseActive(!pulseActive)}
            className={`p-2 rounded-lg border transition-all text-xs font-semibold flex items-center gap-1.5 ${
              pulseActive 
                ? 'bg-[#e3dfff] text-brand-primary border-indigo-200 hover:bg-indigo-100' 
                : 'bg-slate-50 text-slate-500 border-slate-200 hover:bg-slate-100'
            }`}
          >
            {pulseActive ? <Pause size={14} /> : <Play size={14} />}
            <span className="hidden sm:inline">{pulseActive ? 'Live Sync' : 'Paused'}</span>
          </button>

          <button
            onClick={handleAddNewNode}
            className="p-2 bg-[#4d41df] hover:bg-indigo-600 text-white rounded-lg border border-indigo-500 shadow-sm transition-all text-xs font-semibold flex items-center gap-1.5"
          >
            <Plus size={14} />
            <span className="hidden sm:inline">Add Workload</span>
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

        {viewMode === 'workloads' && (
          <div className="absolute bottom-4 left-4 bg-white/95 backdrop-blur-xs border border-brand-border rounded-xl p-3 shadow-lg select-none z-30">
            <span className="font-mono text-[9px] font-bold text-slate-400 tracking-wider uppercase block">
              Average Latency
            </span>
            <span className="font-display font-extrabold text-xl text-brand-primary block leading-none mt-1">
              {avgLatency}ms
            </span>
          </div>
        )}
      </div>

      {/* Selected Node Details Tray */}
      {selectedNode && (
        <div className="mt-4 bg-[#f8f9fa] border border-brand-border rounded-xl p-3 flex flex-wrap items-center justify-between gap-3 relative transition-all duration-300">
          <div className="flex items-center gap-3">
            <div className={`h-8 w-8 rounded-full flex items-center justify-center text-white ${
              selectedNode.status === 'offline' ? 'bg-red-500' : selectedNode.status === 'warning' ? 'bg-amber-500' : 'bg-[#4d41df]'
            }`}>
              {viewMode === 'nodes' ? <Server size={14} /> : <Cpu size={14} />}
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
              <span className={`text-xs font-bold ${selectedNode.latency > 150 ? 'text-red-500' : 'text-[#00ced1]'}`}>
                {selectedNode.latency}ms
              </span>
            </div>
            
            {/* Contextual Actions */}
            {viewMode === 'workloads' && (
              <div className="flex items-center gap-1.5 border-l border-slate-200 pl-3">
                <button
                  onClick={() => {
                    setSystemNodes(prev => prev.map(n => {
                      if (n.id === selectedNode.id) {
                        const nextStatus = n.status === 'active' ? 'warning' : n.status === 'warning' ? 'offline' : 'active';
                        return { ...n, status: nextStatus };
                      }
                      return n;
                    }));
                  }}
                  className="px-2 py-1 text-[10px] font-mono font-bold bg-white hover:bg-slate-100 border border-slate-200 rounded text-slate-700"
                >
                  Toggle State
                </button>
                <button
                  onClick={() => {
                    setSystemNodes(prev => prev.filter(n => n.id !== selectedNode.id));
                    onNodeSelect(systemNodes[0] || null); 
                  }}
                  className="px-2 py-1 text-[10px] font-mono font-bold bg-red-50 hover:bg-red-100 border border-red-200 rounded text-red-600"
                >
                  Delete Pod
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}