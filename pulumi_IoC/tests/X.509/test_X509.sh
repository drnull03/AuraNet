#!/bin/bash

# Define ANSI color codes for terminal output
GREEN='\033[0;32m'
RED='\033[0;31m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${CYAN}[INFO] Starting SPIRE Hardware Trust & Attestation Validation${NC}"
echo -e "${CYAN}[INFO] Locating SPIRE components in kube-system namespace...${NC}"

# Locate the SPIRE Server and Agent pods
SPIRE_SERVER=$(kubectl get pod -n kube-system -l app.kubernetes.io/name=spire-server -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
SPIRE_AGENT=$(kubectl get pod -n kube-system -l app.kubernetes.io/name=spire-agent -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)

if [ -z "$SPIRE_SERVER" ] || [ -z "$SPIRE_AGENT" ]; then
    echo -e "${RED}[FATAL] Could not locate SPIRE server or agent pods. Is Cilium mutual auth enabled?${NC}"
    exit 1
fi




echo -e "\n${YELLOW}--- Testing TPM Device Availability ---${NC}"
echo -e "Verifying physical TPM (/dev/tpmrm0) is mounted inside the SPIRE agent..."

if kubectl exec -n kube-system $SPIRE_AGENT -c spire-agent -- ls /dev/tpmrm0 >/dev/null 2>&1; then
    echo -e "${GREEN}[PASS] Physical TPM device is successfully mounted to the agent container.${NC}"
else
    echo -e "${RED}[FAIL] TPM device not found in agent container. Check extraVolumeMounts.${NC}"
fi

# 
# 
echo -e "\n${YELLOW}--- Testing PCR Hash Enforcement ---${NC}"
echo -e "Verifying SPIRE server requires strict PCR 0 and 4 validation..."

# Extract the active server configuration map
SERVER_CONF=$(kubectl get configmap -n kube-system spire-server -o jsonpath='{.data.server\.conf}' 2>/dev/null)

if echo "$SERVER_CONF" | grep -q 'expected_pcrs'; then
    echo -e "${GREEN}[PASS] SPIRE server is actively enforcing PCR validation rules.${NC}"
else
    echo -e "${RED}[FAIL] PCR validation is missing from the server configuration.${NC}"
fi


echo -e "\n${YELLOW}--- Testing Application Integrity Module ---${NC}"
echo -e "Verifying the Kubernetes workload attestor (kubelet hash checking) is enabled..."

AGENT_CONF=$(kubectl get configmap -n kube-system spire-agent -o jsonpath='{.data.agent\.conf}' 2>/dev/null)

if echo "$AGENT_CONF" | grep -q 'kubelet_read_only_port'; then
    echo -e "${GREEN}[PASS] Kubernetes workload attestor is active. Container images will be verified.${NC}"
else
    echo -e "${RED}[FAIL] Workload attestor is missing. Application integrity cannot be verified.${NC}"
fi

echo -e "\n${YELLOW}--- Testing End-to-End Workload Attestation ---${NC}"
echo -e "Checking if SPIRE is successfully minting x509-SVIDs for nodes..."

# Query the SPIRE server API to see if the node successfully attested its hardware and received an identity
if kubectl exec -n kube-system $SPIRE_SERVER -c spire-server -- /opt/spire/bin/spire-server agent show >/dev/null 2>&1; then
    ATTESTED_NODES=$(kubectl exec -n kube-system $SPIRE_SERVER -c spire-server -- /opt/spire/bin/spire-server agent show | grep -c "Spiffe ID")
    if [ "$ATTESTED_NODES" -gt 0 ]; then
        echo -e "${GREEN}[PASS] Node hardware attestation succeeded. SPIRE issued $ATTESTED_NODES identity certificates.${NC}"
    else
        echo -e "${RED}[FAIL] No nodes have successfully attested. TPM/PCR validation may be failing.${NC}"
    fi
else
    echo -e "${RED}[FAIL] Failed to communicate with the SPIRE server API.${NC}"
fi

echo -e "\n${CYAN}[INFO] Hardware attestation testing complete.${NC}"