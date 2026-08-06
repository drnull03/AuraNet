const { connect, StringCodec } = require("nats");

const NATS_URL = "nats://127.0.0.1:4222"; 
const sc = StringCodec();

async function runSniffer() {
    try {
        console.log(`\n  AuraNet Privacy Audit: Connecting to Message Broker...`);
        const nc = await connect({ servers: NATS_URL });
        console.log(`Connected successfully! Tapping into 'auranet.events.>'`);
        console.log(` Waiting for Edge Nodes to transmit telemetry...\n`);

        const sub = nc.subscribe("auranet.events.>");
        
        for await (const msg of sub) {
            const decodedData = JSON.parse(sc.decode(msg.data));
            console.log(`\n==================================================`);
            console.log(` 📡 INTERCEPTED TELEMETRY: ${msg.subject}`);
            console.log(`==================================================`);
            console.log(JSON.stringify(decodedData, null, 2));
            console.log(`==================================================\n`);
        }
    } catch (err) {
        console.error(" Connection Error (Is the NATS port-forward running?):", err.message);
    }
}

runSniffer();
