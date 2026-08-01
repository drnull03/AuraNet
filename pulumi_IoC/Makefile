# Variables
PORT_API = 4245
PORT_UI = 12000

.PHONY: up-base up-apps up-all down-base down-apps down-all connect status clean test up-aura down-aura


# LAYER 1: BASE PLATFORM

up-base:
	@echo " Provisioning Layer 1 (Cluster + eBPF Mesh)..."
	cd 1-base-platform && pulumi up --yes

down-base:
	@echo " Destroying Layer 1 (Cluster + eBPF Mesh)..."
	cd 1-base-platform && pulumi destroy --yes





# LAYER 2: Auranet
up-aura:
	@echo " Provisioning Layer 2 (AuraNet)..."
	cd 2-auranet && pulumi up --yes


down-aura:
	@echo " Destroying Layer 2 (AuraNet)..."
	cd 2-auranet && pulumi destroy --yes

#  LAYER 3: CORE WORKLOADS

up-apps:
	@echo " Provisioning Layer 3 (Workloads & Policies)..."
	cd 3-workloads && pulumi up --yes

down-apps:
	@echo " Destroying Layer 3 (Workloads & Policies)..."
	cd 3-workloads && pulumi destroy --yes


#  ORCHESTRATION (Do everything at once)

up-all: up-base up-aura up-apps
	@echo "✅ Entire AuraNet architecture is live!"

down-all: clean down-apps down-aura down-base
	@echo "✅ Entire AuraNet architecture destroyed cleanly."


#  NETWORKING & TUNNELS
# these are not used anymore
connect: clean
	@echo " Starting Hubble Relay API port-forward (Port $(PORT_API))..."
	@nohup kubectl port-forward -n kube-system svc/hubble-relay $(PORT_API):80 </dev/null >/dev/null 2>&1 &
	@echo "Starting Hubble UI web interface port-forward (Port $(PORT_UI))..."
	@nohup kubectl port-forward -n kube-system svc/hubble-ui $(PORT_UI):80 --address 0.0.0.0 </dev/null >/dev/null 2>&1 &
	@sleep 1
	@echo " Network tunnels established. Access Hubble UI: http://localhost:$(PORT_UI)"

status:
	@echo " Checking background network tunnels..."
	@ss -tulpn | grep -E "$(PORT_API)|$(PORT_UI)" || echo "❌ No active tunnels found."
	@echo "\n Active cluster nodes:"
	@kubectl get nodes || echo "❌ Cluster not reachable."

clean:
	@echo "Stopping all background port-forward tunnels..."
	@pkill -f "[p]ort-forward" || true


#  TESTING SUITE
# u can add here other testing suite
# but doing them manual in each dir is easier and better and more granular and i would like it to keep it this way
test:
	@echo " Running Pytest Network Validation Suite..."
	@pytest tests/ -v --disable-warnings
	@pytest ../auranet-agent/auranet-engine/tests -v --disable-warnings
	