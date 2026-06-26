import os
import sys
import json
import torch
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

# Ensure the src directory is in the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import config
from model import ZeroTrustAutoencoder
from nlp_model import UrlNlpAutoencoder
from inference_worker import run_inference_pipeline

# Fixtures & Helpers 

@pytest.fixture
def auranet_brains():
    """Initialize the models and buffers before each test."""
    brain_a = ZeroTrustAutoencoder(input_dim=config.ai.INPUT_DIM)
    brain_a.eval()
    
    brain_b = UrlNlpAutoencoder(vocab_size=128, seq_length=150)
    brain_b.eval()
    
    benign_buffer = []
    buffer_lock = MagicMock()
    
    return brain_a, brain_b, benign_buffer, buffer_lock

def generate_mock_event(url, method="GET"):
    """Helper to generate a realistic Hubble raw JSON event."""
    return {
        "flow": {
            "source": {"labels": ["k8s:app=frontend-ui"]},
            "l7": {
                "type": "REQUEST",
                "http": {
                    "url": url,
                    "method": method
                }
            }
        }
    }



@pytest.mark.asyncio
@patch('inference_worker.HubbleStreamProcessor')
@patch('inference_worker.NATS')
async def test_symbolic_null_byte_evasion(mock_nats_class, mock_processor_class, auranet_brains):
    """TEST 1: The symbolic AI should intercept a null byte before the AI even votes."""
    brain_a, brain_b, benign_buffer, buffer_lock = auranet_brains
    
    # Setup NATS Mock
    mock_nc = AsyncMock()
    mock_nats_class.return_value = mock_nc
    
    # Setup Stream Mock (Normal features, but malicious Null Byte URL)
    raw_event = generate_mock_event(url="/api/accounts?id=1%00")
    feature_array = [0.0] * 13 # Perfect normal behavior
    
    mock_processor_instance = mock_processor_class.return_value
    mock_processor_instance.stream_traffic.return_value = [(raw_event, feature_array)]
    
    #Execute
    await run_inference_pipeline(brain_a, brain_b, benign_buffer, buffer_lock)
    
    #Assertions
    mock_nc.publish.assert_called_once()
    published_args = mock_nc.publish.call_args[0]
    payload = json.loads(published_args[1].decode())
    
    assert payload["threat"] == "symbolic_null_byte_evasion"
    assert payload["probability"] == -1


@pytest.mark.asyncio
@patch('inference_worker.HubbleStreamProcessor')
@patch('inference_worker.NATS')
async def test_brain_b_nlp_anomaly(mock_nats_class, mock_processor_class, auranet_brains):
    """TEST 2: Brain B should catch the SQL injection when Brain A is blind to it."""
    brain_a, brain_b, benign_buffer, buffer_lock = auranet_brains
    
    mock_nc = AsyncMock()
    mock_nats_class.return_value = mock_nc
    
    # Provide an anomalous URL payload
    raw_event = generate_mock_event(url="/api/accounts?id=1' OR '1'='1")
    # Provide perfectly normal behavioral features (Brain A will pass this)
    feature_array = [0.0] * 13 
    
    mock_processor_instance = mock_processor_class.return_value
    mock_processor_instance.stream_traffic.return_value = [(raw_event, feature_array)]
    
    # Force Brain B's threshold low to guarantee a tripwire trigger for the test
    config.ai._cache["nlpTripwire"] = -1.0 
    config.ai._cache["tripwireThreshold"] = 100.0 # Force Brain A to ignore
    
    await run_inference_pipeline(brain_a, brain_b, benign_buffer, buffer_lock)
    
    mock_nc.publish.assert_called_once()
    published_args = mock_nc.publish.call_args[0]
    payload = json.loads(published_args[1].decode())
    
    assert payload["threat"] == "payload_anomaly"


@pytest.mark.asyncio
@patch('inference_worker.HubbleStreamProcessor')
@patch('inference_worker.NATS')
async def test_brain_a_behavioral_anomaly(mock_nats_class, mock_processor_class, auranet_brains):
    """TEST 3: Brain A should catch massive volumetric shifts."""
    brain_a, brain_b, benign_buffer, buffer_lock = auranet_brains
    
    mock_nc = AsyncMock()
    mock_nats_class.return_value = mock_nc
    
    # 1. Normal URL (Brain B will pass this)
    raw_event = generate_mock_event(url="/api/accounts?id=5")
    # 2. Highly anomalous feature array (e.g., massive payload sizes)
    feature_array = [1.0] * 13 
    
    mock_processor_instance = mock_processor_class.return_value
    mock_processor_instance.stream_traffic.return_value = [(raw_event, feature_array)]
    
    # 3. Force Brain A's threshold low to guarantee a tripwire trigger
    config.ai._cache["tripwireThreshold"] = -1.0 
    config.ai._cache["nlpTripwire"] = 100.0 # Force Brain B to ignore
    
    await run_inference_pipeline(brain_a, brain_b, benign_buffer, buffer_lock)
    
    mock_nc.publish.assert_called_once()
    published_args = mock_nc.publish.call_args[0]
    payload = json.loads(published_args[1].decode())
    
    assert payload["threat"] == "network_behavior_anomaly"


@pytest.mark.asyncio
@patch('inference_worker.HubbleStreamProcessor')
@patch('inference_worker.NATS')
async def test_benign_traffic_buffering(mock_nats_class, mock_processor_class, auranet_brains):
    """TEST 4: Normal traffic should NOT trigger NATS, and SHOULD be buffered."""
    brain_a, brain_b, benign_buffer, buffer_lock = auranet_brains
    
    mock_nc = AsyncMock()
    mock_nats_class.return_value = mock_nc
    
    raw_event = generate_mock_event(url="/api/accounts?id=4")
    feature_array = [0.0] * 13 
    
    mock_processor_instance = mock_processor_class.return_value
    mock_processor_instance.stream_traffic.return_value = [(raw_event, feature_array)]
    
    # Force thresholds high so neither brain triggers an anomaly
    config.ai._cache["tripwireThreshold"] = 100.0 
    config.ai._cache["nlpTripwire"] = 100.0
    
    await run_inference_pipeline(brain_a, brain_b, benign_buffer, buffer_lock)
    
    # Assert NATS was NEVER called
    mock_nc.publish.assert_not_called()
    # Assert the packet was stored for local training
    assert len(benign_buffer) == 1