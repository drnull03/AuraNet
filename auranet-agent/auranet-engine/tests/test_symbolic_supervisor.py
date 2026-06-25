import pytest
import sys
import os
from unittest.mock import patch, PropertyMock



# Ensure pytest can find your src modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from symbolic_supervisor import SymbolicSupervisor

@pytest.fixture
def supervisor():
    """Provides a fresh instance of the supervisor for each test."""
    return SymbolicSupervisor()

# THE FIX: Use PropertyMock and target the class, not the instance
@patch('config.DynamicConfig.TRUSTED_IDENTITIES', new_callable=PropertyMock)
def test_cryptographic_trust_override(mock_trusted_identities, supervisor):
    """Proves that a kernel-verified eBPF label completely bypasses the threat checks."""
    
    # 1. Inject our mock trusted label using .return_value
    mock_trusted_identities.return_value = {"k8s:app=gitlab-runner"}
    
    # 2. Craft a payload that comes from the trusted CI/CD pipeline
    mock_event = {
        "flow": {
            "source": {
                "labels": ["k8s:app=gitlab-runner"]
            },
            "l7": {
                "type": "REQUEST",
                "http": {
                    "method": "TRACE", # Intentionally using a banned method to prove the override works
                    "url": "http://internal/deploy"
                }
            }
        }
    }
    
    # ASSERTION: The trust label must override the banned method and return "Safe"
    result = supervisor.evaluate(mock_event)
    assert result == "Safe", f"Trust override failed! Expected 'Safe', got '{result}'"

def test_catches_massive_uri_buffer_overflow(supervisor):
    """Proves the supervisor traps URLs exceeding the 2048-character safety limit."""
    
    # Generate a ridiculously long URL payload
    massive_url = "http://api/v1/search?q=" + ("A" * 2500)
    
    mock_event = {
        "flow": {
            "source": {"labels": ["k8s:app=unknown-attacker"]},
            "l7": {
                "type": "REQUEST",
                "http": {
                    "method": "GET",
                    "url": massive_url
                }
            }
        }
    }
    
    result = supervisor.evaluate(mock_event)
    assert result == "symbolic_uri_too_large", "Buffer overflow trap failed!"

def test_catches_path_traversal_attacks(supervisor):
    """Proves the supervisor traps directory escape attempts (both plain and URL-encoded)."""
    
    # Payload 1: Standard Path Traversal
    event_plain = {
        "flow": {
            "source": {"labels": ["k8s:app=unknown-attacker"]},
            "l7": {"type": "REQUEST", "http": {"method": "GET", "url": "http://api/v1/../../../etc/passwd"}}
        }
    }
    
    # Payload 2: URL-Encoded Path Traversal
    event_encoded = {
        "flow": {
            "source": {"labels": ["k8s:app=unknown-attacker"]},
            "l7": {"type": "REQUEST", "http": {"method": "GET", "url": "http://api/v1/%2e%2e%2f%2e%2e%2fshadow"}}
        }
    }
    
    assert supervisor.evaluate(event_plain) == "symbolic_path_traversal", "Plain path traversal missed!"
    assert supervisor.evaluate(event_encoded) == "symbolic_path_traversal", "URL-encoded path traversal missed!"

def test_catches_banned_http_methods(supervisor):
    """Proves the supervisor traps dangerous REST methods."""
    
    mock_event = {
        "flow": {
            "source": {"labels": ["k8s:app=unknown-attacker"]},
            "l7": {
                "type": "REQUEST",
                "http": {
                    "method": "TRACE", # Highly dangerous, used for Cross-Site Tracing (XST)
                    "url": "http://api/v1/health"
                }
            }
        }
    }
    
    result = supervisor.evaluate(mock_event)
    assert result == "symbolic_banned_method", "Banned HTTP method trap failed!"

def test_ignores_benign_traffic(supervisor):
    """Proves the supervisor stays out of the way for normal, safe network traffic."""
    
    mock_event = {
        "flow": {
            "source": {"labels": ["k8s:app=frontend-ui"]},
            "l7": {
                "type": "REQUEST",
                "http": {
                    "method": "POST",
                    "url": "http://api-gateway/api/v1/checkout"
                }
            }
        }
    }
    
    # ASSERTION: Normal traffic must return "Unknown" so the PyTorch model can evaluate it
    result = supervisor.evaluate(mock_event)
    assert result == "Unknown", f"Supervisor falsely flagged benign traffic as {result}!"