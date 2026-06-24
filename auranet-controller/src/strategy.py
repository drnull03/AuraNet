import flwr as fl
from typing import Dict, Optional, Tuple, List
from flwr.common import Parameters, Scalar


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

class AuraNetFedProxStrategy(fl.server.strategy.FedProx):
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
            
        return aggregated_parameters, aggregated_metrics