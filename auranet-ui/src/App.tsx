/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import NetworkFlow from './components/NetworkFlow';
import StressView from './components/StressView';
import StatisticsView from './components/StatisticsView';
import AttackView from './components/AttackView';
import WorkloadView from './components/WorkloadView';
import { ActiveView, SystemNode, MetricData } from './types';
import { INITIAL_NODES, INITIAL_COMMITS } from './data';

export default function App() {
  const [activeView, setActiveView] = useState<ActiveView>('main');
  const [activeSubTab, setActiveSubTab] = useState<string>('Overview');
  const [isCollapsed, setIsCollapsed] = useState<boolean>(false);
  
  // Real-time responsive states
  const [systemNodes, setSystemNodes] = useState<SystemNode[]>(INITIAL_NODES);
  const [selectedNode, setSelectedNode] = useState<SystemNode | null>(INITIAL_NODES[0]); // Default selected central-hub
  const [commitLogs, setCommitLogs] = useState(INITIAL_COMMITS);

  // Compute live metrics dynamically based on node status and telemetry!
  const [metrics, setMetrics] = useState<MetricData>({
    option1: 538,
    option2: 485,
    option3: 12,
    option1Percent: 75,
    option2Percent: 40,
  });

  // Keep metrics updated with active node counts & stats
  useEffect(() => {
    const activeOnes = systemNodes.filter(n => n.status !== 'offline');
    const totalActiveCpu = activeOnes.reduce((acc, curr) => acc + curr.cpu, 0);
    const totalActiveMem = activeOnes.reduce((acc, curr) => acc + curr.memory, 0);
    
    const avgCpu = Math.round(totalActiveCpu / (activeOnes.length || 1));
    const avgMem = Math.round(totalActiveMem / (activeOnes.length || 1));

    // Derive Option values dynamically
    const option1 = systemNodes.reduce((acc, curr) => acc + curr.latency, 0) * 4; // latency sum factor
    const option2 = activeOnes.reduce((acc, curr) => acc + curr.cpu + curr.memory, 0) + 150; // load sum
    const option3 = activeOnes.length; // Active endpoints count

    setMetrics({
      option1: Math.round(option1),
      option2: Math.round(option2),
      option3: option3,
      option1Percent: avgCpu || 0,
      option2Percent: avgMem || 0,
    });
  }, [systemNodes]);

  // Alert count is the count of offline or warning nodes
  const nodeAlertCount = systemNodes.filter(n => n.status === 'offline').length;

  // Handle Export Data - Downloads the state configuration of the nodes
  const handleExportData = () => {
    try {
      const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(systemNodes, null, 2));
      const downloadAnchor = document.createElement('a');
      downloadAnchor.setAttribute("href", dataStr);
      downloadAnchor.setAttribute("download", `auranet_ui_${Date.now()}.json`);
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-brand-bg font-sans" id="app-viewport-root">
      {/* Sidebar Rail Left */}
      <Sidebar 
        activeView={activeView}
        setActiveView={(view) => {
          setActiveView(view);
          // Auto select node when going to main topology
          if (view === 'main' && systemNodes.length > 0) {
            setSelectedNode(systemNodes[0]);
          }
        }}
        isCollapsed={isCollapsed}
        setIsCollapsed={setIsCollapsed}
        onExport={handleExportData}
      />

      {/* Main Container Right */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden" id="main-content-layout">
        {/* Global Header */}
        <Header 
          activeView={activeView}
          activeSubTab={activeSubTab}
          setActiveSubTab={setActiveSubTab}
          isCollapsed={isCollapsed}
          setIsCollapsed={setIsCollapsed}
          nodeAlertCount={nodeAlertCount}
          onProfileClick={() => {}}
        />

        {/* Scrollable Workspace */}
        <main className="flex-1 overflow-y-auto p-6 md:p-8 bg-slate-100/50" id="scrollable-workspace">
          {activeView === 'main' && (
            <div className="h-[calc(100vh-140px)] w-full rounded-2xl overflow-hidden border border-slate-200 bg-white shadow-xs" id="topology-full-viewport">
              <NetworkFlow 
                systemNodes={systemNodes}
                setSystemNodes={setSystemNodes}
                onNodeSelect={setSelectedNode}
                selectedNode={selectedNode}
              />
            </div>
          )}

          {activeView === 'stress' && (
            <StressView systemNodes={systemNodes} setSystemNodes={setSystemNodes} />
          )}

          {activeView === 'statistics' && (
            <StatisticsView systemNodes={systemNodes} metrics={metrics} />
          )}

          {activeView === 'attack' && (
            <AttackView systemNodes={systemNodes} setSystemNodes={setSystemNodes} />
          )}

          {activeView === 'workload' && (
            <WorkloadView systemNodes={systemNodes} setSystemNodes={setSystemNodes} />
          )}
        </main>
      </div>
    </div>
  );
}
