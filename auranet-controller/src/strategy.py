import flwr as fl
from typing import Dict, Optional, Tuple, List
from flwr.common import Parameters, Scalar

class AuraNetKrumStrategy(fl.server.strategy.Krum):
    def __init__(self, num_malicious_clients=0, num_clients_to_keep=0, *args, **kwargs):
        """
        Byzantine Fault Tolerant Aggregation.
        Krum calculates the distance between all client updates and selects the one
        closest to the median, rejecting outliers that might be poisoned by an attacker.
        """
        super().__init__(
            num_malicious_clients=num_malicious_clients,
            num_clients_to_keep=num_clients_to_keep,
            *args, **kwargs
        )

    def aggregate_fit(
        self,
        server_round: int,
        results: List[Tuple[fl.server.client_proxy.ClientProxy, fl.common.FitRes]],
        failures: List[BaseException],
    ) -> Tuple[Optional[Parameters], Dict[str, Scalar]]:
        
        print(f"\n[Aggregator] 🔄 Round {server_round} - Aggregating weights from {len(results)} Agents...")
        
        # The parent Krum class handles the distance calculations and outlier rejection
        aggregated_parameters, aggregated_metrics = super().aggregate_fit(
            server_round, results, failures
        )
        
        if aggregated_parameters is not None:
            print(f"[Aggregator] ✅ Round {server_round} aggregation successful. Poisoned outliers rejected.")
            
        return aggregated_parameters, aggregated_metrics