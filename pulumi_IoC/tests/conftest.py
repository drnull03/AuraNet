import pytest
import time
from kubernetes import client, config
from kubernetes.stream import stream

# ==========================================
# 1. CLUSTER API CLIENTS (Loaded Once)
# ==========================================
@pytest.fixture(scope="session")
def k8s_api():
    config.load_kube_config()
    return client.CoreV1Api()

@pytest.fixture(scope="session")
def k8s_net_api():
    config.load_kube_config()
    return client.NetworkingV1Api()

@pytest.fixture(scope="session")
def k8s_crd_api():
    config.load_kube_config()
    return client.CustomObjectsApi()

# ==========================================
# 2. COMMAND EXECUTOR
# ==========================================
@pytest.fixture(scope="session")
def pod_exec(k8s_api):
    """A fixture that returns a helper function to execute commands inside pods."""
    def _execute(namespace, pod_name, command):
        exec_command = ['/bin/sh', '-c', command]
        return stream(
            k8s_api.connect_get_namespaced_pod_exec,
            name=pod_name,
            namespace=namespace,
            command=exec_command,
            stderr=True, stdin=False,
            stdout=True, tty=False
        )
    return _execute

# ==========================================
# 3. EPHEMERAL TEST ENVIRONMENTS
# ==========================================
@pytest.fixture(scope="function")
def ephemeral_ping_pod(k8s_api):
    """Spins up a single pod for basic network routing tests."""
    pod_name = "test-ping-pod"
    namespace = "default"
    
    manifest = {
        "apiVersion": "v1",
        "kind": "Pod",
        "metadata": {"name": pod_name},
        "spec": {
            "containers": [{"name": "busybox", "image": "busybox", "command": ["sleep", "3600"]}],
            "restartPolicy": "Never"
        }
    }
    
    k8s_api.create_namespaced_pod(body=manifest, namespace=namespace)
    
    while True:
        resp = k8s_api.read_namespaced_pod(name=pod_name, namespace=namespace)
        if resp.status.phase == 'Running':
            break
        time.sleep(1)
        
    yield {"name": pod_name, "namespace": namespace}
    
    k8s_api.delete_namespaced_pod(name=pod_name, namespace=namespace)

@pytest.fixture(scope="function")
def policy_test_env(k8s_api):
    """Spins up a Target Server and a Client Hacker pod for policy enforcement tests."""
    namespace = "default"
    client_name = "test-client"
    target_name = "test-target"

    target_manifest = {
        "apiVersion": "v1", "kind": "Pod",
        "metadata": {"name": target_name, "labels": {"app": "secure-web"}},
        "spec": {"containers": [{"name": "nginx", "image": "nginx:alpine"}]}
    }
    
    client_manifest = {
        "apiVersion": "v1", "kind": "Pod",
        "metadata": {"name": client_name},
        "spec": {
            "containers": [{"name": "curl", "image": "curlimages/curl", "command": ["sleep", "3600"]}],
            "restartPolicy": "Never"
        }
    }

    k8s_api.create_namespaced_pod(body=target_manifest, namespace=namespace)
    k8s_api.create_namespaced_pod(body=client_manifest, namespace=namespace)

    target_ip = None
    while not target_ip:
        resp = k8s_api.read_namespaced_pod(name=target_name, namespace=namespace)
        if resp.status.pod_ip:
            target_ip = resp.status.pod_ip
        time.sleep(1)

    while True:
        resp = k8s_api.read_namespaced_pod(name=client_name, namespace=namespace)
        if resp.status.phase == 'Running':
            break
        time.sleep(1)

    # ---> Existing Yield <---
    yield {"client": client_name, "target_ip": target_ip, "namespace": namespace}

    # ---> NEW Teardown logic <---
    k8s_api.delete_namespaced_pod(name=target_name, namespace=namespace)
    k8s_api.delete_namespaced_pod(name=client_name, namespace=namespace)

    # Wait until both pods are completely wiped from existence before allowing the next test to start
    for pod_name in [target_name, client_name]:
        while True:
            try:
                k8s_api.read_namespaced_pod(name=pod_name, namespace=namespace)
                time.sleep(1)
            except client.exceptions.ApiException as e:
                if e.status == 404:  # 404 Not Found means it's fully gone!
                    break