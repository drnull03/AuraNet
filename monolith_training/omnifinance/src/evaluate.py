import os
import torch
import torch.nn as nn

import config
from dataset import HubbleDataProcessor
from model import ZeroTrustAutoencoder

def evaluate_pipeline():
    print("[SOC] Initializing AuraNet Threat Evaluation Engine...")

    if not os.path.exists(config.MODEL_WEIGHTS_PATH):
        print(f"❌ Error: Model weights not found at {config.MODEL_WEIGHTS_PATH}. Run train.py first!")
        return
    if not os.path.exists(config.TEST_DATA_PATH):
        print(f"❌ Error: Test data not found at {config.TEST_DATA_PATH}. Run the attack simulator!")
        return

    # 1. Process Test Traffic In-Memory
    print("[SOC] Processing raw test telemetry on the fly...")
    processor = HubbleDataProcessor(config.TEST_DATA_PATH)
    processor.load_and_filter()
    processor.engineer_features()
    
    df = processor.get_dataframe()
    raw_events = processor.raw_data 
    input_dim = df.shape[1]
    
    # 2. Load the Trained Model
    model = ZeroTrustAutoencoder(input_dim)
    model.load_state_dict(torch.load(config.MODEL_WEIGHTS_PATH))
    model.eval()
    criterion = nn.MSELoss()
    
    print(f"\n🚀 [SOC] Scanning {len(df)} mixed network flows using Threshold: {config.TRIPWIRE_THRESHOLD}\n")
    print("=" * 80)
    
    anomalies_caught = 0
    total_evaluated = 0
    
    # 3. Evaluate each flow
    for i in range(len(df)):
        total_evaluated += 1
        row_tensor = torch.FloatTensor(df.iloc[i].values)
        context = raw_events[i]
        
        # Format the output context
        src_app = context.get('src_app', 'unknown')
        method = context.get('method', 'NONE')
        url = context.get('url', 'NONE')
        flow_desc = f"[{src_app}] -> {method} {url}"
        
        with torch.no_grad():
            reconstructed = model(row_tensor)
            mse_loss = criterion(reconstructed, row_tensor).item()
        
        # 4. SOAR Tripwire Logic
        if mse_loss > config.TRIPWIRE_THRESHOLD:
            anomalies_caught += 1
            print(f"🚨 ANOMALY DETECTED! (MSE: {mse_loss:.4f})")
            print(f"   Context: {flow_desc}")
            print(f"   Action:  Triggering AutoHeal for {src_app}...\n")
            
    print("=" * 80)
    print(f"🎯 [SOC] Evaluation Complete.")
    print(f"   Total Flows Inspected: {total_evaluated}")
    print(f"   Threats Neutralized:   {anomalies_caught}")

if __name__ == "__main__":
    evaluate_pipeline()