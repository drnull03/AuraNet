

Here is the step-by-step breakdown of how that knowledge moves from the Global Brain back to the Local Nodes.

---

### 1. The Federated Learning Cycle (The "Round")

Federated Learning happens in **Rounds**. A single round looks like this:

1. **Selection:** The Global Server pings all active nodes (Tokyo, London, NYC).
    
2. **Broadcast:** The Global Server sends the **current "Master Model"** to everyone.
    
3. **Local Training:** Each node "refines" that model using its own local, private data.
    
4. **Reporting:** Each node sends its **changes (Gradients/Weights)** back up.
    
5. **Aggregation:** The Global Server merges them into a new Master Model.
    
6. **Update:** The new Master Model is sent back down.