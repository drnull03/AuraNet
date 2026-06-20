const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');
const k8s = require('@kubernetes/client-node');

const configFile = process.argv[2] || '/etc/auranet/naive.conf';

console.log(`Starting AuraNet Bootstrap. Reading configuration from: ${configFile}`);

if (!fs.existsSync(configFile)) {
    console.log(`Configuration file not found. No rules to apply. Exiting cleanly.`);
    process.exit(0);
}

const content = fs.readFileSync(configFile, 'utf-8');
const lines = content.split('\n');

// Initialize the standard Kubernetes clients
const kc = new k8s.KubeConfig();
kc.loadFromCluster();

const customObjectsApi = kc.makeApiClient(k8s.CustomObjectsApi);

const coreV1Api = kc.makeApiClient(k8s.CoreV1Api);

// Helper function to dynamically find a service's port
async function getServicePort(serviceName, namespace = 'default') {
    try {
        const res = await coreV1Api.readNamespacedService(serviceName, namespace);
        // Grab the first port defined in the service
        return res.body.spec.ports[0].port.toString();
    } catch (err) {
        console.log(`[WARNING] Could not find Kubernetes Service named '${serviceName}'. Defaulting to port 80.`);
        return "80"; // Fallback if the service doesn't exist yet
    }
}

async function applyCiliumPolicy(source, dest) {
    const policyName = `bootstrap-allow-${source}-to-${dest}`;
    
    // Dynamically discover the port for the destination!
    const discoveredPort = await getServicePort(dest);
    console.log(`[INFO] Discovered port ${discoveredPort} for destination [${dest}]`);
    
    const policyManifest = {
        apiVersion: 'cilium.io/v2',
        kind: 'CiliumNetworkPolicy',
        metadata: { 
            name: policyName,
            namespace: 'default',
            labels: {
                "app.kubernetes.io/managed-by": "auranet-bootstrap"
            }
        },
        spec: {
            endpointSelector: { 
                matchLabels: { app: dest } 
            },
            ingress: [{
                fromEndpoints: [{ 
                    matchLabels: { app: source } 
                }],
                // Inject the dynamically discovered port here
                toPorts: [{
                    ports: [{
                        port: discoveredPort,
                        protocol: "TCP"
                    }],
                    rules: {
                        http: [{}] // Trigger the Envoy L7 proxy for Hubble
                    }
                }],
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
        console.log(`[SUCCESS] Applied network policy: ${policyName}`);
    } catch (err) {
        if (err.body && err.body.reason === 'AlreadyExists') {
            console.log(`[SKIPPED] Network policy ${policyName} already exists.`);
        } else {
            console.error(`[ERROR] Failed to create policy ${policyName}:`, err.cause ? err.cause.message : err);
        }
    }
}

async function applyRuntimePolicies() {
    const policiesDir = path.join(__dirname, 'policies');
    
    if (!fs.existsSync(policiesDir)) {
        console.log(`[INFO] No policies folder found at ${policiesDir}`);
        return;
    }

    const files = fs.readdirSync(policiesDir);
    for (const file of files) {
        if (file.endsWith('.yaml') || file.endsWith('.yml')) {
            const filePath = path.join(policiesDir, file);
            const fileContent = fs.readFileSync(filePath, 'utf8');
            
            try {
                const manifest = yaml.load(fileContent);
                const name = manifest.metadata.name;
                const namespace = manifest.metadata.namespace || 'default';
                
                try {
                    await customObjectsApi.createNamespacedCustomObject(
                        'cilium.io', 
                        'v1alpha1', 
                        namespace, 
                        'tracingpoliciesnamespaced', 
                        manifest
                    );
                    console.log(`[SUCCESS] Applied runtime policy: ${name}`);
                } catch (err) {
                    if (err.body && err.body.code === 409) {
                        console.log(`[INFO] Runtime policy ${name} already exists. Skipping.`);
                    } else {
                        const errorMsg = err.cause ? err.cause.message : (err.body ? err.body.message : err.message);
                        console.error(`[ERROR] API rejected runtime policy ${name}:`, errorMsg);
                    }
                }
            } catch (err) {
                 const errorMsg = err.cause ? err.cause.message : err.message;
                 console.error(`[ERROR] Failed to parse YAML file ${file}:`, errorMsg);
            }
        }
    }
}

async function run() {
    let appliedCount = 0;

    for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed) continue;

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
    
    await applyRuntimePolicies();
    console.log(`AuraNet Bootstrap complete. Processed ${appliedCount} network configurations.`);
}

run();