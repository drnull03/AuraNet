

I didn't forget the **Zero Trust**—I was treating it as the "Goal," but you are right to call it out. In a thesis, you need to explicitly define how your architecture satisfies the **NIST Zero Trust 7 Tenets.**

Here is how you weave Zero Trust into the project and how you can add a "manual" eBPF component to prove your coding skills.

---

### Part 1: How "AuraNet" is a Zero Trust Architecture (ZTA)

Zero Trust is based on the principle: **"Never Trust, Always Verify."**

1. **Identity-Based Microsegmentation (Verify Explicitly):**
    
    - In your project, you don't use IP addresses. You use Cilium’s **Security Identities**. AuraNet verifies that Pod-A only talks to Pod-B because of their labels (Identity), not their location.
        
2. **Continuous Monitoring (Assume Breach):**
    
    - This is where your **Federated Learning** comes in. Most ZTA systems check a user once at login. Your system **continuously verifies** the behavior of the workload. If the ML model sees a shift in behavior, the "Trust" is revoked.
        
3. **Dynamic Policy Enforcement (Least Privilege):**
    
    - Your "Self-Healing" loop is the definition of **Dynamic Policy**. When the ML model flags a pod, your script instantly narrows the Cilium policy to "Least Privilege" (e.g., blocking all outgoing internet access but keeping internal database access open).
        

---

### Part 2: Proving you worked with eBPF (The "Manual" Task)

Modifying the Cilium source code is a nightmare (it takes 30+ minutes to compile and requires deep knowledge of the Linux networking stack).

**Instead, do this:** Write a **Standalone eBPF Helper** that runs alongside Cilium. This proves you can write, compile, and load eBPF code.

#### The Idea: "The eBPF Process-to-Socket Mapper"

Cilium is great at seeing Network traffic, but sometimes it’s hard to see exactly which **Linux Process (PID)** inside a container started that traffic.

**Your Task:**  
Write a small eBPF program using **BCC (Python/C)** or **Go/Aya (Rust)** that:

1. Hooks into the tcp_connect kernel function.
    
2. Extracts the **Process ID (PID)** and **Command Name** (e.g., curl or python).
    
3. Sends this metadata to your Python FL model.
    

**Why this is perfect for your project:**

- **The "Zero Trust" Angle:** You can argue that a "Trusted" pod is only allowed to send network traffic if it's coming from the java process. If the traffic is coming from a bash process (which your eBPF program detects), it's a "Zero Trust" violation.
    
- **Proof of Skill:** You will have actual C code (program.bpf.c) in your project repository.
    

#### Example code snippet for your eBPF component (C):

codeC

```
#include <uapi/linux/ptrace.h>
#include <net/sock.h>

// This eBPF program runs every time a process tries to connect to the network
int kprobe__tcp_v4_connect(struct pt_regs *ctx, struct sock *sk) {
    u32 pid = bpf_get_current_pid_tgid() >> 32;
    char comm[16];
    bpf_get_current_comm(&comm, sizeof(comm));

    // Print to trace pipe: "PID 1234 (python) is trying to connect!"
    bpf_trace_printk("AuraNet Alert: PID %d (%s) connecting\n", pid, comm);
    return 0;
}
```

---

### Part 3: How to integrate everything (The Final Architecture)

1. **The Foundation (Cilium):** Handles the heavy lifting—routing packets and encrypting traffic.
    
2. **The Custom Spy (Your eBPF Code):** You run your BCC/Python script on the nodes to collect "Process-level" data that Cilium doesn't easily expose.
    
3. **The Brain (Federated Learning):**
    
    - **Input:** Data from Hubble (Network) + Data from Your Custom eBPF tool (Process info).
        
    - **Logic:** Aggregates this data across clusters using Federated Averaging.
        
    - **Decision:** "This Pod is acting like a botnet."
        
4. **The Healer (Python Orchestrator):** Calls the Kubernetes/Cilium API to update the CiliumNetworkPolicy and block the threat.
    

### Why this gets you a high grade:

- **Use of Industry Tools:** Shows you are ready for a real job (Cilium/K8s).