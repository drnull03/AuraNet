import os
import torch
import flwr as fl
import config
from strategy import AuraNetKrumStrategy

# We need a lightweight definition of the model just to extract the initial weights
import torch.nn as nn
class GenesisAutoencoder(nn.Module):
    def __init__(self, input_dim):
        super(GenesisAutoencoder, self).__init__()
        self.encoder = nn.Sequential(nn.Linear(input_dim, 16), nn.ReLU(True), nn.Linear(16, 2))
        self.decoder = nn.Sequential(nn.Linear(2, 16), nn.ReLU(True), nn.Linear(16, input_dim), nn.Sigmoid())

def get_genesis_parameters():
    """Loads the pre-trained weights to Warm-Start the Federated Network."""
    print("🧠 [Controller] Loading Genesis Weights for Warm Start...")
    
    # 13 dimensions based on our optimized dataset.py
    model = GenesisAutoencoder(input_dim=13) 
    
    if os.path.exists(config.GENESIS_WEIGHTS_PATH):
        model.load_state_dict(torch.load(config.GENESIS_WEIGHTS_PATH))
        print(f"✅ [Controller] Successfully loaded {config.GENESIS_WEIGHTS_PATH}")
    else:
        print(f"⚠️ [Controller] Genesis weights not found at {config.GENESIS_WEIGHTS_PATH}. Starting from scratch.")
        
    # Convert PyTorch weights to Flower's parameter format
    ndarrays = [val.cpu().numpy() for _, val in model.state_dict().items()]
    return fl.common.ndarrays_to_parameters(ndarrays)

def start_federated_server():
    print("\n🌐 [Controller] Initializing AuraNet FL Aggregator...")
    
    # 1. Prepare the Byzantine Fault Tolerant Strategy
    # Assuming up to 1 compromised agent per round. Adjust based on cluster size.
    strategy = AuraNetKrumStrategy(
        num_malicious_clients=1, 
        num_clients_to_keep=1,    # In a small cluster, we keep the 1 best median update
        fraction_fit=config.FRACTION_FIT,
        min_fit_clients=config.MIN_AVAILABLE_CLIENTS,
        min_available_clients=config.MIN_AVAILABLE_CLIENTS,
        initial_parameters=get_genesis_parameters()
    )

    # 2. Start the Flower gRPC Server
    print(f"🚀 [Controller] Starting gRPC Server on port 8080...")
    print(f"⏳ [Controller] Aggregation Throttle: 1 Round per {config.ROUND_TIMEOUT_SECONDS} seconds.\n")
    
    fl.server.start_server(
        server_address="0.0.0.0:8080",
        config=fl.server.ServerConfig(num_rounds=config.FL_ROUNDS),
        strategy=strategy,
    )

if __name__ == "__main__":
    start_federated_server()