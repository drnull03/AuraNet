import os

# AGENT IDENTITY (DaemonSet Level)
# Injected via K8s Downward API (spec.nodeName) in the DaemonSet YAML
NODE_NAME = os.getenv("NODE_NAME", "unknown-node")

# HUBBLE RELAY STREAMING
# The standard internal K8s DNS for the Cilium Hubble Relay
HUBBLE_RELAY_ADDRESS = os.getenv("HUBBLE_RELAY_ADDRESS", "hubble-relay.kube-system.svc.cluster.local:80")




NATS_URL = os.getenv("NATS_URL", "nats://auranet-nats-broker.auranet-messaging.svc.cluster.local:4222")
NATS_SUBJECT_PREFIX = "auranet.events.ai."


#NEURAL NETWORK & INFERENCE (WORKER A)

INPUT_DIM = 13
TRIPWIRE_THRESHOLD = 0.05




LOCAL_TRAIN_INTERVAL_SEC = 120  
MAX_BUFFER_SIZE = 5000         
LOCAL_EPOCHS = 5
LEARNING_RATE = 0.001




FL_SERVER_ADDRESS = os.getenv("FL_SERVER_ADDRESS", "auranet-controller.auranet-namespace.svc.cluster.local:8080")