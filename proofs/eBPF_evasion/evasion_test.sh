#!/usr/bin/env bash
set -euo pipefail


# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

NAMESPACE="default"
POD="ebpf-security-test"

cleanup() {
    echo -e "\n${YELLOW}[*] Cleaning up test pod...${NC}"
    kubectl delete pod "$POD" -n "$NAMESPACE" --ignore-not-found >/dev/null 2>&1
}

trap cleanup EXIT


echo -e "${BLUE}[*] Creating temporary test pod...${NC}"

kubectl run "$POD" \
    -n "$NAMESPACE" \
    --image=alpine:latest \
    --restart=Never \
    --command -- sleep 600 >/dev/null

echo -e "${BLUE}[*] Waiting for pod to become Ready...${NC}"

kubectl wait \
    --for=condition=Ready \
    pod/"$POD" \
    -n "$NAMESPACE" \
    --timeout=120s >/dev/null

echo -e "${BLUE}[*] Installing required packages (strace, perl)...${NC}"

kubectl exec -n "$NAMESPACE" "$POD" -- \
    sh -c "apk add --no-cache strace perl >/dev/null"

echo -e "${BLUE}[*] Executing BPF syscall test...${NC}"

OUTPUT=$(
kubectl exec -n "$NAMESPACE" "$POD" -- sh -c '
strace -e bpf perl -e "
\$attr = \"\0\" x 128;
syscall(321,11,\$attr,128);
" 2>&1
'
)

echo
echo -e "${CYAN}--------------- strace Output ---------------${NC}"
echo "$OUTPUT"
echo -e "${CYAN}---------------------------------------------${NC}"
echo

if echo "$OUTPUT" | grep -Eq 'EPERM|EACCES|Operation not permitted|Permission denied'; then
    echo -e "${GREEN}${BOLD}"
    echo "========================================================"
    echo "                     TEST PASSED                         "
    echo "--------------------------------------------------------"
    echo "✓ The bpf() syscall is blocked by the workload policy."
    echo "========================================================"
    echo -e "${NC}"
    exit 0
else
    echo -e "${RED}${BOLD}"
    echo "========================================================"
    echo "                     TEST FAILED                         "
    echo "--------------------------------------------------------"
    echo "✗ The bpf() syscall was NOT blocked."
    echo "========================================================"
    echo -e "${NC}"
    exit 1
fi
