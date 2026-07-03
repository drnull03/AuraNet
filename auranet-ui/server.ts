/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import express from "express";
import path from "path";
import { createServer as createViteServer } from "vite";
import dotenv from "dotenv";
import fs from 'fs'
dotenv.config();
import util from "util";
import { exec } from "child_process";

const app = express();
const PORT = 3000;
const execPromise = util.promisify(exec);
// Middleware
app.use(express.json());





app.get('/api/topology', async (req, res) => {
  try {
    // 1. PROBE AURANET HEALTH
    let isAuraNetHealthy = false;
    try {
      const { stdout: auraOut } = await execPromise('kubectl get pods -n auranet-namespace -o json');
      const auraPods = JSON.parse(auraOut).items;
      // It is healthy if the namespace has pods and at least one is Running
      isAuraNetHealthy = auraPods.length > 0 && auraPods.some((p: any) => p.status.phase === 'Running');
    } catch (e) {
      console.warn("Could not reach auranet-namespace");
    }

    // 2. FETCH REAL WORKLOADS (from default namespace)
    const { stdout: podOut } = await execPromise('kubectl get pods -n default -o json');
    const pods = JSON.parse(podOut).items;
    
    const nodeMap = new Map<string, any>();

    // Map actual K8s pods to UI nodes
    pods.forEach((pod: any) => {
      // Strip random pod hashes to get the base deployment name (e.g., api-gateway-7f5b... -> api-gateway)
      const baseName = pod.metadata.labels?.app || pod.metadata.name.split('-').slice(0, -2).join('-');
      
      if (!nodeMap.has(baseName)) {
        nodeMap.set(baseName, {
          id: baseName,
          label: baseName,
          type: baseName.includes('gateway') ? 'gateway' : baseName.includes('db') ? 'compute' : 'sensor',
          status: pod.status.phase === 'Running' ? 'active' : 'offline',
          latency: 12, 
          region: 'Local Cluster',
          ip: pod.status.podIP || 'Pending',
          cpu: 35,    // Baseline for UI rendering until Metrics Server is attached
          memory: 45, // Baseline for UI rendering until Metrics Server is attached
          connections: []
        });
      }
    });

    // 3. APPLY EDGES FROM NAIVE.CONF
    const configPath = process.env.CONFIG_PATH || path.join(process.cwd(), 'naive.conf');
    if (fs.existsSync(configPath)) {
      const fileContent = fs.readFileSync(configPath, 'utf-8');
      const lines = fileContent.split('\n');
      
      lines.forEach((line) => {
        const cleanLine = line.trim();
        if (!cleanLine || cleanLine.startsWith('#')) return;

        const parts = cleanLine.split('->').map(s => s.trim());
        if (parts.length === 2) {
          const sourceId = parts[0].replace(/^\d+\.\s*/, '');
          const targetId = parts[1].split(':')[0];

          if (nodeMap.has(sourceId)) {
            nodeMap.get(sourceId).connections.push(targetId);
          }
        }
      });
    }

    res.json({ 
      systemNodes: Array.from(nodeMap.values()),
      auranetHealth: isAuraNetHealthy 
    });

  } catch (error) {
    console.error("Cluster topology fetch failed:", error);
    res.status(500).json({ error: "Failed to read cluster state" });
  }
});


// Serve static assets / Vite middleware
async function startServer() {
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
    console.log("Vite development server middleware mounted.");
  } else {
    const distPath = path.join(process.cwd(), 'dist');
    app.use(express.static(distPath));
    app.get('*', (req, res) => {
      res.sendFile(path.join(distPath, 'index.html'));
    });
    console.log("Serving compiled production assets from /dist.");
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`auranet-ui server running on port ${PORT}`);
  });
}

startServer();
