const { Tail } = require('tail');
const { connect, StringCodec } = require('nats');
const fs = require('fs');


// kept the name to tetragon.log for legacy purposes
// this file is present on every node 
const LOG_PATH = process.env.LOG_PATH || '/var/run/cilium/tetragon/tetragon.log';
//the same nat url
const NATS_URL = process.env.NATS_URL || 'nats://auranet-nats-broker.auranet-messaging.svc.cluster.local:4222';
const sc = StringCodec();


// map specific executables or files to the exact threat strings expected by our Trust Engine
//gonna find a way to make this dynamic or something
const THREAT_MAP = {
    // Shells & Remote Access
    'nc': 'nc_execution',
    'ncat': 'nc_execution',
    'netcat': 'nc_execution',
    'sh': 'reverse_shell_detected',    
    'bash': 'reverse_shell_detected',
    'zsh': 'reverse_shell_detected',
    'ash': 'reverse_shell_detected',
    
    // Reconnaissance & Droppers
    'nmap': 'nmap_scan_detected', 
    'curl': 'suspicious_binary_download',
    'wget': 'suspicious_binary_download',
    'tcpdump': 'network_sniffing',
    'tshark': 'network_sniffing',

    // Privilege & Escapes
    'sudo': 'privilege_escalation',
    'su': 'privilege_escalation',
    'nsenter': 'container_escape_attempt',
    'chroot': 'container_escape_attempt',
    'unshare': 'container_escape_attempt',

    // Deep System Attacks
    'insmod': 'kernel_module_injection',
    'modprobe': 'kernel_module_injection',
    'rmmod': 'kernel_module_injection',
    'xmrig': 'crypto_miner_execution',

    // Sensitive Files
    '/etc/passwd': 'unauthorized_file_read',
    '/etc/shadow': 'unauthorized_file_read',
    '/dev/mem': 'memory_dump_attempt',
    '/dev/kmem': 'memory_dump_attempt',
    'id_rsa': 'ssh_key_access',
    'authorized_keys': 'ssh_key_access',
    '/run/secrets/kubernetes.io/serviceaccount/token': 'k8s_token_theft'
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
                
                let processData = null;
                let functionName = null;
                let isExecEvent = false;

                // Check for native Execution events (Bash, nc, nmap, etc.)
                if (event.process_exec) {
                    processData = event.process_exec.process;
                    isExecEvent = true;
                } 
                // Check for custom Kernel Probes (File reads like /etc/passwd)
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
                    // Extract just the binary name (e.g., "/bin/bash" -> "bash")
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
                        
                        threatSignature = THREAT_MAP[filePath] || 
                                          THREAT_MAP[fileName] || 
                                          (filePath.includes('token') ? 'k8s_token_theft' : null) ||
                                          (filePath.includes('.ssh') ? 'ssh_key_access' : null);
                        
                        actionContext = `Accessed file: ${filePath}`;
                    }
                }

                // If we matched a threat, fire it to NATS!
                if (threatSignature) {
                    const subject = `auranet.events.runtime.${workload}`;
                    
                    const payload = {
                        source: "runtime_ebpf",
                        threat: threatSignature,
                        context: actionContext,
                        timestamp: Date.now()
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