import json
import os
import torch
import numpy as np
from torch.utils.data import Dataset

class NlpDataProcessor:
    def __init__(self, json_path, max_seq_length=150):
        self.json_path = json_path
        self.max_seq_length = max_seq_length
        self.urls = []
        self.tensor_data = None

    def load_and_tokenize(self):
        print(f"📖 Reading raw URLs from {self.json_path}...")
        
        with open(self.json_path, 'r') as f:
            for line in f:
                if not line.strip(): continue
                
                try:
                    event = json.loads(line)
                    flow = event.get("flow", {})
                    l7 = flow.get("l7", {})
                except Exception:
                    continue

                # Only process HTTP Requests
                if not l7 or l7.get("type") == "RESPONSE":
                    continue
                    
                url = l7.get("http", {}).get("url", "")
                if url:
                    self.urls.append(url)

        print(f"✅ Extracted {len(self.urls)} HTTP URLs.")
        self._build_tensor()

    def _build_tensor(self):
        """Converts strings to ASCII integers and pads them to max_seq_length."""
        tokenized_list = []
        
        for url in self.urls:
            # Convert each character to its ASCII integer (cap at 127)
            encoded = [min(ord(c), 127) for c in url]
            
            # Truncate if it exceeds max length
            encoded = encoded[:self.max_seq_length]
            
            # Pad with 0s if it's shorter than max length
            padding = [0] * (self.max_seq_length - len(encoded))
            final_sequence = encoded + padding
            
            tokenized_list.append(final_sequence)
            
        self.tensor_data = torch.LongTensor(tokenized_list)
        print(f"🧠 NLP Tensor built: {self.tensor_data.shape}")

class NlpDataset(Dataset):
    def __init__(self, tensor_data):
        self.data = tensor_data

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        x = self.data[idx]
        return x, x  # Autoencoder predicts the input

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_train = os.path.join(current_dir, "../../data/raw/hubble_training_data.json")
    json_test = os.path.join(current_dir, "../../data/raw/hubble_testing_data.json")
    
    out_dir = os.path.join(current_dir, "../../data/processed/nlp")
    os.makedirs(out_dir, exist_ok=True)

    # Process Training URLs
    if os.path.exists(json_train):
        processor = NlpDataProcessor(json_train)
        processor.load_and_tokenize()
        torch.save(processor.tensor_data, os.path.join(out_dir, "nlp_train_tensor.pt"))
        print(f"💾 Saved Train Tensor to {out_dir}/nlp_train_tensor.pt")

    # Process Testing URLs
    if os.path.exists(json_test):
        processor = NlpDataProcessor(json_test)
        processor.load_and_tokenize()
        torch.save(processor.tensor_data, os.path.join(out_dir, "nlp_test_tensor.pt"))
        print(f"💾 Saved Test Tensor to {out_dir}/nlp_test_tensor.pt")