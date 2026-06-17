// index.js
const { connect, StringCodec } = require("nats");
const { determineVirtualPatch } = require("./virtual-patches/rules");

const NATS_URL = process.env.NATS_URL || "nats://127.0.0.1:4222";
const sc = StringCodec();

async function startAutoHeal() {
    try {
        console.log(`[AutoHeal] Connecting to NATS at ${NATS_URL}...`);
        const nc = await connect({ servers: NATS_URL });
        console.log("[AutoHeal] Connected to NATS broker successfully!");

        // Subscribe to the exact subject the ZTC publishes to
        const sub = nc.subscribe("auranet.commands.autoheal.>");
        console.log("[AutoHeal] 🎧 Listening for ZTC Execution Commands...\n");

        for await (const msg of sub) {
            const command = JSON.parse(sc.decode(msg.data));
            
            console.log(`\n🚨 [AutoHeal] RECEIVED KILL ORDER!`);
            console.log(`Target Workload: ${command.target_workload}`);
            console.log(`Threat Signatures:`, command.threat_signatures);

            // Ask the rule engine which patch to apply
            const targetPatch = determineVirtualPatch(command.threat_signatures);
            console.log(`[AutoHeal] 🛡️ Selected Virtual Patch: ${targetPatch}`);
            
            console.log(`[AutoHeal] ⏳ K8s execution paused for Step 2 verification.\n`);
        }

    } catch (err) {
        console.error("[AutoHeal] Fatal Error:", err);
        process.exit(1);
    }
}

startAutoHeal();