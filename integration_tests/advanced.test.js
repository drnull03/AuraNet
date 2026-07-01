const { connect, StringCodec } = require('nats');
const fetch = require('node-fetch');

jest.setTimeout(25000); // 25s timeout for complex state machine tests

const NATS_URL = process.env.NATS_URL || "nats://localhost:4222";
const GATEWAY_URL = process.env.GATEWAY_URL || "http://localhost:10000";
const sc = StringCodec();

let nc;

// Resilient Fetch 
async function fetchWithRetry(url, retries = 5, delayMs = 2000) {
    for (let i = 0; i < retries; i++) {
        try {
            const res = await fetch(url);
            return res; 
        } catch (err) {
            if (i === retries - 1) throw err; 
            await new Promise(resolve => setTimeout(resolve, delayMs));
        }
    }
}

// Event Listeners
function listenForEvent(subjectWildcard, criteriaFn, timeoutMs = 8000) {
    return new Promise((resolve, reject) => {
        const sub = nc.subscribe(subjectWildcard);
        const timeout = setTimeout(() => {
            sub.unsubscribe();
            reject(new Error(`⏳ Timeout: Did not match expected event stream on ${subjectWildcard}`));
        }, timeoutMs);

        (async () => {
            for await (const msg of sub) {
                try {
                    const payload = JSON.parse(sc.decode(msg.data));
                    if (criteriaFn(payload, msg.subject)) {
                        clearTimeout(timeout);
                        sub.unsubscribe();
                        resolve(payload);
                        break;
                    }
                } catch (e) {}
            }
        })();
    });
}

/**
 * Listens for a specific duration and returns ALL matching messages.
 * Used to verify the deduplication locks are working.
 */
function collectEvents(subjectWildcard, durationMs = 5000) {
    return new Promise((resolve) => {
        const msgs = [];
        const sub = nc.subscribe(subjectWildcard);
        
        (async () => {
            for await (const msg of sub) {
                try {
                    msgs.push(JSON.parse(sc.decode(msg.data)));
                } catch (e) {}
            }
        })();

        setTimeout(() => {
            sub.unsubscribe();
            resolve(msgs);
        }, durationMs);
    });
}

// Test Suite 

describe('AuraNet Advanced State Machine Integrations', () => {
    
    beforeAll(async () => {
        nc = await connect({ servers: NATS_URL });
        console.log(`[Advanced Suite] Connected to NATS Observer on ${NATS_URL}`);
    });

    afterAll(async () => {
        if (nc) await nc.close();
    });

    // 8-second cooldown to let AutoHeal completely reset the cluster state between tests
    afterEach(async () => {
        await new Promise(resolve => setTimeout(resolve, 8000));
    });


    test('1. [SYMBOLIC OVERRIDE] Null Byte Evasion instantly triggers Quarantine', async () => {
        // The %00 null byte triggers the deterministic regex, bypassing the neural network
        const targetUrl = `${GATEWAY_URL}/api/accounts?id=3%00`;
        
        const alertPromise = listenForEvent("auranet.events.ai.>", (payload) => {
            return payload.threat === "symbolic_null_byte_evasion";
        });

        const commandPromise = listenForEvent("auranet.commands.autoheal.>", (payload) => {
            return payload.action === "quarantine";
        });

        fetchWithRetry(targetUrl).catch(() => {});

        const alert = await alertPromise;
        expect(alert.threat).toBe("symbolic_null_byte_evasion");
        // Symbolic probabilities are hardcoded to -1
        expect(alert.probability).toBe(-1); 

        const command = await commandPromise;
        expect(command.action).toBe("quarantine");
    });


    test('2. [CONCURRENCY LOCK] Distributed flooding yields exactly ONE AutoHeal command', async () => {
        const maliciousPayload = encodeURIComponent("1' UNION SELECT * FROM secrets--");
        const targetUrl = `${GATEWAY_URL}/api/accounts?id=${maliciousPayload}`;
        
        // Fire 10 concurrent, simultaneous attacks to flood the ZTC queue
        const floodRequests = Array(10).fill(targetUrl).map(url => fetchWithRetry(url).catch(() => {}));
        Promise.all(floodRequests);

        // Listen to the AutoHeal command channel for a full 5 seconds
        const firedCommands = await collectEvents("auranet.commands.autoheal.>", 5000);

        // Filter commands to just this workload in case of cluster noise
        const gatewayCommands = firedCommands.filter(c => c.target_workload === 'api-gateway');

        //Assert the ZTC healingLock prevented duplicate commands
        expect(gatewayCommands.length).toBeGreaterThan(0);
        expect(gatewayCommands.length).toBe(1); 
        console.log(`[Test Match] 10 concurrent threats blocked. Only 1 quarantine issued. Queue flooding mitigated.`);
    });


    test('3. [TRUST DEGRADATION] The 3-Strike Rule (Over Time)', async () => {
        // We use a mock workload name so we don't accidentally kill the real gateway during this isolated test
        const targetWorkload = "mock-payment-service"; 
        const subject = `auranet.events.ai.${targetWorkload}`;
        const payload = sc.encode(JSON.stringify({ threat: "network_behavior_anomaly", probability: 0.95 }));

        console.log(`[Test 3] Simulating slow, persistent attack against ${targetWorkload}...`);

        nc.publish(subject, payload);
        const strike1Commands = await collectEvents(`auranet.commands.autoheal.${targetWorkload}`, 2000);
        expect(strike1Commands.length).toBe(0); // Should survive

        await new Promise(resolve => setTimeout(resolve, 5200));

        nc.publish(subject, payload);
        const strike2Commands = await collectEvents(`auranet.commands.autoheal.${targetWorkload}`, 2000);
        expect(strike2Commands.length).toBe(0); // Should survive again

        await new Promise(resolve => setTimeout(resolve, 5200));

        const finalCommandPromise = listenForEvent(`auranet.commands.autoheal.${targetWorkload}`, p => p.action === "quarantine");
        nc.publish(subject, payload);
        
        const finalCommand = await finalCommandPromise;
        expect(finalCommand).toBeDefined();
        expect(finalCommand.action).toBe("quarantine");
        
        console.log(`[Test Match] Workload survived two 40-point anomalies. Quarantined on the third strike.`);
    });
});
