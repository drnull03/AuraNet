const { connect, StringCodec } = require('nats');
const fetch = require('node-fetch');

// --- Configuration ---
const NATS_URL = process.env.NATS_URL || "nats://localhost:4222";
const GATEWAY_URL = process.env.GATEWAY_URL || "http://localhost:8080";
const sc = StringCodec();

let nc;

// --- Helper Functions ---

/**
 * Listens for a specific NATS subject and resolves when the message arrives.
 * Fails the test if it times out.
 */
function waitForNatsMessage(subject, timeoutMs = 5000) {
    return new Promise((resolve, reject) => {
        // { max: 1 } automatically unsubscribes after receiving the first message
        const sub = nc.subscribe(subject, { max: 1 });
        
        const timeout = setTimeout(() => {
            sub.unsubscribe();
            reject(new Error(`⏳ Timeout: Did not receive NATS message on ${subject}`));
        }, timeoutMs);

        (async () => {
            for await (const msg of sub) {
                clearTimeout(timeout);
                resolve(JSON.parse(sc.decode(msg.data)));
            }
        })();
    });
}

/**
 * Listens for a subject and resolves ONLY if NO message arrives within the window.
 * Used for testing Benign traffic to ensure no false positives.
 */
function ensureNoNatsMessage(subject, listenWindowMs = 3000) {
    return new Promise((resolve, reject) => {
        const sub = nc.subscribe(subject);
        
        const timeout = setTimeout(() => {
            sub.unsubscribe();
            resolve(true); // Success: No message arrived!
        }, listenWindowMs);

        (async () => {
            for await (const msg of sub) {
                clearTimeout(timeout);
                sub.unsubscribe();
                const data = JSON.parse(sc.decode(msg.data));
                reject(new Error(`❌ False Positive: Received unexpected alert on ${subject} -> ${data.threat}`));
            }
        })();
    });
}

// --- Test Suite ---

describe('AuraNet End-to-End Security Integrations', () => {
    
    // Connect to NATS before any tests run
    beforeAll(async () => {
        nc = await connect({ servers: NATS_URL });
        console.log(`[Test Suite] Connected to NATS Observer on ${NATS_URL}`);
    });

    // Close connection after tests finish
    afterAll(async () => {
        await nc.close();
    });

    // We add a delay between tests to ensure Kubernetes has time to cycle pods and lift quarantines
    afterEach(() => new Promise(resolve => setTimeout(resolve, 6000)));

    // ====================================================================

    test('1. [BASELINE] Normal traffic should pass without triggering AI or Runtime', async () => {
        const targetUrl = `${GATEWAY_URL}/api/loans/export?id=123`;
        
        // Fire request
        const response = await fetch(targetUrl);
        expect(response.status).toBe(200);

        // Assert that NO alerts are fired for 3 seconds
        await expect(ensureNoNatsMessage("auranet.events.>", 3000)).resolves.toBe(true);
    }, 10000); // 10s Jest timeout

    // ====================================================================

    test('2. [L7 SHADOW ENGINE] SQLi should be intercepted and quarantine applied', async () => {
        const targetUrl = `${GATEWAY_URL}/api/accounts?id=1 OR 1=1`;
        
        // Setup NATS Listeners
        const alertPromise = waitForNatsMessage("auranet.events.ai.api-gateway");
        const commandPromise = waitForNatsMessage("auranet.commands.autoheal.api-gateway");

        // Fire malicious request (We ignore the HTTP response, as AutoHeal might cut the connection)
        fetch(targetUrl).catch(() => {});

        // 1. Assert AI intercepted the payload
        const alert = await alertPromise;
        expect(alert.threat).toBe("l7_payload_anomaly");
        expect(alert.source).not.toBeNull();

        // 2. Assert ZTC fired the AutoHeal command
        const command = await commandPromise;
        expect(command.action).toBe("quarantine");
        expect(command.target_workload).toBe("api-gateway");
    }, 10000);

    // ====================================================================

    test('3. [eBPF RUNTIME] Command Injection should trigger reverse_shell_detected', async () => {
        // Using url encoding for the semicolon/space to ensure it hits the backend cleanly
        const targetUrl = `${GATEWAY_URL}/api/loans/export?id=123%3B%20cat%20/etc/passwd`;
        
        // Setup NATS Listeners
        const alertPromise = waitForNatsMessage("auranet.events.runtime.loan-service");
        const commandPromise = waitForNatsMessage("auranet.commands.autoheal.loan-service");

        // Fire malicious request
        fetch(targetUrl).catch(() => {});

        // 1. Assert eBPF Runtime agent intercepted the shell
        const alert = await alertPromise;
        // Depending on exact map timing, it might be unauthorized_file_read or reverse_shell_detected
        expect(["reverse_shell_detected", "unauthorized_file_read"]).toContain(alert.threat);

        // 2. Assert ZTC fired the AutoHeal command for the loan service
        const command = await commandPromise;
        expect(command.action).toBe("quarantine");
        expect(command.target_workload).toBe("loan-service");
    }, 10000);

});
