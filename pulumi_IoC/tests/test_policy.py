import time

def test_l4_default_deny_policy(k8s_net_api, policy_test_env, pod_exec):
    """Deploys a default deny NetworkPolicy and ensures traffic is dropped."""
    env = policy_test_env
    policy_name = "default-deny"

    policy_manifest = {
        "apiVersion": "networking.k8s.io/v1",
        "kind": "NetworkPolicy",
        "metadata": {"name": policy_name},
        "spec": {
            "podSelector": {}, 
            "policyTypes": ["Ingress"]
        }
    }

    try:
        # Apply the Deny policy
        k8s_net_api.create_namespaced_network_policy(namespace=env["namespace"], body=policy_manifest)
        time.sleep(2) # Give Cilium time to compile the rule

        # Attempt to curl the target
        command = f"curl --max-time 3 {env['target_ip']}"
        output = pod_exec(env["namespace"], env["client"], command)

        assert "Connection timed out" in output or "Timeout" in output, \
            f"Traffic bypassed the L4 policy! Output: {output}"
        
    finally:
        k8s_net_api.delete_namespaced_network_policy(name=policy_name, namespace=env["namespace"])

def test_l7_http_method_policy(k8s_crd_api, policy_test_env, pod_exec):
    """Deploys a Cilium L7 Policy allowing GET but explicitly dropping POST."""
    env = policy_test_env
    policy_name = "l7-http-enforcement"

    cilium_policy = {
        "apiVersion": "cilium.io/v2",
        "kind": "CiliumNetworkPolicy",
        "metadata": {"name": policy_name},
        "spec": {
            "endpointSelector": {"matchLabels": {"app": "secure-web"}},
            "ingress": [{
                "toPorts": [{
                    "ports": [{"port": "80", "protocol": "TCP"}],
                    "rules": {"http": [{"method": "GET"}]}
                }]
            }]
        }
    }

    try:
        # Inject the CRD
        k8s_crd_api.create_namespaced_custom_object(
            group="cilium.io", version="v2", namespace=env["namespace"],
            plural="ciliumnetworkpolicies", body=cilium_policy
        )
        time.sleep(3) # Wait for proxies to sync

        # Action 1: Send a GET request (Should Succeed)
        get_cmd = f"curl -s -o /dev/null -w '%{{http_code}}' -X GET http://{env['target_ip']}"
        get_status = pod_exec(env["namespace"], env["client"], get_cmd)
        assert get_status.strip() == "200", f"Legitimate GET blocked! Status: {get_status}"

        # Action 2: Send a POST request (Should return 403 Forbidden)
        post_cmd = f"curl -s -o /dev/null -w '%{{http_code}}' -X POST http://{env['target_ip']}"
        post_status = pod_exec(env["namespace"], env["client"], post_cmd)
        assert post_status.strip() == "403", f"Malicious POST allowed! Status: {post_status}"

    finally:
        k8s_crd_api.delete_namespaced_custom_object(
            group="cilium.io", version="v2", namespace=env["namespace"],
            plural="ciliumnetworkpolicies", name=policy_name
        )