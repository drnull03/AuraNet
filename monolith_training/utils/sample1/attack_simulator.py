import subprocess
import time
import random

def get_pod_name(app_label, namespace="default"):
    cmd = f"kubectl get pods -n {namespace} -l app={app_label} -o jsonpath='{{.items[0].metadata.name}}'"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip()

def run_curl(source_pod, target_svc, port, path, method="GET", timeout=1):
    # Added double-quotes around URL to prevent Bash injection errors
    cmd = f"kubectl exec -n default {source_pod} -- curl -s -o /dev/null -w '%{{http_code}}' -X {method} --max-time {timeout} \"http://{target_svc}:{port}{path}\""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(f"[{source_pod}] -> {method} http://{target_svc}:{port}{path} (HTTP {result.stdout})")

def generate_test_traffic():
    print("🐝 Initializing AuraNet SOC Test Simulator (MIXED TRAFFIC)...")
    
    retail_pod = get_pod_name("retail-dashboard")
    invest_pod = get_pod_name("investment-dashboard")
    
    if not retail_pod or not invest_pod:
        print("❌ Error: Could not find pods.")
        return

    print("\n--- PHASE 0: SPIRE mTLS Tunnel Warm-up ---")
    run_curl(retail_pod, "customer-api", 8000, "/health", timeout=5)
    time.sleep(1) 

    print("\n--- PHASE 1: Benign Baseline ---")
    for _ in range(10):
        customer_id = random.randint(1, 25)
        run_curl(retail_pod, "customer-api", 8000, f"/customers/{customer_id}")
        time.sleep(0.2)

    print("\n--- PHASE 2: Boundary Drops ---")
    for _ in range(5):
        customer_id = random.randint(1, 25)
        run_curl(invest_pod, "customer-api", 8000, f"/customers/{customer_id}")
        time.sleep(0.2)

    print("\n--- PHASE 3: INSIDER THREATS & L7 ATTACKS ---")
    l7_attacks = [
        {"path": "/customers/1", "method": "POST"},
        {"path": "/customers/1", "method": "DELETE"},
        {"path": "/customers/admin_dump", "method": "GET"},
        {"path": "/customers/1'%20OR%201=1", "method": "GET"},
    ]
    
    for _ in range(10):
        attack = random.choice(l7_attacks)
        run_curl(retail_pod, "customer-api", 8000, attack["path"], attack["method"])
        time.sleep(0.5)

    print("\n✅ Test traffic generation complete! Extract to hubble_test_data.json")

if __name__ == "__main__":
    generate_test_traffic()