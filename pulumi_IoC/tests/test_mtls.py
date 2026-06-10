import pytest
import time
from kubernetes import client


@pytest.fixture(scope="function")
def mtls_test_env(k8s_api):
    """Spins up a Database, an Authorized AI Engine, and a Rogue Attacker."""
    namespace = "default"
    target_name = "auranet-db"
    auth_client = "auranet-ai-engine"
    rogue_client = "rogue-attacker"

    target_manifest = {
        "apiVersion": "v1", "kind": "Pod",
        "metadata": {"name": target_name, "labels": {"auranet-id": "database-node"}},
        "spec": {"containers": [{"name": "server", "image": "nginx:alpine"}]}
    }
    
    auth_manifest = {
        "apiVersion": "v1", "kind": "Pod",
        "metadata": {"name": auth_client, "labels": {"auranet-id": "ai-engine"}},
        "spec": {
            "containers": [{"name": "client", "image": "curlimages/curl:latest", "command": ["sleep", "3600"]}],
            "restartPolicy": "Never"
        }
    }

    rogue_manifest = {
        "apiVersion": "v1", "kind": "Pod",
        "metadata": {"name": rogue_client, "labels": {"role": "hacker"}},
        "spec": {
            "containers": [{"name": "attacker", "image": "curlimages/curl:latest", "command": ["sleep", "3600"]}],
            "restartPolicy": "Never"
        }
    }

    # Deploy the trio
    k8s_api.create_namespaced_pod(body=target_manifest, namespace=namespace)
    k8s_api.create_namespaced_pod(body=auth_manifest, namespace=namespace)
    k8s_api.create_namespaced_pod(body=rogue_manifest, namespace=namespace)

    # Grab Target IP
    target_ip = None
    while not target_ip:
        resp = k8s_api.read_namespaced_pod(name=target_name, namespace=namespace)
        if resp.status.pod_ip:
            target_ip = resp.status.pod_ip
        time.sleep(1)

    # Wait for clients to be ready
    for pod_name in [auth_client, rogue_client]:
        while True:
            resp = k8s_api.read_namespaced_pod(name=pod_name, namespace=namespace)
            if resp.status.phase == 'Running':
                break
            time.sleep(1)

    yield {
        "target_ip": target_ip,
        "auth_client": auth_client,
        "rogue_client": rogue_client,
        "namespace": namespace
    }

    # Teardown logic
    k8s_api.delete_namespaced_pod(name=target_name, namespace=namespace)
    k8s_api.delete_namespaced_pod(name=auth_client, namespace=namespace)
    k8s_api.delete_namespaced_pod(name=rogue_client, namespace=namespace)

    # Block until completely destroyed
    for pod_name in [target_name, auth_client, rogue_client]:
        while True:
            try:
                k8s_api.read_namespaced_pod(name=pod_name, namespace=namespace)
                time.sleep(1)
            except client.exceptions.ApiException as e:
                if e.status == 404:
                    break



def test_spiffe_mutual_authentication(k8s_crd_api, mtls_test_env, pod_exec):
    """Deploys a CiliumNetworkPolicy requiring SPIFFE mTLS and verifies eBPF enforcement."""
    env = mtls_test_env
    policy_name = "secure-db-access"

    # The exact eBPF policy you built in the terminal
    cilium_policy = {
        "apiVersion": "cilium.io/v2",
        "kind": "CiliumNetworkPolicy",
        "metadata": {"name": policy_name},
        "spec": {
            "endpointSelector": {"matchLabels": {"auranet-id": "database-node"}},
            "ingress": [{
                "fromEndpoints": [{"matchLabels": {"auranet-id": "ai-engine"}}],
                "toPorts": [{"ports": [{"port": "80", "protocol": "TCP"}]}],
                # The Layer 2 Injection
                "authentication": {"mode": "required"}
            }]
        }
    }

    try:
        #  Inject the CRD
        k8s_crd_api.create_namespaced_custom_object(
            group="cilium.io", version="v2", namespace=env["namespace"],
            plural="ciliumnetworkpolicies", body=cilium_policy
        )
        time.sleep(4) # Wait for Cilium Agents to sync the policy and the embedded SPIRE to rotate identities

        #  Execute the Attack (Negative Test)
        # We use a strict 3-second timeout to catch the eBPF drop without hanging the test suite forever
        rogue_cmd = f"curl -m 3 http://{env['target_ip']}"
        rogue_output = pod_exec(env["namespace"], env["rogue_client"], rogue_cmd)
        
        # Ensure the kernel dropped the packet (exit code 28 / timeout)
        assert "timed out" in rogue_output.lower() or "timeout" in rogue_output.lower(), \
            f"Zero Trust failure! Rogue attacker bypassed mTLS. Output: {rogue_output}"

        #  Execute the Authorized Request (Positive Test)
        auth_cmd = f"curl -s -o /dev/null -w '%{{http_code}}' -m 5 http://{env['target_ip']}"
        auth_status = pod_exec(env["namespace"], env["auth_client"], auth_cmd)
        
        # Ensure the SPIFFE handshake succeeded and Nginx responded
        assert auth_status.strip() == "200", \
            f"Authorized client was blocked! Handshake failed. Status: {auth_status}"

    finally:
        # Clean up the policy to leave the cluster state pristine
        k8s_crd_api.delete_namespaced_custom_object(
            group="cilium.io", version="v2", namespace=env["namespace"],
            plural="ciliumnetworkpolicies", name=policy_name
        )