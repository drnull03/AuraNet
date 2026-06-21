import os
import sys
import flwr as fl
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from collections import OrderedDict

import config
from dataset import HubbleDataProcessor, HubbleDataset
from model import ZeroTrustAutoencoder

# 1. Load Local Edge Data (Simulated)
processor = HubbleDataProcessor(config.TRAIN_DATA_PATH)
processor.load_and_filter()
processor.engineer_features()
df_train = processor.get_dataframe()
input_dim = df_train.shape[1]

train_loader = DataLoader(HubbleDataset(df_train), batch_size=8, shuffle=True)

# 2. Initialize Local Model
model = ZeroTrustAutoencoder(input_dim)
criterion = nn.MSELoss()
optimizer = optim.Adam(model.parameters(), lr=0.01)

# 3. Define the Flower Client
class AuraNetClient(fl.client.NumPyClient):
    def get_parameters(self, config):
        """Extracts the PyTorch weights and converts them to NumPy for transmission."""
        return [val.cpu().numpy() for _, val in model.state_dict().items()]

    def set_parameters(self, parameters):
        """Receives global NumPy weights from the Server and loads them into PyTorch."""
        params_dict = zip(model.state_dict().keys(), parameters)
        state_dict = OrderedDict({k: torch.tensor(v) for k, v in params_dict})
        model.load_state_dict(state_dict, strict=True)

    def fit(self, parameters, config):
        """Trains the model locally on the Edge Node's data."""
        self.set_parameters(parameters)
        
        # Train for 1 local epoch per federated round
        model.train()
        for batch_features, _ in train_loader:
            optimizer.zero_grad()
            loss = criterion(model(batch_features), batch_features)
            loss.backward()
            optimizer.step()
            
        # Return updated weights, number of local examples, and any extra metrics
        return self.get_parameters(config={}), len(train_loader.dataset), {}

    def evaluate(self, parameters, config):
        """Evaluates the global model on the Edge Node's local data."""
        self.set_parameters(parameters)
        model.eval()
        loss = 0.0
        
        with torch.no_grad():
            for batch_features, _ in train_loader:
                reconstructed = model(batch_features)
                loss += criterion(reconstructed, batch_features).item()
                
        mse = loss / len(train_loader)
        return float(mse), len(train_loader.dataset), {"mse": float(mse)}

if __name__ == "__main__":
    print("🛡️ Starting AuraNet FL Edge Client...")
    # Connect to our local server
    fl.client.start_client(server_address="127.0.0.1:8080", client=AuraNetClient().to_client())
