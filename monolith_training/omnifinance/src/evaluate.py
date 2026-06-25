import os
import torch
import torch.nn as nn
import numpy as np

import config
from dataset_general import HubbleDataProcessor
from model import ZeroTrustAutoencoder

def evaluate_pipeline():
    print("[SOC] Initializing AuraNet Threat Evaluation Engine (Discovery Mode)...")

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
    
    print(f"\n🚀 [SOC] Scanning {len(df)} network flows to discover baseline MSE...\n")
    print(f"{'MSE LOSS':<10} | {'DIRECTION':<10} | {'METHOD':<8} | {'CONTEXT'}")
    print("=" * 80)
    
    mse_scores = []
    
    # 3. Evaluate each flow and log it
    for i in range(len(df)):
        # THE FIX: Add .copy() and .unsqueeze(0) to match training batch shapes
        row_tensor = torch.FloatTensor(df.iloc[i].values.copy()).unsqueeze(0)
        context = raw_events[i]
        
        direction = context.get('traffic_direction', 'UNKNOWN')
        method = context.get('method', 'NONE')
        url = context.get('url', 'NONE')
        ip_src = context.get('ip_source', 'UNKNOWN')
        
        if method == "" and url == "":
            display_context = f"TCP Flow from {ip_src}"
            method = "TCP"
        else:
            display_context = url[:50] + "..." if len(url) > 50 else url

        # Calculate Loss
        with torch.no_grad():
            reconstructed = model(row_tensor)
            mse_loss = criterion(reconstructed, row_tensor).item()
            
        mse_scores.append(mse_loss)
        
        alert_flag = "🚨" if mse_loss > 0.005 else "  "
        # THE FIX: Increased precision to .6f to see micro-errors
        print(f"{alert_flag} {mse_loss:.6f} | {direction:<10} | {method:<8} | {display_context}")
            
    print("=" * 80)
    
    if mse_scores:
        mean_mse = np.mean(mse_scores)
        max_mse = np.max(mse_scores)
        p95 = np.percentile(mse_scores, 95)
        p99 = np.percentile(mse_scores, 99)
        
        print(f"🎯 [SOC] Threshold Discovery Analysis Complete.")
        print(f"   Total Flows Inspected: {len(df)}")
        print(f"   Mean Error (Normal):   {mean_mse:.6f}")
        print(f"   Absolute Max Error:    {max_mse:.6f}")
        print(f"   95th Percentile:       {p95:.6f} (Filters 5% of highest traffic)")
        print(f"   99th Percentile:       {p99:.6f} (Filters 1% of highest traffic)")
    else:
        print("⚠️ No data was processed.")

if __name__ == "__main__":
    evaluate_pipeline()