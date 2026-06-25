import json
import torch
import torch.nn as nn
import asyncio
from nats.aio.client import Client as NATS

import config
from stream_processor import HubbleStreamProcessor

async def run_inference_pipeline(model, benign_buffer, buffer_lock):
    """
    Worker A: Continuously streams Hubble data, evaluates it via the PyTorch model,
    and publishes alerts to NATS or saves normal traffic for local FL training.
    """
    
    # Connect to the NATS Message Queue
    nc = NATS()
    try:
        print(f"[Worker A]  Connecting to NATS at {config.NATS_URL}...")
        await nc.connect(config.NATS_URL)
        print("[Worker A]  NATS Connected! Real-time inference active.")
    except Exception as e:
        print(f"[Worker A]  Fatal NATS Error: {e}")
        return

    # Initialize the Stream Processor and Loss Function
    processor = HubbleStreamProcessor()
    criterion = nn.MSELoss()

    print("[Worker A]  AI Perception Layer Online. Listening for packets...\n")

    # Consume the Generator
    for raw_event, feature_array in processor.stream_traffic():
        
        # Convert the 13-dim NumPy array to a PyTorch Tensor
        # .unsqueeze(0) adds a batch dimension of 1, which PyTorch requires
        tensor_input = torch.FloatTensor(feature_array).unsqueeze(0)

        # Run Inference (No gradients needed here, saves CPU)
        with torch.no_grad():
            reconstructed = model(tensor_input)
            mse_loss = criterion(reconstructed, tensor_input).item()

        # The Neurosymbolic Supervisor (Placeholder Hook)
        # Future Logic: If raw_event matches an internal CI/CD IP, set this to "Safe"
        symbolic_decision = supervisor.evaluate(raw_event) 
        is_anomaly = mse_loss > config.ai.TRIPWIRE_THRESHOLD

        source_labels = raw_event.get("flow", {}).get("source", {}).get("labels", [])
        culprit_workload = "unknown"
        for label in source_labels:
            if label.startswith("k8s:app="):
                culprit_workload = label.split("=")[1]
                break
        if culprit_workload == "unknown":
            culprit_workload = config.NODE_NAME 
            
        subject = f"{config.NATS_SUBJECT_PREFIX}{culprit_workload}"

        
        if symbolic_decision not in ["Safe", "Unknown"]:
            # SYMBOLIC THREAT
            # The rule engine caught an obvious attack. Fire with -1 probability.
            alert_payload = {
                "threat": symbolic_decision,
                "probability": -1,
                "raw_context": json.dumps(raw_event)
            }
            print(f"[Worker A] DETERMINISTIC THREAT: {symbolic_decision.upper()} -> Firing to {subject}")
            await nc.publish(subject, json.dumps(alert_payload).encode())

        elif is_anomaly and symbolic_decision == "Unknown":
            # NEURAL ANOMALY 
            probability = min((mse_loss / 0.1), 0.99) 
            alert_payload = {
                "threat": "network_anomaly",
                "probability": probability,
                "raw_context": json.dumps(raw_event)
            }
            print(f"🚨 [Worker A] AI THREAT DETECTED! MSE: {mse_loss:.4f} -> Firing to {subject}")
            await nc.publish(subject, json.dumps(alert_payload).encode())

        elif is_anomaly and symbolic_decision == "Safe":
            # SYMBOLIC OVERRIDE 
            print(f"[Worker A] High MSE ({mse_loss:.4f}) overridden by Symbolic Supervisor. Forcing adaptation.")
            with buffer_lock:
                if len(benign_buffer) < config.ai.MAX_BUFFER_SIZE:
                    benign_buffer.append(feature_array)

        else:
            # BENIGN TRAFFIC
            with buffer_lock:
                if len(benign_buffer) < config.ai.MAX_BUFFER_SIZE:
                    benign_buffer.append(feature_array)