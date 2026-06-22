const { Tail } = require('tail');
const { connect, StringCodec } = require('nats');
const fs = require('fs');

const LOG_PATH = process.env.LOG_PATH || '/var/run/cilium/tetragon/tetragon.log';
const NATS_URL = process.env.NATS_URL || 'nats://auranet-nats-broker.auranet-messaging.svc.cluster.local:4222';
const sc = StringCodec();


// Map specific executables or files to the exact threat strings expected by our Trust Engine
const THREAT_MAP = {
    'nc': 'nc_execution',
    'ncat': 'nc_execution',
    'sh': 'nc_execution',    
    'bash': 'nc_execution',   
    'nmap': 'unexpected_outbound_traffic', 
    'curl': 'unexpected_outbound_traffic',
    'wget': 'unexpected_outbound_traffic',
    'sudo': 'privilege_escalation',
    'su': 'privilege_escalation',
    'tcpdump': 'unknown_anomaly', 
    '/etc/passwd': 'unauthorized_file_read',
    '/etc/shadow': 'unauthorized_file_read',
    'token': 'unauthorized_file_read'
};

async function startForwarder() {
    console.log(`[Runtime Forwarder] Starting up...`);
    
    // Ensure the log file exists before tailing
    if (!fs.existsSync(LOG_PATH)) {
        console.error(`[Runtime Forwarder] CRITICAL:  log file not found at ${LOG_PATH}`);
        console.error(`[Runtime Forwarder] Are you sure the volume is mounted correctly?`);
        process.exit(1);
    }

    try {
        console.log(`[Runtime Forwarder] Connecting to NATS at ${NATS_URL}...`);
        const nc = await connect({ servers: NATS_URL });
        console.log("[Runtime Forwarder] Connected to NATS broker successfully!");

        const tail = new Tail(LOG_PATH);
        console.log(`[Runtime Forwarder]  Actively tailing eBPF kernel logs: ${LOG_PATH}\n`);

        tail.on("line", (data) => {
            try {
                const event = JSON.parse(data);
                
                // We are looking for the process_kprobe events triggered by our TracingPolicies
                if (event.process_kprobe) {
                    const processData = event.process_kprobe.process;
                    const functionName = event.process_kprobe.function_name; // e.g., sys_execve or security_file_open
                    
                    if (!processData || !processData.pod) return; // Ignore non-Kubernetes host events

                    const namespace = processData.pod.namespace;
                    const labels = processData.pod.labels || {};
                    const workload = labels['app'] || labels['k8s-app'] || 'unknown-workload';
                    
                    // We only extract podName for local logging, we DO NOT use it in the NATS subject
                    const podName = processData.pod.name; 
                    
                    // Ignore kube-system and our own security pods to prevent infinite loops
                    if (namespace === 'kube-system' || namespace === 'auranet-system') return;

                    let threatSignature = null;
                    let actionContext = '';

                    // Analyze execution events (RCE, Scans, Droppers)
                    if (functionName === 'sys_execve') {
                        const binary = processData.binary.split('/').pop(); // Extracts 'nc' from '/usr/bin/nc'
                        threatSignature = THREAT_MAP[binary];
                        actionContext = `Executed binary: ${binary}`;
                    } 
                    // Analyze file open events (LFI, Token Theft)
                    else if (functionName === 'security_file_open') {
                        const args = event.process_kprobe.args || [];
                        if (args.length > 0 && args[0].file_arg) {
                            const filePath = args[0].file_arg.path;
                            const fileName = filePath.split('/').pop();
                            
                            // Check exact path mapping or fuzzy matching for tokens
                            threatSignature = THREAT_MAP[filePath] || THREAT_MAP[fileName] || 
                                              (filePath.includes('token') ? 'unauthorized_file_read' : null);
                            actionContext = `Accessed file: ${filePath}`;
                        }
                    }

                    // If we matched a threat, fire it to NATS!
                    if (threatSignature) {
                        // STRICT CONFORMANCE TO TRUST ENGINE 
                        // Expected: auranet.events.runtime.<workload> (exactly 4 parts)
                        const subject = `auranet.events.runtime.${workload}`;
                        
                        const payload = {
                            source: "runtime_ebpf",
                            threat: threatSignature,
                            context: actionContext,
                            timestamp: Date.now()
                        };

                        console.log(` [THREAT DETECTED] Host Pod: ${podName} -> ${threatSignature}`);
                        console.log(`   Publishing to Workload Subject: ${subject}`);
                        
                        nc.publish(subject, sc.encode(JSON.stringify(payload)));
                    }
                }
            } catch (parseErr) {
                // Ignore standard parsing errors from malformed log lines
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