const { connect, StringCodec } = require('nats');
const fetch = require('node-fetch');

jest.setTimeout(35000); // 35s timeout to allow for full K8s pod cycling

const NATS_URL = process.env.NATS_URL || "nats://localhost:4222";
const GATEWAY_URL = process.env.GATEWAY_URL || "http://localhost:10000";
const sc = StringCodec();

let nc;

//  Resilient Fetch 
async function fetchWithRetry(url, options = {}, retries = 5, delayMs = 2000) {
    for (let i = 0; i < retries; i++) {
        try {
            const res = await fetch(url, options);
            return res; 
        } catch (err) {
            if (i === retries - 1) throw err; 
            await new Promise(resolve => setTimeout(resolve, delayMs));
        }
    }
}

//  Event Listeners
function listenForEvent(subjectWildcard, criteriaFn, timeoutMs = 8000) {
    return new Promise((resolve, reject) => {
        const sub = nc.subscribe(subjectWildcard);
        const timeout = setTimeout(() => {
            sub.unsubscribe();
            reject(new Error(`Timeout: Did not match expected event stream on ${subjectWildcard}`));
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

//  Test Suite 

describe('AuraNet Edge Cases & Closed-Loop Integration', () => {
    
    beforeAll(async () => {
        nc = await connect({ servers: NATS_URL });
        console.log(`[Edge Cases Suite] Connected to NATS Observer on ${NATS_URL}`);
    });

    afterAll(async () => {
        if (nc) await nc.close();
    });

    // 8-second cooldown to let AutoHeal completely reset the cluster state between tests
    afterEach(async () => {
        await new Promise(resolve => setTimeout(resolve, 8000));
    });


    test('1. [CLOSED-LOOP RECOVERY] AutoHeal broadcasts remediation signal to reset ZTC', async () => {
        const targetUrl = `${GATEWAY_URL}/api/accounts?id=1 OR 1=1`;
        
        // Listen specifically for the remediation success signal
        const remediationPromise = listenForEvent("auranet.remediated.api-gateway", (payload) => {
            return payload.status === "cleared";
        }, 20000); // 20s timeout because cycling K8s pods takes time

        // Fire malicious request to trigger the AutoHeal pipeline
        fetchWithRetry(targetUrl).catch(() => {});

        // Wait for AutoHeal to do its job and report back
        const remediationSignal = await remediationPromise;
        expect(remediationSignal).toBeDefined();
        expect(remediationSignal.status).toBe("cleared");
        
        console.log(`[Test Match] Verified AutoHeal cleanly eradicated pods and broadcasted recovery signal.`);
    });

    test('2. [DOUBLE JEOPARDY] ZTC releases healing locks and can re-quarantine a remediated pod', async () => {
        // Target a different real workload to ensure a clean K8s environment
        const targetWorkload = "frontend-ui";
        const subject = `auranet.events.ai.${targetWorkload}`;
        
        // Simulating a 99% confidence L7 anomaly
        const payload = sc.encode(JSON.stringify({ threat: "l7_payload_anomaly", probability: 0.99 }));

        console.log(`[Test 2] Initiating Strike 1 (Initial Infection on ${targetWorkload})...`);
        
        // STRIKE 1: Publish alert directly to NATS (Bypassing AI Engine's 30s dedupe)
        nc.publish(subject, payload);

        // Wait for AutoHeal to cycle the K8s pod and report success
        await listenForEvent(`auranet.remediated.${targetWorkload}`, p => p.status === "cleared", 20000);
        console.log(`[Test 2] Strike 1 remediated. Simulating immediate re-infection...`);

        // Wait 1.5 seconds to ensure the ZTC has fully flushed the lock release in RAM
        await new Promise(resolve => setTimeout(resolve, 1500));

        // STRIKE 2: Publish the second attack immediately after recovery
        nc.publish(subject, payload);

        // Verify AutoHeal is triggered AGAIN. If the healingLock wasn't released, this will timeout.
        const secondQuarantine = await listenForEvent(`auranet.commands.autoheal.${targetWorkload}`, p => p.action === "quarantine", 15000);

        expect(secondQuarantine).toBeDefined();
        expect(secondQuarantine.action).toBe("quarantine");
        console.log(`[Test Match] Verified ZTC successfully unlocked and caught a second distinct attack cycle.`);
    });


    
});
