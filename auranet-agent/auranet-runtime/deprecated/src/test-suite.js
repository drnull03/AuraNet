const assert = require('assert');




// Extracted .conf parser
function parseConf(rawData) {
    const map = {};
    rawData.split('\n').forEach(line => {
        const trimmed = line.trim();
        if (trimmed && !trimmed.startsWith('#')) {
            const splitIndex = trimmed.indexOf('=');
            if (splitIndex > 0) {
                map[trimmed.substring(0, splitIndex).trim()] = trimmed.substring(splitIndex + 1).trim();
            }
        }
    });
    return map;
}

// Extracted Event Processor
function parseEvent(eventJson, THREAT_MAP, recentAlerts, mockPublishFn) {
    try {
        const event = JSON.parse(eventJson);
        
        let processData = null;
        let functionName = null;
        let isExecEvent = false;

        if (event.process_exec) {
            processData = event.process_exec.process;
            isExecEvent = true;
        } else if (event.process_kprobe) {
            processData = event.process_kprobe.process;
            functionName = event.process_kprobe.function_name;
        } else {
            return; 
        }
        
        if (!processData || !processData.pod) return; 

        const namespace = processData.pod.namespace;
        const workload = processData.pod.workload || 'unknown-workload';
        const podName = processData.pod.name; 
        
        if (namespace === 'kube-system' || namespace === 'auranet-namespace') return;

        let threatSignature = null;
        let actionContext = '';

        if (isExecEvent) {
            const binary = processData.binary.split('/').pop();
            threatSignature = THREAT_MAP[binary];
            actionContext = `Executed binary: ${binary}`;
        } else if (functionName && functionName.includes('security_file_open')) {
            const args = event.process_kprobe.args || [];
            if (args.length > 0 && args[0].file_arg) {
                const filePath = args[0].file_arg.path;
                const fileName = filePath.split('/').pop();
                
                threatSignature = THREAT_MAP[filePath] || 
                                  THREAT_MAP[fileName] || 
                                  (filePath.includes('token') ? 'k8s_token_theft' : null) ||
                                  (filePath.includes('.ssh') ? 'ssh_key_access' : null);
                
                actionContext = `Accessed file: ${filePath}`;
            }
        }

        if (threatSignature) {
            const now = Date.now();
            const alertKey = `${podName}-${threatSignature}-${actionContext}`;
            
            // Deduplication check (2000 ms)
            if (recentAlerts.has(alertKey) && (now - recentAlerts.get(alertKey) < 2000)) {
                return; 
            }
            
            recentAlerts.set(alertKey, now);

            const subject = `auranet.events.runtime.${workload}`;
            const payload = { source: "runtime_ebpf", threat: threatSignature, context: actionContext };
            
            mockPublishFn(subject, payload);
        }
    } catch (err) {
        // Silently ignore malformed JSON
    }
}


console.log("🧪 Starting AuraNet Runtime Test Suite...\n");
let passed = 0;
let failed = 0;

function runTest(testName, testFn) {
    try {
        testFn();
        console.log(`   ✅ PASS: ${testName}`);
        passed++;
    } catch (err) {
        console.error(`   ❌ FAIL: ${testName}`);
        console.error(`      -> ${err.message}`);
        failed++;
    }
}

// Global Mocks for Tests
const mockThreatMap = {
    'bash': 'reverse_shell_detected',
    '/etc/shadow': 'unauthorized_file_read'
};



runTest("Conf Parser correctly ignores comments and parses key=value", () => {
    const rawConf = `
    # This is a comment
    bash=reverse_shell_detected
    /etc/passwd=unauthorized_file_read
    `;
    const parsed = parseConf(rawConf);
    assert.strictEqual(parsed['bash'], 'reverse_shell_detected');
    assert.strictEqual(parsed['/etc/passwd'], 'unauthorized_file_read');
    assert.strictEqual(Object.keys(parsed).length, 2);
});

runTest("Event Parser catches process_exec events (e.g., bash)", () => {
    let publishCalled = false;
    const mockJson = JSON.stringify({
        process_exec: {
            process: { binary: "/bin/bash", pod: { name: "pod-1", namespace: "default", workload: "loan-service" } }
        }
    });
    
    parseEvent(mockJson, mockThreatMap, new Map(), (sub, pay) => {
        publishCalled = true;
        assert.strictEqual(sub, "auranet.events.runtime.loan-service");
        assert.strictEqual(pay.threat, "reverse_shell_detected");
    });
    assert.strictEqual(publishCalled, true, "NATS Publisher was not called");
});

runTest("Event Parser catches process_kprobe events (e.g., /etc/shadow)", () => {
    let publishCalled = false;
    const mockJson = JSON.stringify({
        process_kprobe: {
            function_name: "security_file_open",
            args: [{ file_arg: { path: "/etc/shadow" } }],
            process: { pod: { name: "pod-1", namespace: "default", workload: "records-service" } }
        }
    });
    
    parseEvent(mockJson, mockThreatMap, new Map(), (sub, pay) => {
        publishCalled = true;
        assert.strictEqual(pay.threat, "unauthorized_file_read");
    });
    assert.strictEqual(publishCalled, true);
});

runTest("Deduplication Cache drops identical alerts within 2 seconds", () => {
    let publishCount = 0;
    const recentAlerts = new Map();
    const mockJson = JSON.stringify({
        process_kprobe: {
            function_name: "security_file_open",
            args: [{ file_arg: { path: "/etc/shadow" } }],
            process: { pod: { name: "pod-1", namespace: "default", workload: "records-service" } }
        }
    });
    
    const mockPublish = () => { publishCount++; };

    // Fire it twice immediately
    parseEvent(mockJson, mockThreatMap, recentAlerts, mockPublish);
    parseEvent(mockJson, mockThreatMap, recentAlerts, mockPublish);
    
    assert.strictEqual(publishCount, 1, `Expected 1 publish, but got ${publishCount}. Deduplication failed.`);
});

runTest("Namespace filter ignores 'kube-system' events", () => {
    let publishCalled = false;
    const mockJson = JSON.stringify({
        process_exec: {
            process: { binary: "/bin/bash", pod: { name: "pod-1", namespace: "kube-system", workload: "coredns" } }
        }
    });
    
    parseEvent(mockJson, mockThreatMap, new Map(), () => { publishCalled = true; });
    assert.strictEqual(publishCalled, false, "Publisher fired for kube-system!");
});


console.log("\n========================================");
console.log(`🏁 Test Suite Complete. Pass: ${passed} | Fail: ${failed}`);
console.log("========================================");

process.exit(failed > 0 ? 1 : 0);