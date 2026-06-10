"""Deploys SPIRE to the AuraNet cluster."""

import pulumi
import pulumi_kubernetes as k8s

# 1. Read the state from your Base Platform layer
try:
    base_infra = pulumi.StackReference("organization/1-base-platform/dev")
    kubeconfig = base_infra.get_output("kubeconfig")
    is_local = True
except pulumi.errors.StackReferenceMissingError:
    # If the local stack reference is not found, assume we are running in a different environment
    # and get the kubeconfig from the organization's stack.
    # Note: You might need to adjust the organization name.
    base_infra = pulumi.StackReference("Diaa/AuraNet/dev")
    kubeconfig = base_infra.get_output("kubeconfig")
    is_local = False


# 2. Create a Kubernetes provider using those imported credentials
workload_provider = k8s.Provider(
    "layer-2-k8s-provider",
    kubeconfig=kubeconfig
)

# 3. Create a namespace for SPIRE
spire_namespace = k8s.core.v1.Namespace(
    "spire-namespace",
    metadata={"name": "spire"},
    opts=pulumi.ResourceOptions(provider=workload_provider)
)

# 4. Deploy SPIRE CRDs using the Helm chart
spire_crds_chart = k8s.helm.v3.Chart(
    "spire-crds",
    k8s.helm.v3.ChartOpts(
        chart="spire-crds",
        fetch_opts=k8s.helm.v3.FetchOpts(
            repo="https://spiffe.github.io/helm-charts-hardened"
        ),
        namespace=spire_namespace.metadata["name"],
    ),
    opts=pulumi.ResourceOptions(provider=workload_provider, depends_on=[spire_namespace])
)


# 5. Deploy SPIRE using the Helm chart
spire_chart = k8s.helm.v3.Chart(
    "spire",
    k8s.helm.v3.ChartOpts(
        chart="spire",
        fetch_opts=k8s.helm.v3.FetchOpts(
            repo="https://spiffe.github.io/helm-charts-hardened"
        ),
        namespace=spire_namespace.metadata["name"],
        values={
            "global": {
                "spire": {
                    "trustDomain": "auranet.io",
                    "clusterName": "auranet-cluster",
                }
            },
            "spire-server": {
                "config": {
                    "ca_ttl": "240h",
                    "default_svid_ttl": "10m",
                },
                # Explicitly configure the k8s_psat node attestor
                "node_attestor": {
                    "k8s_psat": {
                        "service_account_allow_list": ["spire:spire-agent"]
                    }
                },
            },
            "spire-agent": {
                "config": {
                    # Configure the agent to use the k8s_psat node attestor
                    "node_attestor": {
                       "k8s_psat": {
                           "cluster": "auranet-cluster"
                       }
                    }
                }
            }
        }
    ),
    opts=pulumi.ResourceOptions(provider=workload_provider, depends_on=[spire_crds_chart])
)

# Export the namespace name
pulumi.export("spire_namespace", spire_namespace.metadata["name"])
pulumi.export("is_local_stack_reference", is_local)
