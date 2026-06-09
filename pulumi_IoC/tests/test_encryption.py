def test_wireguard_encryption_is_active(k8s_api, pod_exec):
    """Verifies the eBPF datapath has loaded WireGuard for node-to-node encryption."""
    # Find a Cilium agent
    pods = k8s_api.list_namespaced_pod("kube-system", label_selector="k8s-app=cilium")
    assert len(pods.items) > 0, "No Cilium agents found!"
    
    cilium_pod_name = pods.items[0].metadata.name
    
    # Query its status
    output = pod_exec("kube-system", cilium_pod_name, "cilium status")
    
    assert "Wireguard" in output, "WireGuard is disabled or missing!"