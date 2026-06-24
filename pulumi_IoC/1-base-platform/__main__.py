import pulumi
import pulumi_command as command
import pulumi_kubernetes as k8s

CLUSTER_NAME = "my-cluster"
CONFIG_PATH = "./cluster/3Nodes.yaml" # this should be injectable and changeable 

print(f"🐝 Pulumi is configuring the AuraNet cluster and eBPF datapath...")


# this should be decoupled in the future 
# TODO: decouple this 
# frist step: Boot up the 3-node Kind cluster
kind_cluster = command.local.Command(
    "kind-cluster",
    create=f"kind create cluster --name {CLUSTER_NAME} --config {CONFIG_PATH}",
    delete=f"kind delete cluster --name {CLUSTER_NAME}",
)

# second step: Extract the kubeconfig dynamically right after the cluster boots
kubeconfig = command.local.Command(
    "get-kubeconfig",
    create=f"kind get kubeconfig --name {CLUSTER_NAME}",
    opts=pulumi.ResourceOptions(depends_on=[kind_cluster])
)


# 2 and a half added later
load_auranet_images = command.local.Command(
    "load-auranet-images",
    create=f"""
        echo "Scanning local Docker registry for auranet/ images..."
        
        # Query Docker for images and tags, then grep for the 'auranet/' prefix
        # Note: The {{{{ }}}} syntax is required to escape the brackets inside a Python f-string
        IMAGES=$(docker images --format '{{{{.Repository}}}}:{{{{.Tag}}}}' | grep '^auranet/' || true)
        
        if [ -z "$IMAGES" ]; then
            echo "No auranet/ images found locally. Skipping load."
            exit 0
        fi
        
        # Loop through the found images and load them into Kind
        for IMAGE in $IMAGES; do
            echo "🐝 Sideloading $IMAGE into {CLUSTER_NAME}..."
            kind load docker-image "$IMAGE" --name {CLUSTER_NAME}
        done
        
        echo "All AuraNet images loaded successfully!"
    """,
    # This must wait for the cluster to actually exist before attempting to load images
    opts=pulumi.ResourceOptions(depends_on=[kind_cluster])
)

# third step: Create a dedicated Kubernetes provider tied directly to this local cluster instance
k8s_provider = k8s.Provider(
    "kind-k8s-provider",
    kubeconfig=kubeconfig.stdout,
    opts=pulumi.ResourceOptions(depends_on=[kubeconfig])
)

#  Install Cilium via Helm Release
cilium_release = k8s.helm.v3.Release(
    "cilium-ebpf-datapath",
    k8s.helm.v3.ReleaseArgs(
        chart="cilium",
        # Standard stable version for local dev setups
        repository_opts=k8s.helm.v3.RepositoryOptsArgs(
            repo="https://helm.cilium.io/"
        ),
        namespace="kube-system",
        values={
            "hubble": {
                "relay": {"enabled": True},
                "ui": {"enabled": True}
            },
            "encryption": {
                "enabled": True,
                "type": "wireguard"
            },
            "authentication": {
                "enabled": True,
                "mutual": {
                    "spire": {
                        "enabled": True,
                        "install": {
                            
                            "enabled": True 
                        }
                    }
                }
            }
        },
    ),
    opts=pulumi.ResourceOptions(provider=k8s_provider, depends_on=[kubeconfig])
)


tetragon_release = k8s.helm.v3.Release(
    "tetragon-security-observability",
    k8s.helm.v3.ReleaseArgs(
        chart="tetragon",
       
        repository_opts=k8s.helm.v3.RepositoryOptsArgs(
            repo="https://helm.cilium.io/"
        ),
        namespace="kube-system",
        
       
        
        values={
            "tetragon": {
                "exportFilename": "tetragon.log",
                "exportDirectory": "/var/log/tetragon/"
            }
        },
    ),
    opts=pulumi.ResourceOptions(
        provider=k8s_provider, 
        depends_on=[cilium_release]
    )
)


#  Automate the 10-Minute Certificate Rotation Patch
patch_spire_ttl = command.local.Command(
    "patch-spire-ttl",
    create="""
        # 1. Extract the raw configuration text using the correct key
        kubectl get configmap spire-server -n cilium-spire --template='{{index .data "server.conf"}}' > current.conf
        
        # 2. Idempotency check: strictly check if EXACTLY 10m is already set
        if grep -q 'default_x509_svid_ttl = "10m"' current.conf; then 
            echo "TTL already correctly patched. Skipping."
            exit 0
        fi
        
        # 3. Smart Injection: Insert the 10m rule and strip out any old/duplicate TTL lines
        awk '/server \\{/ {print; print "    default_x509_svid_ttl = \\"10m\\""; next} /default_x509_svid_ttl/ {next} 1' current.conf > patched.conf
        
        # 4. Push the patched file back into the cluster
        kubectl create configmap spire-server -n cilium-spire --from-file=server.conf=patched.conf -o yaml --dry-run=client | kubectl apply -f -
        
        # 5. Nuke the SPIRE server pod so it reloads
        kubectl delete pod -n cilium-spire spire-server-0
    """,
    opts=pulumi.ResourceOptions(depends_on=[cilium_release])
)



# Export deployment metrics to your terminal output

pulumi.export("deployed_cluster_name", CLUSTER_NAME)
pulumi.export("cilium_status", cilium_release.status.name)
pulumi.export("tetragon_status", tetragon_release.status.name)
pulumi.export("raw_kubeconfig", kubeconfig.stdout)
pulumi.export("images_loaded_status", load_auranet_images.id)
# Export the status of the patch script
pulumi.export("spire_ttl_patched", patch_spire_ttl.id)