import pulumi
import pulumi_kubernetes as k8s

print("🚀 Pulumi is configuring the AuraNet Workload Layer...")

# 1. Read the state from your Base Platform layer
base_infra = pulumi.StackReference("organization/auranet-infrastructure/dev")
kubeconfig = base_infra.get_output("raw_kubeconfig")

# 2. Create a Kubernetes provider using those imported credentials
workload_provider = k8s.Provider(
    "layer-2-k8s-provider",
    kubeconfig=kubeconfig
)

# 3. Deploy a simple Nginx pod using standard Python dictionaries
nginx_pod = k8s.core.v1.Pod(
    "test-nginx-pod",
    metadata={
        "name": "layer-2-nginx",
        "labels": {"app": "test-workload"}
    },
    spec={
        "containers": [{
            "name": "nginx",
            "image": "nginx:alpine"
        }]
    },
    # CRITICAL: We tell Pulumi to use our imported Layer 1 provider
    opts=pulumi.ResourceOptions(provider=workload_provider)
)

# Export the pod name to confirm it was created successfully
pulumi.export("deployed_pod_name", nginx_pod.metadata["name"])