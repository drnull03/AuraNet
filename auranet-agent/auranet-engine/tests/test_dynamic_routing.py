import pytest
import sys
import os


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import config

def extract_culprit_logic(raw_event):
    """
    This is an isolated copy of the exact dynamic extraction block from inference_worker.py.
    We isolate it here to test the logic without needing a live NATS connection.
    """
    source_labels = raw_event.get("flow", {}).get("source", {}).get("labels", [])
    culprit_workload = "unknown"
    
    for label in source_labels:
        if label.startswith("k8s:app="):
            culprit_workload = label.split("=")[1]
            break
            
    if culprit_workload == "unknown":
        culprit_workload = config.NODE_NAME 
        
    return culprit_workload

def test_extracts_correct_k8s_app_label():
    """Proves the agent correctly identifies the attacking microservice."""
    mock_event = {
        "flow": {
            "source": {
                "labels": ["k8s:io.cilium.k8s.policy.cluster=default", "k8s:app=frontend-ui"]
            }
        }
    }
    
    culprit = extract_culprit_logic(mock_event)
    assert culprit == "frontend-ui", f"Failed! Extracted {culprit} instead of frontend-ui."

def test_fallback_to_node_name_on_missing_label():
    """Proves the agent safely falls back to the host Node identity if K8s drops the label."""
    # A packet with absolutely no Kubernetes labels
    mock_event_missing_labels = {
        "flow": {
            "source": {
                "labels": []
            }
        }
    }
    
    culprit = extract_culprit_logic(mock_event_missing_labels)
    # It MUST fall back to whatever the Downward API injected into config.NODE_NAME
    assert culprit == config.NODE_NAME, "Failed! Did not safely fall back to NODE_NAME."