"""
@file strategy.py
@brief Federated learning aggregation strategies for the AuraNet Controller.

Defines the aggregation strategy used by the AuraNet Federated Learning
Controller. The current implementation extends Flower's FedProx strategy
to introduce controlled aggregation intervals between training rounds.
"""
import time
import flwr as fl
from typing import List, Tuple, Union, Optional, Dict
from flwr.common import FitRes, Parameters, Scalar, FitIns
from flwr.server.client_proxy import ClientProxy

import config

"""
@brief Custom FedProx aggregation strategy for AuraNet.

Extends Flower's built-in FedProx strategy by introducing a configurable
delay between federated learning rounds. This allows edge agents
sufficient time to perform local training before the next global model
distribution.
"""
class AuraNetFedProxStrategy(fl.server.strategy.FedProx):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def configure_fit(
        self, server_round: int, parameters: Parameters, client_manager: fl.server.ClientManager
    ) -> List[Tuple[ClientProxy, FitIns]]:
        """
        Executes at the start of every round. 
        We pull the latest variables from Python memory (updated by the file watcher)
        and overwrite the strategy's internal state before it samples clients.
        """
        # Inject dynamic values into the strategy instance
        self.proximal_mu = config.PROXIMAL_MU
        self.fraction_fit = config.FRACTION_FIT
        self.min_fit_clients = config.MIN_AVAILABLE_CLIENTS
        self.min_available_clients = config.MIN_AVAILABLE_CLIENTS
        
        print(f"\n[Controller] Starting Round {server_round} Configuration:")
        print(f"  -> MU: {self.proximal_mu}")
        print(f"  -> Fraction Fit: {self.fraction_fit}")
        print(f"  -> Min Clients: {self.min_fit_clients}")

        # Now call the parent class, which will use the newly updated self.fraction_fit 
        # to determine how many clients to sample for this specific round.
        return super().configure_fit(server_round, parameters, client_manager)

    def aggregate_fit(
        self,
        server_round: int,
        results: List[Tuple[ClientProxy, FitRes]],
        failures: List[Union[Tuple[ClientProxy, FitRes], BaseException]],
    ) -> Tuple[Optional[Parameters], Dict[str, Scalar]]:
        
        print(f"\n[Controller] Aggregating weights for Round {server_round}...")
        
        aggregated_parameters, aggregated_metrics = super().aggregate_fit(
            server_round, results, failures
        )

        if aggregated_parameters is not None:
            print(f"[Controller] Round {server_round} Aggregation Complete.")
            
            if server_round < config.FL_ROUNDS:
                print(f"[Controller] Throttling network. Sleeping for {config.ROUND_TIMEOUT_SECONDS} seconds...")
                # Dynamically uses the latest timeout value pulled by the watcher
                time.sleep(config.ROUND_TIMEOUT_SECONDS)
        else:
            print(f"[Controller] ⚠️ Round {server_round} Aggregation Failed.")

        return aggregated_parameters, aggregated_metrics


# [DISABLED FOR 2-NODE DEMO] Krum Byzantine Fault Tolerance Strategy

# class AuraNetKrumStrategy(fl.server.strategy.Krum):
#     def __init__(self, num_malicious_clients=0, num_clients_to_keep=0, *args, **kwargs):
#         super().__init__(
#             num_malicious_clients=num_malicious_clients,
#             num_clients_to_keep=num_clients_to_keep,
#             *args, **kwargs
#         )
# 
#     def aggregate_fit(
#         self,
#         server_round: int,
#         results: List[Tuple[fl.server.client_proxy.ClientProxy, fl.common.FitRes]],
#         failures: List[BaseException],
#     ) -> Tuple[Optional[Parameters], Dict[str, Scalar]]:
#         print(f"\n[Aggregator]  Round {server_round} - Aggregating weights using KRUM...")
#         aggregated_parameters, aggregated_metrics = super().aggregate_fit(server_round, results, failures)
#         if aggregated_parameters is not None:
#             print(f"[Aggregator]  Round {server_round} Krum aggregation successful. Outliers rejected.")
#         return aggregated_parameters, aggregated_metrics



# [ACTIVE] FedProx Strategy
# Averages all node weights but incorporates a proximal term (mu) 
# to handle statistical heterogeneity across nodes.



#### old code ignore
"""class AuraNetFedProxStrategy(fl.server.strategy.FedProx):
    def aggregate_fit(
        self,
        server_round: int,
        results: List[Tuple[fl.server.client_proxy.ClientProxy, fl.common.FitRes]],
        failures: List[BaseException],
    ) -> Tuple[Optional[Parameters], Dict[str, Scalar]]:
        
        print(f"\n[Aggregator]  Round {server_round} - Aggregating weights from {len(results)} Agents using FEDPROX...")
        
        aggregated_parameters, aggregated_metrics = super().aggregate_fit(
            server_round, results, failures
        )
        
        if aggregated_parameters is not None:
            print(f"[Aggregator]  Round {server_round} FedProx aggregation successful. All nodes merged safely.")
            
        return aggregated_parameters, aggregated_metrics"""



class AuraNetFedProxKrumStrategy(fl.server.strategy.Krum):
    """
    Hybrid FL Strategy combining FedProx and Krum.
    
    Instructs edge nodes to use FedProx regularization during local training 
    to handle heterogeneous data, while using Krum on the server side to 
    reject poisoned updates during aggregation.
    """
    def __init__(self, num_malicious_clients=0, num_clients_to_keep=0, *args, **kwargs):
        super().__init__(
            num_malicious_clients=num_malicious_clients,
            num_clients_to_keep=num_clients_to_keep,
            *args, **kwargs
        )

    def configure_fit(
        self, server_round: int, parameters: Parameters, client_manager: fl.server.ClientManager
    ) -> List[Tuple[ClientProxy, FitIns]]:
        
        # Get the baseline client sampling configurations from the parent class
        config_list = super().configure_fit(server_round, parameters, client_manager)
        
        #  Inject the dynamic PROXIMAL_MU value into every client's instruction payload
        print(f"\n[Controller] Round {server_round} Configuration:")
        print(f"  -> Injecting FedProx MU: {config.PROXIMAL_MU}")
        
        for _, fit_ins in config_list:
            fit_ins.config["proximal_mu"] = config.PROXIMAL_MU
            
        return config_list