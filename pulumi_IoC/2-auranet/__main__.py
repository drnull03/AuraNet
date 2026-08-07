import pulumi
import pulumi_kubernetes as k8s

print(f"🐝 Pulumi is configuring AuraNet Layer 2")
AURANET_CHART_PACKAGE = "../../releases/auranet-core-1.0.0.tgz"
#  Pull the Kubeconfig from Layer 1 (StackReference)

infra_reference = pulumi.StackReference("dev") 
kubeconfig_from_layer1 = infra_reference.get_output("raw_kubeapp_namespaceconfig")

# Instantiate a K8s Provider using Layer 1's dynamic cluster connection
k8s_provider = k8s.Provider(
    "layer2-k8s-provider",
    kubeconfig=kubeconfig_from_layer1
)


# Create the Main Application Namespace 
app_namespace = k8s.core.v1.Namespace(
    "auranet-app-namespace",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name="auranet-namespace",
        labels={
            "access-nats": "true" # Label used by NetworkPolicy
        }
    ),
    opts=pulumi.ResourceOptions(provider=k8s_provider)
)


# Create an isolation policy for auranet-namespace to block 'default' (and others)
app_network_policy = k8s.networking.v1.NetworkPolicy(
    "auranet-app-isolation-policy",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name="isolate-auranet-namespace",
        namespace=app_namespace.metadata.name,
    ),
    spec=k8s.networking.v1.NetworkPolicySpecArgs(
        # Empty pod_selector applies this policy to ALL pods in the auranet-namespace
        pod_selector=k8s.meta.v1.LabelSelectorArgs(),
        policy_types=["Ingress"],
        ingress=[
            k8s.networking.v1.NetworkPolicyIngressRuleArgs(
                from_=[
                    # Explicitly allow traffic ONLY from within the auranet-namespace itself.
                    # Because there is no namespace_selector, it defaults to the local namespace.
                    # This drops all traffic from 'default' and any other external namespaces.
                    k8s.networking.v1.NetworkPolicyPeerArgs(
                        pod_selector=k8s.meta.v1.LabelSelectorArgs()
                    )
                ]
            )
        ]
    ),
    opts=pulumi.ResourceOptions(
        provider=k8s_provider,
        depends_on=[app_namespace]
    )
)

# Create a dedicated namespace for NATS to isolate system messaging
nats_namespace = k8s.core.v1.Namespace(
    "nats-namespace",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name="auranet-messaging"
    ),
    opts=pulumi.ResourceOptions(provider=k8s_provider)
)


nats_network_policy = k8s.networking.v1.NetworkPolicy(
    "nats-network-policy",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name="nats-allow-app-namespace-only",
        namespace=nats_namespace.metadata.name,
    ),
    spec=k8s.networking.v1.NetworkPolicySpecArgs(
        # Empty pod_selector applies this policy to ALL pods in the auranet-messaging namespace
        pod_selector=k8s.meta.v1.LabelSelectorArgs(), 
        policy_types=["Ingress"],
        ingress=[
            k8s.networking.v1.NetworkPolicyIngressRuleArgs(
                from_=[
                    # Allow traffic from the auranet-namespace
                    k8s.networking.v1.NetworkPolicyPeerArgs(
                        namespace_selector=k8s.meta.v1.LabelSelectorArgs(
                            match_labels={"access-nats": "true"}
                        )
                    ),
                    # Allow traffic from other NATS pods in the same namespace (required for JetStream/clustering)
                    k8s.networking.v1.NetworkPolicyPeerArgs(
                        pod_selector=k8s.meta.v1.LabelSelectorArgs() 
                    )
                ],
                # Explicitly open only the ports NATS uses
                ports=[
                    k8s.networking.v1.NetworkPolicyPortArgs(port=4222), # Client connections
                    k8s.networking.v1.NetworkPolicyPortArgs(port=6222), # Routing / Clustering
                    k8s.networking.v1.NetworkPolicyPortArgs(port=8222), # Monitoring
                ]
            )
        ]
    ),
    opts=pulumi.ResourceOptions(
        provider=k8s_provider, 
        depends_on=[nats_namespace, app_namespace]
    )
)



nats_release = k8s.helm.v3.Release(
    "auranet-nats-broker", # Pulumi logical name
    k8s.helm.v3.ReleaseArgs(
        name="auranet-nats-broker", # FORCE EXACT HELM RELEASE NAME
        chart="nats",
        repository_opts=k8s.helm.v3.RepositoryOptsArgs(
            repo="https://nats-io.github.io/k8s/helm/charts/"
        ),
        namespace=nats_namespace.metadata.name,
        values={
            "fullnameOverride": "auranet-nats-broker", # FORCE EXACT K8S SERVICE NAME
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

auranet_core_release = k8s.helm.v3.Release(
    "auranet-core-release",
    k8s.helm.v3.ReleaseArgs(
        name="auranet", 
        chart=AURANET_CHART_PACKAGE, 
        namespace=app_namespace.metadata.name,
        # No repository_opts needed when passing a local file path
    ),
    opts=pulumi.ResourceOptions(
        provider=k8s_provider,
        depends_on=[app_namespace,app_network_policy ,nats_release, nats_network_policy,] 
    )
)




# Export layer outputs for layer 3 or validation checking
pulumi.export("app_namespace", app_namespace.metadata.name)
pulumi.export("nats_namespace", nats_namespace.metadata.name)
pulumi.export("nats_status", nats_release.status.name)
pulumi.export("nats_connection_string", "nats://auranet-nats-broker.auranet-messaging.svc.cluster.local:4222")
pulumi.export("auranet_core_status", auranet_core_release.status.name)