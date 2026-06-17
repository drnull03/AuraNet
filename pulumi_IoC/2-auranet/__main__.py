import pulumi
import pulumi_kubernetes as k8s

print(f"🐝 Pulumi is configuring AuraNet Layer 2 (NATS Messaging Engine)...")

#  Pull the Kubeconfig from Layer 1 (StackReference)

infra_reference = pulumi.StackReference("dev") 
kubeconfig_from_layer1 = infra_reference.get_output("raw_kubeconfig")

# Instantiate a K8s Provider using Layer 1's dynamic cluster connection
k8s_provider = k8s.Provider(
    "layer2-k8s-provider",
    kubeconfig=kubeconfig_from_layer1
)


# Create the Main Application Namespace 
app_namespace = k8s.core.v1.Namespace(
    "auranet-app-namespace",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name="auranet-namespace"
    ),
    opts=pulumi.ResourceOptions(provider=k8s_provider)
)

# Create a dedicated namespace for NATS to isolate system messaging
nats_namespace = k8s.core.v1.Namespace(
    "nats-namespace",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name="auranet-messaging"
    ),
    opts=pulumi.ResourceOptions(provider=k8s_provider)
)

nats_release = k8s.helm.v3.Release(
    "auranet-nats-broker", # Pulumi logical name
    k8s.helm.v3.ReleaseArgs(
        name="auranet-nats-broker", # 1. FORCE EXACT HELM RELEASE NAME
        chart="nats",
        repository_opts=k8s.helm.v3.RepositoryOptsArgs(
            repo="https://nats-io.github.io/k8s/helm/charts/"
        ),
        namespace=nats_namespace.metadata.name,
        values={
            "fullnameOverride": "auranet-nats-broker", # 2. FORCE EXACT K8S SERVICE NAME
            "config": {             
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
pulumi.export("app_namespace", app_namespace.metadata.name)
pulumi.export("nats_namespace", nats_namespace.metadata.name)
pulumi.export("nats_status", nats_release.status.name)
pulumi.export("nats_connection_string", "nats://my-nats.auranet-messaging.svc.cluster.local:4222")