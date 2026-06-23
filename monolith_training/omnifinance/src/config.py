import os

# Pointing to the root of the omnifinance directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Data Paths
TRAIN_DATA_PATH = os.path.join(BASE_DIR, "data", "raw", "hubble_training_data.json")
TEST_DATA_PATH = os.path.join(BASE_DIR, "data", "raw", "hubble_testing_data.json")

# Model Paths
MODEL_DIR = os.path.join(BASE_DIR, "models", "omnifinance")
MODEL_WEIGHTS_PATH = os.path.join(MODEL_DIR, "zerotrust_ae_v1.pth")

# Neural Network Hyperparameters
EPOCHS = 100
BATCH_SIZE = 8
LEARNING_RATE = 0.01

# SOC Inference Settings
TRIPWIRE_THRESHOLD = 0.05