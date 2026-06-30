const { connect, StringCodec } = require("nats");
const trustEngine = require("./trust-engine"); 

// In production, we'll use the K8s DNS name. For local testing, defaults to localhost.
const NATS_URL = process.env.NATS_URL || "nats://auranet-nats-broker.auranet-messaging.svc.cluster.local:4222";
const sc = StringCodec();

async function startZTC() {
    try {
        console.log(`[ZTC] Connecting to NATS at ${NATS_URL}...`);
        const nc = await connect({ servers: NATS_URL });
        console.log("[ZTC] Connected to NATS broker successfully!");

        // Initialize JetStream and the JetStream Manager
        const js = nc.jetstream();
        const jsm = await nc.jetstreamManager();

        // Ensure the Stream exists to store our alerts durably
        // This acts as the "Hard Drive" for the alerts. 
        //jetstreams here read from harddrive not ram for durablity 
        const streamName = "AURANET_EVENTS";
        try {
            await jsm.streams.add({
                name: streamName,
                subjects: ["auranet.events.>"], // Listen to all AI and Runtime events
                retention: "workqueue" // Messages are deleted once ACK'd
            });
            console.log(`[ZTC] JetStream '${streamName}' initialized.`);
        } catch (err) {
            console.log(`[ZTC] Stream check: ${err.message}`);
        }

        //  Create the Durable Pull Consumer
        // the consumer is attached to this process
        const consumerName = "ztc_consumer";
        await jsm.consumers.add(streamName, {
            durable_name: consumerName,
            ack_policy: "explicit", // We must manually ACK after processing
        });
        //attach the consumer to this process using the js communicator
        const consumer = await js.consumers.get(streamName, consumerName);
        console.log(`[ZTC] Durable Pull Consumer '${consumerName}' ready.`);

        const THROTTLE_INTERVAL_MS = 1000; 
        console.log(`[ZTC] Initialization complete. Entering sleep state.`);
        console.log(`[ZTC] Throttled Worker Loop set to wake up every ${THROTTLE_INTERVAL_MS / 1000} seconds.\n`);

        //  The Throttled Pull Loop 
        setInterval(async () => {
            console.log(`[${new Date().toISOString()}] Waking up to process security alerts...`);
            
            try {
                // Ask JetStream for up to 30 messages. If empty, wait max 2 seconds.
                // this connected to the harddrive 
                const messages = await consumer.fetch({ max_messages: 30, expires: 2000 });
                
                let processedCount = 0;
                let batchedAlerts = [];

                for await (const msg of messages) {
                    const decodedData = JSON.parse(sc.decode(msg.data));
                    const subject = msg.subject; // e.g., auranet.events.runtime.payment-api
                    
                    console.log(`[ZTC] Read Alert -> Subject: ${subject}`);
                    batchedAlerts.push({ subject, data: decodedData });

                    // Acknowledge the message so it gets removed from the queue
                    msg.ack(); 
                    processedCount++;
                }

                if (processedCount === 0) {
                    console.log(`[ZTC] Queue is empty. No threats detected.`);
                } else {
                    console.log(`[ZTC] Successfully ACK'd ${processedCount} alerts.`);
                    
                    //  Pass `batchedAlerts` to trust-engine.js
                    const condemnedWorkloads = trustEngine.evaluateBatch(batchedAlerts);
                    
                    //  Fire execution commands to the AutoHeal microservice
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
                            console.log(`[ZTC] Payload:`, commandPayload);
                        }
                        console.log("\n");
                    }
                }

            } catch (loopError) {
                // JetStream fetch throws a harmless error if it expires with 0 messages. We ignore it.
                if (loopError.code !== '404' && loopError.code !== 'TIMEOUT') {
                    console.error("[ZTC] Error pulling messages:", loopError);
                }
            }

            console.log(`[${new Date().toISOString()}] Going back to sleep.\n`);
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