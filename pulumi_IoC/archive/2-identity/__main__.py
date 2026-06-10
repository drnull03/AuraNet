"""Deploys SPIRE to the AuraNet cluster with Dynamic Workload Registration."""

import pulumi
import pulumi_kubernetes as k8s

# 1. Read the state from your Base Platform layer
try:
    # Using a local Pulumi backend, so the stack name is just "dev"
    base_infra = pulumi.StackReference("dev")
    kubeconfig = base_infra.get_output("kubeconfig")
    is_local = True
except Exception as e:
    raise Exception(f"Failed to find the Base Platform stack. Ensure it is deployed and named 'dev'. Error: {e}")

# 2. Create an explicit Kubernetes provider bound ONLY to Layer 1's cluster
workload_provider = k8s.Provider(
    "layer-2-k8s-provider",
    kubeconfig=kubeconfig
)

# 3. Create a namespace for SPIRE
spire_namespace = k8s.core.v1.Namespace(
    "spire-namespace",
    metadata={
        "name": "spire-system",
        "labels": {
            # Required for the SPIFFE CSI driver to mount sockets directly to hosts
            "pod-security.kubernetes.io/enforce": "privileged" 
        }
    },
    opts=pulumi.ResourceOptions(provider=workload_provider)
)

# 4. Deploy SPIRE CRDs
spire_crds_release = k8s.helm.v3.Release(
    "spire-crds",
    k8s.helm.v3.ReleaseArgs(
        name="spire-crds", # <--- THE FIX: Forces deterministic naming
        chart="spire-crds",
        repository_opts=k8s.helm.v3.RepositoryOptsArgs(
            repo="https://spiffe.github.io/helm-charts-hardened/"
        ),
        namespace=spire_namespace.metadata["name"],
    ),
    opts=pulumi.ResourceOptions(provider=workload_provider, depends_on=[spire_namespace])
)

# 5. Deploy SPIRE Engine
spire_release = k8s.helm.v3.Release(
    "spire",
    k8s.helm.v3.ReleaseArgs(
        name="spire", # <--- THE FIX: Prevents Pulumi from appending the hash
        chart="spire",
        repository_opts=k8s.helm.v3.RepositoryOptsArgs(
            repo="https://spiffe.github.io/helm-charts-hardened/"
        ),
        namespace=spire_namespace.metadata["name"],
        values={
            "global": {
                "spire": {
                    "trustDomain": "auranet.dev",
                    "clusterName": "auranet-cluster",
                }
            },
            "spire-server": {
                "ca_ttl": "24h",
                "default_svid_ttl": "10m",
                "nodeAttestor": {
                    "k8sPSAT": {
                        "enabled": True
                    }
                }
            },
            "spire-agent": {
                "nodeAttestor": {
                    "k8sPSAT": {
                        "enabled": True
                    }
                }
            }
        }
    ),
    opts=pulumi.ResourceOptions(provider=workload_provider, depends_on=[spire_crds_release])
)

# 6. Deploy the Master Dynamic Auto-Registration Rule
# This eliminates manual entry management by converting pod labels directly into SPIFFE identities
dynamic_identity_rule = k8s.apiextensions.CustomResource(
    "auranet-master-dynamic-id",
    api_version="spire.spiffe.io/v1alpha1",
    kind="ClusterSPIFFEID",
    metadata={
        "name": "auranet-dynamic-router"
    },
    spec={
        # THE MISSING LINK: Tell the controller to actually process this rule
        "className": "spire-system-spire",
        
        "spiffeIDTemplate": "spiffe://auranet.dev/{{ index .PodMeta.Labels \"auranet-id\" }}",
        "podSelector": {
            "matchExpressions": [{
                "key": "auranet-id",
                "operator": "Exists"
            }]
        }
    },
    opts=pulumi.ResourceOptions(provider=workload_provider, depends_on=[spire_crds_release])
)
# 7. Export critical state metrics
pulumi.export("spire_namespace", spire_namespace.metadata["name"])
pulumi.export("is_local_stack_reference", is_local)