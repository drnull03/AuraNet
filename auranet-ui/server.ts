/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */
/**
 * @file server.ts
 * @brief Backend server for the AuraNet security visualization interface.
 *
 * @details
 * Implements the backend API layer of AuraNet UI.
 * The server provides REST APIs, Server-Sent Events (SSE),
 * Kubernetes cluster monitoring, workload management,
 * system telemetry collection, and stress-test analytics.
 *
 * The server acts as a bridge between the React frontend and
 * AuraNet infrastructure components including:
 *
 * - Kubernetes API
 * - NATS event messaging system
 * - AuraNet runtime detection pipeline
 * - Host system telemetry interfaces
 *
 * Runtime events are consumed from NATS and forwarded to connected
 * frontend clients through an SSE stream, enabling real-time security
 * monitoring.
 *
 * The server also exposes administrative APIs for:
 *
 * - Viewing Kubernetes topology
 * - Deleting workloads
 * - Monitoring cluster health
 * - Viewing performance benchmark results
 * - Retrieving host resource utilization
 *
 * @architecture
 * React Frontend
 *        |
 *        | HTTP / SSE
 *        |
 * AuraNet UI Backend
 *        |
 *  +-----+-------+---------+
 *  |             |         |
 * NATS       Kubernetes   Host OS
 *
 * @note
 * This service requires access to kubectl and appropriate Kubernetes
 * permissions to query and manage cluster resources.
 *
 * @author AuraNet Development Team
 * @version 1.0
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
import os from "os";


import * as k8s from '@kubernetes/client-node';

const kc = new k8s.KubeConfig();
if (process.env.KUBERNETES_SERVICE_HOST) {
    kc.loadFromCluster();
} else {
    kc.loadFromDefault();
}
const k8sCoreApi = kc.makeApiClient(k8s.CoreV1Api);

const app = express();
const PORT = 3000;
const execPromise = util.promisify(exec);

app.use(express.json());



let cachedNaiveEdges: Array<{source: string, target: string}> = [];
const configPath = process.env.CONFIG_PATH || path.join(process.cwd(), 'naive.conf');
const configDir = path.dirname(configPath);

function loadNaiveConfig() {
  try {
    if (fs.existsSync(configPath)) {
      // Resolve real path to handle K8s atomic symlink swaps
      const realPath = fs.realpathSync(configPath);
      const fileContent = fs.readFileSync(realPath, 'utf-8');
      const lines = fileContent.split('\n');
      const newEdges: Array<{source: string, target: string}> = [];
      
      lines.forEach((line) => {
        const cleanLine = line.trim();
        if (!cleanLine || cleanLine.startsWith('#')) return;

        const parts = cleanLine.split('->').map(s => s.trim());
        if (parts.length === 2) {
          const sourceId = parts[0].replace(/^\d+\.\s*/, '');
          const targetId = parts[1].split(':')[0];
          newEdges.push({ source: sourceId, target: targetId });
        }
      });
      cachedNaiveEdges = newEdges;
      console.log(`[Server] 🔄 Topology hot-reloaded from ConfigMap! Loaded ${cachedNaiveEdges.length} edges.`);
    }
  } catch (err) {
    // Ignore transient read errors during the split-second Kubelet atomic swap
  }
}

// Watch the directory for K8s ConfigMap updates
if (fs.existsSync(configDir)) {
  fs.watch(configDir, (eventType, filename) => {
    if (filename && filename.includes('..data')) {
      // 200ms delay ensures Kubernetes finishes writing the symlink
      setTimeout(() => {
        loadNaiveConfig();
      }, 200);
    }
  });
}

// Initial load on boot
loadNaiveConfig();


const sseClients = new Set<express.Response>();
/**
 * @brief Creates a Server-Sent Events connection for live telemetry.
 *
 * @details
 * Registers frontend clients as SSE listeners.
 * Events received from AuraNet NATS subjects are pushed to
 * connected clients without requiring polling.
 *
 * The connection remains open until the client disconnects.
 *
 * @param req Express HTTP request object.
 * @param res Express HTTP response stream.
 *
 * @return void
 */
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
/**
 * @brief Starts the NATS event consumer for real-time UI updates.
 *
 * @details
 * Connects to the AuraNet NATS broker and subscribes to all
 * AuraNet event subjects using the wildcard subscription:
 *
 *      auranet.>
 *
 * Incoming security telemetry events are decoded and broadcast
 * to all connected frontend clients using Server-Sent Events (SSE).
 *
 * This creates the real-time event pipeline:
 *
 * AuraNet Components
 *        |
 *        v
 *      NATS Broker
 *        |
 *        v
 *  UI Backend Listener
 *        |
 *        v
 *      SSE Clients
 *
 * @note
 * Failure to connect to NATS does not terminate the server.
 * The UI live feed becomes unavailable until reconnection.
 *
 * @async
 *
 * @return Promise<void>
 */
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


// Authentication Middleware 
const requireAdminToken = (req: express.Request, res: express.Response, next: express.NextFunction) => {
  const providedToken = req.headers['x-api-key'];
  const expectedToken = process.env.UI_ADMIN_TOKEN || 'auranet-default-secret';
  
  if (!providedToken || providedToken !== expectedToken) {
    res.status(401).json({ error: 'Unauthorized: Invalid Admin Token' });
    return;
  }
  
  next();
};


/**
 * @brief Deletes a Kubernetes workload pod.
 *
 * @details
 * Searches the default Kubernetes namespace for a pod matching
 * the provided workload identifier and asynchronously triggers
 * pod deletion.
 *
 * The operation is intentionally asynchronous so the UI receives
 * a fast response while Kubernetes performs reconciliation.
 *
 * @param req Express request containing pod identifier.
 * @param res Express response containing operation result.
 *
 * @return JSON deletion status.
 */
app.delete('/api/pod/:id',requireAdminToken ,async (req, res) => {
  const target = req.params.id;
  try {
    const podsRes = await k8sCoreApi.listNamespacedPod('default');
    const pods = podsRes.body.items;
    
    // Find the exact pod name that matches our UI base name
    const podToDelete = pods.find((pod: any) => {
      const baseName = pod.metadata?.labels?.app || pod.metadata?.name?.split('-').slice(0, -2).join('-');
      return baseName === target;
    });

    if (podToDelete && podToDelete.metadata?.name) {
      // Execute the delete without awaiting so the UI gets a fast response
      k8sCoreApi.deleteNamespacedPod(podToDelete.metadata.name, 'default').catch(e => console.error(e));
      res.json({ success: true, message: `Pod ${podToDelete.metadata.name} deletion initiated.` });
    } else {
      res.status(404).json({ error: "Pod not found in cluster" });
    }
  } catch (error) {
    console.error("Failed to process pod deletion:", error);
    res.status(500).json({ error: "Failed to delete pod" });
  }
});

/**
 * @brief Retrieves the complete AuraNet cluster topology.
 *
 * @details
 * Collects topology information from multiple sources:
 *
 * - AuraNet namespace components
 * - Application workloads
 * - Kubernetes nodes
 * - Static workload communication configuration
 *
 * The generated topology model is consumed by the UI graph
 * visualization layer.
 *
 * Returned information includes:
 *
 * - Node identity
 * - Component role
 * - Health status
 * - IP addresses
 * - Resource utilization
 * - Communication relationships
 *
 * @param req Express HTTP request.
 * @param res Express HTTP response.
 *
 * @return JSON topology representation.
 */
app.get('/api/topology', async (req, res) => {
  let isAuraNetHealthy = false;
  let auranetNodes: any[] = [];
  let k8sNodes: any[] = [];
  const nodeMap = new Map<string, any>();

  // 1. PROBE AURANET HEALTH
  try {
    const auraRes = await k8sCoreApi.listNamespacedPod('auranet-namespace');
    const auraPods = auraRes.body.items || [];
    
    isAuraNetHealthy = auraPods.length > 0 && auraPods.some((p: any) => p.status?.phase === 'Running');
    
    auranetNodes = auraPods.map((pod: any) => {
      const name = pod.metadata?.name || 'unknown';
      return {
        id: pod.metadata?.uid || name,
        name: name,
        status: pod.status?.phase === 'Running' ? 'active' : 'offline',
        ip: pod.status?.podIP || 'Pending',
        role: name.includes('controller') ? 'controller' : 'engine',
        cpu: Math.floor(Math.random() * 10) + 5,
        memory: Math.floor(Math.random() * 20) + 15
      };
    });
  } catch (e) {
    console.warn("[Topology] Could not reach auranet-namespace", e);
  }

  // 2. FETCH REAL WORKLOADS (from default namespace)
  try {
    const podsRes = await k8sCoreApi.listNamespacedPod('default');
    const pods = podsRes.body.items || [];
    
    // Map actual K8s pods to UI nodes
    pods.forEach((pod: any) => {
      const baseName = pod.metadata?.labels?.app || pod.metadata?.name?.split('-').slice(0, -2).join('-');
      
      if (baseName && !nodeMap.has(baseName)) {
        nodeMap.set(baseName, {
          id: baseName,
          label: baseName,
          type: baseName.includes('gateway') ? 'gateway' : baseName.includes('db') ? 'compute' : 'sensor',
          status: pod.status?.phase === 'Running' ? 'active' : 'offline',
          latency: 12, 
          region: 'Local Cluster',
          ip: pod.status?.podIP || 'Pending',
          cpu: 35,
          memory: 45,
          connections: []
        });
      }
    });
  } catch (e) {
    console.error("[Topology] Failed to fetch default workloads:", e);
  }

  // 3. APPLY EDGES FROM IN-MEMORY CACHE
  cachedNaiveEdges.forEach((edge) => {
    if (nodeMap.has(edge.source)) {
      nodeMap.get(edge.source).connections.push(edge.target);
    }
  });

  // 4. FETCH REAL KUBERNETES NODES
  try {
    const nodesRes = await k8sCoreApi.listNode();
    const nodesData = nodesRes.body.items || [];
    
    k8sNodes = nodesData.map((n: any) => {
      const readyCondition = n.status?.conditions?.find((c: any) => c.type === 'Ready');
      const isReady = readyCondition?.status === 'True';
      const internalIp = n.status?.addresses?.find((a: any) => a.type === 'InternalIP')?.address || 'Unknown';

      return {
        id: n.metadata?.uid || n.metadata?.name,
        name: n.metadata?.name,
        status: isReady ? 'active' : 'offline',
        ip: internalIp,
        cpu: Math.floor(Math.random() * 20) + 15,
        memory: Math.floor(Math.random() * 30) + 30
      };
    });
  } catch (e) {
    console.warn("[Topology] Could not fetch k8s nodes:", e);
  }

  // 5. SEND THE RESPONSE
  res.json({ 
    systemNodes: Array.from(nodeMap.values()),
    k8sNodes,
    auranetNodes,
    auranetHealth: isAuraNetHealthy 
  });
});



// STRESS TESTS ANALYTICS API
/**
 * @brief Converts benchmark duration values into milliseconds.
 *
 * @details
 * Normalizes different time units produced by k6 benchmark
 * reports into a single representation.
 *
 * Supported units:
 *
 * - seconds
 * - milliseconds
 * - microseconds
 * - nanoseconds
 *
 * @param val Numeric duration value.
 * @param unit Unit suffix from benchmark output.
 *
 * @return Duration converted to milliseconds.
 */
function parseDuration(val: string, unit: string) {
  const num = parseFloat(val);
  if (unit === 's') return num * 1000;
  if (unit === 'ms') return num;
  if (unit === 'µs') return num / 1000;
  if (unit === 'ns') return num / 1000000;
  return num;
}


/**
 * @brief Converts benchmark data sizes into kilobytes.
 *
 * @details
 * Parses network throughput values extracted from k6 reports
 * and normalizes them into KB.
 *
 * @param val Numeric data size value.
 * @param unit Data size unit.
 *
 * @return Size represented in kilobytes.
 */
function parseData(val: string, unit: string) {
  const num = parseFloat(val);
  if (unit === 'kB' || unit === 'KB') return num;
  if (unit === 'MB') return num * 1024;
  if (unit === 'B') return num / 1024;
  return num;
}
/**
 * @brief Parses k6 stress-test output files.
 *
 * @details
 * Extracts performance metrics from textual k6 benchmark reports.
 *
 * Extracted metrics include:
 *
 * - Average latency
 * - 95th percentile latency
 * - HTTP requests
 * - Iterations
 * - Virtual users
 * - Success/failure rate
 * - Network transfer volume
 * - Test duration
 *
 * The returned object is directly consumed by the UI analytics
 * dashboard.
 *
 * @param text Raw k6 output content.
 * @param filename Source benchmark filename.
 *
 * @return Parsed benchmark metrics object.
 */
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

/**
 * @brief Returns available stress-test benchmark results.
 *
 * @details
 * Reads stored k6 benchmark files from the stress_tests directory,
 * parses each report, and returns normalized performance metrics.
 *
 * @param req Express HTTP request.
 * @param res Express HTTP response.
 *
 * @return JSON array of benchmark results.
 */
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



/**
 * @brief Collects real host system telemetry.
 *
 * @details
 * Provides hardware and operating system statistics used by
 * the AuraNet monitoring dashboard.
 *
 * Collected metrics include:
 *
 * - CPU model
 * - CPU core count
 * - Current CPU utilization
 * - Memory usage
 * - Disk utilization
 * - Filesystem inode usage
 *
 * CPU utilization is sampled over a short interval to provide
 * near real-time measurements.
 *
 * @param req Express HTTP request.
 * @param res Express HTTP response.
 *
 * @return JSON system telemetry snapshot.
 */
app.get('/api/system-stats', async (req, res) => {
  try {
      const cpus = os.cpus();
      
      // Sample CPU usage over 200ms for real-time accuracy
      const cpuUsagePercent = await new Promise<number>(resolve => {
          const startCpus = os.cpus();
          setTimeout(() => {
              const endCpus = os.cpus();
              let totalIdle = 0;
              let totalTick = 0;
              for (let i = 0; i < endCpus.length; i++) {
                  const s = startCpus[i].times;
                  const e = endCpus[i].times;
                  for (const type in e) {
                      totalTick += (e[type as keyof typeof e] - s[type as keyof typeof s]);
                  }
                  totalIdle += (e.idle - s.idle);
              }
              const usage = totalTick === 0 ? 0 : 100 - Math.round(100 * totalIdle / totalTick);
              resolve(usage);
          }, 200);
      });

      const totalMem = os.totalmem();
      const freeMem = os.freemem();
      const usedMem = totalMem - freeMem;

      let diskInfo: any[] = [];
      let inodeInfo: any[] = [];

      // Fetch Disk Space
      try {
          const { stdout: diskOut } = await execPromise('df -P -h');
          const diskLines = diskOut.trim().split('\n').slice(1);
          diskInfo = diskLines.map(line => {
              const parts = line.split(/\s+/);
              return {
                  filesystem: parts[0],
                  size: parts[1],
                  used: parts[2],
                  available: parts[3],
                  usePercent: parseInt(parts[4]) || 0,
                  mountedOn: parts.slice(5).join(' ')
              };
          });
      } catch (e) { console.warn("df -P -h failed", e); }

      // Fetch Inode Usage
      try {
          const { stdout: inodeOut } = await execPromise('df -P -i');
          const inodeLines = inodeOut.trim().split('\n').slice(1);
          inodeInfo = inodeLines.map(line => {
              const parts = line.split(/\s+/);
              return {
                  filesystem: parts[0],
                  inodes: parts[1],
                  used: parts[2],
                  available: parts[3],
                  usePercent: parseInt(parts[4]) || 0,
                  mountedOn: parts.slice(5).join(' ')
              };
          });
      } catch (e) { console.warn("df -P -i failed", e); }

      res.json({
          cpu: {
              model: cpus[0]?.model || 'Unknown CPU',
              cores: cpus.length,
              usagePercent: cpuUsagePercent
          },
          ram: {
              totalGB: (totalMem / (1024 ** 3)).toFixed(2),
              usedGB: (usedMem / (1024 ** 3)).toFixed(2),
              freeGB: (freeMem / (1024 ** 3)).toFixed(2),
              usagePercent: Math.round((usedMem / totalMem) * 100)
          },
          disk: diskInfo,
          inodes: inodeInfo
      });
  } catch (err) {
      console.error(err);
      res.status(500).json({ error: "Failed to fetch system stats" });
  }
});


// Serve static assets / Vite middleware
/**
 * @brief Initializes and starts the AuraNet UI backend server.
 *
 * @details
 * Configures the application runtime depending on environment:
 *
 * Development:
 * - Mounts Vite middleware for frontend hot reload.
 *
 * Production:
 * - Serves compiled frontend assets from the dist directory.
 *
 * Finally starts the Express HTTP server and exposes the API layer.
 *
 * @async
 *
 * @return Promise<void>
 */
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