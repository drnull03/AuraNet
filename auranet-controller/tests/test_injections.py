import os
import sys
import numpy as np
from unittest import mock
import flwr as fl
from flwr.common import ndarrays_to_parameters

# Ensure tests can find the src module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from strategy import AuraNetFedProxKrumStrategy

class MockClientProxy(fl.server.client_proxy.ClientProxy):
    def __init__(self, cid):
        super().__init__(cid)
    def get_properties(self, ins, timeout, group_id): pass
    def get_parameters(self, ins, timeout, group_id): pass
    def fit(self, ins, timeout, group_id): pass
    def evaluate(self, ins, timeout, group_id): pass
    def reconnect(self, ins, timeout, group_id): pass

@mock.patch('strategy.config')
def test_hybrid_strategy_injects_proximal_mu(mock_config):
    # Set a fake dynamic MU value
    mock_config.PROXIMAL_MU = 0.77
    mock_config.MIN_AVAILABLE_CLIENTS = 1
    mock_config.FRACTION_FIT = 1.0
    
    strategy = AuraNetFedProxKrumStrategy(
        num_malicious_clients=0, 
        num_clients_to_keep=1
    )
    
    # Create a mock client manager and register one client
    client_manager = fl.server.SimpleClientManager()
    client = MockClientProxy("Test_Agent")
    client_manager.register(client)
    
    # Generate dummy global parameters to pass down
    dummy_parameters = ndarrays_to_parameters([np.array([1.0])])
    
    # Trigger the configuration phase
    instructions = strategy.configure_fit(
        server_round=1, 
        parameters=dummy_parameters, 
        client_manager=client_manager
    )
    
    assert len(instructions) > 0, "No instructions generated for clients."
    
    # Extract the configuration dictionary sent to the first client
    _, fit_ins = instructions[0]
    
    assert "proximal_mu" in fit_ins.config, "proximal_mu was not injected into the client config payload."
    assert fit_ins.config["proximal_mu"] == 0.77, f"Expected MU 0.77, but got {fit_ins.config['proximal_mu']}"
