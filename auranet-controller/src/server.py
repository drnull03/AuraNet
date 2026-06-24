import os
import torch
import flwr as fl
import config

# Swap out the imports
# from strategy import AuraNetKrumStrategy
from strategy import AuraNetFedProxStrategy

import torch.nn as nn

class GenesisAutoencoder(nn.Module):
    def __init__(self, input_dim):
        super(GenesisAutoencoder, self).__init__()
        self.encoder = nn.Sequential(nn.Linear(input_dim, 16), nn.ReLU(True), nn.Linear(16, 2))
        self.decoder = nn.Sequential(nn.Linear(2, 16), nn.ReLU(True), nn.Linear(16, input_dim), nn.Sigmoid())

def get_genesis_parameters():
    """Loads the pre-trained weights to Warm-Start the Federated Network."""
    print("[Controller] Loading Genesis Weights for Warm Start...")
    
    model = GenesisAutoencoder(input_dim=13) 
    
    if os.path.exists(config.GENESIS_WEIGHTS_PATH):
        model.load_state_dict(torch.load(config.GENESIS_WEIGHTS_PATH))
        print(f"[Controller] Successfully loaded {config.GENESIS_WEIGHTS_PATH}")
    else:
        print(f"⚠️ [Controller] Genesis weights not found at {config.GENESIS_WEIGHTS_PATH}. Starting from scratch.")
        
    ndarrays = [val.cpu().numpy() for _, val in model.state_dict().items()]
    return fl.common.ndarrays_to_parameters(ndarrays)

def start_federated_server():
    print("\n [Controller] Initializing AuraNet FL Aggregator...")
    
    
    # DISABLED: Krum Strategy
   
    # strategy = AuraNetKrumStrategy(
    #     num_malicious_clients=1, 
    #     num_clients_to_keep=1,
    #     fraction_fit=config.FRACTION_FIT,
    #     min_fit_clients=config.MIN_AVAILABLE_CLIENTS,
    #     min_available_clients=config.MIN_AVAILABLE_CLIENTS,
    #     initial_parameters=get_genesis_parameters()
    # )

  
    # ACTIVE: FedProx Strategy
  
    strategy = AuraNetFedProxStrategy(
        proximal_mu=0.1,  # Proximal term to keep local updates from diverging
        fraction_fit=config.FRACTION_FIT,
        min_fit_clients=config.MIN_AVAILABLE_CLIENTS,
        min_available_clients=config.MIN_AVAILABLE_CLIENTS,
        initial_parameters=get_genesis_parameters()
    )

    print(f"🚀 [Controller] Starting gRPC Server on port 8080...")
    print(f"⏳ [Controller] Aggregation Throttle: 1 Round per {config.ROUND_TIMEOUT_SECONDS} seconds.\n")
    
    fl.server.start_server(
        server_address="0.0.0.0:8080",
        config=fl.server.ServerConfig(num_rounds=config.FL_ROUNDS),
        strategy=strategy,
    )

if __name__ == "__main__":
    start_federated_server()