import sys
import os
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
import torch
import torch.nn as nn
import asyncio
import json
from collections import deque
import threading

# Add src to path as requested
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))


class MockAIConfig:
    Z_SCORE_WINDOW_SIZE = 100
    TRIPWIRE_THRESHOLD = 5.0
    Z_SCORE_THRESHOLD = 3.0
    NLP_TRIPWIRE = 2.0
    NLP_BODY_TRIPWIRE = 2.0
    THIRD_BRAIN = True
    LEARNING_ENGINE = True
    MAX_BUFFER_SIZE = 1000

class MockConfig:
    NATS_URL = "nats://mock:4222"
    NATS_SUBJECT_PREFIX = "auranet.events.ai."
    NODE_NAME = "test-node"
    ai = MockAIConfig()

# Inject the mock config into sys.modules BEFORE importing the worker
sys.modules['config'] = MockConfig()

# Now we can safely import the worker and its dependencies
from inference_worker import run_inference_pipeline

class DummyBrainA(nn.Module):
    def __init__(self, force_anomaly=False):
        super().__init__()
        self.force_anomaly = force_anomaly
    def forward(self, x):
        # Adding 10.0 forces a massive MSE Loss. Returning x forces 0.0 MSE Loss.
        return x + 10.0 if self.force_anomaly else x

# Dummy Brain B & C (NLP Transformers/LSTMs)
class DummyBrainNLP(nn.Module):
    def __init__(self, force_anomaly=False):
        super().__init__()
        self.force_anomaly = force_anomaly
    def forward(self, x):
        batch, seq_len = x.shape
        logits = torch.zeros(batch, seq_len, 128)
        if self.force_anomaly:
            # Force high CrossEntropy loss by predicting completely wrong chars
            logits[:, :, 0] = 10.0 
        else:
            # Force near-zero CE loss by correctly predicting the input chars
            for b in range(batch):
                for s in range(seq_len):
                    logits[b, s, x[b, s]] = 10.0
        return logits

class TestInferenceShortCircuit(unittest.IsolatedAsyncioTestCase):
    
    def setUp(self):
        # Standard mock event that triggers all brains (HTTP GET with query and body)
        self.mock_event = {
            "flow": {
                "source": {"labels": ["k8s:app=frontend-ui"]},
                "l7": {
                    "http": {
                        "method": "POST",
                        "url": "/api/test?q=1",
                        "body": "{\"dummy\": \"data\"}"
                    }
                }
            }
        }
        self.mock_features = [0.0] * 13
        self.benign_buffer = deque(maxlen=100)
        self.buffer_lock = threading.Lock()

    @patch('inference_worker.NATS')
    @patch('inference_worker.HubbleStreamProcessor')
    @patch('inference_worker.SymbolicSupervisor')
    async def test_1_symbolic_threat_early_exit(self, MockSupervisor, MockStream, MockNats):
        """Test: Symbolic Supervisor catches a threat. Brains A, B, and C MUST NOT run."""
        # Setup Mocks
        mock_nc = AsyncMock()
        MockNats.return_value = mock_nc
        
        mock_stream_instance = MagicMock()
        mock_stream_instance.stream_traffic.return_value = [(self.mock_event, self.mock_features)]
        MockStream.return_value = mock_stream_instance
        
        mock_supervisor_instance = MagicMock()
        mock_supervisor_instance.evaluate.return_value = "symbolic_uri_too_large"
        MockSupervisor.return_value = mock_supervisor_instance

        # Wrap models in MagicMocks so we can count their invocations
        brain_a = MagicMock(wraps=DummyBrainA(force_anomaly=False))
        brain_b = MagicMock(wraps=DummyBrainNLP(force_anomaly=False))
        brain_c = MagicMock(wraps=DummyBrainNLP(force_anomaly=False))

        # Execute
        await run_inference_pipeline(brain_a, brain_b, brain_c, self.benign_buffer, self.buffer_lock)

        # Assertions
        mock_nc.publish.assert_called_once()
        publish_args = mock_nc.publish.call_args[0]
        self.assertIn(b'"threat": "symbolic_uri_too_large"', publish_args[1])
        
        # PROVE THE SHORT-CIRCUIT WORKED
        brain_a.assert_not_called()
        brain_b.assert_not_called()
        brain_c.assert_not_called()
        self.assertEqual(len(self.benign_buffer), 0)

    @patch('inference_worker.NATS')
    @patch('inference_worker.HubbleStreamProcessor')
    @patch('inference_worker.SymbolicSupervisor')
    async def test_2_symbolic_safe_override(self, MockSupervisor, MockStream, MockNats):
        """Test: Identity is explicitly trusted ('Safe'). Brain A runs, Brains B/C skip."""
        mock_nc = AsyncMock()
        MockNats.return_value = mock_nc
        
        mock_stream_instance = MagicMock()
        mock_stream_instance.stream_traffic.return_value = [(self.mock_event, self.mock_features)]
        MockStream.return_value = mock_stream_instance
        
        mock_supervisor_instance = MagicMock()
        mock_supervisor_instance.evaluate.return_value = "Safe"
        MockSupervisor.return_value = mock_supervisor_instance

        brain_a = MagicMock(wraps=DummyBrainA(force_anomaly=True)) # Even if anomalous, 'Safe' overrides
        brain_b = MagicMock(wraps=DummyBrainNLP(force_anomaly=True))
        brain_c = MagicMock(wraps=DummyBrainNLP(force_anomaly=True))

        await run_inference_pipeline(brain_a, brain_b, brain_c, self.benign_buffer, self.buffer_lock)

        # Assertions
        mock_nc.publish.assert_not_called() # Safe overrides all alerts
        brain_a.assert_called_once()        # Brain A MUST run to update baseline
        
        # PROVE THE SHORT-CIRCUIT WORKED
        brain_b.assert_not_called()
        brain_c.assert_not_called()
        self.assertEqual(len(self.benign_buffer), 1) # Forced adaptation occurred

    @patch('inference_worker.NATS')
    @patch('inference_worker.HubbleStreamProcessor')
    @patch('inference_worker.SymbolicSupervisor')
    async def test_3_brain_a_anomaly_early_exit(self, MockSupervisor, MockStream, MockNats):
        """Test: Brain A flags anomaly. Brains B and C skip."""
        mock_nc = AsyncMock()
        MockNats.return_value = mock_nc
        
        mock_stream_instance = MagicMock()
        mock_stream_instance.stream_traffic.return_value = [(self.mock_event, self.mock_features)]
        MockStream.return_value = mock_stream_instance
        
        mock_supervisor_instance = MagicMock()
        mock_supervisor_instance.evaluate.return_value = "Unknown"
        MockSupervisor.return_value = mock_supervisor_instance

        brain_a = MagicMock(wraps=DummyBrainA(force_anomaly=True))
        brain_b = MagicMock(wraps=DummyBrainNLP(force_anomaly=False))
        brain_c = MagicMock(wraps=DummyBrainNLP(force_anomaly=False))

        await run_inference_pipeline(brain_a, brain_b, brain_c, self.benign_buffer, self.buffer_lock)

        mock_nc.publish.assert_called_once()
        publish_args = mock_nc.publish.call_args[0]
        self.assertIn(b'"threat": "network_behavior_anomaly"', publish_args[1])
        
        brain_a.assert_called_once()
        # PROVE THE SHORT-CIRCUIT WORKED
        brain_b.assert_not_called()
        brain_c.assert_not_called()
        self.assertEqual(len(self.benign_buffer), 0)

    @patch('inference_worker.NATS')
    @patch('inference_worker.HubbleStreamProcessor')
    @patch('inference_worker.SymbolicSupervisor')
    async def test_4_brain_b_anomaly_early_exit(self, MockSupervisor, MockStream, MockNats):
        """Test: Brain A is clean, Brain B flags anomaly. Brain C skips."""
        mock_nc = AsyncMock()
        MockNats.return_value = mock_nc
        
        mock_stream_instance = MagicMock()
        mock_stream_instance.stream_traffic.return_value = [(self.mock_event, self.mock_features)]
        MockStream.return_value = mock_stream_instance
        
        mock_supervisor_instance = MagicMock()
        mock_supervisor_instance.evaluate.return_value = "Unknown"
        MockSupervisor.return_value = mock_supervisor_instance

        brain_a = MagicMock(wraps=DummyBrainA(force_anomaly=False))
        brain_b = MagicMock(wraps=DummyBrainNLP(force_anomaly=True))
        brain_c = MagicMock(wraps=DummyBrainNLP(force_anomaly=False))

        await run_inference_pipeline(brain_a, brain_b, brain_c, self.benign_buffer, self.buffer_lock)

        mock_nc.publish.assert_called_once()
        publish_args = mock_nc.publish.call_args[0]
        self.assertIn(b'"threat": "l7_payload_anomaly"', publish_args[1])
        
        brain_a.assert_called_once()
        brain_b.assert_called_once()
        # PROVE THE SHORT-CIRCUIT WORKED
        brain_c.assert_not_called()
        self.assertEqual(len(self.benign_buffer), 0)

    @patch('inference_worker.NATS')
    @patch('inference_worker.HubbleStreamProcessor')
    @patch('inference_worker.SymbolicSupervisor')
    async def test_5_benign_traffic_full_pipeline(self, MockSupervisor, MockStream, MockNats):
        """Test: Fully benign traffic survives the entire gauntlet."""
        mock_nc = AsyncMock()
        MockNats.return_value = mock_nc
        
        mock_stream_instance = MagicMock()
        mock_stream_instance.stream_traffic.return_value = [(self.mock_event, self.mock_features)]
        MockStream.return_value = mock_stream_instance
        
        mock_supervisor_instance = MagicMock()
        mock_supervisor_instance.evaluate.return_value = "Unknown"
        MockSupervisor.return_value = mock_supervisor_instance

        brain_a = MagicMock(wraps=DummyBrainA(force_anomaly=False))
        brain_b = MagicMock(wraps=DummyBrainNLP(force_anomaly=False))
        brain_c = MagicMock(wraps=DummyBrainNLP(force_anomaly=False))

        await run_inference_pipeline(brain_a, brain_b, brain_c, self.benign_buffer, self.buffer_lock)

        # No alerts fired
        mock_nc.publish.assert_not_called()
        
        # All brains evaluated
        brain_a.assert_called_once()
        brain_b.assert_called_once()
        brain_c.assert_called_once()
        
        # Appended to the benign buffer for FL training
        self.assertEqual(len(self.benign_buffer), 1)

if __name__ == '__main__':
    unittest.main(verbosity=2)