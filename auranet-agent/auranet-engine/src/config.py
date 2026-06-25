import os
import json

#static config
NODE_NAME = os.getenv("NODE_NAME", "unknown-node")
HUBBLE_RELAY_ADDRESS = os.getenv("HUBBLE_RELAY_ADDRESS", "hubble-relay.kube-system.svc.cluster.local:80")
NATS_URL = os.getenv("NATS_URL", "nats://auranet-nats-broker.auranet-messaging.svc.cluster.local:4222")
FL_SERVER_ADDRESS = os.getenv("FL_SERVER_ADDRESS", "auranet-controller.auranet-namespace.svc.cluster.local:8080")
NATS_SUBJECT_PREFIX = "auranet.events.ai."

#config map stuff
CONFIG_FILE_PATH = "/etc/auranet/config/ai-config.json"

class DynamicConfig:
    def __init__(self):
        self.last_modified = 0
        self._cache = {
            "inputDim": 13,
            "tripwireThreshold": 0.05,
            "localTrainIntervalSec": 120,
            "maxBufferSize": 5000,
            "localEpochs": 5,
            "learningRate": 0.001,
            "trustedIdentities": []
        }
        self._reload_if_changed()

    def _reload_if_changed(self):
        """Silently reloads the JSON file if Kubernetes has updated the ConfigMap."""
        if os.path.exists(CONFIG_FILE_PATH):
            mtime = os.path.getmtime(CONFIG_FILE_PATH)
            if mtime > self.last_modified:
                try:
                    with open(CONFIG_FILE_PATH, 'r') as f:
                        new_config = json.load(f)
                        self._cache.update(new_config)
                    self.last_modified = mtime
                    print("[Engine] 🔄 Security Policy Hot-Reloaded from ConfigMap!")
                except Exception as e:
                    print(f"[Engine] ⚠️ Failed to parse ConfigMap JSON: {e}")

    
    
    @property
    def INPUT_DIM(self):
        self._reload_if_changed()
        return self._cache.get("inputDim", 13)

    @property
    def TRIPWIRE_THRESHOLD(self):
        self._reload_if_changed()
        return self._cache.get("tripwireThreshold", 0.05)

    @property
    def LOCAL_TRAIN_INTERVAL_SEC(self):
        self._reload_if_changed()
        return self._cache.get("localTrainIntervalSec", 120)

    @property
    def MAX_BUFFER_SIZE(self):
        self._reload_if_changed()
        return self._cache.get("maxBufferSize", 5000)

    @property
    def LOCAL_EPOCHS(self):
        self._reload_if_changed()
        return self._cache.get("localEpochs", 5)

    @property
    def LEARNING_RATE(self):
        self._reload_if_changed()
        return self._cache.get("learningRate", 0.001)

    @property
    def TRUSTED_IDENTITIES(self):
        self._reload_if_changed()
        return set(self._cache.get("trustedIdentities", []))

# Instantiate the dynamic config object
ai = DynamicConfig()