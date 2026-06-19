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
        if not labels:
            return "unknown"
        for label in labels:
            if label.startswith("k8s:app="):
                return label.split("=")[1]
        return "unknown"

    def load_and_filter(self):
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
                event_type = flow.get("event_type", {}).get("type", 0)
                drop_reason = flow.get("drop_reason_desc", "")
                
                # 1. Drop Kubelet health probes
                if "reserved:host" in source_labels:
                    continue
                
                # 2. Prevent Double-Logging, but CAPTURE ALL PHYSICAL DROPS
                if verdict == "DROPPED" and event_type != 1:
                    continue
                    
                # 3. IGNORE SPIRE mTLS HANDSHAKE DROPS
                if verdict == "DROPPED" and drop_reason == "AUTH_REQUIRED":
                    continue

                l7 = flow.get("l7", {})
                
                # 4. IGNORE L7 RESPONSES
                if l7 and l7.get("type") == "RESPONSE":
                    continue

                is_http_l7 = verdict == "FORWARDED" and l7 and "http" in l7
                
                # 5. Keep unique physical drops OR valid HTTP REQUESTS
                if verdict == "DROPPED" or is_http_l7:
                    
                    self.raw_json_events.append(event)

                    src_app = self.extract_app_label(source_labels)
                    dst_app = self.extract_app_label(flow.get("destination", {}).get("labels", []))
                    
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

        print(f"✅ Filtered down to {len(filtered_events)} pure, relevant network events.")
        self.raw_data = filtered_events

    def engineer_features(self):
        df = pd.DataFrame(self.raw_data)
        
        df['is_dropped'] = (df['verdict'] == 'DROPPED').astype(float)
        
        # --- FIXED REGEX ---
        # .*: Matches the "http://customer-api:8000" part dynamically
        # \d+$: Ensures it strictly ends with a number (no SQL injections allowed)
        valid_path_regex = re.compile(r".*/customers/\d+$")
        df['is_valid_path'] = df['url'].apply(lambda x: 1.0 if valid_path_regex.match(x) else 0.0)
        
        df['is_get'] = (df['method'] == 'GET').astype(float)
        df['is_post'] = (df['method'] == 'POST').astype(float)
        df['is_delete'] = (df['method'] == 'DELETE').astype(float)
        
        df['src_is_retail'] = (df['src_app'] == 'retail-dashboard').astype(float)
        df['src_is_invest'] = (df['src_app'] == 'investment-dashboard').astype(float)
        
        df['dst_is_customer_api'] = (df['dst_app'] == 'customer-api').astype(float)
        df['dst_is_vault'] = (df['dst_app'] == 'vault-db').astype(float)

        self.dataframe = df.drop(columns=['verdict', 'src_app', 'dst_app', 'method', 'url'])
        print(f"🧠 Engineered Feature Matrix: {self.dataframe.shape[1]} dimensions.")

    def get_dataframe(self):
        return self.dataframe

    def save_raw_events(self, output_path):
        with open(output_path, 'w') as f:
            json.dump(self.raw_json_events, f, indent=4)
        print(f"💾 Saved {len(self.raw_json_events)} unique raw Hubble events to {output_path}")

class HubbleDataset(Dataset):
    def __init__(self, dataframe):
        self.data = torch.FloatTensor(dataframe.values)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        x = self.data[idx]
        return x, x

if __name__ == "__main__":
    import os
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_file = os.path.join(current_dir, "..", "data", "raw", "hubble_training_data.json")
    
    if os.path.exists(json_file):
        processor = HubbleDataProcessor(json_file)
        processor.load_and_filter()
        
        raw_out_path = os.path.join(current_dir, "..", "data", "raw", "hubble_filtered_raw.json")
        processor.save_raw_events(raw_out_path)
        
        processor.engineer_features()
        
        df = processor.get_dataframe()
        print("\n--- Preview of the Numerical Feature Tensor ---")
        print(df.head())
        
        torch_dataset = HubbleDataset(df)
        print(f"\n✅ PyTorch Dataset ready! Contains {len(torch_dataset)} exact samples.")
        
        tensor_path = os.path.join(current_dir, "..", "data", "processed", "training_tensor.pt")
        os.makedirs(os.path.dirname(tensor_path), exist_ok=True)
        torch.save(torch_dataset.data, tensor_path)
        print(f"💾 Saved PyTorch Tensor to {tensor_path}")
    else:
        print(f"❌ Could not find {json_file}. Did you run the extractor script?")