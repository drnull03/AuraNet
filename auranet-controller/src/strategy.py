





import time
import flwr as fl
from typing import List, Tuple, Union, Optional, Dict
from flwr.common import FitRes, Parameters, Scalar
from flwr.server.client_proxy import ClientProxy

import config

class AuraNetFedProxStrategy(fl.server.strategy.FedProx):
    def __init__(self, *args, **kwargs):
        # We inherit all the heavy mathematical lifting from Flower's FedProx strategy
        super().__init__(*args, **kwargs)

    def aggregate_fit(
        self,
        server_round: int,
        results: List[Tuple[ClientProxy, FitRes]],
        failures: List[Union[Tuple[ClientProxy, FitRes], BaseException]],
    ) -> Tuple[Optional[Parameters], Dict[str, Scalar]]:
        """
        Overrides the default aggregation to inject  10-minute throttle.
        """
        print(f"\n[Controller]  Aggregating weights for Round {server_round}...")
        
        #  Run the standard FedProx mathematical aggregation
        aggregated_parameters, aggregated_metrics = super().aggregate_fit(
            server_round, results, failures
        )

        if aggregated_parameters is not None:
            print(f"[Controller] Round {server_round} Aggregation Complete.")
            
            #  THE THROTTLE: Force the server to sleep before broadcasting the next round
            # We skip the sleep on the final round to allow the server to shut down cleanly
            if server_round < config.FL_ROUNDS:
                print(f"[Controller]  Throttling network. Sleeping for {config.ROUND_TIMEOUT_SECONDS} seconds to allow edge nodes to train locally...")
                time.sleep(config.ROUND_TIMEOUT_SECONDS)
        else:
            print(f"[Controller] ⚠️ Round {server_round} Aggregation Failed. Not enough clients.")

        #  Return the new master brain. Once this returns, the server begins the next round.
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