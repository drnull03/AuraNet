##
# @file model.py
# @brief Defines the AuraNet Zero Trust Autoencoder architecture.
#
# @details
# Implements the neural network used for learning normal
# network behaviour and detecting anomalies through
# reconstruction error.
#
import torch.nn as nn
##
# @class ZeroTrustAutoencoder
# @brief Neural network model for Zero Trust anomaly detection.
#
# @details
# Uses an encoder-decoder architecture to compress network
# behaviour into latent representation and reconstruct inputs.
#
class ZeroTrustAutoencoder(nn.Module):
##
# @brief Initializes encoder and decoder layers.
#
# @param input_dim Number of input telemetry features.
#
    def __init__(self, input_dim):
        super(ZeroTrustAutoencoder, self).__init__()
        
        # Encoder: Compresses the network context into a bottleneck
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 16),
            nn.ReLU(True),
            nn.Linear(16, 8),
            nn.ReLU(True),
            nn.Linear(8, 4)  # Latent space bottleneck
        )
        
        # Decoder: Attempts to reconstruct the original network context
        self.decoder = nn.Sequential(
            nn.Linear(4, 8),
            nn.ReLU(True),
            nn.Linear(8, 16),
            nn.ReLU(True),
            nn.Linear(16, input_dim),
            nn.Sigmoid() # Bounds output between 0 and 1
        )
##
# @brief Performs forward inference through the autoencoder.
#
# @param x Input feature tensor.
#
# @return Reconstructed feature tensor.
#
    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded