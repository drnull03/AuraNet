"""
@file fl_client.py
@brief AuraNet Federated Learning client.

Implements the edge-node Flower client responsible for exchanging
local model updates with the AuraNet Controller and synchronizing
global federated learning weights.
"""
import flwr as fl
import torch
import copy
from typing import Dict, List
import numpy as np

import config
"""
@brief Flower client implementation for AuraNet edge nodes.

Handles model parameter serialization, global weight updates,
and local model synchronization during federated learning rounds.
"""
class AuraNetFlowerClient(fl.client.NumPyClient):
    def __init__(self, model, model_lock, global_state):
        self.model = model
        self.model_lock = model_lock
        self.global_state = global_state
    """
@brief Extracts local model parameters.

Converts PyTorch tensors into NumPy arrays suitable for
Flower gRPC federated learning communication.

@param config Flower client configuration.
@return List of NumPy arrays containing model weights.
"""
    def get_parameters(self, config: Dict[str, fl.common.Scalar]) -> List[np.ndarray]:
        """Extracts the PyTorch tensors and converts them to NumPy for gRPC transport."""
        with self.model_lock:
            return [val.cpu().numpy() for _, val in self.model.state_dict().items()]
"""
@brief Applies global model parameters received from the controller.

Updates the local PyTorch model and stores a copy of the latest
global weights for local FedProx training.

@param parameters Global model weights from the aggregator.
@returns None
"""
def set_parameters(self, parameters: List[np.ndarray]):
    """Injects the new global weights from the server into the local PyTorch model."""
    params_dict = zip(self.model.state_dict().keys(), parameters)
    state_dict = dict({k: torch.tensor(np.copy(v)) for k, v in params_dict})

    with self.model_lock:
        self.model.load_state_dict(state_dict, strict=True)

        # Save a deep copy of the global weights to the shared state dictionary
        self.global_state["master_weights"] = copy.deepcopy(list(self.model.parameters()))
"""
@brief Executes one federated learning training round.

Receives the global model, performs local synchronization,
and returns local model updates to the AuraNet Controller.

@param parameters Global model parameters.
@param fl_config Federated learning configuration.
@return Updated parameters, sample count, and metrics.
"""
def fit(self, parameters: List[np.ndarray], fl_config: Dict[str, fl.common.Scalar]):
    """
        Triggered by the server every 10 minutes.
        """
    print("\n[Worker C]  Federated Round Triggered by Controller!")

    if not self.global_state.get("is_initialized", False):
        print("[Worker C]  First boot: Warm monolith received. Skipping upload to protect global model.")
        self.set_parameters(parameters)
        self.global_state["is_initialized"] = True

        # Return the exact parameters we just received
        return parameters, 1, {}

        # Standard Flow for Round 2 and beyond
        # Extract local training insights
        local_parameters = self.get_parameters(config={})
        print("[Worker C] Local training insights extracted.")

        # Hot-swap the new global brain
        self.set_parameters(parameters)
        print("[Worker C] New global brain successfully hot-swapped.")

        # Return local weights back to aggregator
        return local_parameters, 1, {}
"""
@brief Starts the AuraNet Flower client.

Creates the federated learning client and connects it to the
central AuraNet Controller.

@param model Local PyTorch model.
@param model_lock Synchronization lock for model access.
@param global_state Shared federated learning state.
@returns None
"""
def start_fl_client(model, model_lock, global_state):
    """Initializes and connects the Flower client to the central server."""
    client = AuraNetFlowerClient(model, model_lock, global_state)

    print(f"[Worker C] 🔌 Connecting to AuraNet Aggregator at {config.FL_SERVER_ADDRESS}...")

    fl.client.start_numpy_client(
        server_address=config.FL_SERVER_ADDRESS,
        client=client,
    )