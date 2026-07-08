const { connect, StringCodec } = require('nats');
const fetch = require('node-fetch');

// Set Jest's global test and hook timeout to 15 seconds to allow for async K8s/AI pipelines
jest.setTimeout(15000);

const NATS_URL = process.env.NATS_URL || "nats://localhost:4222";
const GATEWAY_URL = process.env.GATEWAY_URL || "http://localhost:10000";
const sc = StringCodec();





let nc;



/**
 * Wraps Node Fetch with a retry mechanism to handle Kubernetes pod cycling
 * and temporary port-forward tunnel drops.
 */
async function fetchWithRetry(url, retries = 5, delayMs = 2000) {
    for (let i = 0; i < retries; i++) {
        try {
            const res = await fetch(url);
            return res; // Success!
        } catch (err) {
            if (i === retries - 1) throw err; // Out of retries
            console.log(`[Network] Tunnel syncing or pod booting. Retrying in ${delayMs/1000}s...`);
            await new Promise(resolve => setTimeout(resolve, delayMs));
        }
    }
}

/**
 * Robust asynchronous observer that captures the next message on a wildcard subject
 * matching a specific internal criteria function.
 */
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
                } catch (e) {
                    // Ignore malformed JSON or parsing errors from other test noise
                }
            }
        })();
    });
}

function ensureNoNatsTraffic(subjectWildcard, listenWindowMs = 3000) {
    return new Promise((resolve, reject) => {
        const sub = nc.subscribe(subjectWildcard);
        
        const timeout = setTimeout(() => {
            sub.unsubscribe();
            resolve(true);
        }, listenWindowMs);

        (async () => {
            for await (const msg of sub) {
                clearTimeout(timeout);
                sub.unsubscribe();
                reject(new Error(`❌ False Positive: Detected unexpected traffic on ${msg.subject}`));
            }
        })();
    });
}

describe('AuraNet End-to-End Security Integrations', () => {
    
    beforeAll(async () => {
        nc = await connect({ servers: NATS_URL });
        console.log(`[Test Suite] Connected to NATS Observer on ${NATS_URL}`);
    });

    afterAll(async () => {
        if (nc) await nc.close();
    });

    // Clean cooldown that cleanly returns a promise without hitting the 5s hook limit
    afterEach(async () => {
        await new Promise(resolve => setTimeout(resolve, 6000));
    });


    test('1. [BASELINE] Normal traffic should pass without triggering AI or Runtime', async () => {
        const targetUrl = `${GATEWAY_URL}/api/loans/export?id=123`;
        
        const response = await fetchWithRetry(targetUrl);
        expect(response.status).toBe(200);

        await expect(ensureNoNatsTraffic("auranet.events.>", 3000)).resolves.toBe(true);
    });


    test('2. [L7 SHADOW ENGINE] SQLi should be intercepted and quarantine applied', async () => {
        // 1. Fully URL-encode the payload to prevent early truncation
        // 2. Use a distinct SQLi pattern that forces anomalous feature vector evaluation
        const maliciousPayload = encodeURIComponent("1' UNION SELECT username, password FROM users--");
        const targetUrl = `${GATEWAY_URL}/api/accounts?id=${maliciousPayload}`;
        
        console.log(`[Test 2 Executing] Firing payload: ${targetUrl}`);

        // Listen to the wildcard pool, matching the threat type inside the body
        const alertPromise = listenForEvent("auranet.events.ai.>", (payload) => {
            return payload.threat === "l7_payload_anomaly";
        });

        const commandPromise = listenForEvent("auranet.commands.autoheal.>", (payload) => {
            return payload.action === "quarantine";
        });

        // Fire malicious request
        fetchWithRetry(targetUrl).catch(() => {});

        const alert = await alertPromise;
        expect(alert.threat).toBe("l7_payload_anomaly");
        // Ensure probability field exists or remove if your model uses a raw reconstruction score
        if (alert.probability) {
            expect(alert.probability).toBeGreaterThan(0.01);
        }

        const command = await commandPromise;
        expect(command.action).toBe("quarantine");
        console.log(`[Test Match] Verified AI Threat triggered mitigation for: ${command.target_workload}`);
    });

    test('3. [eBPF RUNTIME] Command Injection should trigger active defense', async () => {
        const targetUrl = `${GATEWAY_URL}/api/loans/export?id=123%3B%20cat%20/etc/passwd`;
        
        // Listen to runtime events, resolving if either eBPF signature catches the breach
        const alertPromise = listenForEvent("auranet.events.runtime.>", (payload) => {
            return ["reverse_shell_detected", "unauthorized_file_read"].includes(payload.threat);
        });

        const commandPromise = listenForEvent("auranet.commands.autoheal.>", (payload) => {
            return payload.action === "quarantine";
        });

        fetchWithRetry(targetUrl).catch(() => {});

        const alert = await alertPromise;
        expect(["reverse_shell_detected", "unauthorized_file_read"]).toContain(alert.threat);

        const command = await commandPromise;
        expect(command.action).toBe("quarantine");
        console.log(`[Test Match] Verified eBPF Runtime triggered mitigation for: ${command.target_workload}`);
    });

});