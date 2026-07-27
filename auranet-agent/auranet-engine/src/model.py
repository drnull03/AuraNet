"""
@file model.py
@brief Behavioral anomaly detection model.

Defines the Zero Trust autoencoder used by AuraNet for detecting
network behavior anomalies through reconstruction error.
"""
import torch.nn as nn
"""
@brief Neural autoencoder for network behavior analysis.

Compresses network feature vectors into a latent representation
and reconstructs them to calculate anomaly scores.
"""
class ZeroTrustAutoencoder(nn.Module):
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
"""
@brief Performs model inference.

Encodes the input feature vector and reconstructs it through
the decoder.

@param x Input network feature tensor.
@return Reconstructed feature tensor.
"""
    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded