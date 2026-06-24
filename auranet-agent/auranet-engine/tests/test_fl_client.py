import pytest
import torch
import torch.nn as nn
import numpy as np
import threading
import sys
import os

# Ensure pytest can find your src modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from fl_client import AuraNetFlowerClient

# 1. Create a tiny, ultra-fast dummy model just for testing the hot-swap mechanics
class DummyModel(nn.Module):
    def __init__(self):
        super(DummyModel, self).__init__()
        self.fc = nn.Linear(10, 2)

def test_round_1_poison_pill_protection():
    """
    Proves that on Round 1, the client accepts the warm monolith weights 
    but bounces them straight back to protect the server from random local weights.
    """
    model = DummyModel()
    model_lock = threading.Lock()
    global_state = {"is_initialized": False} # Simulating a fresh boot

    client = AuraNetFlowerClient(model, model_lock, global_state)

    # Mock the server sending down an array of ones (The Warm Monolith)
    incoming_weights = [np.ones((2, 10), dtype=np.float32), np.ones((2,), dtype=np.float32)]

    # Trigger the federated round
    returned_weights, _, _ = client.fit(incoming_weights, {})

    # ASSERTION 1: The state should now be locked so this never happens again
    assert global_state["is_initialized"] is True
    
    # ASSERTION 2: The client MUST have returned the exact weights it just received
    assert np.array_equal(returned_weights[0], incoming_weights[0]), "Failed! Client leaked random weights on Round 1."

def test_standard_round_hot_swap():
    """
    Proves that on Round 2+, the client correctly extracts local insights FIRST, 
    then overwrites the local model, and updates the shared memory for FedProx.
    """
    model = DummyModel()
    model_lock = threading.Lock()
    global_state = {"is_initialized": True} # Simulating Round 2+

    client = AuraNetFlowerClient(model, model_lock, global_state)
    
    # Capture the original local weights (simulating what Worker B just trained)
    original_local_weights = client.get_parameters({})

    # Mock the server sending down an array of zeros (The New Global Brain)
    incoming_weights = [np.zeros((2, 10), dtype=np.float32), np.zeros((2,), dtype=np.float32)]

    # Trigger the federated round
    returned_weights, _, _ = client.fit(incoming_weights, {})

    # ASSERTION 1: The weights sent to the server MUST match the original local weights
    assert np.array_equal(returned_weights[0], original_local_weights[0]), "Failed! Client sent the wrong weights to the server."
    
    # ASSERTION 2: The PyTorch model's physical memory must now hold the new server weights
    current_model_weights = client.get_parameters({})
    assert np.array_equal(current_model_weights[0], incoming_weights[0]), "Failed! Hot-swap did not overwrite the local model."
    
    # ASSERTION 3: The deep copy for Worker B's FedProx proximal penalty must exist
    assert global_state.get("master_weights") is not None, "Failed! FedProx master weights were not saved to shared memory."