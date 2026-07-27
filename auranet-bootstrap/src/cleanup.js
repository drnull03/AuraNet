/**
 * @file cleanup.js
 * @brief AuraNet Bootstrap cleanup utility.
 *
 * Removes all network and runtime security policies previously
 * deployed by the AuraNet Bootstrap microservice.
 */
const k8s = require('@kubernetes/client-node');

const kc = new k8s.KubeConfig();
kc.loadFromCluster();
const customObjectsApi = kc.makeApiClient(k8s.CustomObjectsApi);
/**
 * Deletes all AuraNet-managed Cilium network policies and
 * tracing policies from the Kubernetes cluster.
 *
 * Intended for development, testing, or complete environment
 * teardown prior to redeployment.
 *
 * @async
 * @returns {Promise<void>}
 */
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