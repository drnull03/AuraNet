// this file is meant as an integration test 


const { connect, StringCodec } = require("nats");

const NATS_URL = "nats://127.0.0.1:4222";
const sc = StringCodec();

async function runLiveTests() {
    try {
        const nc = await connect({ servers: NATS_URL });
        console.log(`[Tester]  Connected to NATS at ${NATS_URL}`);

        // phase 1 mock the autoheal
        // We set up the listener first so it doesn't miss the command
        const sub = nc.subscribe("auranet.commands.autoheal.>");
        
        console.log("[Tester] 🎧 Listening for ZTC Execution Commands...");
        
        // Asynchronous loop to catch the command when the ZTC fires it
        (async () => {
            for await (const msg of sub) {
                const command = JSON.parse(sc.decode(msg.data));
                console.log(`\n==================================================`);
                console.log(`✅ TEST PASSED: QUARANTINE COMMAND INTERCEPTED!`);
                console.log(`==================================================`);
                console.log(`Target: ${command.target_workload}`);
                console.log(`Final Trust Score: ${command.final_score}`);
                console.log(`Signatures:`, command.threat_signatures);
                console.log(`==================================================\n`);
                
                // Close the connection and exit successfully
                await nc.close();
                process.exit(0); 
            }
        })();


        // phase 2 fire attack sequence
        console.log("\n[Tester]  Firing Simulated Attack Sequence into JetStream...");
        const targetWorkload = "payment-api";

        // attack 1: Neural AI detects weird traffic (20% confidence = -20 points)
        // Trust Score drops 100 -> 80
        nc.publish(`auranet.events.ai.${targetWorkload}`, sc.encode(JSON.stringify({
            probability: 0.20 
        })));
        console.log(`  -> Sent Neural AI Anomaly (20%)`);

        // attack 2: Runtime catches a file read (-60 points)
        // Trust Score drops 80 -> 20 (Still above the quarantine threshold of 10!)
        nc.publish(`auranet.events.runtime.${targetWorkload}`, sc.encode(JSON.stringify({
            threat: "unauthorized_file_read"
        })));
        console.log(`  -> Sent Runtime Alert (unauthorized_file_read)`);

        // Attack 3: Symbolic AI definitively catches an anomaly using your -1 logic (-30 points)
        // Trust Score drops 20 -> -10 (Breaches the threshold!)
        nc.publish(`auranet.events.ai.${targetWorkload}`, sc.encode(JSON.stringify({
            threat: "unknown_anomaly",
            probability: -1
        })));
        console.log(`  -> Sent Symbolic AI Alert (-1 explicit hit)`);

        console.log("\n[Tester] ⏳ Attack payload delivered. Waiting for ZTC to wake up and process...");

        // Safety timeout in case the ZTC fails to fire
        setTimeout(() => {
            console.error("\n❌ TEST FAILED: Timeout reached. The ZTC never issued a quarantine command.");
            process.exit(1);
        }, 15000); // 15 seconds allows for at least one full 10-second ZTC tick

    } catch (err) {
        console.error("[Tester] Fatal Error:", err);
    }
}

runLiveTests();