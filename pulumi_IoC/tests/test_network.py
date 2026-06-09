def test_cross_namespace_ping(ephemeral_ping_pod, pod_exec):
    """Tests that a pod can resolve and ping the Hubble Relay service."""
    env = ephemeral_ping_pod
    command = "ping -c 4 hubble-relay.kube-system.svc.cluster.local"
    
    output = pod_exec(env["namespace"], env["name"], command)
    
    assert "0% packet loss" in output, f"Ping failed! Output:\n{output}"