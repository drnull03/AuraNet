const { connect, StringCodec } = require("nats");
const trustEngine = require("./trust-engine"); 

// In production, we'll use the K8s DNS name. For local testing, defaults to localhost.
const NATS_URL = process.env.NATS_URL || "nats://auranet-nats-broker.auranet-messaging.svc.cluster.local:4222";
const sc = StringCodec();

async function startZTC() {
    try {
        console.log(`[ZTC] Connecting to NATS at ${NATS_URL}...`);
        const nc = await connect({ servers: NATS_URL });
        console.log("[ZTC] Connected to NATS broker successfully (RAM Mode)!");

        // The RAM Buffer for micro-batching
        let alertBuffer = [];

        // Subscribe to all events directly in RAM (No JetStream)
        const sub = nc.subscribe("auranet.events.>");
        console.log(`[ZTC] Subscribed to 'auranet.events.>'. Listening for real-time alerts...`);

        const remediationSub = nc.subscribe("auranet.remediated.>");
        (async () => {
            for await (const msg of remediationSub) {
                const workload = msg.subject.split('.').pop();
                trustEngine.resetWorkload(workload);
            }
        })();
        


        // Asynchronously collect incoming alerts into the RAM buffer
        // Asynchronously collect incoming alerts into the RAM buffer
        (async () => {
            for await (const msg of sub) {
                try {
                    const decodedData = JSON.parse(sc.decode(msg.data));
                    console.log(`\n[ZTC] 🔍 GHOST PACKET INTERCEPTED -> Subject: ${msg.subject}`);
                    console.log(`[ZTC] Threat Type: ${decodedData.threat}`);
                    
                    // This will print the raw Hubble JSON that triggered the AI
                    if (decodedData.raw_context) {
                        const contextObj = JSON.parse(decodedData.raw_context);
                        const httpData = contextObj.flow?.l7?.http || {};
                        console.log(`[ZTC] Target URL: ${httpData.url}`);
                        console.log(`[ZTC] Node Source: ${contextObj.node_name}`);
                    }
                    console.log(`---------------------------------------------------`);
                    
                    alertBuffer.push({ subject: msg.subject, data: decodedData });
                } catch (err) {
                    console.error("[ZTC] Failed to decode incoming message:", err);
                }
            }
        })();

        const THROTTLE_INTERVAL_MS = 1000; 
        console.log(`[ZTC] Initialization complete. Throttled Worker Loop set to ${THROTTLE_INTERVAL_MS}ms.\n`);

        // Process the buffer every second
        setInterval(() => {
            // Skip processing if no new alerts arrived
            if (alertBuffer.length === 0) return;

            console.log(`\n[${new Date().toISOString()}] Processing ${alertBuffer.length} batched alerts...`);
            
            // Copy the current buffer and immediately clear it to catch new alerts
            const batchedAlerts = [...alertBuffer];
            alertBuffer = []; 

            // Pass the batched array to trust-engine.js
            const condemnedWorkloads = trustEngine.evaluateBatch(batchedAlerts);
            
            // Fire execution commands to the AutoHeal microservice
            if (condemnedWorkloads.length > 0) {
                console.log(`\n[ZTC] 🚨 INITIATING QUARANTINE FOR ${condemnedWorkloads.length} WORKLOAD(S)...`);
                
                for (const target of condemnedWorkloads) {
                    const commandPayload = {
                        action: "quarantine",
                        target_workload: target.workload,
                        final_score: target.finalScore,
                        threat_signatures: target.reasons,
                        timestamp: Date.now()
                    };

                    // Route the command via a dedicated action subject
                    const commandSubject = `auranet.commands.autoheal.${target.workload}`;
                    
                    // Publish the payload directly to the network
                    nc.publish(commandSubject, sc.encode(JSON.stringify(commandPayload)));
                    
                    console.log(`[ZTC] Fired AutoHeal Command -> Subject: ${commandSubject}`);
                }
                console.log("\n");
            }
        }, THROTTLE_INTERVAL_MS);

        const setupShutdown = (signal) => {
            process.on(signal, async () => {
                console.log(`\n[ZTC] Received ${signal}. Closing NATS connection cleanly...`);
                await nc.close();
                console.log("[ZTC] NATS connection closed. Exiting process.");
                process.exit(0);
            });
        };
        setupShutdown("SIGTERM");
        setupShutdown("SIGINT");

    } catch (err) {
        console.error("[ZTC] Fatal Error during startup:", err);
        process.exit(1);
    }
}

startZTC();