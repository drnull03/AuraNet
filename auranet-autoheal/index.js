// index.js
const fs = require("fs");
const path = require("path");
const { connect, StringCodec } = require("nats");
const k8s = require("@kubernetes/client-node");
const yaml = require("js-yaml");
const { determineVirtualPatch } = require("./virtual-patches/rules");

const NATS_URL = process.env.NATS_URL || "nats://127.0.0.1:4222";
const NAMESPACE = process.env.POD_NAMESPACE || "default";
const sc = StringCodec();

// Initialize Kubernetes API Clients
const kc = new k8s.KubeConfig();
// Load from cluster context if running inside a pod, fallback to local kubeconfig
if (process.env.KUBERNETES_SERVICE_HOST) {
    kc.loadFromCluster();
} else {
    kc.loadFromDefault();
}

const k8sCoreApi = kc.makeApiClient(k8s.CoreV1Api);
const k8sCustomApi = kc.makeApiClient(k8s.CustomObjectsApi);

/**
 * Reads a local YAML patch file, parses it, and applies it to the cluster via the CustomObjectsApi.
 */
async function applyVirtualPatch(patchFileName) {
    try {
        const patchPath = path.join(__dirname, "virtual-patches", patchFileName);
        if (!fs.existsSync(patchPath)) {
            console.error(`[K8s] Patch file not found: ${patchFileName}. Skipping application.`);
            return;
        }

        const fileContent = fs.readFileSync(patchPath, "utf8");
        const patchObj = yaml.load(fileContent);

        console.log(`[K8s] Applying custom security policy: ${patchObj.metadata.name}...`);

        // CiliumNetworkPolicies are custom objects: group, version, plural
        await k8sCustomApi.createNamespacedCustomObject(
            "cilium.io",
            "v2",
            NAMESPACE,
            "ciliumnetworkpolicies",
            patchObj
        );
        console.log(`[K8s] Successfully applied patch: ${patchFileName}`);
    } catch (err) {
        // If the policy already exists, we log it and move forward
        if (err.body && err.body.reason === "AlreadyExists") {
            console.log(`[K8s] Security policy already active in cluster.`);
        } else {
            const errorMsg = err.cause?.message || err.message || err;
            console.error(`[K8s] Failed to apply virtual patch:`, errorMsg);
        }
    }
}

/**
 * Issues a hard deletion of the target pod to force a replica cycle.
 */
async function cyclePod(podName) {
    try {
        console.log(`[K8s] Eradicating compromised pod: ${podName}...`);
        await k8sCoreApi.deleteNamespacedPod(podName, NAMESPACE);
        console.log(`[K8s] Pod ${podName} successfully signaled for deletion.`);
    } catch (err) {
        const errorMsg = err.cause?.message || err.message || err;
        console.error(`[K8s] Error deleting pod ${podName}:`, errorMsg);
    }
}

async function startAutoHeal() {
    try {
        console.log(`[AutoHeal] Connecting to NATS at ${NATS_URL}...`);
        const nc = await connect({ servers: NATS_URL });
        console.log("[AutoHeal] Connected to NATS broker successfully!");

        const sub = nc.subscribe("auranet.commands.autoheal.>");
        console.log("[AutoHeal] 🎧 Listening for ZTC Quarantine Orders...\n");

        for await (const msg of sub) {
            const command = JSON.parse(sc.decode(msg.data));
            
            console.log(`\n🚨 [AutoHeal] RECEIVED QUARANTINE ORDER!`);
            console.log(`Target Workload: ${command.target_workload}`);
            console.log(`Threat Signatures:`, command.threat_signatures);

            // 1. Determine the highest-severity patch file name
            const targetPatch = determineVirtualPatch(command.threat_signatures);
            console.log(`[AutoHeal] 🛡️ Selected Action Patch: ${targetPatch}`);

            // 2. Execute K8s Pipeline
            // Apply the virtual patch / quarantine network parameters
            await applyVirtualPatch(targetPatch);

            // Cycle the pod (deletes it so a clean instance replaces it)
            await cyclePod(command.target_workload);
            
            console.log(`[AutoHeal] ✅ Mitigation pipeline executed for ${command.target_workload}.`);
            console.log(`========================================================\n`);
        }

    } catch (err) {
        console.error("[AutoHeal] Fatal Runtime Error:", err);
        process.exit(1);
    }
}

startAutoHeal();