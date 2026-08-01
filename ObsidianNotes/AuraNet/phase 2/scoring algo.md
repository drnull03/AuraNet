

In a Zero Trust Architecture (ZTA), the "Trust Algorithm" is the brain of the operation. It is the process used by the **Policy Decision Point (PDP)** to determine whether to grant access to a resource.

In practical environments, these algorithms aren't just single formulas; they are complex engines that ingest telemetry from various sources. Here are the most common scoring algorithms and models used in industry today:

---

### 1. Weighted Linear Combination (WLC)

This is the most common algorithm used by vendors like **Microsoft (Conditional Access)** and **Okta**.

- **How it works:** Each security signal is assigned a "weight" based on its importance. The algorithm calculates a final score by multiplying the value of each signal by its weight and summing them up.
    
- **The Formula:** 
    
    ```
    TrustScore=(w1×Identity)+(w2×Device)+(w3×Network)+(w4×Context)TrustScore=(w1×Identity)+(w2×Device)+(w3×Network)+(w4×Context)
    ```
    
- **Practical Example:**
    
    - If MFA is satisfied, Identity = 1.
        
    - If the device is managed (MDM), Device = 1.
        
    - If the location is a known high-risk country, Context = -0.5.
        
    - If the total score falls below a threshold (e.g., 0.7), access is denied or a step-up challenge is issued.
        

### 2. Google’s BeyondCorp "Trust Tiering"

Google pioneered ZTA with BeyondCorp. Instead of a single numerical score, they use a **Tiered Classification** model.

- **How it works:** Devices and users are assigned to specific "Trust Tiers" (e.g., Tier 1: Unmanaged, Tier 2: Managed, Tier 3: Managed + Compliant + Secure Hardware).
    
- **Logic:** Access policies are written as "Resource X requires Tier 3."
    
- **Practicality:** This is used in environments with high device diversity. It simplifies management because administrators don't have to tweak decimal points; they just define "tiers" of security posture.
    

### 3. UEBA Anomaly Scoring (Z-Score / Distance-Based)

User and Entity Behavior Analytics (UEBA) is used by tools like **Exabeam, Splunk, or CrowdStrike** to detect "impossible travel" or unusual data access.

- **How it works:** It establishes a "baseline" for a user. It then uses **Standard Deviation (Z-Score)** to see how far the current activity deviates from the norm.
    
- **The Logic:** If a user typically downloads 10MB of data and suddenly downloads 5GB, the "Anomaly Score" spikes.
    
- **Practicality:** If the Anomaly Score exceeds a threshold, the ZTA engine automatically terminates the active session, even if the user initially authenticated correctly.
    

### 4. NIST 800-207 "Trust Algorithm" (Singular vs. Contextual)

NIST defines two primary approaches to scoring in their ZTA standard:

- **Singular (Score-Based):** The PDP evaluates the request against a set of rules and generates a single score.
    
- **Contextual (Criteria-Based):** This is a "Checklist" algorithm. It doesn't care about a weighted score; it requires 100% compliance with specific attributes (e.g., Is the OS patched? AND is the user in the Finance group? AND is the time between 9-5?).
    
- **Practicality:** Used in high-compliance environments (Gov/Defense) where "almost secure" (a score of 0.8) isn't good enough.
    

### 5. Risk-Based Authentication (RBA) / Probability Scoring

Used heavily by **Cloudflare One** and **Zscaler**, this uses machine learning (often Naive Bayes or Logistic Regression) to calculate the probability that a request is malicious.

- **How it works:** The algorithm compares the current request against millions of global data points (e.g., "Is this IP address currently part of a botnet?").
    
- **The Score:** It outputs a "Risk Probability" from 0 to 100.
    
- **Practicality:** It is highly effective at stopping automated attacks and credential stuffing before the user even enters a password.
    

### 6. Continuous Adaptive Risk and Trust Assessment (CARTA)

Proposed by Gartner, this isn't a static formula but a **Time-Based Scoring** algorithm.

- **How it works:** Most algorithms score at the "moment of login." CARTA scores **continuously**.
    
- **The Logic:**









#### algo with federated learning

Your intuition is spot on. For **East-West (E-W) traffic**—which is service-to-service communication within a data center or cloud—a **Contextual (Criteria-Based) Algorithm** is indeed the strongest choice.

However, because you are using **Federated Learning (FL)** for anomaly detection, you shouldn't use a "static" contextual model. Instead, you should use what is known as an **Adaptive Contextual Enforcement** model.

Here is how you should structure the scoring algorithm so that your Federated Learning model effectively influences the Zero Trust PDP (Policy Decision Point) for East-West traffic.

---

### Why Contextual is best for East-West (E-W)

In E-W traffic, you aren't dealing with humans logging in; you are dealing with workloads (microservices, databases, containers).

1. **Strictness:** E-W traffic should be highly predictable. A "Finance Service" should only talk to the "Finance DB." A weighted score of 0.8 is too risky; it’s either allowed or it’s not.
    
2. **Identity-First:** You rely on workload identities (like SPIFFE/ID or mTLS) rather than passwords.
    
3. **Low Latency:** Scoring needs to happen at the sidecar (like Istio/Envoy) or the kernel level (eBPF). Contextual checks are faster than complex math.
    

---

### The Practical Algorithm: "Adaptive Contextual Enforcement"

In this model, the **Federated Learning (FL) output** becomes a dynamic "Attribute" within your Contextual Checklist.

#### 1. How the FL Model influences the Score

In Federated Learning, your local nodes train on traffic patterns (packet size, frequency, entropy) and send updates to a global model. The global model sends back a refined weights-set.

- **The Output:** Your FL model generates a **Local Anomaly Score (LAS)** for every connection attempt or active stream.
    
- **The Integration:** The LAS is treated as a **Boolean Gate** in your contextual policy.
    

#### 2. The Logic Flow (The Algorithm)

The PDP evaluates the request against a "Required Context Set." Access is granted **only if all are TRUE**:

1. **Identity Context:** Is the mTLS certificate valid and signed by the internal CA? (YES/NO)
    
2. **Topology Context:** Is this specific Service A allowed to talk to Service B according to the Service Graph? (YES/NO)
    
3. **Environmental Context:** Is the request coming from an approved Namespace/VPC? (YES/NO)
    
4. **FL Anomaly Context (The "Brain"):** Is the Local_Anomaly_Score < Dynamic_Threshold? (YES/NO)
    

**If ANY of these are NO, the trust score is 0. Access is Denied.**

---

### Why this is better than "Weighted" for Federated Learning

If you used a **Weighted Linear Combination**, a service with a "Very High Anomaly Score" might still get access if its Identity and Location scores were perfect.

- **Example of failure in Weighted:** (Identity 1.0 * 0.5) + (Location 1.0 * 0.3) + (FL Anomaly 0.1 * 0.2) = 0.82.
    
- In a weighted model, a score of **0.82** might pass the threshold, even though the FL model detected a massive SQL injection attempt.
    

In your **Contextual Model**, the FL model acts as a **Circuit Breaker**. Even if the Identity is 100% authenticated, if the FL model detects an anomaly (e.g., lateral movement), the "Anomaly Context" becomes **FALSE**, and the connection is killed immediately.

---

### Implementation in an FL Environment

Since you are using Federated Learning, your scoring algorithm should be implemented in three layers:

#### Layer 1: The Local Inference (The Scorer)

The FL model sits close to the traffic (e.g., as an **Envoy Filter** or an **eBPF probe**). It calculates the anomaly score in real-time. This ensures that the "Contextual" check doesn't have to wait for a cloud round-trip.

#### Layer 2: The Adaptive Threshold (The Logic)

The "Threshold" for what constitutes an anomaly shouldn't be hardcoded.

- **During "Training" mode:** The contextual algorithm might be more lenient (Threshold = 0.9).
    
- **During "High Alert" mode:** If the Global FL model sees an attack in another part of the network, it pushes an update that lowers the local threshold to 0.4.
    

#### Layer 3: The Continuous Evaluation

Unlike North-South traffic (login once), E-W traffic is long-lived. Your contextual algorithm should **re-evaluate** the FL score every 

```
XX
```

 seconds or every 

```
NN
```

 megabytes of data.

- Initial Context: Allowed.
    
- Mid-session Context: FL model detects "Data Exfiltration" pattern 
    
    ```
    →→
    ```
    
     Context becomes "Anomalous"