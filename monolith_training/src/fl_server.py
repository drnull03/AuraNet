import flwr as fl

def main():
    print("🚀 Starting AuraNet Federated Server...")
    
    # We use FedProx to aggregate weights. 
    # The proximal_mu parameter keeps heterogeneous edge nodes from diverging too wildly.
    strategy = fl.server.strategy.FedProx(
        fraction_fit=1.0,           # Sample 100% of available clients for training
        fraction_evaluate=1.0,      # Sample 100% of available clients for evaluation
        min_fit_clients=2,          # Wait until at least 2 edge nodes connect to train
        min_evaluate_clients=2,     # Wait until at least 2 edge nodes connect to evaluate
        min_available_clients=2,    # Wait until 2 total clients are in the pool
        proximal_mu=0.1             # The proximal penalty term
    )
    
    # Start the server on localhost port 8080 for 3 full Federated Learning rounds
    fl.server.start_server(
        server_address="0.0.0.0:8080",api-gateway
        config=fl.server.ServerConfig(num_rounds=3),
        strategy=strategy,
    )

if __name__ == "__main__":
    main()