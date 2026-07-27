
Step 1: Build the Docker Image


Bash
# Run this from the root of your project 
docker build -t auranet-loader:latest .
Step 2: Make the Image Available to the Cluster


Bash
# Replace 'kind' with your actual cluster name if it differs
kind load docker-image auranet-loader:latest --name kind
Step 3: Install or Upgrade the Helm Chart

If you loaded the image locally into a tool like KinD, it is crucial to set imagePullPolicy=Never or IfNotPresent so Kubernetes doesn't try to pull it from the internet and fail.

Bash
helm upgrade --install auranet-loader ./chart \
  --namespace auranet-namespace \
  --create-namespace \
  --set loader.image.repository=auranet-loader \
  --set loader.image.tag=latest \
  --set loader.image.pullPolicy=Never


Step 4: Verify the Deployment
Once the Helm chart is deployed, you can verify that the DaemonSet is running and successfully pinned the eBPF maps to the host node.

1. Check the Pod Status:

Bash
kubectl get pods -n auranet-namespace -l app.kubernetes.io/name=auranet-loader -o wide
You should see the pod(s) in a Running state.

2. Check the Logs:
Because we added that echo and sleep infinity in the Dockerfile entrypoint, you can verify it succeeded by checking the pod logs:

Bash
kubectl logs -n auranet-namespace daemonset/auranet-loader
Expected Output:

Plaintext
AuraNet eBPF successfully pinned to /sys/fs/bpf/auranet
Monitoring active...
3. Verify the Pinned Files on the Node:
You can exec into the node (or one of the pods) to verify the virtual filesystem actually contains your pinned eBPF objects:

Bash
# Exec into the running pod
kubectl exec -it ds/auranet-loader -n auranet-namespace -- sh

# List the pinned BPF objects
ls -la /sys/fs/bpf/
You should see auranet_events (your RingBuffer map) and the tracepoint links present in that directory. Your eBPF program is now autonomously running in the kernel!