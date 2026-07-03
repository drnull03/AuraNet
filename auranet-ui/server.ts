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
import { connect, StringCodec } from "nats";

const app = express();
const PORT = 3000;
const execPromise = util.promisify(exec);

app.use(express.json());

// ==========================================
// NATS -> SSE EVENT STREAMING
// ==========================================
const sseClients = new Set<express.Response>();

app.get('/api/events/stream', (req, res) => {
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.flushHeaders();

  sseClients.add(res);

  req.on('close', () => {
    sseClients.delete(res);
  });
});

async function startNatsListener() {
  try {
    const NATS_URL = process.env.NATS_URL || 'nats://auranet-nats-broker.auranet-messaging.svc.cluster.local:4222';
    console.log("[Server] Connecting to NATS for UI SSE broadcast at:", NATS_URL);
    
    const nc = await connect({ servers: NATS_URL });
    const sc = StringCodec();

    // Subscribe to all AuraNet system events
    const sub = nc.subscribe("auranet.>");
    console.log("[Server] Subscribed to NATS 'auranet.>' telemetry stream.");

    for await (const msg of sub) {
      const subject = msg.subject;
      let decodedData;
      
      try {
        decodedData = JSON.parse(sc.decode(msg.data));
      } catch (e) {
        decodedData = { raw: sc.decode(msg.data) };
      }
      
      const payload = JSON.stringify({ subject, data: decodedData });
      
      // Broadcast to all connected React clients
      sseClients.forEach(client => {
        client.write(`data: ${payload}\n\n`);
      });
    }
  } catch (err) {
    console.warn("[Server] WARNING: Could not connect to NATS. Live SSE feed will be unavailable.", err);
  }
}

// Initialize the background listener
startNatsListener();

// ==========================================
// TOPOLOGY POLLING API
// ==========================================
app.get('/api/topology', async (req, res) => {
  try {
    // 1. PROBE AURANET HEALTH
    let isAuraNetHealthy = false;
    let auranetNodes: any[] = [];
    try {
      const { stdout: auraOut } = await execPromise('kubectl get pods -n auranet-namespace -o json');
      const auraPods = JSON.parse(auraOut).items;
      // It is healthy if the namespace has pods and at least one is Running
      isAuraNetHealthy = auraPods.length > 0 && auraPods.some((p: any) => p.status.phase === 'Running');
      
      auranetNodes = auraPods.map((pod: any) => {
        const name = pod.metadata.name;
        return {
          id: pod.metadata.uid || name,
          name: name,
          status: pod.status.phase === 'Running' ? 'active' : 'offline',
          ip: pod.status.podIP || 'Pending',
          role: name.includes('controller') ? 'controller' : 'engine',
          cpu: Math.floor(Math.random() * 10) + 5,
          memory: Math.floor(Math.random() * 20) + 15
        };
      });
    } catch (e) {
      console.warn("Could not reach auranet-namespace");
    }

    // 2. FETCH REAL WORKLOADS (from default namespace)
    const { stdout: podOut } = await execPromise('kubectl get pods -n default -o json');
    const pods = JSON.parse(podOut).items;
    
    const nodeMap = new Map<string, any>();

    // Map actual K8s pods to UI nodes
    pods.forEach((pod: any) => {
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
          cpu: 35,
          memory: 45,
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

    // 4. FETCH REAL KUBERNETES NODES
    let k8sNodes: any[] = [];
    try {
      const { stdout: nodeOut } = await execPromise('kubectl get nodes -o json', { maxBuffer: 1024 * 1024 * 10 });
      const nodesData = JSON.parse(nodeOut);
      k8sNodes = nodesData.items.map((n: any) => {
        const readyCondition = n.status?.conditions?.find((c: any) => c.type === 'Ready');
        const isReady = readyCondition?.status === 'True';
        const internalIp = n.status?.addresses?.find((a: any) => a.type === 'InternalIP')?.address || 'Unknown';

        return {
          id: n.metadata.uid || n.metadata.name,
          name: n.metadata.name,
          status: isReady ? 'active' : 'offline',
          ip: internalIp,
          cpu: Math.floor(Math.random() * 20) + 15,
          memory: Math.floor(Math.random() * 30) + 30
        };
      });
    } catch (e) {
      console.warn("Could not fetch k8s nodes:", e);
    }

    res.json({ 
      systemNodes: Array.from(nodeMap.values()),
      k8sNodes,
      auranetNodes,
      auranetHealth: isAuraNetHealthy 
    });

  } catch (error) {
    console.error("Cluster topology fetch failed:", error);
    res.status(500).json({ error: "Failed to read cluster state" });
  }
});




// STRESS TESTS ANALYTICS API
function parseDuration(val: string, unit: string) {
  const num = parseFloat(val);
  if (unit === 's') return num * 1000;
  if (unit === 'ms') return num;
  if (unit === 'µs') return num / 1000;
  if (unit === 'ns') return num / 1000000;
  return num;
}

function parseData(val: string, unit: string) {
  const num = parseFloat(val);
  if (unit === 'kB' || unit === 'KB') return num;
  if (unit === 'MB') return num * 1024;
  if (unit === 'B') return num / 1024;
  return num;
}

function parseK6Output(text: string, filename: string) {
  const result: any = {
      name: filename.replace('.txt', '').replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
      metrics: {}
  };

  // Extract Response Times
  const durationMatch = text.match(/http_req_duration.*?avg=([\d.]+)([a-zµ]+).*?p\(95\)=([\d.]+)([a-zµ]+)/);
  if (durationMatch) {
      result.metrics.avgDuration = parseDuration(durationMatch[1], durationMatch[2]);
      result.metrics.p95Duration = parseDuration(durationMatch[3], durationMatch[4]);
  }

  // Extract Requests & Iterations
  const reqsMatch = text.match(/http_reqs.*?:\s+(\d+)/);
  if (reqsMatch) result.metrics.httpReqs = parseInt(reqsMatch[1]);

  const iterationsMatch = text.match(/iterations.*?:\s+(\d+)/);
  if (iterationsMatch) result.metrics.iterations = parseInt(iterationsMatch[1]);

  // Extract VUs
  const vusMatch = text.match(/vus_max.*?max=(\d+)/);
  if (vusMatch) result.metrics.vusMax = parseInt(vusMatch[1]);

  // Extract Checks
  const checksSuccessMatch = text.match(/checks_succeeded.*?:\s+([\d.]+)%/);
  if (checksSuccessMatch) result.metrics.checksSuccessRate = parseFloat(checksSuccessMatch[1]);

  const checksFailedMatch = text.match(/checks_failed.*?:\s+([\d.]+)%/);
  if (checksFailedMatch) result.metrics.checksFailedRate = parseFloat(checksFailedMatch[1]);

  // Extract Network Data
  const dataRecvMatch = text.match(/data_received.*?:\s+([\d.]+)\s*([a-zA-Z]+)/);
  if (dataRecvMatch) result.metrics.dataReceived = parseData(dataRecvMatch[1], dataRecvMatch[2]);

  const dataSentMatch = text.match(/data_sent.*?:\s+([\d.]+)\s*([a-zA-Z]+)/);
  if (dataSentMatch) result.metrics.dataSent = parseData(dataSentMatch[1], dataSentMatch[2]);

  // Extract Run Time
  const runTimeMatch = text.match(/running\s+\(([^)]+)\)/);
  if (runTimeMatch) result.metrics.runTime = runTimeMatch[1];

  return result;
}

app.get('/api/stress-tests', (req, res) => {
  const stressTestsDir = path.join(process.cwd(), 'stress_tests');
  if (!fs.existsSync(stressTestsDir)) {
      return res.json([]);
  }

  const files = fs.readdirSync(stressTestsDir).filter(f => f.endsWith('.txt'));
  const results = [];

  for (const file of files) {
      const filePath = path.join(stressTestsDir, file);
      const content = fs.readFileSync(filePath, 'utf-8');
      const parsed = parseK6Output(content, file);
      results.push(parsed);
  }

  res.json(results);
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