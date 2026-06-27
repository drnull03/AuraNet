const { Tail } = require('tail');
const { connect, StringCodec } = require('nats');
const fs = require('fs');

// kept the name to tetragon.log for legacy purposes
// this file is present on every node 
const LOG_PATH = process.env.LOG_PATH || '/var/run/cilium/tetragon/tetragon.log';
// the same nat url
const NATS_URL = process.env.NATS_URL || 'nats://auranet-nats-broker.auranet-messaging.svc.cluster.local:4222';
const THREAT_MAP_PATH = process.env.THREAT_MAP_PATH || '/etc/auranet/runtime/threat-map.json';
const sc = StringCodec();

//load the injectable map using helm chart configmap
let THREAT_MAP = {};
try {
    const rawData = fs.readFileSync(THREAT_MAP_PATH, 'utf8');
    THREAT_MAP = JSON.parse(rawData);
    console.log(`[Runtime Forwarder] Successfully loaded Threat Map with ${Object.keys(THREAT_MAP).length} signatures from Helm.`);
} catch (err) {
    console.error(`[Runtime Forwarder] CRITICAL: Failed to load Threat Map from ${THREAT_MAP_PATH}`);
    console.error(err.message);
    process.exit(1);
}

// Map to store recent alerts to prevent double-firing (Deduplication)
// dumb solution but it is  a linux kernel thingy can't do anything about it
// cat read the file twice once when it read the meta data and the second time when it reads the file
const recentAlerts = new Map();
const DEDUPE_WINDOW_MS = 2000; // 2 seconds enough time for actull naive double cat problem

async function startForwarder() {
    console.log(`[Runtime Forwarder] Starting up...`);
    
    // Ensure the log file exists before tailing
    if (!fs.existsSync(LOG_PATH)) {
        console.error(`[Runtime Forwarder] CRITICAL: log file not found at ${LOG_PATH}`);
        console.error(`[Runtime Forwarder] Are you sure the volume is mounted correctly?`);
        process.exit(1);
    }

    try {
        console.log(`[Runtime Forwarder] Connecting to NATS at ${NATS_URL}...`);
        const nc = await connect({ servers: NATS_URL });
        console.log("[Runtime Forwarder] Connected to NATS broker successfully!");

        const tail = new Tail(LOG_PATH);
        console.log(`[Runtime Forwarder] Actively tailing eBPF kernel logs: ${LOG_PATH}\n`);

        tail.on("line", (data) => {
            try {
                const event = JSON.parse(data);
                
                let processData = null;
                let functionName = null;
                let isExecEvent = false;

                // Check for native Execution events (Bash, nc, nmap, etc.)
                if (event.process_exec) {
                    processData = event.process_exec.process;
                    isExecEvent = true;
                } 
                //  Check for custom Kernel Probes (File reads like /etc/passwd)
                else if (event.process_kprobe) {
                    processData = event.process_kprobe.process;
                    functionName = event.process_kprobe.function_name;
                } else {
                    return; // Ignore other event types (like process_exit)
                }
                
                if (!processData || !processData.pod) return; 

                const namespace = processData.pod.namespace;
                const workload = processData.pod.workload || 'unknown-workload';
                const podName = processData.pod.name; 
                
                // Ignore system namespaces to prevent infinite loops
                if (namespace === 'kube-system' || namespace === 'auranet-namespace') return;

                let threatSignature = null;
                let actionContext = '';

                // Analyze Execution Events (from process_exec)
                if (isExecEvent) {
                    const binary = processData.binary.split('/').pop();
                    threatSignature = THREAT_MAP[binary];
                    actionContext = `Executed binary: ${binary}`;
                } 
                // Analyze File Open Events (from process_kprobe)
                else if (functionName && functionName.includes('security_file_open')) {
                    const args = event.process_kprobe.args || [];
                    if (args.length > 0 && args[0].file_arg) {
                        const filePath = args[0].file_arg.path;
                        const fileName = filePath.split('/').pop();
                        //might remove the includes soon because the threat map are gonna be injectable
                        threatSignature = THREAT_MAP[filePath] || 
                                          THREAT_MAP[fileName] || 
                                          (filePath.includes('token') ? 'k8s_token_theft' : null) ||   
                                          (filePath.includes('.ssh') ? 'ssh_key_access' : null);
                        
                        actionContext = `Accessed file: ${filePath}`;
                    }
                }

                // If we matched a threat, verify it's not a duplicate before firing to NATS
                if (threatSignature) {
                    const now = Date.now();
                    const alertKey = `${podName}-${threatSignature}-${actionContext}`;
                    
                    // Deduplication check
                    if (recentAlerts.has(alertKey) && (now - recentAlerts.get(alertKey) < DEDUPE_WINDOW_MS)) {
                        return; // Silently drop the duplicate
                    }
                    
                    // Log it and update the cache
                    recentAlerts.set(alertKey, now);
                    
                    // Periodic cache cleanup to prevent memory leaks
                    //might lower this even more
                    if (recentAlerts.size > 1000) {
                        recentAlerts.clear();
                    }

                    const subject = `auranet.events.runtime.${workload}`;
                    const payload = {
                        source: "runtime_ebpf",
                        threat: threatSignature,
                        context: actionContext,
                        timestamp: now
                    };

                    console.log(`🚨 [THREAT DETECTED] Host Pod: ${podName} -> ${threatSignature}`);
                    console.log(`   Publishing to Workload Subject: ${subject}`);
                    
                    nc.publish(subject, sc.encode(JSON.stringify(payload)));
                }
            } catch (parseErr) {
                // Ignore malformed lines
            }
        });

        tail.on("error", function(error) {
            console.log('[Runtime Forwarder] Tailing ERROR: ', error);
        });

        // Graceful shutdown
        const setupShutdown = (signal) => {
            process.on(signal, async () => {
                console.log(`\n[Runtime Forwarder] Received ${signal}. Closing NATS connection...`);
                tail.unwatch();
                await nc.close();
                process.exit(0);
            });
        };
        setupShutdown("SIGTERM");
        setupShutdown("SIGINT");

    } catch (err) {
        console.error("[Runtime Forwarder] Fatal Error during startup:", err);
        process.exit(1);
    }
}

startForwarder();