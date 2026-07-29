const assert = require('assert');

const THREAT_MAP = {
    'nc': 'nc_execution',
    'sh': 'nc_execution',
    'bash': 'nc_execution',
    'nmap': 'unexpected_outbound_traffic',
    '/etc/passwd': 'unauthorized_file_read',
    'token': 'unauthorized_file_read'
};

// This pure function takes a raw log string, and a MOCK function to call if a threat is found
function parseTetragonEvent(eventJson, mockPublishFn) {
    try {
        const event = JSON.parse(eventJson);
        if (!event.process_kprobe) return;

        const processData = event.process_kprobe.process;
        const functionName = event.process_kprobe.function_name;
        
        if (!processData || !processData.pod) return;

        const namespace = processData.pod.namespace;
        const labels = processData.pod.labels || {};
        const workload = labels['app'] || labels['k8s-app'] || 'unknown-workload';
        
        // Ignore system namespaces
        if (namespace === 'kube-system' || namespace === 'auranet-namespace') return;

        let threatSignature = null;
        let actionContext = '';

        if (functionName === 'sys_execve') {
            const binary = processData.binary.split('/').pop();
            threatSignature = THREAT_MAP[binary];
            actionContext = `Executed binary: ${binary}`;
        } else if (functionName === 'security_file_open') {
            const args = event.process_kprobe.args || [];
            if (args.length > 0 && args[0].file_arg) {
                const filePath = args[0].file_arg.path;
                const fileName = filePath.split('/').pop();
                threatSignature = THREAT_MAP[filePath] || THREAT_MAP[fileName] || 
                                  (filePath.includes('token') ? 'unauthorized_file_read' : null);
                actionContext = `Accessed file: ${filePath}`;
            }
        }

        if (threatSignature) {
            const subject = `auranet.events.runtime.${workload}`;
            const payload = { source: "runtime_ebpf", threat: threatSignature, context: actionContext };
            
            // Trigger the mock instead of the real network!
            mockPublishFn(subject, payload);
        }
    } catch (err) {
        // Silently ignore malformed JSON just like the real forwarder
    }
}


console.log("🧪 Starting Pure Logic Mock Tests...\n");
let passed = 0;
let failed = 0;

function runTest(testName, mockJson, expectedSubject, expectedThreat) {
    console.log(`[TEST] ${testName}`);
    
    let publishCalled = false;
    
    // inject this fake NATS publisher to spy on the logic's output
    const mockNatsPublish = (subject, payload) => {
        publishCalled = true;
        try {
            assert.strictEqual(subject, expectedSubject, `Subject mismatch: Expected ${expectedSubject}, got ${subject}`);
            assert.strictEqual(payload.threat, expectedThreat, `Threat mismatch: Expected ${expectedThreat}, got ${payload.threat}`);
            console.log(`   ✅ PASS: Mock caught threat [${payload.threat}] and routed to [${subject}]`);
            passed++;
        } catch (err) {
            console.error(`   ❌ FAIL: ${err.message}`);
            failed++;
        }
    };

    // Run the logic
    parseTetragonEvent(mockJson, mockNatsPublish);

    // Verify outcomes
    if (!expectedSubject && !publishCalled) {
         console.log(`   ✅ PASS: Event correctly ignored (No threat detected)`);
         passed++;
    } else if (expectedSubject && !publishCalled) {
         console.error(`   ❌ FAIL: Expected alert for ${expectedThreat}, but mock publisher was never called.`);
         failed++;
    }
}


// MOCK 1: A normal, benign command. The logic should completely ignore it.
const mockBenign = JSON.stringify({
    process_kprobe: {
        function_name: "sys_execve",
        process: { binary: "/bin/ls", pod: { namespace: "default", labels: { app: "loan-service" } } }
    }
});
runTest("Benign Execution (/bin/ls)", mockBenign, null, null);

// MOCK 2: Command Injection / RCE. The logic should catch the shell and route it to loan-service.
const mockRce = JSON.stringify({
    process_kprobe: {
        function_name: "sys_execve",
        process: { binary: "/bin/sh", pod: { namespace: "default", labels: { app: "loan-service" } } }
    }
});
runTest("Command Injection (/bin/sh)", mockRce, "auranet.events.runtime.loan-service", "nc_execution");

// MOCK 3: Local File Inclusion (LFI). The logic should catch the file access and route it.
const mockLfi = JSON.stringify({
    process_kprobe: {
        function_name: "security_file_open",
        args: [{ file_arg: { path: "/etc/passwd" } }],
        process: { pod: { namespace: "default", labels: { app: "records-service" } } }
    }
});
runTest("Path Traversal LFI (/etc/passwd)", mockLfi, "auranet.events.runtime.records-service", "unauthorized_file_read");

// MOCK 4: Ignore System Pods. Even if an attacker hits kube-system, we ignore it to prevent infinite loops.
const mockSystem = JSON.stringify({
    process_kprobe: {
        function_name: "sys_execve",
        process: { binary: "/bin/nc", pod: { namespace: "kube-system", labels: { app: "coredns" } } }
    }
});
runTest("System Namespace Ignore Rule", mockSystem, null, null);

console.log("\n========================================");
console.log(`🏁 Logic Test Suite Complete. Pass: ${passed} | Fail: ${failed}`);
console.log("========================================");

process.exit(failed > 0 ? 1 : 0);