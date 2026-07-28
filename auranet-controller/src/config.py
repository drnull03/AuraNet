import os
import json
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Default parameters
FL_ROUNDS = 1000
MIN_AVAILABLE_CLIENTS = 2
FRACTION_FIT = 1.0
ROUND_TIMEOUT_SECONDS = 600
PROXIMAL_MU = 0.1



# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_GENESIS_WEIGHTS_PATH = os.path.join(BASE_DIR, "models", "zerotrust_ae_v1.pth")

# Static startup injection: Uses env var if defined, otherwise falls back to default
GENESIS_WEIGHTS_PATH = os.environ.get("GENESIS_WEIGHTS_PATH") or DEFAULT_GENESIS_WEIGHTS_PATHCONFIG_FILE_PATH = "/app/config/config.json"

def load_config():
    global FL_ROUNDS, MIN_AVAILABLE_CLIENTS, FRACTION_FIT, ROUND_TIMEOUT_SECONDS, PROXIMAL_MU
    if os.path.exists(CONFIG_FILE_PATH):
        with open(CONFIG_FILE_PATH, 'r') as f:
            data = json.load(f)
            FL_ROUNDS = data.get("fl_rounds", FL_ROUNDS)
            MIN_AVAILABLE_CLIENTS = data.get("min_available_clients", MIN_AVAILABLE_CLIENTS)
            FRACTION_FIT = data.get("fraction_fit", FRACTION_FIT)
            ROUND_TIMEOUT_SECONDS = data.get("round_timeout_seconds", ROUND_TIMEOUT_SECONDS)
            PROXIMAL_MU = data.get("proximal_mu", PROXIMAL_MU)
            print(f"[Config] Reloaded configuration: MU={PROXIMAL_MU}, Timeout={ROUND_TIMEOUT_SECONDS}s")

class K8sConfigWatcher(FileSystemEventHandler):
    def on_modified(self, event):
        # Trigger reload if the config directory changes
        if "/app/config" in event.src_path:
            load_config()

# Execute initial load on startup
load_config()

# Start background file watcher
observer = Observer()
# Watch the parent directory because Kubernetes uses symlinks
observer.schedule(K8sConfigWatcher(), path="/app/config", recursive=False)
observer.start()