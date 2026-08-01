



This is the "million-dollar question" in Zero Trust. How do you let an **untrusted** person from the public internet into your **highly trusted** internal network without letting them "infect" it?

The concept you need to master is the **Policy Enforcement Point (PEP)**, specifically implemented as a **Zero Trust Ingress Gateway.**

Here is the 4-step architectural concept to connect "Messy Users" to "Secure AuraNet":

---

### Concept 1: The "Identity Termination" Point

You must never allow a direct network connection (TCP/IP) from a public user to an internal server. Instead, you use a **Gateway** that acts as a "Translator."

- **Public Side:** The user talks to the Gateway using standard HTTPS.
    
- **The Termination:** The Gateway "kills" that connection. It looks at the **JWT (User Identity)**.
    
- **The Internal Side:** If the JWT is valid, the Gateway starts a **brand new connection** inside the AuraNet mesh.
    
- **The Zero Trust Angle:** The internal servers **never** see the user’s IP address. They only see the Gateway’s **Cilium Identity**.
    

### Concept 2: The "Micro-Perimeter" (Namespace Isolation)

To keep it secure, you put your Gateway in its own "Quarantine" zone (a Kubernetes Namespace).

1. **Incoming:** The Gateway is the only workload allowed to have a **Public IP**.
    
2. **Outgoing:** You write a **Cilium Network Policy** that says: "The Gateway is ONLY allowed to talk to the 'Frontend-API' workload. It is BLOCKED from talking to the 'Database' or 'Admin-Panel'."
    
3. **Result:** Even if a hacker takes full control of the Gateway, they are "trapped" in a tiny box. They can’t see the rest of your WAN.
    

### Concept 3: eBPF-Powered Edge Defense

Since you want to use eBPF to prove your skills, you use it to protect this entry point.

- **The Concept:** Use eBPF to filter traffic **before** it even hits the Gateway software.
    
- **Your Project Logic:**
    
    - If a web client sends a "malformed packet" or tries a "DDoS" attack, your **eBPF program** (which lives in the Kernel) drops the packet immediately.
        
    - This saves CPU power and protects the Gateway from crashing.
        

### Concept 4: The "Self-Healing" Feedback Loop

This is where your **Federated Learning (FL)** makes the connection secure.

1. **Monitor:** Your FL model learns the "Normal Behavior" of the Gateway (e.g., "The Gateway usually sends 1KB requests to the Frontend").
    
2. **Detect:** A user exploits a bug in the Gateway and tries to make it download a virus from the internet.
    
3. **Heal:** Your FL model sees this "unusual outbound connection." AuraNet instantly updates the **Cilium Policy** to "Lockdown Mode," cutting the Gateway's access to the internal network until an admin checks it.
    

---

### How to Visualize the Flow (The "AuraNet" Pipeline)

1. **User** → Sends Request + **JWT** → **Public Internet**.
    
2. **AuraNet Gateway (The PEP)**:
    
    - **Kernel Level (eBPF):** Checks for DDoS/Bad packets.
        
    - **App Level (Envoy/Cilium):** Verifies **JWT** signature.
        
    - **Identity:** Gateway presents its **TPM-verified** identity to the internal mesh.
        
3. **Internal WAN (The ZT Zone)**:
    
    - Traffic is encrypted via **WireGuard**.
        
    - **Cilium** ensures the Gateway can only talk to specific internal apps.
        
4. **AuraNet Brain (The ML)**:
    
    - Collects **Hubble** logs from the Gateway.
        
    - Uses **Federated Learning** to ensure the Gateway isn't being "misused" by a client.
        

---

### Key Terminology for your Project:

If you use these terms, your professors will see you understand the industry standards:

- **PEP (Policy Enforcement Point):** The Gateway that sits between the user and the app.
    
- **PDP (Policy Decision Point):** Your **AuraNet Brain** (The ML + Controller) that decides if the traffic should be allowed.