import torch
import torch.nn as nn
import torch.optim as optim

#  Define the exact model architecture (Ensure input_dim is 13)
class ZeroTrustAutoencoder(nn.Module):
    def __init__(self, input_dim=13):
        super(ZeroTrustAutoencoder, self).__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 16),
            nn.ReLU(),
            nn.Linear(16, 8),
            nn.ReLU(),
            nn.Linear(8, 4),
            nn.ReLU()
        )
        self.decoder = nn.Sequential(
            nn.Linear(4, 8),
            nn.ReLU(),
            nn.Linear(8, 16),
            nn.ReLU(),
            nn.Linear(16, input_dim),
            nn.Sigmoid() # Squishes output back to [0, 1]
        )

    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded

# Load the newly generated data
print("Loading Universal Feature Tensor...")
data = torch.load("data/processed/training_tensor.pt")
print(f"Data shape: {data.shape}")

# 3. Initialize Model, Loss, and Optimizer
model = ZeroTrustAutoencoder(input_dim=13)
criterion = nn.MSELoss()
optimizer = optim.Adam(model.parameters(), lr=0.005)

# 4. Quick Monolithic Training Loop
epochs = 50
print("\nStarting Training...")
for epoch in range(epochs):
    optimizer.zero_grad()
    
    # Autoencoder predicts itself (data -> data)
    reconstructed = model(data)
    loss = criterion(reconstructed, data)
    
    loss.backward()
    optimizer.step()
    
    if (epoch + 1) % 10 == 0:
        print(f"Epoch [{epoch+1}/{epochs}], MSE Loss: {loss.item():.4f}")

# 5. The Live Simulation Test
print("\n=== Simulating Inference ===")
model.eval()

with torch.no_grad():
    # SIMULATION A: A completely normal internal API call
    # Features: Inbound, internal IP, HTTP GET, path depth 3, 0 params, small headers
    benign_packet = torch.FloatTensor([[1, 0, 0, 0, 0, 1, 1, 0, 0.3, 0.0, 0.05, 0, 0]])
    
    benign_recon = model(benign_packet)
    benign_mse = criterion(benign_recon, benign_packet).item()
    print(f"Benign Packet MSE: {benign_mse:.4f}")
    
    # SIMULATION B: A sudden path traversal / buffer overflow attack
    # Features: External IP, HTTP POST, path depth 10 (maxed), massive headers (maxed)
    attack_packet = torch.FloatTensor([[1, 0, 1, 0, 0, 1, 0, 1, 1.0, 0.0, 1.0, 0, 0]])
    
    attack_recon = model(attack_packet)
    attack_mse = criterion(attack_recon, attack_packet).item()
    print(f"Attack Packet MSE: {attack_mse:.4f}")