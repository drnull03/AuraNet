import pytest
import time
from kubernetes import client, config
from kubernetes.stream import stream

# --- 1. SESSION API CONNECTION ---
@pytest.fixture(scope="session")
def k8s_api():
    """Loads your local Pulumi-generated kubeconfig once for the whole test run."""
    config.load_kube_config() 
    return client.CoreV1Api()

# --- 2. THE EPHEMERAL POD LIFECYCLE ---
@pytest.fixture(scope="function")
def ephemeral_pod(k8s_api):
    """
    Creates a temporary dummy pod, hands it to the test, and absolutely 
    GUARANTEES it is deleted afterwards, leaving the cluster clean.
    """
    pod_name = "integration-test-ping"
    namespace = "default"

    # 1. Define a sleeping pod so it stays alive long enough for us to 'exec' into it
    pod_manifest = {
        "apiVersion": "v1",
        "kind": "Pod",
        "metadata": {"name": pod_name},
        "spec": {
            "containers": [{
                "name": "busybox",
                "image": "busybox",
                "command": ["sleep", "3600"] 
            }],
            "restartPolicy": "Never"
        }
    }

    # 2. Boot it up
    k8s_api.create_namespaced_pod(body=pod_manifest, namespace=namespace)

    # 3. Wait until it is fully running (avoids exec errors)
    while True:
        resp = k8s_api.read_namespaced_pod(name=pod_name, namespace=namespace)
        if resp.status.phase == 'Running':
            break
        time.sleep(1)

    # ---> YIELD control to the actual test below <---
    yield pod_name

    # 4. TEARDOWN: This runs no matter what happens (Pass, Fail, or Crash)
    k8s_api.delete_namespaced_pod(name=pod_name, namespace=namespace)
    
    # Wait until it is entirely wiped from existence
    while True:
        try:
            k8s_api.read_namespaced_pod(name=pod_name, namespace=namespace)
            time.sleep(1)
        except client.exceptions.ApiException as e:
            if e.status == 404: # 404 Not Found means it's gone!
                break
                
# --- 3. THE ACTUAL TEST ---
def test_cross_namespace_ping(k8s_api, ephemeral_pod):
    """
    Tests that a pod in 'default' can successfully resolve and ping
    a core service in the 'kube-system' namespace.
    """
    exec_command = [
        '/bin/sh', '-c', 
        'ping -c 4 hubble-relay.kube-system.svc.cluster.local'
    ]
    
    # Run the ping command inside the ephemeral pod
    response = stream(
        k8s_api.connect_get_namespaced_pod_exec,
        name=ephemeral_pod,
        namespace="default",
        command=exec_command,
        stderr=True, stdin=False,
        stdout=True, tty=False
    )

    # Assert we didn't drop packets
    assert "0% packet loss" in response, f"Ping failed! Output:\n{response}"