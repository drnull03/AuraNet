import numpy as np
import flwr as fl
from flwr.common import FitRes, Status, Code, ndarrays_to_parameters, parameters_to_ndarrays
from strategy import AuraNetKrumStrategy

# A dummy client proxy to simulate our auranet-engine edge nodes
class MockClientProxy(fl.server.client_proxy.ClientProxy):
    def __init__(self, cid):
        super().__init__(cid)
    def get_properties(self, ins, timeout, group_id): pass
    def get_parameters(self, ins, timeout, group_id): pass
    def fit(self, ins, timeout, group_id): pass
    def evaluate(self, ins, timeout, group_id): pass
    def reconnect(self, ins, timeout, group_id): pass

def create_mock_fit_res(weights_array):
    """Wraps raw numpy weights into Flower's gRPC payload format."""
    return FitRes(
        status=Status(code=Code.OK, message=""),
        parameters=ndarrays_to_parameters(weights_array),
        num_examples=100, # Assume each node trained on 100 HTTP requests
        metrics={}
    )

def test_krum_rejects_poisoned_weights():
    # Initialize the strategy: Expect 1 attacker, keep the 1 best central update
    strategy = AuraNetKrumStrategy(
        num_malicious_clients=1, 
        num_clients_to_keep=1
    )

    # 1. Simulate Benign Agents (Weights hovering around ~1.0)
    agent_a_weights = [np.array([[1.0, 1.1], [1.0, 1.1]])]
    agent_b_weights = [np.array([[1.1, 1.0], [1.1, 1.0]])]

    # 2. Simulate Compromised Agent (Data Poisoning Attack - Weights spiked to 99.0)
    attacker_weights = [np.array([[99.0, 99.0], [99.0, 99.0]])]

    # 3. Package the simulated payloads as they would arrive over the network
    results = [
        (MockClientProxy("Agent_A"), create_mock_fit_res(agent_a_weights)),
        (MockClientProxy("Agent_B"), create_mock_fit_res(agent_b_weights)),
        (MockClientProxy("Attacker_Node"), create_mock_fit_res(attacker_weights))
    ]

    # 4. Trigger the Aggregator
    aggregated_params, _ = strategy.aggregate_fit(server_round=1, results=results, failures=[])

    # 5. Extract the resulting global master weights
    assert aggregated_params is not None, "Aggregation failed and returned None"
    global_weights = parameters_to_ndarrays(aggregated_params)

    # 6. ASSERTION: The global weights MUST be immune to the attacker's 99.0 spike
    # Krum should have selected one of the benign arrays (values ~1.0)
    max_weight_value = np.max(global_weights[0])
    
    print(f"\n[Test Result] Max aggregated weight: {max_weight_value}")
    assert max_weight_value < 2.0, "🚨 CRITICAL: Krum failed to reject the poisoned update!"
