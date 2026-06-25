import json
import re
import pandas as pd
import numpy as np
import torch
from torch.utils.data import Dataset

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
                
                if "reserved:host" in source_labels:
                    continue
                
                if verdict == "DROPPED" and event_type != 1:
                    continue
                    
                if verdict == "DROPPED" and drop_reason == "AUTH_REQUIRED":
                    continue

                l7 = flow.get("l7", {})
                raw_port = flow.get("destination", {}).get("port")
                try:
                    dst_port = int(raw_port) if raw_port else 0
                except ValueError:
                    dst_port = 0

                tcp_flags = flow.get("l4", {}).get("TCP", {}).get("flags", {})
                is_syn = tcp_flags.get("SYN", False)
                is_ack = tcp_flags.get("ACK", False)
                
                if l7 and l7.get("type") == "RESPONSE":
                    continue

                is_http_l7 = verdict == "FORWARDED" and l7 and "http" in l7
                is_db_l4 = verdict == "FORWARDED" and dst_port == 5432 and is_syn and not is_ack
                
                if verdict == "DROPPED" or is_http_l7 or is_db_l4:
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
                        "url": url,
                        "dst_port": dst_port
                    })

        print(f"✅ Filtered down to {len(filtered_events)} pure, relevant network events.")
        self.raw_data = filtered_events

    def engineer_features(self):
        df = pd.DataFrame(self.raw_data)
        
        # Target Label
        df['is_dropped'] = (df['verdict'] == 'DROPPED').astype(float)
        
        # Path Validations
        acc_regex = re.compile(r"^.*/api/accounts\?id=[0-9]+$")
        loan_regex = re.compile(r"^.*/api/loans/export\?id=L-[0-9]+$")
        
        df['is_valid_acc_path'] = df['url'].apply(lambda x: 1.0 if acc_regex.match(str(x)) else 0.0)
        df['is_valid_loan_path'] = df['url'].apply(lambda x: 1.0 if loan_regex.match(str(x)) else 0.0)
        
        # Request Types
        df['is_get'] = (df['method'] == 'GET').astype(float)
        df['is_db_traffic'] = (df['dst_port'] == 5432).astype(float)
        
        # Source Pod Matrix
        df['src_is_frontend'] = (df['src_app'] == 'frontend-ui').astype(float)
        df['src_is_gateway'] = (df['src_app'] == 'api-gateway').astype(float)
        df['src_is_account'] = (df['src_app'] == 'account-service').astype(float)
        df['src_is_loan'] = (df['src_app'] == 'loan-service').astype(float)
        
        # Destination Pod Matrix
        df['dst_is_gateway'] = (df['dst_app'] == 'api-gateway').astype(float)
        df['dst_is_account'] = (df['dst_app'] == 'account-service').astype(float)
        df['dst_is_loan'] = (df['dst_app'] == 'loan-service').astype(float)
        df['dst_is_db'] = (df['dst_app'] == 'finance-db').astype(float)

        self.dataframe = df.drop(columns=['verdict', 'src_app', 'dst_app', 'method', 'url', 'dst_port'])
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
    json_file = os.path.join(current_dir, "..", "data", "raw", "hubble_data.json")
    
    if os.path.exists(json_file):
        processor = HubbleDataProcessor(json_file)
        processor.load_and_filter()
        
        raw_out_path = os.path.join(current_dir, "..", "data", "raw", "hubble_filtered_raw.json")
        processor.save_raw_events(raw_out_path)
        
        processor.engineer_features()
        
        df = processor.get_dataframe()
        print("\nPreview of the Numerical Feature Tensor ")
        print(df.head())
        
        torch_dataset = HubbleDataset(df)
        print(f"\n✅ PyTorch Dataset ready! Contains {len(torch_dataset)} exact samples.")
        
        tensor_path = os.path.join(current_dir, "..", "data", "processed", "training_tensor.pt")
        os.makedirs(os.path.dirname(tensor_path), exist_ok=True)
        torch.save(torch_dataset.data, tensor_path)
        print(f"💾 Saved PyTorch Tensor to {tensor_path}")