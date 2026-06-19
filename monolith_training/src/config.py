import os


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Data Paths
TRAIN_DATA_PATH = os.path.join(BASE_DIR ,"data", "raw", "hubble_training_data.json")
TEST_DATA_PATH = os.path.join(BASE_DIR ,"data", "raw", "hubble_attack_data.json")
PROCESSED_TENSOR_PATH = os.path.join(BASE_DIR ,"data", "processed", "training_tensor.pt")

# Model Paths
MODEL_DIR = os.path.join(BASE_DIR,"models")
MODEL_WEIGHTS_PATH = os.path.join(MODEL_DIR ,"zerotrust_ae_v1.pth")

# NEURAL NETWORK HYPERPARAMETERS
#it is enough for specially since microsegmentation is applied here
EPOCHS = 100
BATCH_SIZE = 8
LEARNING_RATE = 0.01

# SOC INFERENCE SETTINGS 
# The exact Mean Squared Error (MSE) at which we classify a packet as a Zero-Day Threat
TRIPWIRE_THRESHOLD = 0.05