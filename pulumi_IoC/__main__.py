import pulumi
import pulumi_command as command
import pulumi_kubernetes as k8s

CLUSTER_NAME = "my-cluster"
CONFIG_PATH = "./cluster/3Nodes.yaml"

print(f"🐝 Pulumi is configuring the AuraNet cluster and eBPF datapath...")

# 1. Boot up the 3-node Kind cluster
kind_cluster = command.local.Command(
    "kind-cluster",
    create=f"kind create cluster --name {CLUSTER_NAME} --config {CONFIG_PATH}",
    delete=f"kind delete cluster --name {CLUSTER_NAME}",
)

# 2. Extract the kubeconfig dynamically right after the cluster boots
# We track this as a separate command so we can pass its stdout directly to the provider.
kubeconfig = command.local.Command(
    "get-kubeconfig",
    create=f"kind get kubeconfig --name {CLUSTER_NAME}",
    opts=pulumi.ResourceOptions(depends_on=[kind_cluster])
)

# 3. Create a dedicated Kubernetes provider tied directly to this local cluster instance
k8s_provider = k8s.Provider(
    "kind-k8s-provider",
    kubeconfig=kubeconfig.stdout,
    opts=pulumi.ResourceOptions(depends_on=[kubeconfig])
)

# 4. Install Cilium via Helm Release
# This completely replaces 'cilium install --set hubble.relay.enabled=true...'
cilium_release = k8s.helm.v3.Release(
    "cilium-ebpf-datapath",
    k8s.helm.v3.ReleaseArgs(
        chart="cilium",
        version="1.15.5", # Standard stable version for local dev setups
        repository_opts=k8s.helm.v3.RepositoryOptsArgs(
            repo="https://helm.cilium.io/"
        ),
        namespace="kube-system",
        # We pass your Hubble settings directly into the chart values
        values={
            "hubble": {
                "relay": {"enabled": True},
                "ui": {"enabled": True}
            },
            "encryption": {
                "enabled": True,
                "type": "wireguard"
            }
        },
    ),
    # Crucial: We tell Pulumi to deploy this using our specific Kind provider instance
    opts=pulumi.ResourceOptions(provider=k8s_provider, depends_on=[kubeconfig])
)

# Export deployment metrics to your terminal output
pulumi.export("deployed_cluster_name", CLUSTER_NAME)
pulumi.export("cilium_status", cilium_release.status.name)