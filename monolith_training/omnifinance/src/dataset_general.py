import json
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

        self.MAX_PATH_DEPTH = 10.0
        self.MAX_QUERY_PARAMS = 10.0
        self.MAX_HEADER_SIZE = 8192.0 
        self.MAX_URL_LENGTH = 500.0   

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
                
                if not (verdict == "DROPPED" or is_http_l7 or is_db_l4):
                    continue

                traffic_direction = flow.get("traffic_direction", "UNKNOWN")
                ip_source = flow.get("IP", {}).get("source", "")

                http_data = l7.get("http", {}) if l7 else {}
                method = http_data.get("method", "")
                url = http_data.get("url", "")
                status_code = http_data.get("code", 0)
                
                headers = http_data.get("headers", [])
                header_size = sum(len(h.get("key", "")) + len(h.get("value", "")) for h in headers)

                self.raw_json_events.append(event)

                filtered_events.append({
                    "traffic_direction": traffic_direction,
                    "ip_source": ip_source,
                    "verdict": verdict,
                    "is_http": 1 if is_http_l7 else 0,
                    "method": method,
                    "url": url,
                    "status_code": status_code,
                    "header_size": header_size
                })

        print(f"✅ Filtered down to {len(filtered_events)} pure, relevant network events.")
        self.raw_data = filtered_events

    def is_external_ip(self, ip_str):
        if not ip_str: return 0.0
        if ip_str.startswith("10.") or ip_str.startswith("192.168.") or ip_str.startswith("172."):
            return 0.0
        return 1.0

    def engineer_features(self):
        df = pd.DataFrame(self.raw_data)
        
        # --- L3 Network Baseline ---
        df['is_inbound'] = (df['traffic_direction'] == 'INGRESS').astype(float)
        df['is_outbound'] = (df['traffic_direction'] == 'EGRESS').astype(float)
        df['is_external_ip'] = df['ip_source'].apply(self.is_external_ip)
        
        # --- Zero Trust Policy ---
        df['is_dropped'] = (df['verdict'] == 'DROPPED').astype(float)
        
        valid_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS', '']
        df['is_unknown_method'] = (~df['method'].isin(valid_methods)).astype(float)

        # --- L7 HTTP Structural Metadata ---
        df['is_http'] = df['is_http'].astype(float)
        
        df['is_read_method'] = df['method'].isin(['GET', 'OPTIONS', 'HEAD']).astype(float)
        df['is_write_method'] = df['method'].isin(['POST', 'PUT', 'DELETE', 'PATCH']).astype(float)
        
        df['url_path_depth'] = df['url'].apply(lambda x: str(x).count('/'))
        df['query_param_count'] = df['url'].apply(lambda x: str(x).count('&') + 1 if '?' in str(x) else 0)
        
        df['url_path_depth'] = np.clip(df['url_path_depth'] / self.MAX_PATH_DEPTH, 0.0, 1.0)
        df['query_param_count'] = np.clip(df['query_param_count'] / self.MAX_QUERY_PARAMS, 0.0, 1.0)
        df['req_header_size'] = np.clip(df['header_size'] / self.MAX_HEADER_SIZE, 0.0, 1.0)
        
        # REPLACED req_body_size WITH url_length
        df['url_length'] = df['url'].apply(lambda x: len(str(x)))
        df['url_length'] = np.clip(df['url_length'] / self.MAX_URL_LENGTH, 0.0, 1.0)
        
        df['is_error_status'] = (df['status_code'] >= 400).astype(float)

        cols_to_drop = ['traffic_direction', 'ip_source', 'verdict', 'method', 'url', 'status_code', 'header_size']
        self.dataframe = df.drop(columns=cols_to_drop)
        
        print(f"🧠 Engineered Universal Feature Matrix: {self.dataframe.shape[1]} dimensions.")

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
        print("\n=== Preview of the Universal Vector Space ===")
        print(df.head())
        
        torch_dataset = HubbleDataset(df)
        print(f"\n✅ PyTorch Dataset ready! Contains {len(torch_dataset)} exact behavioral samples.")
        
        tensor_path = os.path.join(current_dir, "..", "data", "processed", "training_tensor.pt")
        os.makedirs(os.path.dirname(tensor_path), exist_ok=True)
        torch.save(torch_dataset.data, tensor_path)
        print(f"💾 Saved PyTorch Tensor to {tensor_path}")