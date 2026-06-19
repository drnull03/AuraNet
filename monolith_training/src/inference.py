import os
import torch
import torch.nn as nn
import pandas as pd

# Import the classes we already built!
from dataset import HubbleDataProcessor
from model import ZeroTrustAutoencoder

def run_soc_inference():
    print("🛡️ Initializing AuraNet AI Inference Engine...")

    current_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(current_dir, "..", "models", "zerotrust_ae_v1.pth")
    test_data_path = os.path.join(current_dir, "..", "data", "raw", "hubble_attack_data.json")

    if not os.path.exists(model_path):
        print(f"❌ Error: Model weights not found at {model_path}. Did you train it?")
        return
    if not os.path.exists(test_data_path):
        print(f"❌ Error: Test data not found at {test_data_path}.")
        print("   Run test_simulator.py and collect logs into this file first!")
        return

    # 1. Process the incoming test traffic
    print("📊 Processing incoming network telemetry...")
    processor = HubbleDataProcessor(test_data_path)
    processor.load_and_filter()
    processor.engineer_features()
    
    df = processor.get_dataframe()
    # We kept raw_data in our class so we can print human-readable alerts!
    raw_events = processor.raw_data 
    
    # 2. Load the trained AI Brain
    input_dim = df.shape[1]
    model = ZeroTrustAutoencoder(input_dim)
    model.load_state_dict(torch.load(model_path))
    model.eval() # Turn off training mode
    
    criterion = nn.MSELoss()
    
    # 3. Set the Tripwire Threshold
    # Since normal traffic MSE is 0.0000, any error above 0.05 is mathematically massive.
    TRIPWIRE_THRESHOLD = 0.05
    
    print(f"\n🚀 Scanning {len(df)} network flows for Zero-Day Anomalies...\n")
    print("=" * 80)
    
    anomalies_caught = 0
    
    # 4. Evaluate each flow one by one
    for i in range(len(df)):
        # Get the numerical features (The AI Input)
        row_tensor = torch.FloatTensor(df.iloc[i].values)
        
        # Get the human-readable context (For the SOC Analyst)
        context = raw_events[i]
        flow_desc = f"[{context['src_app']}] -> {context['method']} {context['url']}"
        
        # Ask the AI to reconstruct the flow
        with torch.no_grad(): # Don't calculate gradients (saves memory/time)
            reconstructed = model(row_tensor)
            mse_loss = criterion(reconstructed, row_tensor).item()
        
        # 5. Trigger the SOAR Tripwire
        if mse_loss > TRIPWIRE_THRESHOLD:
            anomalies_caught += 1
            print(f"🚨 ANOMALY DETECTED! (MSE: {mse_loss:.4f})")
            print(f"   Context: {flow_desc}")
            print(f"   Action:  Isolating Pod {context['src_app']}...\n")
        else:
            # It's normal traffic. We can silently allow it.
            # print(f"✅ Normal (MSE: {mse_loss:.4f}) | {flow_desc}")
            pass
            
    print("=" * 80)
    print(f"🎯 Inference Complete. Caught {anomalies_caught} anomalous network flows.")

if __name__ == "__main__":
    run_soc_inference()