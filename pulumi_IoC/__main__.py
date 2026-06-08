import pulumi
import pulumi_command as command

CLUSTER_NAME = "my-cluster"
CONFIG_PATH = "./cluster/3Nodes.yaml"

print(f"🧹 Pulumi is verifying or preparing the infrastructure state...")

# Define the Kind Cluster resource
# Pulumi tracking ensures that if this resource is removed from the code, 
# or if you run 'pulumi destroy', the delete command executes automatically.
kind_cluster = command.local.Command(
    "kind-cluster",
    create=f"kind create cluster --name {CLUSTER_NAME} --config {CONFIG_PATH}",
    delete=f"kind delete cluster --name {CLUSTER_NAME}",
    opts=pulumi.ResourceOptions(retain_on_delete=False)
)

# Export the cluster name to the terminal output upon completion
pulumi.export("deployed_cluster_name", CLUSTER_NAME)