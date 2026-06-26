import os
import json

#static config
NODE_NAME = os.getenv("NODE_NAME", "unknown-node")
HUBBLE_RELAY_ADDRESS = os.getenv("HUBBLE_RELAY_ADDRESS", "hubble-relay.kube-system.svc.cluster.local:80")
NATS_URL = os.getenv("NATS_URL", "nats://auranet-nats-broker.auranet-messaging.svc.cluster.local:4222")
FL_SERVER_ADDRESS = os.getenv("FL_SERVER_ADDRESS", "auranet-controller.auranet-namespace.svc.cluster.local:8080")
NATS_SUBJECT_PREFIX = "auranet.events.ai."


NLP_WEIGHTS_PATH = os.getenv("NLP_WEIGHTS_PATH", "models/nlp_ae_v1.pth")

#config map stuff
CONFIG_FILE_PATH = "/etc/auranet/config/ai-config.json"

class DynamicConfig:
    def __init__(self):
        self.last_modified = 0
        self._cache = {
            "inputDim": 13,
            "nlpTripwire": 2.0,
            "nlpBodyTripwire": 2.0,
            "zScoreThreshold": 3.0,    
            "zScoreWindowSize": 1000,
            "tripwireThreshold": 0.05,
            "localTrainIntervalSec": 120,
            "maxBufferSize": 5000,
            "localEpochs": 5,
            "learningRate": 0.001,
            "trustedIdentities": [],
            "learningEngine": True,
            "thirdBrain": False
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

    @property
    def LEARNING_ENGINE(self):
        self._reload_if_changed()
        return self._cache.get("learningEngine", True)

    @property
    def NLP_TRIPWIRE(self):
        self._reload_if_changed()
        return self._cache.get("nlpTripwire", 2.0)
    @property
    def Z_SCORE_THRESHOLD(self):
        self._reload_if_changed()
        return self._cache.get("zScoreThreshold", 3.0)

    @property
    def Z_SCORE_WINDOW_SIZE(self):
        self._reload_if_changed()
        return self._cache.get("zScoreWindowSize", 1000)
        
    @property                                               # :) update
    def NLP_BODY_TRIPWIRE(self):                            # :) update
        self._reload_if_changed()                           # :) update
        return self._cache.get("nlpBodyTripwire", 2.0)      # :) update
        
    @property                                               # :) update
    def THIRD_BRAIN(self):                                  # :) update
        self._reload_if_changed()                           # :) update
        return self._cache.get("thirdBrain", False)

# Instantiate the dynamic config object
ai = DynamicConfig()