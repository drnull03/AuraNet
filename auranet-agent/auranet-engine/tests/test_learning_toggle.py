import pytest
import asyncio
import threading
import torch
import torch.nn as nn
import numpy as np
import sys
import os
from unittest.mock import patch, PropertyMock, AsyncMock, MagicMock

# Ensure pytest can find your src modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from inference_worker import run_inference_pipeline
import config

pytestmark = pytest.mark.asyncio

class DummyAutoencoder(nn.Module):
    """A dummy model that perfectly reconstructs input, guaranteeing an MSE of 0.0 (Benign)."""
    def __init__(self):
        super(DummyAutoencoder, self).__init__()
        
    def forward(self, x):
        return x 

@pytest.fixture
def mock_dependencies():
    """Mocks the NATS client and Stream Processor to prevent infinite loops and network calls."""
    with patch('inference_worker.NATS') as mock_nats, \
         patch('inference_worker.HubbleStreamProcessor') as mock_processor:
        
        # 1. Setup the NATS mock to successfully connect asynchronously
        mock_nats_instance = MagicMock()
        mock_nats_instance.connect = AsyncMock()
        mock_nats_instance.publish = AsyncMock()
        mock_nats.return_value = mock_nats_instance
        
        # 2. Setup the Processor to yield exactly 3 benign packets, then stop
        # This prevents the async loop from running forever in the test
        mock_processor_instance = MagicMock()
        mock_event = {"flow": {"source": {"labels": ["k8s:app=test-app"]}}}
        mock_feature_array = np.zeros(13, dtype=np.float32)
        
        mock_processor_instance.stream_traffic.return_value = [
            (mock_event, mock_feature_array),
            (mock_event, mock_feature_array),
            (mock_event, mock_feature_array)
        ]
        mock_processor.return_value = mock_processor_instance
        
        yield

@patch('config.DynamicConfig.LEARNING_ENGINE', new_callable=PropertyMock)
async def test_inference_respects_learning_disabled(mock_learning_engine, mock_dependencies):
    """Proves that when LEARNING_ENGINE is False, Worker A drops benign packets instead of saving them."""
    
    # Disable the learning engine
    mock_learning_engine.return_value = False
    
    model = DummyAutoencoder()
    benign_buffer = []
    buffer_lock = threading.Lock()
    
    # Run the worker (it will process the 3 mocked packets and exit)
    await run_inference_pipeline(model, benign_buffer, buffer_lock)
    
    # ASSERTION: The buffer MUST remain empty to prevent memory leaks
    assert len(benign_buffer) == 0, "Memory Leak! Worker A saved packets while learning was disabled."

@patch('config.DynamicConfig.LEARNING_ENGINE', new_callable=PropertyMock)
async def test_inference_respects_learning_enabled(mock_learning_engine, mock_dependencies):
    """Proves that when LEARNING_ENGINE is True, Worker A correctly buffers benign packets for Worker B."""
    
    # Enable the learning engine
    mock_learning_engine.return_value = True
    
    model = DummyAutoencoder()
    benign_buffer = []
    buffer_lock = threading.Lock()
    
    # Run the worker (it will process the 3 mocked packets and exit)
    await run_inference_pipeline(model, benign_buffer, buffer_lock)
    
    # ASSERTION: The buffer MUST contain exactly 3 packets
    assert len(benign_buffer) == 3, "Data Loss! Worker A failed to save packets for training."