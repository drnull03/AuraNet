import os

# 
# NATS MESSAGING & ROUTING (WORKER A)

# Defaulting to the internal K8s DNS we established in your trust-engine
NATS_URL = os.getenv("NATS_URL", "nats://auranet-nats-broker.auranet-messaging.svc.cluster.local:4222")
NATS_SUBJECT_PREFIX = "auranet.events.ai."

# We need to know what microservice this specific agent is protecting
# This will be injected via Kubernetes Downward API in the deployment YAML later
WORKLOAD_NAME = os.getenv("WORKLOAD_NAME", "unknown-workload")


# 
# NEURAL NETWORK & INFERENCE (WORKER A)
# 
INPUT_DIM = 13
TRIPWIRE_THRESHOLD = 0.05


# 
# LOCAL TRAINING ENGINE (WORKER B)
# 
LOCAL_TRAIN_INTERVAL_SEC = 120  # Throttle: Wake up every 2 minutes
# Critical limit to prevent the agent from eating the node's RAM before the 2-minute loop triggers
MAX_BUFFER_SIZE = 5000         
LOCAL_EPOCHS = 5
LEARNING_RATE = 0.001


# 
# FEDERATED LEARNING CLIENT (WORKER C)
# 
# Pointing to the new controller we just spun up in the auranet-namespace
FL_SERVER_ADDRESS = os.getenv("FL_SERVER_ADDRESS", "auranet-controller.auranet-namespace.svc.cluster.local:8080")