/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import express from "express";
import path from "path";
import { createServer as createViteServer } from "vite";
import { GoogleGenAI } from "@google/genai";
import dotenv from "dotenv";

dotenv.config();

const app = express();
const PORT = 3000;

// Middleware
app.use(express.json());

// Lazy-initialize Gemini client to avoid crashes if API key is not set immediately
let aiClient: GoogleGenAI | null = null;

function getGeminiClient(): GoogleGenAI {
  if (!aiClient) {
    const apiKey = process.env.GEMINI_API_KEY;
    if (!apiKey) {
      throw new Error("GEMINI_API_KEY environment variable is required to access the AI Operator Console");
    }
    aiClient = new GoogleGenAI({
      apiKey,
      httpOptions: {
        headers: {
          'User-Agent': 'aistudio-build',
        }
      }
    });
  }
  return aiClient;
}

// API: Check health & credentials status
app.get("/api/health", (req, res) => {
  const hasKey = !!process.env.GEMINI_API_KEY;
  res.json({ 
    status: "healthy", 
    aiConfigured: hasKey,
    timestamp: new Date().toISOString()
  });
});

// API: AI Operator console chat proxied safely on server
app.post("/api/chat", async (req, res) => {
  try {
    const { messages, networkNodes } = req.body;

    if (!messages || !Array.isArray(messages)) {
      res.status(400).json({ error: "Invalid messages format. Expected an array." });
      return;
    }

    const ai = getGeminiClient();

    // Context preparation: serialize network nodes so the model has actual system awareness
    const serializedNodes = networkNodes && Array.isArray(networkNodes)
      ? networkNodes.map((node: any) => 
          `- Node Name: ${node.label} (${node.id}) | Type: ${node.type} | Status: ${node.status.toUpperCase()} | Latency: ${node.latency}ms | IP: ${node.ip} | CPU: ${node.cpu}% | Memory: ${node.memory}%`
        ).join("\n")
      : "No network node telemetry data provided.";

    const systemInstruction = `You are "Alpha-AI", the advanced server-side neural network coprocessor and AI Operator for Project Alpha (Graduation 2024). 
You help Emily Rose (Senior Network Architect) monitor, optimize, and diagnose distributed node meshes.

Here is the current LIVE network telemetry state:
${serializedNodes}

Guidelines for response:
1. Speak with professional, highly systematic composure. Be brief, scientific, and technical.
2. Directly refer to specific nodes, latencies, CPU percentages, and statuses in the live telemetry when answering questions.
3. If any nodes are offline (e.g., Africa South Node is currently OFFLINE at 320ms), point it out as a concern and offer network troubleshooting recommendations (such as traceroute validation, routing tables recalculation, or power recycling).
4. Feel free to explain distributed mesh topics (e.g. Paxos consensus, BGP routing, edge sensing, or latency minimization).
5. Always render answers in beautifully formatted clean Markdown. Keep responses relatively concise and focused on network solutions.`;

    // Map client messages to Gemini contents structure
    // Gemini 3.5 expects standard structure
    const contents = messages.map((m: any) => ({
      role: m.sender === 'user' ? 'user' : 'model',
      parts: [{ text: m.content }]
    }));

    // Generate content using gemini-3.5-flash
    const response = await ai.models.generateContent({
      model: "gemini-3.5-flash",
      contents,
      config: {
        systemInstruction,
        temperature: 0.7,
      }
    });

    res.json({ 
      content: response.text || "I was unable to compile a system analysis response. Please check network logs.",
      sender: "assistant"
    });

  } catch (error: any) {
    console.error("Gemini API server-side call error:", error);
    res.status(500).json({ 
      error: error.message || "Internal server error contacting distributed coprocessor." 
    });
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
    console.log(`System Node Visualizer server running on port ${PORT}`);
  });
}

startServer();
