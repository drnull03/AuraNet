import json
import re
import pandas as pd
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader

class HubbleDataProcessor:
    def __init__(self, json_path):
        self.json_path = json_path
        self.raw_data = []
        self.raw_json_events = []
        self.dataframe = None

    def extract_app_label(self, labels):
        """Extracts the 'app' name from Cilium's k8s label array."""
        if not labels:
            return "unknown"
        for label in labels:
            if label.startswith("k8s:app="):
                return label.split("=")[1]
        return "unknown"

    def load_and_filter(self):
        """Phase 1: Filter out the noise and keep only L7 requests and Policy Drops."""
        print(f"🐝 Loading raw Hubble logs from {self.json_path}...")
        
        filtered_events = []
        with open(self.json_path, 'r') as f:
            for line in f:
                if not line.strip():
                    continue
                
                try:
                    event = json.loads(line)
                    flow = event.get("flow", {})
                except json.JSONDecodeError:
                    continue

                verdict = flow.get("verdict", "")
                source_labels = flow.get("source", {}).get("labels", [])
                
                # 1. Drop Kubelet health probes
                if "reserved:host" in source_labels:
                    continue

                l7 = flow.get("l7", {})
                
                # 2. Keep if it's a DROPPED packet OR if it has HTTP L7 data
                if verdict == "DROPPED" or (verdict == "FORWARDED" and l7):
                    
                    self.raw_json_events.append(event)

                    src_app = self.extract_app_label(source_labels)
                    dst_app = self.extract_app_label(flow.get("destination", {}).get("labels", []))
                    
                    # Extract HTTP details if they exist (L4 drops won't have this)
                    http_data = l7.get("http", {}) if l7 else {}
                    method = http_data.get("method", "NONE")
                    url = http_data.get("url", "NONE")

                    filtered_events.append({
                        "verdict": verdict,
                        "src_app": src_app,
                        "dst_app": dst_app,
                        "method": method,
                        "url": url
                    })

        print(f"✅ Filtered down to {len(filtered_events)} relevant network events.")
        self.raw_data = filtered_events

    def engineer_features(self):
        """Phase 2: Convert text/labels into numerical features for the Autoencoder."""
        df = pd.DataFrame(self.raw_data)
        
        # 1. Verdict (0 = Forwarded, 1 = Dropped)
        df['is_dropped'] = (df['verdict'] == 'DROPPED').astype(float)
        
        # 2. Path Validity (1 = Matches /customers/INT, 0 = Anomalous/Other)
        # This regex strictly matches exactly /customers/ followed by digits
        valid_path_regex = re.compile(r"^/customers/\d+$")
        df['is_valid_path'] = df['url'].apply(lambda x: 1.0 if valid_path_regex.match(x) else 0.0)
        
        # 3. HTTP Methods (One-Hot Encoding)
        df['is_get'] = (df['method'] == 'GET').astype(float)
        df['is_post'] = (df['method'] == 'POST').astype(float)
        df['is_delete'] = (df['method'] == 'DELETE').astype(float)
        
        # 4. Source App (One-Hot Encoding)
        df['src_is_retail'] = (df['src_app'] == 'retail-dashboard').astype(float)
        df['src_is_invest'] = (df['src_app'] == 'investment-dashboard').astype(float)
        
        # 5. Destination App (One-Hot Encoding)
        df['dst_is_customer_api'] = (df['dst_app'] == 'customer-api').astype(float)
        df['dst_is_vault'] = (df['dst_app'] == 'vault-db').astype(float)

        # Drop the original text columns, keep only the numbers
        self.dataframe = df.drop(columns=['verdict', 'src_app', 'dst_app', 'method', 'url'])
        print(f"🧠 Engineered Feature Matrix: {self.dataframe.shape[1]} dimensions.")

    def get_dataframe(self):
        return self.dataframe
    def save_raw_events(self, output_path):
        """Dumps the unfiltered, raw Hubble JSON for the accepted flows."""
        with open(output_path, 'w') as f:
            json.dump(self.raw_json_events, f, indent=4)
        print(f"💾 Saved {len(self.raw_json_events)} raw Hubble events to {output_path}")


class HubbleDataset(Dataset):
    """Phase 3: PyTorch Dataset Wrapper"""
    def __init__(self, dataframe):
        # Convert the Pandas DataFrame into a PyTorch FloatTensor
        self.data = torch.FloatTensor(dataframe.values)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        # For an Autoencoder, the input and the target are the same thing!
        # We return (X, X) because the model tries to recreate its own input.
        x = self.data[idx]
        return x, x

    


if __name__ == "__main__":
    # Test the pipeline by running this file directly
    import os
    
    # Adjust path assuming this runs from inside the src/ folder
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_file = os.path.join(current_dir, "..", "data", "raw", "hubble_training_data.json")
    
    if os.path.exists(json_file):
        processor = HubbleDataProcessor(json_file)
        processor.load_and_filter()
        
        raw_out_path = os.path.join(current_dir, "..", "data", "raw", "hubble_62_raw.json")
        processor.save_raw_events(raw_out_path)
        
        processor.engineer_features()
        
        df = processor.get_dataframe()
        print("\n--- Preview of the Numerical Feature Tensor ---")
        print(df.head())
        
        # Create PyTorch Dataset
        torch_dataset = HubbleDataset(df)
        print(f"\n✅ PyTorch Dataset ready! Contains {len(torch_dataset)} samples.")
    else:
        print(f"❌ Could not find {json_file}. Did you run the extractor script?")