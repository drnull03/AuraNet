

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