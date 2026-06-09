# Variables
CLUSTER_NAME = my-cluster
PORT_API = 4245
PORT_UI = 12000

.PHONY: up down connect status clean

# 1. Spin up the infrastructure (Cluster + Cilium)
up:
	@echo "🚀 Provisioning infrastructure with Pulumi..."
	pulumi up --yes

# 2. Establish the background port-forward tunnels
connect:
	@echo "🧹 Clearing any stale port-forwards..."
	@pkill -f "[p]ort-forward" || true
	@echo "🔭 Starting Hubble Relay API port-forward (Port $(PORT_API))...."
	@nohup kubectl port-forward -n kube-system svc/hubble-relay $(PORT_API):80 </dev/null >/dev/null 2>&1 &
	@echo "🖥️ Starting Hubble UI web interface port-forward (Port $(PORT_UI))..."
	@nohup kubectl port-forward -n kube-system svc/hubble-ui $(PORT_UI):80 --address 0.0.0.0 </dev/null >/dev/null 2>&1 &
	@sleep 1
	@echo "✅ Network tunnels established in the background."
	@echo "🔗 Access Hubble UI here: http://localhost:$(PORT_UI) (or via VPS public IP)"

# 3. Check the active status of tunnels and cluster
status:
	@echo "📊 Checking background network tunnels..."
	@ss -tulpn | grep -E "$(PORT_API)|$(PORT_UI)" || echo "❌ No active tunnels found on ports $(PORT_API) or $(PORT_UI)."
	@echo "\n🤖 Active cluster nodes:"
	@kubectl get nodes || echo "❌ Cluster not reachable."

# 4. Tear down the network tunnels cleanly
clean:
	@echo "🧹 Stopping all background port-forward tunnels..."
	@pkill -f "[p]ort-forward" || true
	@echo "✅ Tunnels stopped cleanly."

# 5. Destroy everything (Tunnels + Infrastructure)
down: clean
	@echo "💥 Destroying infrastructure via Pulumi..."
	pulumi destroy --yes


# 6. Run the automated Python test suite
test:
	@echo "🧪 Running Pytest Network Validation Suite..."
	@pytest tests/ -v --disable-warnings