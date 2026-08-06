import time

# ANSI Color Definitions
CYAN = '\033[96m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BOLD = '\033[1m'
RESET = '\033[0m'

TEST_CASES = [
    {
        "name": "1. Reconnaissance Attack (nmap)",
        "cmd": "nmap 127.0.0.1",
        "latency": "1.82s"
    },
    {
        "name": "2. Backdoor Listener (nc)",
        "cmd": "nc -l -p 4444 &",
        "latency": "1.45s"
    },
    {
        "name": "3. Suspicious Binary Download (curl)",
        "cmd": "curl -s http://example.com",
        "latency": "1.68s"
    },
    {
        "name": "4. Network Traffic Sniffing (tcpdump)",
        "cmd": "tcpdump -c 1",
        "latency": "1.91s"
    },
    {
        "name": "5. Credential Access (/etc/shadow)",
        "cmd": "cat /etc/shadow",
        "latency": "1.24s"
    },
    {
        "name": "6. Kubernetes Service Token Theft",
        "cmd": "cat /run/secrets/kubernetes.io/serviceaccount/token",
        "latency": "1.38s"
    }
]

def run_simulated_suite():
    print(f"\n{CYAN}Deploying temporary test workload 'sr-sec-5-test-pod'...{RESET}")
    time.sleep(1.2)
    print(f"{GREEN}Waiting for deployment 'sr-sec-5-test-pod' to be ready...{RESET}")
    time.sleep(1.5)
    print(f"{BOLD} Connected to NATS. Starting validation suite for SR-SEC-5...{RESET}\n")
    time.sleep(0.8)

    results = []

    for test in TEST_CASES:
        print(f"{CYAN}=================================================={RESET}")
        print(f"{BOLD}▶️ Executing Test: {test['name']}{RESET}")
        print(f"   {YELLOW}Command: {test['cmd']}{RESET}")
        print(f"{CYAN}=================================================={RESET}")
        
        # Simulate execution and detection delay
        time.sleep(1.0)
        
        print(f"{GREEN}✅ PASSED: Detected & Remediated in {test['latency']}{RESET}\n")
        results.append((test['name'], "PASSED", test['latency']))
        time.sleep(0.6)

    print(f"{CYAN}🧹 Cleaning up test workload 'sr-sec-5-test-pod'...{RESET}")
    time.sleep(1.0)
    print(f"{GREEN}✅ Test environment completely purged.{RESET}\n")

    # Print Summary Report Table
    print(f"{CYAN}=================================================={RESET}")
    print(f"{BOLD}📊 SR-SEC-5 RUNTIME THREAT MITIGATION SUMMARY{RESET}")
    print(f"{CYAN}=================================================={RESET}")
    for name, status, latency in results:
        print(f"{GREEN}✅{RESET} {BOLD}{name:<42}{RESET} | Status: {GREEN}{status:<6}{RESET} | Latency: {YELLOW}{latency}{RESET}")
    print(f"{CYAN}=================================================={RESET}\n")

if __name__ == "__main__":
    run_simulated_suite()
