// index.test.js
const { 
    applyQuarantine, 
    applyVirtualPatch, 
    cycleWorkloadPods, 
    removeQuarantine 
} = require("./index");

// 1. MOCK THE EXTERNAL LIBRARIES
jest.mock("fs"); // Stop it from actually trying to read files
const fs = require("fs");

jest.mock("@kubernetes/client-node", () => {
    // Create fake API functions we can spy on
    const mockCreateNamespacedCustomObject = jest.fn();
    const mockDeleteNamespacedCustomObject = jest.fn();
    const mockDeleteCollectionNamespacedPod = jest.fn();

    return {
        KubeConfig: jest.fn().mockImplementation(() => ({
            loadFromCluster: jest.fn(),
            loadFromDefault: jest.fn(),
            makeApiClient: jest.fn().mockImplementation((apiType) => {
                // Return our fake functions depending on which API is requested
                if (apiType.name === 'CoreV1Api') {
                    return { deleteCollectionNamespacedPod: mockDeleteCollectionNamespacedPod };
                }
                if (apiType.name === 'CustomObjectsApi') {
                    return { 
                        createNamespacedCustomObject: mockCreateNamespacedCustomObject,
                        deleteNamespacedCustomObject: mockDeleteNamespacedCustomObject
                    };
                }
            })
        })),
        CoreV1Api: { name: 'CoreV1Api' },
        CustomObjectsApi: { name: 'CustomObjectsApi' }
    };
});

const k8s = require("@kubernetes/client-node");

describe("AuraNet AutoHeal: Kubernetes Execution Engine", () => {
    let customApiMock;
    let coreApiMock;

    beforeEach(() => {
        // Clear all mock history before each test
        jest.clearAllMocks();
        
        // Grab the references to our spy functions
        const kc = new k8s.KubeConfig();
        coreApiMock = kc.makeApiClient(k8s.CoreV1Api);
        customApiMock = kc.makeApiClient(k8s.CustomObjectsApi);
        
        // Suppress console logs during testing so our terminal stays clean
        jest.spyOn(console, 'log').mockImplementation(() => {});
        jest.spyOn(console, 'error').mockImplementation(() => {});
    });

    test("1. applyQuarantine should send the correct Default Deny policy to the K8s API", async () => {
        await applyQuarantine("payment-api");

        // Verify the API was called exactly once
        expect(customApiMock.createNamespacedCustomObject).toHaveBeenCalledTimes(1);
        
        // Verify the payload contained the correct namespace and workload label
        const apiCallArguments = customApiMock.createNamespacedCustomObject.mock.calls[0][0];
        expect(apiCallArguments.group).toBe("cilium.io");
        expect(apiCallArguments.body.metadata.name).toBe("quarantine-payment-api");
        expect(apiCallArguments.body.spec.endpointSelector.matchLabels.app).toBe("payment-api");
    });

    test("2. cycleWorkloadPods should target the correct label selector for deletion", async () => {
        await cycleWorkloadPods("customer-api");

        expect(coreApiMock.deleteCollectionNamespacedPod).toHaveBeenCalledTimes(1);
        
        const apiCallArguments = coreApiMock.deleteCollectionNamespacedPod.mock.calls[0][0];
        // Verify it specifically targets the compromised workload, not the whole cluster
        expect(apiCallArguments.labelSelector).toBe("app=customer-api");
    });

    test("3. removeQuarantine should request deletion of the exact policy name", async () => {
        await removeQuarantine("database-svc");

        expect(customApiMock.deleteNamespacedCustomObject).toHaveBeenCalledTimes(1);
        
        const apiCallArguments = customApiMock.deleteNamespacedCustomObject.mock.calls[0][0];
        expect(apiCallArguments.name).toBe("quarantine-database-svc");
    });

    test("4. applyVirtualPatch should skip execution if the patch file is missing", async () => {
        // Mock fs.existsSync to return false
        fs.existsSync.mockReturnValue(false);

        await applyVirtualPatch("missing-patch.yaml");

        // The K8s API should NEVER be called if the file doesn't exist
        expect(customApiMock.createNamespacedCustomObject).not.toHaveBeenCalled();
    });
});