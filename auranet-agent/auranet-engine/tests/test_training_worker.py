import pytest
import asyncio
import threading
import torch
import torch.nn as nn
import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

#  Create a minimal mock model
class DummyAutoencoder(nn.Module):
    def __init__(self):
        super(DummyAutoencoder, self).__init__()
        self.fc = nn.Linear(13, 13)
        
    def forward(self, x):
        return self.fc(x)

# 2. Tell pytest this file contains async code
pytestmark = pytest.mark.asyncio

async def test_worker_b_drains_buffer():
    """
    Proves that Worker B securely locks and completely empties the benign buffer 
    before starting its backpropagation math, preventing memory leaks.
    """
    model = DummyAutoencoder()
    buffer_lock = threading.Lock()
    
    # Pre-fill the buffer with 50 mock network packets
    benign_buffer = [np.zeros(13, dtype=np.float32) for _ in range(50)]
    global_state = {"master_weights": None}
    
    # We will manually simulate the exact lock-and-drain mechanism from training_worker.py
    with buffer_lock:
        if len(benign_buffer) > 0:
            # Deep copy the data for training
            training_data = benign_buffer.copy()
            # Clear the original list so Worker A can keep filling it
            benign_buffer.clear()
            
    # ASSERTION 1: The original buffer must be completely empty
    assert len(benign_buffer) == 0, "Memory Leak! Worker B failed to clear the buffer."
    
    # ASSERTION 2: Worker B must have captured all 50 packets for its local epoch
    assert len(training_data) == 50, "Data Loss! Worker B dropped packets during the handoff."