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
    
    # Connect to the NATS Broker
    nc = NATS()
    try:
        print(f"[Worker A] Connecting to NATS at {config.NATS_URL}...")
        await nc.connect(config.NATS_URL)
        print("[Worker A] ✅ NATS Connected! Real-time inference active.")
    except Exception as e:
        print(f"[Worker A] ❌ Fatal NATS Error: {e}")
        return

    # Initialize the Stream Processor and Loss Function
    processor = HubbleStreamProcessor()
    criterion = nn.MSELoss()

    print("[Worker A] AI Perception Layer Online. Listening for packets...\n")

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
        symbolic_decision = "Unknown" 

        # The Decision Matrix
        is_anomaly = mse_loss > config.TRIPWIRE_THRESHOLD

        if is_anomaly and symbolic_decision == "Unknown":
            # NEURAL AI CAUGHT AN ATTACK
            
            # Map the MSE into a probability % for the Node.js Trust Engine
            # E.g., an MSE of 0.08 / 0.1 = 0.80 (80% confidence)
            probability = min((mse_loss / 0.1), 0.99) 
            
            alert_payload = {
                "threat": "network_anomaly",
                "probability": probability,
                "raw_context": json.dumps(raw_event)
            }
            
            # Construct subject: e.g., auranet.events.ai.payment-api
            subject = f"{config.NATS_SUBJECT_PREFIX}{config.WORKLOAD_NAME}"
            
            print(f"🚨 [Worker A] THREAT DETECTED! MSE: {mse_loss:.4f} -> Firing to {subject}")
            await nc.publish(subject, json.dumps(alert_payload).encode())

        elif is_anomaly and symbolic_decision == "Safe":
            #SYMBOLIC OVERRIDE (Concept Drift Mitigation)
            # The AI panicked, but the hardcoded rules know this is safe CI/CD traffic.
            print(f"[Worker A] High MSE ({mse_loss:.4f}) overridden by Symbolic Supervisor. Forcing adaptation.")
            
            # Lock the buffer safely and force the model to learn this new behavior
            with buffer_lock:
                if len(benign_buffer) < config.MAX_BUFFER_SIZE:
                    benign_buffer.append(feature_array)

        else:
            # BENIGN TRAFFIC (Normal Operations)
            # Lock the memory queue and save it for the 2-minute local training loop
            with buffer_lock:
                if len(benign_buffer) < config.MAX_BUFFER_SIZE:
                    benign_buffer.append(feature_array)