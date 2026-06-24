import numpy as np
import sys
import os

# Ensure pytest can find your src modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from stream_processor import HubbleStreamProcessor

def test_noise_filter_drops_health_probes():
    """Test that reserved Kubelet host traffic is correctly ignored."""
    processor = HubbleStreamProcessor()
    
    # Mock a Kubelet health probe event
    health_probe_event = {
        "flow": {
            "verdict": "FORWARDED",
            "source": {
                "labels": ["reserved:host"]
            }
        }
    }
    
    result = processor.process_event(health_probe_event)
    assert result is None, "Stream processor failed to filter out a Kubelet health probe!"

def test_feature_extraction_valid_http():
    """Test that a valid frontend-to-gateway HTTP GET request maps to the correct 13-dim array."""
    processor = HubbleStreamProcessor()
    
    # Mock a valid Zero Trust API request
    valid_http_event = {
        "flow": {
            "verdict": "FORWARDED",
            "source": {"labels": ["k8s:app=frontend-ui"]},
            "destination": {"labels": ["k8s:app=api-gateway"], "port": 80},
            "l4": {"TCP": {"flags": {"SYN": True, "ACK": True}}},
            "l7": {
                "type": "REQUEST",
                "http": {
                    "method": "GET",
                    "url": "http://api-gateway/api/accounts?id=12345"
                }
            }
        }
    }
    
    result = processor.process_event(valid_http_event)
    
    # Ensure it wasn't dropped
    assert result is not None
    # Ensure strict 13-dimensional NumPy array
    assert result.shape == (13,)
    assert result.dtype == np.float32
    
    # Validate specific feature indices based on our monolithic mapping:
    # Index 0: Target Label (0.0 for FORWARDED)
    assert result[0] == 0.0
    # Index 1: is_valid_acc_path (Should be 1.0 based on regex)
    assert result[1] == 1.0
    # Index 3: is_get (Should be 1.0)
    assert result[3] == 1.0
    # Index 5: src_is_frontend (Should be 1.0)
    assert result[5] == 1.0
    # Index 9: dst_is_gateway (Should be 1.0)
    assert result[9] == 1.0

def test_feature_extraction_db_connection():
    """Test that an initial Database connection (L4 TCP SYN) is captured."""
    processor = HubbleStreamProcessor()
    
    # Mock a TCP SYN packet to PostgreSQL
    db_event = {
        "flow": {
            "verdict": "FORWARDED",
            "source": {"labels": ["k8s:app=account-service"]},
            "destination": {"labels": ["k8s:app=finance-db"], "port": 5432},
            "l4": {"TCP": {"flags": {"SYN": True, "ACK": False}}} # SYN without ACK = Connection Start
        }
    }
    
    result = processor.process_event(db_event)
    
    assert result is not None
    # Index 4: is_db_traffic (Should be 1.0 for port 5432)
    assert result[4] == 1.0
    # Index 7: src_is_account (Should be 1.0)
    assert result[7] == 1.0
    # Index 12: dst_is_db (Should be 1.0)
    assert result[12] == 1.0