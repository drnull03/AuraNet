/**
 * @file integration.test.js
 * @brief Automated Zero Trust Network validation using Jest and kubectl.
 */
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const NAIVE_CONF_PATH = path.join(__dirname, 'test-naive.conf');
const PODS_YAML_PATH = path.join(__dirname, 'test-pods.yaml');

beforeAll(() => {
    console.log(" Setting up Zero Trust Test Environment...");

    const podsYaml = `
apiVersion: v1
kind: Pod
metadata:
  name: api-gateway
  labels:
    app: api-gateway
spec:
  containers:
  - name: web
    image: nginx:alpine
    ports:
    - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: api-gateway
spec:
  selector:
    app: api-gateway
  ports:
  - port: 80
    targetPort: 80
---
apiVersion: v1
kind: Pod
metadata:
  name: frontend-ui
  labels:
    app: frontend-ui
spec:
  containers:
  - name: tool
    image: wbitt/network-multitool
    command: ["sleep", "3600"]
---
apiVersion: v1
kind: Pod
metadata:
  name: rogue-pod
  labels:
    app: rogue-pod
spec:
  containers:
  - name: tool
    image: wbitt/network-multitool
    command: ["sleep", "3600"]
`;
    fs.writeFileSync(PODS_YAML_PATH, podsYaml);
    execSync(`kubectl apply -f ${PODS_YAML_PATH}`, { stdio: 'ignore' });

    console.log(" Waiting for all pods to reach Ready state...");
    execSync('kubectl wait --for=condition=Ready pod/api-gateway pod/frontend-ui pod/rogue-pod --timeout=90s', { stdio: 'ignore' });

    //  Generate the exact naive.conf to enforce the authorized connection
    fs.writeFileSync(NAIVE_CONF_PATH, "1. frontend-ui -> api-gateway:80\n");

    //  Trigger the AuraNet Bootstrap engine to generate the Cilium policy
    console.log(" Running AuraNet Bootstrap to enforce policies...");
    execSync(`node ${path.join(__dirname, 'index.js')} ${NAIVE_CONF_PATH}`, { stdio: 'inherit' });
    
    // Allow Cilium 3 seconds to fully inject the eBPF datapath rules
    execSync('sleep 3');
});

afterAll(() => {
    console.log(" Tearing down test environment...");
    try {
        execSync(`kubectl delete -f ${PODS_YAML_PATH} --ignore-not-found=true`, { stdio: 'ignore' });
        if (fs.existsSync(PODS_YAML_PATH)) fs.unlinkSync(PODS_YAML_PATH);
        if (fs.existsSync(NAIVE_CONF_PATH)) fs.unlinkSync(NAIVE_CONF_PATH);
        
        // Use your native cleanup utility to eradicate test policies
        execSync(`node ${path.join(__dirname, 'cleanup.js')}`, { stdio: 'ignore' });
    } catch (e) {
        console.error("Warning during cleanup:", e.message);
    }
});

describe("AuraNet Dynamic Network Isolation (Cilium)", () => {
    test(" Authorized Source: 'frontend-ui' MUST successfully connect to 'api-gateway'", () => {
        try {
            // max-time 3s, silent output
            const result = execSync('kubectl exec frontend-ui -- curl -s --max-time 3 http://api-gateway:80').toString();
            expect(result).toContain("Welcome to nginx!");
        } catch (error) {
            throw new Error(`Traffic was incorrectly dropped: ${error.message}`);
        }
    });

    test(" Rogue Source: 'rogue-pod' MUST trigger a timeout when attempting to connect", () => {
        let didFail = false;
        try {
            // Because of the default deny ingress, Cilium silently drops the packet, causing a hang/timeout
            execSync('kubectl exec rogue-pod -- curl -s --max-time 3 http://api-gateway:80', { stdio: 'pipe' });
        } catch (error) {
            didFail = true;
            // Exit code 28 = curl connection timed out
            expect(error.status).toBe(28); 
        }
        expect(didFail).toBe(true);
    });
});