/**
 * @file index.js
 * @brief AuraNet Bootstrap microservice.
 *
 * Initializes the AuraNet Zero Trust environment by reading the
 * bootstrap configuration and deploying the required Cilium network
 * and runtime security policies into the Kubernetes cluster.
 */
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

const kc = new k8s.KubeConfig();
if (process.env.KUBERNETES_SERVICE_HOST) {
    kc.loadFromCluster();
} else {
    kc.loadFromDefault(); 
}

const customObjectsApi = kc.makeApiClient(k8s.CustomObjectsApi);
/**
 * Creates and deploys a Cilium L7 network policy for a permitted
 * service-to-service communication path.
 *
 * The generated policy enforces mutual authentication and routes
 * traffic through the Envoy L7 proxy for observability.
 *
 * @async
 * @param {string} source Source workload name.
 * @param {string} dest Destination workload name.
 * @param {string|number} port Destination TCP port.
 * @returns {Promise<void>}
 */
async function applyCiliumPolicy(source, dest, port) {
    const policyName = `bootstrap-allow-${source}-to-${dest}`;
    
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
                toPorts: [{
                    ports: [{
                        port: port.toString(),
                        protocol: "TCP"
                    }]
                }]
            }]
        }
    };

    // this is for debugging and can be ignored 
    if (port.toString() !== '5432') {
        policyManifest.spec.ingress[0].toPorts[0].rules = { http: [{}] };
        policyManifest.spec.ingress[0].authentication = { mode: "required" };
    }

    try {
        await customObjectsApi.createNamespacedCustomObject(
            'cilium.io',
            'v2',
            'default',
            'ciliumnetworkpolicies',
            policyManifest
        );
        console.log(`[SUCCESS] Applied network policy: ${policyName} on port ${port}`);
    } catch (err) {
        if (err.body && err.body.reason === 'AlreadyExists') {
            console.log(`[SKIPPED] Network policy ${policyName} already exists.`);
        } else {
            console.error(`[ERROR] Failed to create policy ${policyName}:`, err.cause ? err.cause.message : (err.body ? err.body.message : err.message));
        }
    }
}
// this feature might be deprecated soon as it is not so  necessary
//if not deprecated it should be decoupled at least
/**
 * Applies all predefined runtime security policies found in the
 * local policies directory.
 *
 * Each YAML manifest is parsed and deployed as a Cilium
 * TracingPolicyNamespaced resource.
 *
 * @async
 * @returns {Promise<void>}
 */
//this is no longer effective 
//gonna remove this soon
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
                    // Reverted to positional arguments
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


/**
 * Compares the desired state (from naive.conf) against the cluster's
 * current state and deletes any orphaned policies managed by AuraNet.
 *
 * @async
 * @param {Set<string>} desiredPolicies A set of policy names that should exist.
 * @returns {Promise<void>}
 */
async function cleanupOrphanedPolicies(desiredPolicies) {
    try {
        console.log("\n[INFO] Reconciling state: Checking for orphaned policies...");
        
        // Fetch all current Cilium policies in the default namespace
        const cnps = await customObjectsApi.listNamespacedCustomObject(
            'cilium.io', 'v2', 'default', 'ciliumnetworkpolicies'
        );

        for (const item of cnps.body.items) {
            // Check if the policy belongs to our bootstrap script
            const isManaged = item.metadata.labels && 
                              item.metadata.labels["app.kubernetes.io/managed-by"] === "auranet-bootstrap";

            // If it belongs to us but is NOT in the desired list, delete it
            if (isManaged && !desiredPolicies.has(item.metadata.name)) {
                console.log(`[CLEANUP] Orphaned policy detected: ${item.metadata.name}. Deleting...`);
                await customObjectsApi.deleteNamespacedCustomObject(
                    'cilium.io', 'v2', 'default', 'ciliumnetworkpolicies', item.metadata.name
                );
                console.log(`[SUCCESS] Deleted orphaned policy: ${item.metadata.name}`);
            }
        }
    } catch (err) {
        const errorMsg = err.cause ? err.cause.message : (err.body ? err.body.message : err.message);
        console.error("[ERROR] Failed during state reconciliation:", errorMsg);
    }
}

/**
 * Executes the AuraNet bootstrap process.
 *
 * Reads the bootstrap configuration, parses all permitted service
 * communication rules, deploys the corresponding network policies,
 * applies runtime security policies, and reports the deployment
 * summary.
 *
 * @async
 * @returns {Promise<void>}
 */
/**
 * Executes the AuraNet bootstrap process.
 */
async function run() {
    let appliedCount = 0;
    
    // Initialize a Set to track the exact names of the policies we want to exist
    const desiredPolicies = new Set();

    for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed) continue;

        const match = trimmed.match(/^\d+\.\s*([a-zA-Z0-9-]+)\s*->\s*([a-zA-Z0-9-]+):(\d+)$/);
        
        if (match) {
            const source = match[1];
            const destination = match[2];
            const port = match[3];
            console.log(`Parsed rule: Allow traffic from [${source}] to [${destination}] on port ${port}`);
            
            // Calculate the policy name exactly as applyCiliumPolicy formats it
            const expectedPolicyName = `bootstrap-allow-${source}-to-${destination}`;
            desiredPolicies.add(expectedPolicyName); // Add to our tracking list
            
            await applyCiliumPolicy(source, destination, port);
            appliedCount++;
        } else {
            console.log(`[WARNING] Ignoring invalid line format: ${trimmed}`);
        }
    }
    
    // Execute the diffing cleanup using our tracked policies
    await cleanupOrphanedPolicies(desiredPolicies);
    
    await applyRuntimePolicies();
    console.log(`AuraNet Bootstrap complete. Processed ${appliedCount} network configurations.`);
}

run();
