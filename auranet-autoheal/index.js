/**
 * @file autoheal.js
 * @brief AuraNet AutoHeal service.
 *
 * Listens for remediation commands from the AuraNet Controller via NATS and
 * executes the self-healing pipeline on Kubernetes.
 *
 * Pipeline:
 * 1. Apply emergency network quarantine.
 * 2. Deploy a virtual patch.
 * 3. Restart compromised workload pods.
 * 4. Remove quarantine after remediation.
 *
 * @version 1.0.0
 */



const fs = require("fs");
const path = require("path");
const { connect, StringCodec } = require("nats");
const k8s = require("@kubernetes/client-node");
const yaml = require("js-yaml");
const { determineVirtualPatch, isRuntimeThreat } = require("./virtual-patches/rules");


const { getThreatMatrix } = require("./virtual-patches/threat-parser");
const NATS_URL = process.env.NATS_URL || "nats://127.0.0.1:4222";


//always gonna be default during this project
const TARGET_NAMESPACE = "default"; 
const sc = StringCodec();

// Initialize K8s Clients
const kc = new k8s.KubeConfig();
if (process.env.KUBERNETES_SERVICE_HOST) {
    kc.loadFromCluster();
} else {
    kc.loadFromDefault();
}
const k8sCoreApi = kc.makeApiClient(k8s.CoreV1Api);
const k8sCustomApi = kc.makeApiClient(k8s.CustomObjectsApi);



const CONFIG_DIR = "/etc/auranet/config/";
if (fs.existsSync(CONFIG_DIR)) {
    fs.watch(CONFIG_DIR, (eventType, filename) => {
        if (filename && filename.includes('..data')) {
            // 200ms delay ensures Kubernetes finishes writing the symlink
            setTimeout(() => {
                console.log(`\n[AutoHeal] K8s ConfigMap update detected. Hot-reloading Threat Matrix...`);
                getThreatMatrix();
            }, 200);
        }
    });
}


// Helper to safely extract K8s error messages
/**
 * Extracts a human-readable Kubernetes API error.
 *
 * @param {Error} err Kubernetes API error object.
 * @returns {{statusCode: number|string, message: string}}
 * An object containing the HTTP status code and error message.
 */
function getK8sError(err) {
    const statusCode = err.statusCode || (err.response && err.response.statusCode) || (err.body && err.body.code) || "UNKNOWN_CODE";
    const message = (err.body && err.body.message) ? err.body.message : (err.message || "Unknown K8s Error");
    return { statusCode, message };
}
/**
 * Applies an emergency Cilium network policy that isolates the target workload
 * by denying all ingress and egress traffic.
 *
 * @async
 * @param {string} workloadName Name of the Kubernetes workload.
 * @returns {Promise<void>}
 */
async function applyQuarantine(workloadName) {
    const policyName = `quarantine-${workloadName}`;
    const quarantineManifest = {
        apiVersion: "cilium.io/v2",
        kind: "CiliumNetworkPolicy",
        metadata: { name: policyName, namespace: TARGET_NAMESPACE },
        spec: {
            endpointSelector: { matchLabels: { app: workloadName } },
            ingressDeny: [
                { fromEntities: ["all"] },
                { fromEndpoints: [{}] }
            ],
            egressDeny: [
                { toEntities: ["all"] },
                { toEndpoints: [{}] }
            ]
        }
    };
    try {
        console.log(`[K8s] 🚨 Applying emergency network quarantine to [${workloadName}]...`);
        await k8sCustomApi.createNamespacedCustomObject({
            group: "cilium.io",
            version: "v2",
            namespace: TARGET_NAMESPACE,
            plural: "ciliumnetworkpolicies",
            body: quarantineManifest
        });
        console.log(`[K8s] Quarantine active: ${policyName}`);
    } catch (err) {
        const errorDetails = getK8sError(err);
        if (errorDetails.statusCode === 409) {
            console.log(`[K8s] Quarantine is already active for: ${workloadName}. Proceeding.`);
        } else if (errorDetails.statusCode === 403) {
            console.error(`[K8s] FATAL 403 FORBIDDEN: Service Account lacks permissions to create CiliumNetworkPolicies!`);
        } else {
            console.error(`[K8s] Quarantine failed: [${errorDetails.statusCode}] ${errorDetails.message}`);
        }
    }
}

// VIRTUAL PATCH
/**
 * Applies a virtual patch by deploying a predefined
 * CiliumNetworkPolicy manifest.
 *
 * Existing policies with the same name are removed before deployment
 * to prevent resource conflicts.
 *
 * @async
 * @param {string} patchFileName Name of the YAML patch file.
 * @returns {Promise<void>}
 */
async function applyVirtualPatch(patchFileName) {
    try {
        const patchPath = path.join(__dirname, "virtual-patches", patchFileName);
        if (!fs.existsSync(patchPath)) {
            console.error(`[K8s] Patch file not found: ${patchFileName}. Skipping.`);
            return;
        }

        const patchObj = yaml.load(fs.readFileSync(patchPath, "utf8"));
        
        // 1. Force wipe the old policy state to prevent 409 Conflicts
        try {
            await k8sCustomApi.deleteNamespacedCustomObject({
                group: "cilium.io",
                version: "v2",
                namespace: TARGET_NAMESPACE,
                plural: "ciliumnetworkpolicies",
                name: patchObj.metadata.name
            });
            console.log(`[K8s] Cleared stale virtual patch state: ${patchObj.metadata.name}`);
        } catch (delErr) {
            // Ignore 404s, it just means the state is already clean
        }

        // 2. Apply cleanly
        console.log(`[K8s]Applying virtual patch: ${patchObj.metadata.name}...`);
        await k8sCustomApi.createNamespacedCustomObject({
            group: "cilium.io",
            version: "v2",
            namespace: TARGET_NAMESPACE,
            plural: "ciliumnetworkpolicies",
            body: patchObj
        });
        console.log(`[K8s] Virtual patch applied successfully.`);
    } catch (err) {
        const errorDetails = getK8sError(err);
        console.error(`[K8s] Patch failed: [${errorDetails.statusCode}] ${errorDetails.message}`);
    }
}
// CYCLE (restarting the pod) 
/**
 * Deletes all pods belonging to a compromised workload.
 *
 * Kubernetes automatically recreates healthy replacement pods through
 * the owning Deployment or ReplicaSet.
 *
 * @async
 * @param {string} workloadName Name of the compromised workload.
 * @returns {Promise<void>}
 */
async function cycleWorkloadPods(workloadName) {
    try {
        console.log(`[K8s] ♻️ Cycling compromised pods for [${workloadName}]...`);
        
        await k8sCoreApi.deleteCollectionNamespacedPod({
            namespace: TARGET_NAMESPACE,
            labelSelector: `app=${workloadName}`
        });
        console.log(`[K8s] ♻️ Pods eradicated. Clean replicas are spinning up.`);
    } catch (err) {
        const errorDetails = getK8sError(err);
        console.error(`[K8s] Failed to cycle pods: [${errorDetails.statusCode}] ${errorDetails.message}`);
    }
}
// LIFT QUARANTINE
/**
 * Removes the emergency quarantine network policy from a workload.
 *
 * @async
 * @param {string} workloadName Name of the Kubernetes workload.
 * @returns {Promise<void>}
 */
async function removeQuarantine(workloadName) {
    const policyName = `quarantine-${workloadName}`;
    try {
        console.log(`[K8s] Lifting emergency quarantine for [${workloadName}]...`);
        await k8sCustomApi.deleteNamespacedCustomObject({
            group: "cilium.io",
            version: "v2",
            namespace: TARGET_NAMESPACE,
            plural: "ciliumnetworkpolicies",
            name: policyName
        });
        console.log(`[K8s] Quarantine lifted. System restored.`);
    } catch (err) {
        const errorDetails = getK8sError(err);
        if (errorDetails.statusCode === 404) {
            console.log(`[K8s] Quarantine policy already removed for ${workloadName}.`);
        } else if (errorDetails.statusCode === 403) {
            console.error(`[K8s] FATAL 403 FORBIDDEN: Service Account lacks permissions to delete CiliumNetworkPolicies!`);
        } else {
            console.error(`[K8s] Failed to lift quarantine: [${errorDetails.statusCode}] ${errorDetails.message}`);
        }
    }
}









/**
 * Starts the AuraNet AutoHeal service.
 *
 * Establishes a connection to the NATS broker and continuously listens
 * for remediation commands. For each received command, the complete
 * self-healing pipeline is executed.
 *
 * Pipeline:
 * 1. Apply quarantine.
 * 2. Determine the required virtual patch.
 * 3. Apply the virtual patch.
 * 4. Restart compromised pods.
 * 5. Wait for propagation.
 * 6. Remove quarantine.
 * 7. Notify the controller that remediation has completed.
 *
 * @async
 * @returns {Promise<void>}
 */
/**
 * Starts the AuraNet AutoHeal service.
 *
 * @async
 * @returns {Promise<void>}
 */

async function startAutoHeal() {
    try {
        console.log(`[AutoHeal] Connecting to NATS at ${NATS_URL}...`);
        const nc = await connect({ servers: NATS_URL });
        console.log("[AutoHeal] Connected to NATS broker successfully!");

        console.log("[AutoHeal] Listening for ZTC Quarantine Orders...\n");
        const sub = nc.subscribe("auranet.commands.autoheal.>");

        // In-memory tracker for applied patch file names (Branch A)
        const appliedPatches = new Set();

        for await (const msg of sub) {
            const command = JSON.parse(sc.decode(msg.data));
            const workload = command.target_workload;
            const threatSignatures = command.threat_signatures || [];
            
          
        
            if (isRuntimeThreat(threatSignatures)) {
                console.log(`\n[AutoHeal]  RUNTIME HOST THREAT DETECTED FOR: ${workload}`);
                console.log(`[AutoHeal]  Cinematic delay active (6s) to allow terminal output on-screen...`);
                
                // this is for demo purposes pnly 
                await new Promise(resolve => setTimeout(resolve, 1200));

                console.log(`[AutoHeal]  INITIATING RUNTIME EVACUATION PIPELINE FOR: ${workload}`);
                
                await applyQuarantine(workload);
                
                
                await cycleWorkloadPods(workload);
                
                console.log(`[AutoHeal]  Permanent Isolation Enforced. Skipping removeQuarantine for ${workload}.\n`);
                
                nc.publish(`auranet.remediated.${workload}`, sc.encode(JSON.stringify({ status: "permanent_quarantine" })));
                continue;
            }
            
            
            
            const targetPatch = determineVirtualPatch(threatSignatures);

            if (appliedPatches.has(targetPatch)) {
                console.log(`\n[AutoHeal]  Patch file '${targetPatch}' is already active for ${workload}. Skipping redundant AutoHeal sequence.`);
                
                nc.publish(`auranet.remediated.${workload}`, sc.encode(JSON.stringify({ 
                    status: "skipped", 
                    reason: "patch_already_active" 
                })));
                continue; 
            }

            console.log(`\n[AutoHeal]  INITIATING L7 NETWORK PATCH PIPELINE FOR: ${workload}`);
            
            await applyQuarantine(workload);
            await applyVirtualPatch(targetPatch);
            
            appliedPatches.add(targetPatch);
            
            await cycleWorkloadPods(workload);
            
            console.log(`[AutoHeal]  Waiting 5 seconds for propagation...`);
            await new Promise(resolve => setTimeout(resolve, 5000));
            
            await removeQuarantine(workload);
            
            console.log(`[AutoHeal] ✅ L7 Remediation complete. Threat neutralized for ${workload}.\n`);
            nc.publish(`auranet.remediated.${workload}`, sc.encode(JSON.stringify({ status: "cleared" })));
        }
    } catch (err) {
        console.error("[AutoHeal] Fatal Runtime Error:", err);
        process.exit(1);
    }
}

if (require.main === module) {
    startAutoHeal();
}


/**
 * @module AutoHeal
 *
 * @exports applyQuarantine
 * @exports applyVirtualPatch
 * @exports cycleWorkloadPods
 * @exports removeQuarantine
 */
module.exports = { applyQuarantine, applyVirtualPatch, cycleWorkloadPods, removeQuarantine };