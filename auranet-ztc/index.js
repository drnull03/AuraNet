const { connect, StringCodec } = require("nats");

// In production, we'll use the K8s DNS name. For local testing, defaults to localhost.
const NATS_URL = process.env.NATS_URL || "nats://auranet-nats-broker.auranet-messaging.svc.cluster.local:4222";
const sc = StringCodec();

async function startZTC() {
    try {
        console.log(`[ZTC] Connecting to NATS at ${NATS_URL}...`);
        // Establish connection to the NATS broker
        const nc = await connect({ servers: NATS_URL });
        console.log("[ZTC] Connected to NATS broker successfully!");

        // Initialize the JetStream context for durable storage and Pull mode capabilities
        const js = nc.jetstream();

        // Throttling configuration: Wake up every 10 seconds for the demo
       
        const THROTTLE_INTERVAL_MS = 10 * 1000; 
        
        console.log(`[ZTC] Initialization complete. Entering sleep state.`);
        console.log(`[ZTC] Throttled Worker Loop set to wake up every ${THROTTLE_INTERVAL_MS / 1000} seconds.\n`);

        // The Throttled Pull Loop (Tumbling window for fetching, sliding window for scoring)
        setInterval(async () => {
            console.log(`[${new Date().toISOString()}] Waking up to process security alerts...`);
            
            try {
                // --> STEP 3 WILL GO HERE: Fetch a batch of up to 30 messages from JetStream
                // --> STEP 4 WILL GO HERE: Pass the batch to trust-engine.js sliding window
                // --> STEP 5 WILL GO HERE: Send quarantine requests to auranet-autoheal via NATS
            } catch (loopError) {
                console.error("[ZTC] Error during processing tick:", loopError);
            }

            console.log(`[${new Date().toISOString()}] Processing complete. Going back to sleep.\n`);
        }, THROTTLE_INTERVAL_MS);

        // Handle clean termination signals from Kubernetes (SIGTERM/SIGINT)
        const setupShutdown = (signal) => {
            process.on(signal, async () => {
                console.log(`[ZTC] Received ${signal}. Closing NATS connection cleanly...`);
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

// Execute the controller shell
startZTC();