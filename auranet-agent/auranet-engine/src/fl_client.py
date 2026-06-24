import flwr as fl
import torch
import copy
from typing import Dict, List

import config

class AuraNetFlowerClient(fl.client.NumPyClient):
    def __init__(self, model, model_lock, global_state):
        self.model = model
        self.model_lock = model_lock
        self.global_state = global_state

    def get_parameters(self, config: Dict[str, fl.common.Scalar]) -> List[np.ndarray]:
        """Extracts the PyTorch tensors and converts them to NumPy for gRPC transport."""
        with self.model_lock:
            return [val.cpu().numpy() for _, val in self.model.state_dict().items()]

    def set_parameters(self, parameters: List[np.ndarray]):
        """Injects the new global weights from the server into the local PyTorch model."""
        params_dict = zip(self.model.state_dict().keys(), parameters)
        state_dict = dict({k: torch.tensor(v) for k, v in params_dict})
        
        with self.model_lock:
            self.model.load_state_dict(state_dict, strict=True)
            
            # Save a deep copy of the global weights to the shared state dictionary
            # Worker B uses this later to calculate the FedProx Proximal penalty!
            self.global_state["master_weights"] = copy.deepcopy(list(self.model.parameters()))

    def fit(self, parameters: List[np.ndarray], fl_config: Dict[str, fl.common.Scalar]):
        """
        Triggered by the server every 10 minutes. 
        Because our training is handled asynchronously by Worker B, this method 
        just performs a hot-swap of the weights and immediately returns the latest local state.
        """
        print("\n[Worker C] 🌐 Federated Round Triggered by Controller!")
        print("[Worker C] 📥 Downloading new global brain...")
        
        # Hot-swap the new global weights into our local model
        self.set_parameters(parameters)
        print("[Worker C] ✅ Global weights successfully hot-swapped.")

        # Extract our current local weights to send back to the aggregator
        local_parameters = self.get_parameters(config={})
        
        #Return the weights, the size of our dataset (used for weighted averaging), and metrics
        # We hardcode num_examples to 1 for the demo so all nodes carry equal weight
        return local_parameters, 1, {}

def start_fl_client(model, model_lock, global_state):
    """Initializes and connects the Flower client to the central server."""
    client = AuraNetFlowerClient(model, model_lock, global_state)
    
    print(f"[Worker C] 🔌 Connecting to AuraNet Aggregator at {config.FL_SERVER_ADDRESS}...")
    
    fl.client.start_numpy_client(
        server_address=config.FL_SERVER_ADDRESS,
        client=client,
    )