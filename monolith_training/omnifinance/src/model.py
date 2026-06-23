import torch.nn as nn

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

    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded