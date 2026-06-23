import subprocess
import time
import random

def get_pod_name(app_label, namespace="default"):
    cmd = f"kubectl get pods -n {namespace} -l app={app_label} -o jsonpath='{{.items[0].metadata.name}}'"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip()

def run_request(source_pod, target_svc, port, path, timeout=2):
    # Using wget -qO- since we confirmed it works reliably in your alpine-based containers
    cmd = f"kubectl exec -n default {source_pod} -- wget -qO- -T {timeout} \"http://{target_svc}:{port}{path}\""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    # Simple status check based on return code
    status = "OK" if result.returncode == 0 else "FAIL"
    print(f"[{source_pod}] -> GET http://{target_svc}:{port}{path} ({status})")

def generate_baseline_traffic():
    print("🏦 Initializing OmniFinance Baseline Simulator (NORMAL TRAFFIC ONLY)...")
    
    frontend_pod = get_pod_name("frontend-ui")
    
    if not frontend_pod:
        print("❌ Error: Could not find frontend-ui pod.")
        return

    print("\n PHASE 0: Route Warm-up ")
    # Quick warm-up to establish initial TCP handshakes
    run_request(frontend_pod, "api-gateway", 8080, "/api/accounts?id=1", timeout=5)
    time.sleep(1) 

    print("\nPHASE 1: Generating Benign Telemetry")
    # Generating 200 clean requests to build a solid L4/L7 Autoencoder baseline
    for _ in range(200):
        if random.choice([True, False]):
            # Valid Account Lookups (IDs 1-25)
            acc_id = random.randint(1, 25)
            run_request(frontend_pod, "api-gateway", 8080, f"/api/accounts?id={acc_id}")
        else:
            # Valid Loan Exports (IDs 101-125)
            loan_id = random.randint(101, 125)
            run_request(frontend_pod, "api-gateway", 8080, f"/api/loans/export?id=L-{loan_id}")
        
        # Slight delay to ensure Hubble processes the flows cleanly
        time.sleep(0.1)

    print("\n✅ Baseline traffic generation complete! Extract to data/raw/hubble_training_data.json")

if __name__ == "__main__":
    generate_baseline_traffic()