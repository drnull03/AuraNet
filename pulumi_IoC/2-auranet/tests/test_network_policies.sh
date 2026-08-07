#!/bin/bash

# Define ANSI color codes for terminal output
GREEN='\033[0;32m'
RED='\033[0;31m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${CYAN}[INFO] Starting Zero Trust Network Policy Validation${NC}"
echo -e "${CYAN}[INFO] Provisioning temporary target pod in 'auranet-namespace'...${NC}"

# Spin up a temporary NGINX pod to act as a ping target for the app_network_policy tests
kubectl run test-target --image=nginx:alpine -n auranet-namespace --labels="access-nats=true" >/dev/null 2>&1

# Wait for the pod to boot and grab its internal IP
kubectl wait --for=condition=ready pod/test-target -n auranet-namespace --timeout=30s >/dev/null 2>&1
TARGET_IP=$(kubectl get pod test-target -n auranet-namespace -o jsonpath='{.status.podIP}')
NATS_SVC="auranet-nats-broker.auranet-messaging.svc.cluster.local"

# TEST SUITE 1: app_network_policy (App Namespace Isolation)
echo -e "\n${YELLOW}--- Testing app_network_policy (App Isolation) ---${NC}"

# TEST 1A: Attempt connection from 'default' to 'auranet-namespace' (Should Block)
echo -e "Testing connection from [default] -> [auranet-namespace]..."
if kubectl run test-client-1 --rm -i --image=alpine -n default --restart=Never --command -- nc -w 2 -z $TARGET_IP 80 >/dev/null 2>&1; then
    echo -e "${RED}[FAIL] Traffic was allowed! The default namespace breached the isolation policy.${NC}"
else
    echo -e "${GREEN}[PASS] Traffic was successfully dropped by default deny.${NC}"
fi

# TEST 1B: Attempt connection within 'auranet-namespace' (Should Allow)
echo -e "Testing connection from [auranet-namespace] -> [auranet-namespace]..."
if kubectl run test-client-2 --rm -i --image=alpine -n auranet-namespace --restart=Never --command -- nc -w 2 -z $TARGET_IP 80 >/dev/null 2>&1; then
    echo -e "${GREEN}[PASS] Traffic successfully allowed inside the isolated namespace.${NC}"
else
    echo -e "${RED}[FAIL] Traffic was blocked! Internal pod-to-pod routing is broken.${NC}"
fi

# TEST SUITE 2: nats_network_policy (NATS Broker Isolation)
echo -e "\n${YELLOW}--- Testing nats_network_policy (NATS Isolation) ---${NC}"

# TEST 2A: Attempt connection from 'default' to NATS (Should Block)
echo -e "Testing connection from [default] -> [NATS Broker]..."
if kubectl run test-client-3 --rm -i --image=alpine -n default --restart=Never --command -- nc -w 2 -z $NATS_SVC 4222 >/dev/null 2>&1; then
    echo -e "${RED}[FAIL] Traffic to NATS was allowed from the default namespace!${NC}"
else
    echo -e "${GREEN}[PASS] Unauthorized traffic to NATS successfully dropped.${NC}"
fi

# TEST 2B: Attempt connection from 'auranet-namespace' to NATS (Should Allow)
echo -e "Testing connection from [auranet-namespace] -> [NATS Broker]..."
if kubectl run test-client-4 --rm -i --image=alpine -n auranet-namespace --labels="access-nats=true" --restart=Never --command -- nc -w 2 -z $NATS_SVC 4222 >/dev/null 2>&1; then
    echo -e "${GREEN}[PASS] Authorized traffic from the app namespace to NATS allowed.${NC}"
else
    echo -e "${RED}[FAIL] Authorized traffic to NATS was blocked!${NC}"
fi

# CLEANUP
echo -e "\n${CYAN}[INFO] Tests complete. Cleaning up temporary resources...${NC}"
kubectl delete pod test-target -n auranet-namespace >/dev/null 2>&1
echo -e "${CYAN}[INFO] Cleanup finished.${NC}"
