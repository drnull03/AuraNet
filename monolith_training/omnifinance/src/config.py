##
# @file config.py
# @brief Central configuration module for the AuraNet Monolith Training Engine.
#
# @details
# Defines paths, machine learning hyperparameters, model locations,
# and SOC inference thresholds used by the training and evaluation pipelines.
#
# This module acts as the single source of truth for configurable
# parameters shared across training, testing, and inference components.
#
import os

# Pointing to the root of the omnifinance directory
##
# @brief Root directory of the AuraNet ML training module.
#
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Data Paths
##
# @brief Dataset file locations used for training and evaluation.
#
# @details
# Defines paths for raw Hubble telemetry collected from the cluster.
#
TRAIN_DATA_PATH = os.path.join(BASE_DIR, "data", "raw", "hubble_training_data.json")
TEST_DATA_PATH = os.path.join(BASE_DIR, "data", "raw", "hubble_testing_data.json")

# Model Paths
##
# @brief Neural network model storage configuration.
#
# @details
# Defines where trained Zero Trust Autoencoder weights are stored.
#
MODEL_DIR = os.path.join(BASE_DIR, "models", "omnifinance")
MODEL_WEIGHTS_PATH = os.path.join(MODEL_DIR, "zerotrust_ae_v1.pth")

# Neural Network Hyperparameters
##
# @brief Training hyperparameters for the anomaly detection model.
#
# @details
# Controls epochs, batch size, and optimizer learning rate.
#
EPOCHS = 100
BATCH_SIZE = 8
LEARNING_RATE = 0.01

# SOC Inference Settings
#good for both specific and general
##
# @brief MSE anomaly detection threshold used by SOC evaluation.
#
# @details
# Flows producing reconstruction error above this value
# are considered suspicious and trigger anomaly handling.
#
TRIPWIRE_THRESHOLD = 0.05