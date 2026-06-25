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

        # STATELESS SCALING 
        # Mandatory for ensuring live edge inference perfectly matches notebook training
        self.MAX_PATH_DEPTH = 10.0
        self.MAX_QUERY_PARAMS = 10.0
        self.MAX_HEADER_SIZE = 8192.0 # 8KB is a standard web server limit

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
                
                # Drop Kubelet health probes
                if "reserved:host" in source_labels:
                    continue
                
                #  Prevent Double-Logging
                if verdict == "DROPPED" and event_type != 1:
                    continue
                    
                # Ignore SPIRE mTLS Handshake Drops (Normal Zero Trust operations)
                if verdict == "DROPPED" and drop_reason == "AUTH_REQUIRED":
                    continue

                traffic_direction = flow.get("traffic_direction", "UNKNOWN")
                ip_source = flow.get("IP", {}).get("source", "")
                
                tcp_flags = flow.get("l4", {}).get("TCP", {}).get("flags", {})
                is_syn = tcp_flags.get("SYN", False)
                is_rst = tcp_flags.get("RST", False)
                
                l7 = flow.get("l7", {})
                is_http = 1 if (l7 and "http" in l7) else 0

                http_data = l7.get("http", {}) if l7 else {}
                method = http_data.get("method", "")
                url = http_data.get("url", "")
                status_code = http_data.get("code", 0)
                
                # Calculate raw header sizes
                headers = http_data.get("headers", [])
                header_size = sum(len(h.get("key", "")) + len(h.get("value", "")) for h in headers)

                self.raw_json_events.append(event)

                filtered_events.append({
                    "traffic_direction": traffic_direction,
                    "ip_source": ip_source,
                    "is_syn": is_syn,
                    "is_rst": is_rst,
                    "is_http": is_http,
                    "method": method,
                    "url": url,
                    "status_code": status_code,
                    "header_size": header_size
                })

        print(f"✅ Filtered down to {len(filtered_events)} pure, relevant network events.")
        self.raw_data = filtered_events

    def is_external_ip(self, ip_str):
        """Simple heuristic: If it doesn't match standard K8s internal CIDRs, it's external."""
        if not ip_str: return 0.0
        if ip_str.startswith("10.") or ip_str.startswith("192.168.") or ip_str.startswith("172."):
            return 0.0
        return 1.0

    def engineer_features(self):
        df = pd.DataFrame(self.raw_data)
        
       
        
        #  L3/L4 Network Baseline 
        df['is_inbound'] = (df['traffic_direction'] == 'INGRESS').astype(float)
        df['is_outbound'] = (df['traffic_direction'] == 'EGRESS').astype(float)
        df['is_external_ip'] = df['ip_source'].apply(self.is_external_ip)
        df['is_tcp_syn'] = df['is_syn'].astype(float)
        df['is_tcp_rst'] = df['is_rst'].astype(float)

        #  L7 HTTP Structural Metadata 
        df['is_http'] = df['is_http'].astype(float)
        
        df['is_read_method'] = df['method'].isin(['GET', 'OPTIONS', 'HEAD']).astype(float)
        df['is_write_method'] = df['method'].isin(['POST', 'PUT', 'DELETE', 'PATCH']).astype(float)
        
        df['url_path_depth'] = df['url'].apply(lambda x: str(x).count('/'))
        df['query_param_count'] = df['url'].apply(lambda x: str(x).count('&') + 1 if '?' in str(x) else 0)
        
        #  Stateless Scaling (Bounding values to [0, 1]) 
        df['url_path_depth'] = np.clip(df['url_path_depth'] / self.MAX_PATH_DEPTH, 0.0, 1.0)
        df['query_param_count'] = np.clip(df['query_param_count'] / self.MAX_QUERY_PARAMS, 0.0, 1.0)
        df['req_header_size'] = np.clip(df['header_size'] / self.MAX_HEADER_SIZE, 0.0, 1.0)
        
        # Note: Hubble does not consistently log request body sizes in the standard JSON dump without heavy eBPF overhead.
        # We set this to a static 0.0 for now to maintain the 13-dim mathematical shape. 
        df['req_body_size'] = 0.0 
        
        df['is_error_status'] = (df['status_code'] >= 400).astype(float)

        # Drop the raw string columns
        cols_to_drop = ['traffic_direction', 'ip_source', 'is_syn', 'is_rst', 'method', 'url', 'status_code', 'header_size']
        self.dataframe = df.drop(columns=cols_to_drop)
        
        print(f"🧠 Engineered Universal Feature Matrix: {self.dataframe.shape[1]} dimensions.")

    def get_dataframe(self):
        return self.dataframe

class HubbleDataset(Dataset):
    def __init__(self, dataframe):
        # Convert the strictly numerical DataFrame into a PyTorch FloatTensor
        self.data = torch.FloatTensor(dataframe.values)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        # Autoencoders map X to X
        x = self.data[idx]
        return x, x

if __name__ == "__main__":
    import os
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_file = os.path.join(current_dir, "..", "data", "raw", "hubble_training_data.json")
    
    if os.path.exists(json_file):
        processor = HubbleDataProcessor(json_file)
        processor.load_and_filter()
        processor.engineer_features()
        
        df = processor.get_dataframe()
        print("\n=== Preview of the Universal Vector Space ===")
        print(df.head())
        
        torch_dataset = HubbleDataset(df)
        print(f"\n PyTorch Dataset ready! Contains {len(torch_dataset)} exact behavioral samples.")
        
        tensor_path = os.path.join(current_dir, "..", "data", "processed", "training_tensor.pt")
        os.makedirs(os.path.dirname(tensor_path), exist_ok=True)
        torch.save(torch_dataset.data, tensor_path)
        print(f" Saved PyTorch Tensor to {tensor_path}")
    else:
        print(f"Could not find {json_file}. Did you extract the Hubble data?")