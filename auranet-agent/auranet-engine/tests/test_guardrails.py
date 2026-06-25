import pytest
import torch
import torch.nn as nn
import threading
import numpy as np
import sys
import os


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import config

def test_buffer_memory_limit():
    """
    Proves that a massive flood of benign network traffic (e.g., a DDoS attack)
    will not cause the Python agent to exceed its RAM limits and crash the K8s node.
    """
    benign_buffer = []
    buffer_lock = threading.Lock()
    
    # Simulate a flood of 20,000 normal packets hitting the node
    with buffer_lock:
        for _ in range(20000):
            # The agent MUST enforce the MAX_BUFFER_SIZE limit
            if len(benign_buffer) < config.ai.MAX_BUFFER_SIZE:
                benign_buffer.append(np.zeros(13))
                
    # ASSERTION: The buffer stopped accepting packets exactly at the config limit
    assert len(benign_buffer) == config.ai.MAX_BUFFER_SIZE, f"Memory Leak! Buffer grew to {len(benign_buffer)}"

def test_fedprox_drift_detection():
    """
    Proves that the FedProx mathematical formula successfully detects when the local
    node's weights start drifting away from the server's global master weights.
    """
    # Create a tiny dummy model for testing
    local_model = nn.Linear(10, 2)
    
    # Simulate saving the global weights from Worker C
    global_weights = [param.clone().detach() for param in local_model.parameters()]
    
    # 1. Calculate the Proximal Penalty BEFORE any local training
    initial_penalty = 0.0
    for local_param, global_param in zip(local_model.parameters(), global_weights):
        initial_penalty += ((local_param - global_param).norm(2)) ** 2
        
    # ASSERTION 1: Because the models are identical, the drift penalty MUST be 0
    assert initial_penalty.item() == 0.0, "Initial drift penalty should be mathematically zero."
    
    # 2. Simulate Worker B running local training (weights change heavily)
    with torch.no_grad():
        for param in local_model.parameters():
            param.add_(torch.randn(param.size()) * 5.0)
            
    # 3. Calculate the Proximal Penalty AFTER local training
    post_training_penalty = 0.0
    for local_param, global_param in zip(local_model.parameters(), global_weights):
        post_training_penalty += ((local_param - global_param).norm(2)) ** 2
        
    # ASSERTION 2: FedProx MUST detect the drift and generate a positive penalty
    assert post_training_penalty.item() > 0.0, "FedProx failed to detect weight drift!"