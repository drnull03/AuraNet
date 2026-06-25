import os
import json
import torch
import torch.nn as nn
import numpy as np

from nlp_model import UrlNlpAutoencoder

def evaluate_nlp_pipeline():
    print("[NLP] Initializing Brain B Evaluation Engine...")
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    tensor_path = os.path.join(current_dir, "../../data/processed/nlp/nlp_test_tensor.pt")
    weights_path = os.path.join(current_dir, "../../models/omnifinance/nlp_ae_v1.pth")
    json_test = os.path.join(current_dir, "../../data/raw/hubble_testing_data.json")
    
    if not os.path.exists(tensor_path) or not os.path.exists(weights_path):
        print("❌ Error: Missing tensor or model weights. Run nlp_dataset.py and nlp_train.py first.")
        return

    # 1. Load the Model
    model = UrlNlpAutoencoder(vocab_size=128, seq_length=150)
    model.load_state_dict(torch.load(weights_path))
    model.eval()
    
    # reduction='none' allows us to get the loss for each individual character
    criterion = nn.CrossEntropyLoss(ignore_index=0, reduction='none')

    # 2. Load the Data
    test_tensor = torch.load(tensor_path)
    
    # Extract the raw strings for context printing
    urls = []
    with open(json_test, 'r') as f:
        for line in f:
            if not line.strip(): continue
            try:
                event = json.loads(line)
                l7 = event.get("flow", {}).get("l7", {})
                if l7 and l7.get("type") != "RESPONSE":
                    url = l7.get("http", {}).get("url", "")
                    if url: urls.append(url)
            except Exception:
                continue

    print(f"\n[NLP] Scanning {len(urls)} URLs for Grammatical Anomalies...\n")
    print(f"{'LOSS':<8} | {'CONTEXT (URL)'}")
    print("=" * 80)
    
    losses = []

    # 3. Evaluate each URL
    for i in range(len(test_tensor)):
        row_tensor = test_tensor[i].unsqueeze(0) # Add batch dimension (1, 150)
        url_string = urls[i]
        
        with torch.no_grad():
            logits = model(row_tensor)
            # Reshape for CrossEntropyLoss: (batch, classes, seq_length)
            logits = logits.transpose(1, 2)
            
            char_losses = criterion(logits, row_tensor) # Shape: (1, 150)
            
            # Mask out the padding (0s) so they don't drag down the average loss
            mask = row_tensor != 0
            if mask.sum().item() > 0:
                # Calculate the average loss ONLY for the actual characters in the URL
                seq_loss = char_losses.sum().item() / mask.sum().item()
            else:
                seq_loss = 0.0
                
        losses.append(seq_loss)
        
        # Visual indicator (Threshold set to 2.0 just for visual scanning)
        alert_flag = "🚨" if seq_loss > 2.0 else "  "
        
        # Truncate for terminal readability
        display_url = url_string[:70] + "..." if len(url_string) > 70 else url_string
        print(f"{alert_flag} {seq_loss:.4f} | {display_url}")

    print("=" * 80)
    
    # 4. Statistical Breakdown
    if losses:
        mean_loss = np.mean(losses)
        p95 = np.percentile(losses, 95)
        p99 = np.percentile(losses, 99)
        
        print(f"🎯 [NLP] Threshold Discovery Complete.")
        print(f"   Total URLs Inspected: {len(losses)}")
        print(f"   Mean Loss (Normal):   {mean_loss:.4f}")
        print(f"   95th Percentile:      {p95:.4f}")
        print(f"   99th Percentile:      {p99:.4f}")

if __name__ == "__main__":
    evaluate_nlp_pipeline()
