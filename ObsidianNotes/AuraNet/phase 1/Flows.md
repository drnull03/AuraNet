

This is a detailed walkthrough of the **AuraNet** architecture in a Banking environment.

### The Setup

- **Nodes:** 3 Branches (Tokyo, London, New York).
    
- **The Guard:** eBPF (lives in the kernel).
    
- **The Brain:** Local AI (on-site) + Global AI (Federated Aggregator).
    
- **The ID:** Zero Trust (SPIFFE/SPIRE).
    

---

### Flow 1: The "Known Evil" (Instant eBPF Drop)

Scenario: A hacker sends a "Ping of Death" or a packet designed to crash a database port that should be closed.

1. **Packet Arrival:** A malicious packet hits the Tokyo branch network card.
    
2. **Kernel Hook (eBPF):** Before the packet even reaches the Operating System's main memory, an eBPF program (XDP) intercepts it.
    
3. **Hard-Rule Match:** eBPF checks its "Blacklist." It sees the packet is trying to access Port 22 (SSH) from an external IP—a violation of a hard security policy.
    
4. **The Drop:** eBPF drops the packet **instantly** in the kernel.
    
5. **Result:** The CPU doesn't waste cycles, the application never "sees" the attack, and no AI was needed because it was an obvious violation.
    

---

### Flow 2: The "Sneaky Thief" (AI + Zero Trust + Healing)

Scenario: An "insider threat." A bank teller's computer in Tokyo starts downloading 10,000 small customer files at 3:00 AM. This looks like a normal user doing normal things, just "too much" of it.

1. **Observation:** eBPF monitors the system calls (sys_read). It doesn't block them because the teller is allowed to read files.
    
2. **Telemetry to Local AI:** eBPF sends the metadata (User ID, File Count, Time) to the **Local AI Agent**.
    
3. **AI Suspicion:** The Local AI compares this to the branch's history. “Usually, this teller reads 10 files a day. Today they are reading 10,000.” The AI marks this as **Suspicious (90% Anomaly)**.
    
4. **Zero Trust Re-Verification:** The system triggers a "Trust Check." It asks the Zero Trust Controller: "Does this Teller ID have a high-security clearance for bulk exports?"
    
5. **Access Denied:** The Zero Trust Controller responds: "No. Identity verified, but permission for this volume is NOT granted."
    
6. **Isolation (The Bodyguard):** The system tells eBPF: "Quarantine PID 405 (the teller's app)." eBPF immediately blocks all network outgoing traffic for that specific process only.
    
7. **Self-Healing (The Doctor):** The Kubernetes Orchestrator sees the "Hacked" process is isolated. It **kills** the container and **restarts** a fresh one with a "Restricted" profile (e.g., can only read 1 file per minute) while alerting Security.
    

---

### Flow 3: The Global AI Loop (Federated Learning)

How the London branch stays safe because Tokyo got attacked.

1. **Local Learning:** After the Tokyo attack, the Tokyo Local AI updates its internal math: "Small file reads + High Frequency + Off-hours = Data Exfiltration."
    
2. **Weight Update:** Tokyo sends **only the mathematical changes (weights)**—not the customer names or logs—to the Global Aggregator.
    
3. **Aggregation:** The Global Aggregator combines Tokyo’s new knowledge with data from NYC and London.
    
4. **Global Update:** A new "Global Security Model" is pushed out to all branches.
    
5. **Proactive Protection:** The **London branch** now has the "vaccine." If a teller in London tries the same thing 5 minutes later, the London Local AI catches it **instantly** because it "remembers" what happened in Tokyo.
    

---

### Flow 4: The "Happy Path" (Normal Flow)

Scenario: A customer logs into the mobile app to check their balance.

1. **Request:** Packet arrives at the London Branch API.
    
2. **eBPF Check:** eBPF sees the packet. It's on Port 443 (Allowed). It passes it to the app.
    
3. **Zero Trust Check:** The app presents a SPIFFE ID (a digital certificate). The system verifies: "Yes, this is the official Mobile-API talking to the Balance-Service."
    
4. **AI Inference:** Local AI looks at the behavior. “One login, one database read, one logout. This is 100% normal.”
    
5. **Completion:** The user gets their balance. No friction, no blocks.
    

---

### Other Use Cases & Flows

#### Use Case A: The "Ransomware" Block (File System Focus)






# More detailed flow 


Thoughts

Expand to view model thoughts

chevron_right

6.1s

This is the complete lifecycle of a request within the **AuraNet** system.

---

### Part 1: The Detailed Flow (Step-by-Step)

Imagine a **Service A** in the London Branch trying to send data to **Service B**.

#### 1. The Entry (eBPF Hard-Check)

- **Action:** Service A sends a network packet.
    
- **The Guard (eBPF):** Before the packet leaves the network card, an eBPF program hooks into the XDP or TC layer.
    
- **Logic:** It checks a pre-loaded "Deny List." If the destination IP is a known malicious command-and-center, it drops the packet in **nanoseconds**. No AI is involved yet.
    

#### 2. The ID Check (Zero Trust Verification)

- **Action:** eBPF extracts the **SPIFFE ID** (cryptographic identity) from the packet.
    
- **The Guard (ZT):** It checks the **Zero Trust Policy**: "Is Service A authorized to talk to Service B?"
    
- **Logic:** If the policy says "No," the connection is killed. If "Yes," the packet proceeds.
    

#### 3. The Observation (Async Telemetry)

- **Action:** As the data flows, eBPF captures **Metadata** (packet frequency, byte size, system calls like sys_write).
    
- **The Pipeline:** It sends this metadata via a **Ring Buffer** (shared memory) to the **Local AI Agent** running on that specific server.
    
- **Performance:** The packet continues to its destination; it does **not** wait for the AI.
    

#### 4. The Local Inference (The "Brain" Thinks)

- **Action:** The Local AI (the Neural Network we coded earlier) processes the metadata.
    
- **Logic:** It asks: "Service A is authorized, but it is sending 50GB of data. Usually, it only sends 10MB. Is this a data leak?"
    
- **Result:** It calculates an **Anomaly Score (0.0 to 1.0)**.
    

#### 5. The Enforcement & Healing (The System Acts)

- **Action:** If the Anomaly Score is high (e.g., 0.95), the Local AI sends a command to the **Local Controller**.
    
- **Enforcement:** The Controller updates the eBPF Map: BLOCK Service A. eBPF instantly cuts all existing and future connections for Service A.
    
- **Healing:** The Controller pings **Kubernetes**: "Service A is compromised. Delete the Pod and restart it from the 'Golden Image' (the original clean code)."
    

#### 6. The Knowledge Share (Federated Learning)

- **Action:** At the end of the hour, the Local AI prepares its "Learning Summary" (the math weights) to send to the Global Server.
    

---

### Part 2: Frequency & Training Strategy

You asked: How frequent is the data sent? How many times per day? How is the choice made?

In Federated Learning, we don't send data for every packet. We send it in **Rounds**.

#### 1. How Frequent? (The Timing)

There are two ways to decide when to sync the Local AI with the Global AI:

- **Scheduled Sync (The Heartbeat):**
    
    - **Frequency:** Typically every **30 minutes to 1 hour**.
        
    - **Why:** This ensures the "Global Brain" is always fresh without clogging the network with constant math updates.
        
- **Event-Driven Sync (The "Panic" Button):**
    
    - **Frequency:** Immediate/Instant.