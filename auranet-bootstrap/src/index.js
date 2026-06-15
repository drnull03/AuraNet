const fs = require('fs');
const k8s = require('@kubernetes/client-node');

// Accept file path from command line arguments or default to the mounted config path
const configFile = process.argv[2] || '/etc/auranet/naive.conf';

console.log(`Starting AuraNet Bootstrap. Reading configuration from: ${configFile}`);

if (!fs.existsSync(configFile)) {
    console.log(`Configuration file not found. No rules to apply. Exiting cleanly.`);
    process.exit(0);
}

const content = fs.readFileSync(configFile, 'utf-8');
const lines = content.split('\n');

// Initialize the standard Kubernetes client using the pod's internal service account
const kc = new k8s.KubeConfig();
kc.loadFromCluster();
const customObjectsApi = kc.makeApiClient(k8s.CustomObjectsApi);

async function applyCiliumPolicy(source, dest) {
    const policyName = `bootstrap-allow-${source}-to-${dest}`;
    
    // Define the CiliumNetworkPolicy payload
    
    const policyManifest = {
        apiVersion: 'cilium.io/v2',
        kind: 'CiliumNetworkPolicy',
        metadata: { 
            name: policyName,
            namespace: 'default' 
        },
        spec: {
            endpointSelector: { 
                matchLabels: { app: dest } 
            },
            ingress: [{
                fromEndpoints: [{ 
                    matchLabels: { app: source } 
                }],
                // NEW: Force SPIRE mutual authentication for this network path
                authentication: {
                    mode: "required"
                }
            }]
        }
    };

    try {
        await customObjectsApi.createNamespacedCustomObject(
            'cilium.io', 
            'v2', 
            'default', 
            'ciliumnetworkpolicies', 
            policyManifest
        );
        console.log(`[SUCCESS] Applied policy: ${policyName}`);
    } catch (err) {
        if (err.body && err.body.reason === 'AlreadyExists') {
            console.log(`[SKIPPED] Policy ${policyName} already exists.`);
        } else {
            console.error(`[ERROR] Failed to create policy ${policyName}:`, err.body ? err.body.message : err);
        }
    }
}

async function run() {
    let appliedCount = 0;

    for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed) continue;

        // Regex to match "1.retail-dashboard -> customer-api"
        // Captures Group 1: Source, Group 2: Destination
        const match = trimmed.match(/^\d+\.\s*([a-zA-Z0-9-]+)\s*->\s*([a-zA-Z0-9-]+)$/);
        
        if (match) {
            const source = match[1];
            const destination = match[2];
            console.log(`Parsed rule: Allow traffic from [${source}] to [${destination}]`);
            await applyCiliumPolicy(source, destination);
            appliedCount++;
        } else {
            console.log(`[WARNING] Ignoring invalid line format: ${trimmed}`);
        }
    }

    console.log(`AuraNet Bootstrap complete. Processed ${appliedCount} policies.`);
}

run();