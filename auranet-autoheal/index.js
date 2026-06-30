const fs = require("fs");
const path = require("path");
const { connect, StringCodec } = require("nats");
const k8s = require("@kubernetes/client-node");
const yaml = require("js-yaml");
const { determineVirtualPatch } = require("./virtual-patches/rules");

const NATS_URL = process.env.NATS_URL || "nats://127.0.0.1:4222";

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

// Helper to safely extract K8s error messages
function getK8sError(err) {
    const statusCode = err.statusCode || (err.response && err.response.statusCode) || (err.body && err.body.code) || "UNKNOWN_CODE";
    const message = (err.body && err.body.message) ? err.body.message : (err.message || "Unknown K8s Error");
    return { statusCode, message };
}

async function applyQuarantine(workloadName) {
    const policyName = `quarantine-${workloadName}`;
    const quarantineManifest = {
        apiVersion: "cilium.io/v2",
        kind: "CiliumNetworkPolicy",
        metadata: { name: policyName, namespace: TARGET_NAMESPACE },
        spec: {
            endpointSelector: { matchLabels: { app: workloadName } },
            ingress: [{}], // Default Deny
            egress: [{}]   // Default Deny
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
async function applyVirtualPatch(patchFileName) {
    try {
        const patchPath = path.join(__dirname, "virtual-patches", patchFileName);
        if (!fs.existsSync(patchPath)) {
            console.error(`[K8s] Patch file not found: ${patchFileName}. Skipping.`);
            return;
        }

        const patchObj = yaml.load(fs.readFileSync(patchPath, "utf8"));
        console.log(`[K8s] 🛡️ Applying virtual patch: ${patchObj.metadata.name}...`);
        
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
        if (errorDetails.statusCode === 409) {
            console.log(`[K8s] 🛡️ Virtual patch '${patchFileName}' is already active. Proceeding.`);
        } else {
            console.error(`[K8s] Patch failed: [${errorDetails.statusCode}] ${errorDetails.message}`);
        }
    }
}
// CYCLE (restarting the pod) 
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

// MAIN EXECUTION LOOP
async function startAutoHeal() {
    try {
        console.log(`[AutoHeal] Connecting to NATS at ${NATS_URL}...`);
        const nc = await connect({ servers: NATS_URL });
        console.log("[AutoHeal] Connected to NATS broker successfully!");

        console.log("[AutoHeal] 🎧 Listening for ZTC Quarantine Orders...\n");
        const sub = nc.subscribe("auranet.commands.autoheal.>");

        for await (const msg of sub) {
            const command = JSON.parse(sc.decode(msg.data));
            const workload = command.target_workload;
            
            console.log(`\n[AutoHeal] INITIATING PIPELINE FOR: ${workload}`);
            
            await applyQuarantine(workload);
            
            const targetPatch = determineVirtualPatch(command.threat_signatures);
            await applyVirtualPatch(targetPatch);
            
            await cycleWorkloadPods(workload);
            
            console.log(`[AutoHeal] ⏳ Waiting 5 seconds for propagation...`);
            await new Promise(resolve => setTimeout(resolve, 5000));
            
            await removeQuarantine(workload);
            
            console.log(`[AutoHeal] ✅ Pipeline complete. Threat neutralized for ${workload}.\n`);
        }
    } catch (err) {
        console.error("[AutoHeal] Fatal Runtime Error:", err);
        process.exit(1);
    }
}

if (require.main === module) {
    startAutoHeal();
}

module.exports = { applyQuarantine, applyVirtualPatch, cycleWorkloadPods, removeQuarantine };