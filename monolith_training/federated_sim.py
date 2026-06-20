import collections
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
import flwr as fl
from flwr.common import Context

# Import your exact configuration and model from the src folder
import src.config as config
from src.model import ZeroTrustAutoencoder

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def load_federated_datasets():
    print(f"Loading training tensor from: {config.PROCESSED_TENSOR_PATH}")
    train_tensor = torch.load(config.PROCESSED_TENSOR_PATH, map_location=device)
    
    # Split the pre-processed tensor exactly in half for the 2 simulated nodes
    midpoint = len(train_tensor) // 2
    node1_tensor = train_tensor[:midpoint]
    node2_tensor = train_tensor[midpoint:]
    
    # Wrap them into TensorDatasets (Autoencoders use input as target)
    node1_dataset = TensorDataset(node1_tensor, node1_tensor)
    node2_dataset = TensorDataset(node2_tensor, node2_tensor)
    
    return node1_dataset, node2_dataset

node1_data, node2_data = load_federated_datasets()


def get_parameters(net) -> list[np.ndarray]:
    return [val.cpu().numpy() for _, val in net.state_dict().items()]

def set_parameters(net, parameters: list[np.ndarray]):
    params_dict = zip(net.state_dict().keys(), parameters)
    state_dict = collections.OrderedDict({k: torch.tensor(v) for k, v in params_dict})
    net.load_state_dict(state_dict, strict=True)

class ZeroTrustClient(fl.client.NumPyClient):
    def __init__(self, dataset):
        self.dataset = dataset
        self.model = ZeroTrustAutoencoder(input_dim=9).to(device)
        self.criterion = nn.MSELoss()

    def fit(self, parameters, flwr_config):
        set_parameters(self.model, parameters)
        
        # Pull FedProx mu from strategy config
        mu = flwr_config.get("proximal_mu", 0.1)
        
        # Keep frozen snapshot of global weights for proximal penalty calculation
        global_model = ZeroTrustAutoencoder(input_dim=9).to(device)
        set_parameters(global_model, parameters)
        
        # Use hyperparameters straight from your config
        optimizer = optim.Adam(self.model.parameters(), lr=config.LEARNING_RATE)
        train_loader = DataLoader(self.dataset, batch_size=config.BATCH_SIZE, shuffle=True)
        
        self.model.train()
        # Simulating 5 local epochs per federated round
        for epoch in range(5):
            for inputs, targets in train_loader:
                inputs, targets = inputs.to(device), targets.to(device)
                optimizer.zero_grad()
                
                outputs = self.model(inputs)
                loss = self.criterion(outputs, targets)
                
                # FedProx Proximal Term calculation
                proximal_term = 0.0
                for local_p, global_p in zip(self.model.parameters(), global_model.parameters()):
                    proximal_term += (local_p - global_p).norm(2) ** 2
                
                total_loss = loss + (mu / 2) * proximal_term
                total_loss.backward()
                optimizer.step()
                
        return get_parameters(self.model), len(self.dataset), {}

    def evaluate(self, parameters, flwr_config):
        # We rely on server aggregation metrics, skipping local evaluation steps
        return float(0.0), len(self.dataset), {}

# ==========================================
# 4. NODE SPAWNER (UPDATED FOR FLOWER 1.8+)
# ==========================================
def client_fn(context: Context) -> fl.client.Client:
    # Flower now uses a Context object which contains a numeric node_id
    node_id = context.node_id
    if node_id == 0:
        return ZeroTrustClient(node1_data).to_client()
    else:
        return ZeroTrustClient(node2_data).to_client()

# ==========================================
# 5. RUN SIMULATION
# ==========================================
if __name__ == "__main__":
    
    print("Generating initial global model weights for the Server...")
    initial_model = ZeroTrustAutoencoder(input_dim=9).to(device)
    initial_weights = get_parameters(initial_model)
    initial_parameters = fl.common.ndarrays_to_parameters(initial_weights)

    strategy = fl.server.strategy.FedProx(
        proximal_mu=0.1,
        fraction_fit=1.0,
        min_fit_clients=2,
        min_available_clients=2,
        initial_parameters=initial_parameters 
    )
    
    # FIX: Define how much system power each simulated node is allowed to use.
    # If you are running out of memory, setting num_cpus to 1 prevents Ray from 
    # aggressively parallelizing and crashing the system.
    # If you are using a GPU, set "num_gpus": 0.5 so both nodes share the single GPU.
    # If you are strictly on CPU, set "num_gpus": 0.0
    client_resources = {
        "num_cpus": 1,
        "num_gpus": 0.0 # Change to 0.5 ONLY if you have an Nvidia GPU setup
    }
    
    print("Starting ZeroTrust Federated Server Simulation...")
    print(f"Using baseline configurations: Batch Size={config.BATCH_SIZE}, LR={config.LEARNING_RATE}")
    
    fl.simulation.start_simulation(
        client_fn=client_fn,
        num_clients=2,
        config=fl.server.ServerConfig(num_rounds=5),
        strategy=strategy,
        client_resources=client_resources # <--- Inject the limits here
    )