"""
@file config.py
@brief AuraNet Engine configuration management.

Defines static deployment parameters and provides dynamic configuration
loading from Kubernetes ConfigMaps. Supports runtime hot-reloading of
AI detection thresholds, learning parameters, and Zero Trust policies.
"""
import os
import json

# Static config
NODE_NAME = os.getenv("NODE_NAME", "unknown-node")
HUBBLE_RELAY_ADDRESS = os.getenv("HUBBLE_RELAY_ADDRESS", "hubble-relay.kube-system.svc.cluster.local:80")
NATS_URL = os.getenv("NATS_URL", "nats://auranet-nats-broker.auranet-messaging.svc.cluster.local:4222")
FL_SERVER_ADDRESS = os.getenv("FL_SERVER_ADDRESS", "auranet-controller.auranet-namespace.svc.cluster.local:8080")
NATS_SUBJECT_PREFIX = "auranet.events.ai."

NLP_WEIGHTS_PATH = os.getenv("NLP_WEIGHTS_PATH", "models/nlp_ae_v1.pth")
NLP_BODY_WEIGHTS_PATH = os.getenv("NLP_BODY_WEIGHTS_PATH", "models/nlp_ae_v1_body.pth")

CONFIG_FILE_PATH = "/etc/auranet/config/ai-config.json"
"""
@brief Runtime configuration manager for AuraNet Engine.

Maintains a cached configuration loaded from Kubernetes ConfigMap data
and automatically reloads changes when the configuration file is updated.

Provides dynamic access to AI model parameters, anomaly thresholds,
federated learning settings, and trusted workload identities.
"""
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
            "learningRate": 0.01,
            "trustedIdentities": [],
            "learningEngine": True,
            "thirdBrain": False
        }
        # Initial load on boot
        self.reload_if_changed()

    def reload_if_changed(self):
        """Called periodically by a background task to safely reload ConfigMap updates."""
        if os.path.exists(CONFIG_FILE_PATH):
            try:
                # Resolve the real symlink path to handle Kubernetes ConfigMap swaps
                real_path = os.path.realpath(CONFIG_FILE_PATH)
                mtime = os.path.getmtime(real_path)
                
                if mtime > self.last_modified:
                    with open(real_path, 'r') as f:
                        new_config = json.load(f)
                        self._cache.update(new_config)
                    self.last_modified = mtime
                    print("[Engine] 🔄 Security Policy Hot-Reloaded from ConfigMap!")
            except Exception as e:
                pass # Ignore transient read errors during atomic Kubelet updates

    # Clean In-Memory Properties (Zero Disk I/O) 
    @property
    def INPUT_DIM(self):
        return self._cache.get("inputDim", 13)

    @property
    def TRIPWIRE_THRESHOLD(self):
        return self._cache.get("tripwireThreshold", 0.05)

    @property
    def LOCAL_TRAIN_INTERVAL_SEC(self):
        return self._cache.get("localTrainIntervalSec", 120)

    @property
    def MAX_BUFFER_SIZE(self):
        return self._cache.get("maxBufferSize", 5000)

    @property
    def LOCAL_EPOCHS(self):
        return self._cache.get("localEpochs", 5)

    @property
    def LEARNING_RATE(self):
        return self._cache.get("learningRate", 0.001)

    @property
    def TRUSTED_IDENTITIES(self):
        return set(self._cache.get("trustedIdentities", []))

    @property
    def LEARNING_ENGINE(self):
        return self._cache.get("learningEngine", True)

    @property
    def NLP_TRIPWIRE(self):
        return self._cache.get("nlpTripwire", 2.0)

    @property
    def Z_SCORE_THRESHOLD(self):
        return self._cache.get("zScoreThreshold", 3.0)

    @property
    def Z_SCORE_WINDOW_SIZE(self):
        return self._cache.get("zScoreWindowSize", 1000)
        
    @property                                                
    def NLP_BODY_TRIPWIRE(self):                             
        return self._cache.get("nlpBodyTripwire", 2.0)      
        
    @property                                               
    def THIRD_BRAIN(self):                                  
        return self._cache.get("thirdBrain", False)

# Instantiate global dynamic config object
ai = DynamicConfig()



