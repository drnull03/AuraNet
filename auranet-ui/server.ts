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

const app = express();
const PORT = 3000;

// Middleware
app.use(express.json());





app.get('/api/topology', (req, res) => {
  try {
    // In K8s, we will mount the ConfigMap to this path
    const configPath = process.env.CONFIG_PATH || path.join(process.cwd(), 'naive.conf');
    const fileContent = fs.readFileSync(configPath, 'utf-8');
    
    const lines = fileContent.split('\n');
    const nodeSet = new Set<string>();
    const edges: any[] = [];
    
    lines.forEach((line, index) => {
      const cleanLine = line.trim();
      if (!cleanLine || cleanLine.startsWith('#')) return;

      // Parse format: source -> target:port
      const parts = cleanLine.split('->').map(s => s.trim());
      if (parts.length === 2) {
        const source = parts[0].replace(/^\d+\.\s*/, ''); // Strip leading numbers like "1. "
        const targetRaw = parts[1];
        const targetNode = targetRaw.split(':')[0]; // Strip the port for the node ID
        
        nodeSet.add(source);
        nodeSet.add(targetNode);
        
        edges.push({
          id: `edge-${index}`,
          source: source,
          target: targetNode,
          type: 'default',
          animated: true,
          style: { stroke: '#cbd5e1', strokeWidth: 2 }
        });
      }
    });

    // Format nodes for React Flow
    const nodes = Array.from(nodeSet).map((nodeId, idx) => ({
      id: nodeId,
      type: 'satelliteNode', // Using the custom component from NetworkFlow.tsx
      position: { x: 250 + (idx * 150), y: 200 + (idx % 2 === 0 ? 50 : -50) }, // Basic layout, can be improved with dagre.js later
      data: { 
        label: nodeId,
        status: 'active', // Default state, can be updated via live telemetry later
        cpu: 0 
      }
    }));

    res.json({ nodes, edges });
  } catch (error) {
    console.error("Failed to parse topology config:", error);
    res.status(500).json({ error: "Failed to read topology configuration" });
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
