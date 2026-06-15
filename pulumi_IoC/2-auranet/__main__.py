import pulumi
import pulumi_kubernetes as k8s

print(f"🐝 Pulumi is configuring AuraNet Layer 2 (NATS Messaging Engine)...")

# 1. Pull the Kubeconfig from Layer 1 (StackReference)
# Format: "<organization_name>/<project_name>/<stack_name>"
# If using the default local backend, you can typically use just "dev" or your local stack name path.
infra_reference = pulumi.StackReference("dev") 
kubeconfig_from_layer1 = infra_reference.get_output("raw_kubeconfig")

# 2. Instantiate a K8s Provider using Layer 1's dynamic cluster connection
k8s_provider = k8s.Provider(
    "layer2-k8s-provider",
    kubeconfig=kubeconfig_from_layer1
)

# 3. Create a dedicated namespace for NATS to isolate system messaging
nats_namespace = k8s.core.v1.Namespace(
    "nats-namespace",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name="auranet-messaging"
    ),
    opts=pulumi.ResourceOptions(provider=k8s_provider)
)

# 4. Deploy highly available Central NATS Cluster via Helm
nats_release = k8s.helm.v3.Release(
    "auranet-nats-broker",
    k8s.helm.v3.ReleaseArgs(
        chart="nats",
        repository_opts=k8s.helm.v3.RepositoryOptsArgs(
            repo="https://nats-io.github.io/k8s/helm/charts/"
        ),
        namespace=nats_namespace.metadata.name,
        values={
            "nats": {
                # JetStream enables persistence queues/buffers so your inference engine never drops data
                "jetstream": {
                    "enabled": True
                }
            }
        },
    ),
    opts=pulumi.ResourceOptions(
        provider=k8s_provider, 
        depends_on=[nats_namespace]
    )
)

# Export layer outputs for layer 3 or validation checking
pulumi.export("nats_namespace", nats_namespace.metadata.name)
pulumi.export("nats_status", nats_release.status.name)
pulumi.export("nats_connection_string", "nats://my-nats.auranet-messaging.svc.cluster.local:4222")