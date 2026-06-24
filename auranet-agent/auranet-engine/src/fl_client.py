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
        """
        print("\n[Worker C] 🌐 Federated Round Triggered by Controller!")
        
        # 1. FIRST: Extract our current local weights (the ones Worker B has been training)
        local_parameters = self.get_parameters(config={})
        print("[Worker C] 📤 Local training insights extracted.")
        
        # 2. SECOND: Hot-swap the new global weights from the server into our local model
        self.set_parameters(parameters)
        print("[Worker C] 📥 New global brain successfully hot-swapped.")

        # 3. Return our extracted local weights back to the aggregator
        # We hardcode num_examples to 1 for the demo so all nodes carry equal weight
        return local_parameters, 1, {}
def start_fl_client(model, model_lock, global_state):
    """Initializes and connects the Flower client to the central server."""
    client = AuraNetFlowerClient(model, model_lock, global_state)
    
    print(f"[Worker C]  Connecting to AuraNet Aggregator at {config.FL_SERVER_ADDRESS}...")
    
    fl.client.start_numpy_client(
        server_address=config.FL_SERVER_ADDRESS,
        client=client,
    )