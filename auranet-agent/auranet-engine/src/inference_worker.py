import json
import torch
import torch.nn as nn
import asyncio
from nats.aio.client import Client as NATS
from symbolic_supervisor import SymbolicSupervisor
import config
from stream_processor import HubbleStreamProcessor
from collections import deque
import numpy as np

async def run_inference_pipeline(brain_a, brain_b, brain_c, benign_buffer, buffer_lock):
    """
    Worker A: The Cascade Funnel. Evaluates lightweight behavior first,
    then triggers heavy NLP payload inspection only for valid L7 requests.
    """
    
    nc = NATS()
    try:
        print(f"[Worker A] Connecting to NATS at {config.NATS_URL}...")
        await nc.connect(config.NATS_URL)
        print("[Worker A] NATS Connected! Real-time Two-Brain inference active.")
    except Exception as e:
        print(f"[Worker A] Fatal NATS Error: {e}")
        return

    processor = HubbleStreamProcessor()
    mse_criterion = nn.MSELoss()
    ce_criterion = nn.CrossEntropyLoss(ignore_index=0, reduction='none')
    supervisor = SymbolicSupervisor()

    rolling_mse_window = deque(maxlen=config.ai.Z_SCORE_WINDOW_SIZE)
    MIN_WARMUP_SAMPLES = 100
    
    print("[Worker A] Dual AI Perception Layer Online. Listening for packets...\n")

    for raw_event, feature_array in processor.stream_traffic():
        
        # Brain A (Behavioral Geometry)
        
        tensor_input = torch.FloatTensor(feature_array).unsqueeze(0)

        with torch.no_grad():
            reconstructed = brain_a(tensor_input)
            mse_loss = mse_criterion(reconstructed, tensor_input).item()

        is_anomaly_a = False
        z_score = 0.0
        if len(rolling_mse_window) < MIN_WARMUP_SAMPLES:
            # fallback to static threshold during initial agent boot
            is_anomaly_a = mse_loss > config.ai.TRIPWIRE_THRESHOLD
        else:
            # Calculate Dynamic Z-Score
            current_mean = np.mean(rolling_mse_window)
            # this took our to debug it turned out it is dividing by zero problem
            current_std = np.std(rolling_mse_window) + 1e-8    # Add epsilon to prevent divide-by-zero
            z_score = (mse_loss - current_mean) / current_std
            
            is_anomaly_a = z_score > config.ai.Z_SCORE_THRESHOLD
        
        # Brain B (Grammatical Payload)
        nlp_loss = 0.0
        is_anomaly_b = False
        
        url = raw_event.get("flow", {}).get("l7", {}).get("http", {}).get("url", "")
        
        if url and '?' in url:
            # On-the-fly Tokenization
            encoded = [min(ord(c), 127) for c in url][:150]
            padding = [0] * (150 - len(encoded))
            tensor_nlp = torch.LongTensor(encoded + padding).unsqueeze(0)
            
            with torch.no_grad():
                logits = brain_b(tensor_nlp).transpose(1, 2)
                char_losses = ce_criterion(logits, tensor_nlp)
                
                mask = tensor_nlp != 0
                if mask.sum().item() > 0:
                    nlp_loss = char_losses.sum().item() / mask.sum().item()
            
            is_anomaly_b = nlp_loss > config.ai.NLP_TRIPWIRE

        nlp_body_loss = 0.0                                                        
        is_anomaly_c = False                                                        
        
        body = raw_event.get("flow", {}).get("l7", {}).get("http", {}).get("body", "")
        
        if config.ai.THIRD_BRAIN and body:                                          
            # On-the-fly Tokenization (Using 512 length for bodies)                 
            encoded_body = [min(ord(c), 127) for c in body][:512]                   
            padding_body = [0] * (512 - len(encoded_body))                          
            tensor_nlp_body = torch.LongTensor(encoded_body + padding_body).unsqueeze(0) 
            
            with torch.no_grad():                                                  
                logits_body = brain_c(tensor_nlp_body).transpose(1, 2)              
                char_losses_body = ce_criterion(logits_body, tensor_nlp_body)       
                
                mask_body = tensor_nlp_body != 0                                    
                if mask_body.sum().item() > 0:                                      
                    nlp_body_loss = char_losses_body.sum().item() / mask_body.sum().item() 
            
            is_anomaly_c = nlp_body_loss > config.ai.NLP_BODY_TRIPWIRE

        # The Symbolic Supervisor & Routing
        symbolic_decision = supervisor.evaluate(raw_event) 

        source_labels = raw_event.get("flow", {}).get("source", {}).get("labels", [])
        culprit_workload = "unknown"
        for label in source_labels:
            if label.startswith("k8s:app="):
                culprit_workload = label.split("=")[1]
                break
        if culprit_workload == "unknown":
            culprit_workload = config.NODE_NAME 
            
        subject = f"{config.NATS_SUBJECT_PREFIX}{culprit_workload}"
        
        # DECISION TREE
        if symbolic_decision not in ["Safe", "Unknown"]:
            alert_payload = {"threat": symbolic_decision, "probability": -1, "raw_context": json.dumps(raw_event)}
            print(f"[Worker A] SYMBOLIC THREAT: {symbolic_decision.upper()} -> Firing to {subject}")
            await nc.publish(subject, json.dumps(alert_payload).encode())

        elif is_anomaly_b and symbolic_decision == "Unknown":
            # brain B take higher priority than brain A because it is static
            probability = min((nlp_loss / (config.ai.NLP_TRIPWIRE * 2)), 0.99)
            alert_payload = {"threat": "payload_anomaly", "probability": probability, "raw_context": json.dumps(raw_event)}
            print(f"[Worker A]  NLP PAYLOAD THREAT! CE Loss: {nlp_loss:.4f} -> Firing to {subject}")
            await nc.publish(subject, json.dumps(alert_payload).encode())


        elif is_anomaly_c and symbolic_decision == "Unknown":                                                           
            probability = min((nlp_body_loss / (config.ai.NLP_BODY_TRIPWIRE * 2)), 0.99)                                
            alert_payload = {"threat": "l7_body_anomaly", "probability": probability, "raw_context": json.dumps(raw_event)} 
            print(f"[Worker A] 🚨 NLP BODY THREAT! CE Loss: {nlp_body_loss:.4f} -> Firing to {subject}")                
            await nc.publish(subject, json.dumps(alert_payload).encode())

        elif is_anomaly_a and symbolic_decision == "Unknown":
            probability = min((z_score / (config.ai.Z_SCORE_THRESHOLD * 2)), 0.99) if len(rolling_mse_window) >= MIN_WARMUP_SAMPLES else 0.99
            alert_payload = {"threat": "network_behavior_anomaly", "probability": probability, "raw_context": json.dumps(raw_event)}
            print(f"[Worker A] BEHAVIORAL THREAT! Z-Score: {z_score:.2f} (MSE: {mse_loss:.4f}) -> Firing to {subject}")
            await nc.publish(subject, json.dumps(alert_payload).encode())

        elif (is_anomaly_a or is_anomaly_b or is_anomaly_c) and symbolic_decision == "Safe":
            # this is for when we delegate trust with auranet-cli
            # after delegating trust brain A can learn the new flows
            # and we can untrust the flow again using cli again 
            # might make auranet-cli trust timed for 30 minutes or so in the future we will see
            print(f"[Worker A]  High AI Loss overridden by Symbolic Supervisor. Forcing adaptation.")
            rolling_mse_window.append(mse_loss)
            if config.ai.LEARNING_ENGINE:
                with buffer_lock:
                    if len(benign_buffer) < config.ai.MAX_BUFFER_SIZE:
                        benign_buffer.append(feature_array)

        else:
            # Benign Traffic
            rolling_mse_window.append(mse_loss)
            if config.ai.LEARNING_ENGINE:
                with buffer_lock:
                    if len(benign_buffer) < config.ai.MAX_BUFFER_SIZE:
                        benign_buffer.append(feature_array)