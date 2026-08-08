"""
@file server.py
@brief AuraNet Federated Learning Controller.

Starts the Flower federated learning server, initializes the aggregation
strategy, loads the Genesis model for warm-start training, and coordinates
global model aggregation across all participating AuraNet edge agents.
"""
import os
import torch
import flwr as fl
import config

#from strategy import AuraNetFedProxStrategy
from strategy import AuraNetFedProxKrumStrategy
import torch.nn as nn
"""
@brief Initial global autoencoder model used for federated learning.

Provides the initial neural network architecture whose pretrained
weights are distributed to participating edge agents during
the first federated learning round.
"""
class GenesisAutoencoder(nn.Module):
    def __init__(self, input_dim):
        super(GenesisAutoencoder, self).__init__()
        
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 16),
            nn.ReLU(True),
            nn.Linear(16, 8),
            nn.ReLU(True),
            nn.Linear(8, 4)  # 4-dimensional latent space
        )
        
        self.decoder = nn.Sequential(
            nn.Linear(4, 8),
            nn.ReLU(True),
            nn.Linear(8, 16),
            nn.ReLU(True),
            nn.Linear(16, input_dim),
            nn.Sigmoid()
        )
"""
@brief Loads the Genesis model parameters for warm-start training.

Initializes the global model using pretrained weights when available.
If no pretrained model exists, the federated learning process starts
from randomly initialized parameters.

@return Flower Parameters object containing the initial global model.
"""
def get_genesis_parameters():
    """Loads the pre-trained weights to Warm-Start the Federated Network."""
    print("[Controller] Loading Genesis Weights for Warm Start...")
    
    model = GenesisAutoencoder(input_dim=config.INPUT_DIM) 
    
    if os.path.exists(config.GENESIS_WEIGHTS_PATH):
        model.load_state_dict(torch.load(config.GENESIS_WEIGHTS_PATH))
        print(f"[Controller] Successfully loaded {config.GENESIS_WEIGHTS_PATH}")
    else:
        print(f"⚠️ [Controller] Genesis weights not found at {config.GENESIS_WEIGHTS_PATH}. Starting from scratch.")
        
    ndarrays = [val.cpu().numpy() for _, val in model.state_dict().items()]
    return fl.common.ndarrays_to_parameters(ndarrays)
"""
@brief Starts the AuraNet Federated Learning Controller.

Initializes the FedProx aggregation strategy, configures the Flower
server, and begins coordinating federated learning rounds with all
connected AuraNet edge agents.

@return None
"""
"""
def start_federated_server():
    print("\n [Controller] Initializing AuraNet FL Aggregator...")
    
    strategy = AuraNetFedProxStrategy(
        proximal_mu=config.PROXIMAL_MU,  
        fraction_fit=config.FRACTION_FIT,
        min_fit_clients=config.MIN_AVAILABLE_CLIENTS,
        min_available_clients=config.MIN_AVAILABLE_CLIENTS,
        initial_parameters=get_genesis_parameters()
    )

    print(f"[Controller] Starting gRPC Server on port 8080...")
    print(f"[Controller] Aggregation Throttle: 1 Round per {config.ROUND_TIMEOUT_SECONDS} seconds.\n")
    
    fl.server.start_server(
        server_address="0.0.0.0:8080",
        config=fl.server.ServerConfig(num_rounds=config.FL_ROUNDS),
        strategy=strategy,
    )
"""

def start_federated_server():
    print("\n [Controller] Initializing AuraNet FL Aggregator...")
    
    strategy = AuraNetFedProxKrumStrategy(
        num_malicious_clients=1,   # Number of expected compromised nodes
        num_clients_to_keep=1,     # Number of benign updates to aggregate
        initial_parameters=get_genesis_parameters()
    )

    print(f"[Controller] Starting gRPC Server on port 8080...")
    print(f"[Controller] Aggregation Throttle: 1 Round per {config.ROUND_TIMEOUT_SECONDS} seconds.\n")
    
    fl.server.start_server(
        server_address="0.0.0.0:8080",
        config=fl.server.ServerConfig(num_rounds=config.FL_ROUNDS),
        strategy=strategy,
    )


if __name__ == "__main__":
    start_federated_server()