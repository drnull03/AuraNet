const k8s = require('@kubernetes/client-node');

const kc = new k8s.KubeConfig();
kc.loadFromCluster();
const customObjectsApi = kc.makeApiClient(k8s.CustomObjectsApi);

async function wipePolicies() {
    console.log("Nuking all dynamic AuraNet policies for a clean slate...");
    try {
        // Fetch all current Cilium policies in the default namespace
        const res = await customObjectsApi.listNamespacedCustomObject('cilium.io', 'v2', 'default', 'ciliumnetworkpolicies');
        const policies = res.body.items;

        if (policies.length === 0) {
            console.log("No policies found. Clean slate confirmed.");
            return;
        }

        // Loop through and delete each one
        for (const p of policies) {
            console.log(`Deleting policy: ${p.metadata.name}...`);
            await customObjectsApi.deleteNamespacedCustomObject('cilium.io', 'v2', 'default', 'ciliumnetworkpolicies', p.metadata.name);
        }
        
        console.log("Cleanup complete! Environment is wiped.");
    } catch (err) {
        console.error("Failed to clean up policies:", err.body ? err.body.message : err);
        process.exit(1);
    }
}

wipePolicies();