const k8s = require('@kubernetes/client-node');

const kc = new k8s.KubeConfig();
kc.loadFromCluster();
const customObjectsApi = kc.makeApiClient(k8s.CustomObjectsApi);

async function wipePolicies() {
    console.log("Starting AuraNet Teardown Sequence...");

    //  Wipe Cilium Network Policies
    try {
        const cnps = await customObjectsApi.listNamespacedCustomObject(
            'cilium.io', 'v2', 'default', 'ciliumnetworkpolicies'
        );
        for (const item of cnps.body.items) {
            await customObjectsApi.deleteNamespacedCustomObject(
                'cilium.io', 'v2', 'default', 'ciliumnetworkpolicies', item.metadata.name
            );
            console.log(`[CLEANED] Deleted Network Policy: ${item.metadata.name}`);
        }
    } catch (e) {
        const trueError = e.body ? JSON.stringify(e.body) : (e.cause ? e.cause.message : e.message);
        console.error("[ERROR] wiping network policies:", trueError);
    }

    //  Wipe  Tracing PoliciesapplyRuntimePolicies
    // because old naive policies were tracing policeis
    try {
        const tracingPolicies = await customObjectsApi.listNamespacedCustomObject(
            'cilium.io', 'v1alpha1', 'default', 'tracingpoliciesnamespaced'
        );
        for (const item of tracingPolicies.body.items) {
            await customObjectsApi.deleteNamespacedCustomObject(
                'cilium.io', 'v1alpha1', 'default', 'tracingpoliciesnamespaced', item.metadata.name
            );
            console.log(`[CLEANED] Deleted Tracing Policy: ${item.metadata.name}`);
        }
    } catch (e) {
        const trueError = e.body ? JSON.stringify(e.body) : (e.cause ? e.cause.message : e.message);
        console.error("[ERROR] wiping tracing policies:", trueError);
    }
}

wipePolicies();