import os

# Federated Learning Global Parameters
FL_ROUNDS = 1000               # Essentially run forever
MIN_AVAILABLE_CLIENTS = 2      # Minimum agents needed to start a round
FRACTION_FIT = 1.0             # Train on 100% of available agents per round
ROUND_TIMEOUT_SECONDS = 600    # 10 Minutes per round (Throttle)

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GENESIS_WEIGHTS_PATH = os.path.join(BASE_DIR, "models", "zerotrust_ae_v1.pth")