import pulumi
import pulumi_kubernetes as k8s

print("🐝 Pulumi is configuring AuraNet Layer 3 [Workloads]")

# Paths & Configurations
OMNIFINANCE_TARBALL = "./omnifinance-1.0.0.tgz"

# Reference Lower Layers
# Pull Kubeconfig from Layer 1 (Assuming your Layer 1 stack is named 'dev')
infra_reference = pulumi.StackReference("dev")
kubeconfig_from_layer1 = infra_reference.get_output("raw_kubeconfig")

# 3. Instantiate the Kubernetes Provider
k8s_provider = k8s.Provider(
    "layer3-k8s-provider",
    kubeconfig=kubeconfig_from_layer1
)

# 4. Deploy Omnifinance straight into the default namespace
omnifinance_release = k8s.helm.v3.Release(
    "omnifinance-workload",
    k8s.helm.v3.ReleaseArgs(
        name="omnifinance",
        chart=OMNIFINANCE_TARBALL,
        namespace="default", # Installs to default namespace
    ),
    opts=pulumi.ResourceOptions(
        provider=k8s_provider
    )
)

# Export status check
pulumi.export("workload_status", omnifinance_release.status.name)