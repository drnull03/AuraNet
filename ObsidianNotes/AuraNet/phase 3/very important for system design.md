


In a high-end system like **AuraNet**, the learning is **continuous**. It does not stop once the system goes live.

To understand how this works without slowing down your bank's performance, you have to think of the system as having two separate "loops" running at the same time.

### 1. The Real-Time Detection Loop (Inference)

- **Status:** Always running.
    
- **Action:** Every time a packet moves through the cluster, Cilium (via eBPF) sends a log of that event to the **Inference Engine**.
    
- **The Model:** This engine uses the **latest available** version of the Global Model.
    
- **Decision:** It calculates the "Reconstruction Error" instantly. If the error is high, it triggers the self-healing.
    
- **Performance:** This is extremely fast because it’s just one mathematical pass through the neural network.
    

### 2. The Background Adaptation Loop (Learning)

- **Status:** Running in the background (asynchronous).
    
- **Action:** While the Inference Engine is busy protecting the pods, a **Local Data Buffer** is collecting those same logs.
    
- **The Process:**
    
    1. **Buffering:** Every 5 or 10 minutes, the pod gathers all the "Normal" traffic it has seen.
        
    2. **Training:** The **Local Learner** takes that buffer and "fine-tunes" the model. It says, "Okay, I've seen 10,000 more examples of normal traffic; let me adjust my weights to be even more accurate."
        
    3. **Aggregation:** This is the FL part. Every hour (or whatever interval you set), the worker sends these tiny weight adjustments to the Aggregator.
        
    4. **The Swap:** The Aggregator sends back a "Refined Global Model." The pod then **hot-swaps** the model used in the Detection Loop.
        

---

### Why "Static" Models fail in Zero Trust

If you made the model static (trained once and then finished), your "AuraNet" would break within a week.

**Scenario:** The Bank's developers update the "Trading App" to use a new API endpoint.

- **A Static Model** will see this new API traffic, realize it doesn't match the training from last month, and **kill the app** (False Positive).
    
- **A Continuous Model** will initially see a slight rise in error, but as the Federated rounds continue, it "learns" that this new API traffic is the new normal. The error rate will drop back down, and the system stays "Healed."
    

---

### How to implement this "Dual" approach for your project:

In your Python code for the Departmental Worker, you will use **Multi-threading** or **Asynchronous Tasks**:

1. **Thread A (Detection):**
    
    codePython
    
    ```
    while True:
        traffic_log = get_hubble_stream()
        error = model.check_anomaly(traffic_log) # Using CURRENT weights
        if error > threshold:
            trigger_self_healing()
    ```
    
2. **Thread B (Learning - The Flower Client):**
    
    codePython
    
    ```
    # This runs in the background
    def on_federated_round():
        new_data = get_buffer_since_last_round()
        model.train(new_data) # Updating the weights
        send_weights_to_aggregator()
        # Once global weights come back, Thread A starts using them
    ```
    

### Summary for your Thesis

You should call this **"Online Federated Learning for Dynamic Zero Trust."**

- **Continuous Learning:** Ensures the system adapts to new software deployments and changing network patterns without manual policy updates.
    
- **Real-time Inference:** Ensures that even while the system is "learning," it is still "policing" every single connection.
    

**This is what makes "AuraNet" truly "Autonomous." It doesn't just heal from attacks; it evolves to understand the environment it is protecting.**

15.7s

Model 1:23 PM