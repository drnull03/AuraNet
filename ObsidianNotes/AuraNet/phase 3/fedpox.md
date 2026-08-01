

FedProx (Federated Proximal) is essentially **FedAvg with a leash**.

The main problem it solves is that in real federated learning systems, client datasets are often **non-IID** (different distributions). For example:

- Hospital A mostly has elderly patients.
    
- Hospital B mostly has young patients.
    
- Hospital C mostly has cancer cases.
    

If each client trains locally for several epochs, their models may drift in very different directions. When the server averages them, training becomes unstable or converges slowly. ([Hugging Face](https://huggingface.co/papers/1812.06127?utm_source=chatgpt.com "Paper page - Federated Optimization in Heterogeneous Networks"))

---

## FedAvg refresher

In FedAvg:

1. Server sends global model (w_t).
    
2. Client trains locally on its data.
    
3. Client returns updated model (w_k).
    
4. Server computes weighted average:
    

[  
w_{t+1} = \sum_k \frac{n_k}{n} w_k  
]

Simple and effective, but sensitive to heterogeneous data. ([PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC11024864/?utm_source=chatgpt.com "PGFed: Personalize Each Client’s Global Objective for Federated Learning - PMC"))

---

## What FedProx changes

FedProx modifies the client's local optimization objective.

Instead of minimizing only the local loss:

[  
F_k(w)  
]

the client minimizes:

[  
F_k(w)  
+  
\frac{\mu}{2}  
|w-w_t|^2  
]

where:

- (F_k(w)) = local loss
    
- (w_t) = current global model received from server
    
- (\mu) = proximal coefficient
    
- (|w-w_t|^2) = penalty for moving too far from the global model ([fl-sim.readthedocs.io](https://fl-sim.readthedocs.io/en/latest/algorithms/proximal.html?utm_source=chatgpt.com "Proximal Algorithms in Federated Learning — fl-sim 0.0.1 documentation"))
    

---

## Intuition

Imagine the global model starts at position 0.

### FedAvg

Client A:

```
0 ------------> +10
```

Client B:

```
0 <------------ -12
```

Both clients aggressively optimize for their local datasets.

When averaged:

```
(+10 + -12)/2 = -1
```

Updates fight each other.

---

### FedProx

The proximal term acts like a spring attached to the global model:

```
Global model
      |
      | spring
      V
Client update
```

Now clients are discouraged from drifting too far:

```
0 -----> +4
0 <----- -5
```

The aggregated update is more stable. ([ResearchGate](https://www.researchgate.net/publication/403106105_Genetic_Algorithm-Driven_Hyperparameter_Optimization_for_FedProx_in_Federated_Learning?utm_source=chatgpt.com "(PDF) Genetic Algorithm-Driven Hyperparameter Optimization for FedProx in Federated Learning"))

---

## Training workflow

### Round t

#### Step 1: Server

Current model:

[  
w_t  
]

Broadcast to selected clients.

---

#### Step 2: Client receives model

Client starts with:

[  
w=w_t  
]

---

#### Step 3: Local optimization

Client computes:

[  
L(w)=F_k(w)+\frac{\mu}{2}|w-w_t|^2  
]

Gradient becomes:

[  
\nabla F_k(w)  
+  
\mu(w-w_t)  
]

The second term continuously pulls the model back toward the global model. ([ResearchGate](https://www.researchgate.net/publication/389680078_Federated_Learning_for_Lung_Cancer_Detection_Comparative_Analysis_and_Visual_Interpretability_Federated_Learning_for_Lung_Cancer_Detection_Comparative_Analysis_and_Visual_Interpretability?utm_source=chatgpt.com "(PDF) Federated Learning for Lung Cancer Detection: Comparative Analysis and Visual Interpretability Federated Learning for Lung Cancer Detection: Comparative Analysis and Visual Interpretability"))

---

#### Step 4: Client sends update

After local epochs:

[  
w_k^{t+1}  
]

is sent to server.

---

#### Step 5: Server aggregation

Exactly the same as FedAvg:

# [  
w_{t+1}

\sum_k \frac{n_k}{n} w_k^{t+1}  
]

No special aggregation is required. ([ResearchGate](https://www.researchgate.net/publication/389680078_Federated_Learning_for_Lung_Cancer_Detection_Comparative_Analysis_and_Visual_Interpretability_Federated_Learning_for_Lung_Cancer_Detection_Comparative_Analysis_and_Visual_Interpretability?utm_source=chatgpt.com "(PDF) Federated Learning for Lung Cancer Detection: Comparative Analysis and Visual Interpretability Federated Learning for Lung Cancer Detection: Comparative Analysis and Visual Interpretability"))

---

## Role of μ (mu)

### μ = 0

FedProx becomes:

[  
F_k(w)  
]

which is just FedAvg. ([ResearchGate](https://www.researchgate.net/publication/403557029_The_Importance_of_Key_Parameters_in_Federated_Learning_for_Cross-Device_Scenarios_An_In-depth_Performance_Evaluation?utm_source=chatgpt.com "(PDF) The Importance of Key Parameters in Federated Learning for Cross-Device Scenarios: An In-Depth Performance Evaluation"))

---

### Small μ

Clients have freedom to adapt locally.

Example:

```
μ = 0.001
```

Almost FedAvg.

---

### Large μ

Clients stay close to global model.

Example:

```
μ = 1
```

Very conservative updates.

Too large a value can slow learning because clients cannot learn enough from local data. ([aman.ai](https://aman.ai/primers/ai/federated-learning/?utm_source=chatgpt.com "Aman's AI Journal • Primers • Federated Learning"))

---

## Why it helps with non-IID data

Suppose:

- Client A sees only cats
    
- Client B sees only dogs
    

FedAvg allows each model to overfit toward its own distribution.

FedProx says:

> "You may optimize for your local data, but don't move too far away from the shared global knowledge."

This reduces client drift and typically improves convergence under heterogeneous data distributions. ([Hugging Face](https://huggingface.co/papers/1812.06127?utm_source=chatgpt.com "Paper page - Federated Optimization in Heterogeneous Networks"))

---

## FedAvg vs FedProx

|Feature|FedAvg|FedProx|
|---|---|---|
|Local objective|Local loss only|Local loss + proximal penalty|
|Extra communication|No|No|
|Extra server state|No|No|
|Handles non-IID data|Moderate|Better|
|Handles slow/partial clients|Weak|Better|
|Hyperparameter|None|μ|

([fl-sim.readthedocs.io](https://fl-sim.readthedocs.io/en/latest/algorithms/proximal.html?utm_source=chatgpt.com "Proximal Algorithms in Federated Learning — fl-sim 0.0.1 documentation"))

---

## In your AuraNet-style FL system

If you're doing federated learning across Kubernetes clusters or edge nodes where:

- each cluster observes different traffic patterns,
    
- each site sees different attack types,
    
- datasets are highly non-IID,
    

FedProx is often a good baseline because it's almost as simple as FedAvg but much more stable under heterogeneity.

A typical workflow would be:

1. Global IDS model distributed from aggregator.
    
2. Each cluster trains on its local telemetry.
    
3. Local training uses FedProx objective.
    
4. Models are aggregated.
    
5. New global model is redistributed.
    

This prevents one cluster that sees a unique attack pattern from pulling the global model too far away from the rest of the federation. ([Hugging Face](https://huggingface.co/papers/1812.06127?utm_source=chatgpt.com "Paper page - Federated Optimization in Heterogeneous Networks"))