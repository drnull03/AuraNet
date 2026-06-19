import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset


# Define the PyTorch Autoencoder Architecture

class ZeroTrustAutoencoder(nn.Module):
    def __init__(self, input_dim):
        super(ZeroTrustAutoencoder, self).__init__()
        
        # Encoder: Compresses the network context into a bottleneck
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 16),
            nn.ReLU(True),
            nn.Linear(16, 8),
            nn.ReLU(True),
            nn.Linear(8, 4)  # The bottleneck layer (latent space)
        )
        
        # Decoder: Attempts to reconstruct the original network context
        self.decoder = nn.Sequential(
            nn.Linear(4, 8),
            nn.ReLU(True),
            nn.Linear(8, 16),
            nn.ReLU(True),
            nn.Linear(16, input_dim),
            nn.Sigmoid() # Sigmoid to output values between 0 and 1
        )

    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded


# Main Training Logic

def train_model():
    print("🐝 Initializing PyTorch Autoencoder Training...")

    # Load the processed tensor from dataset.py
    current_dir = os.path.dirname(os.path.abspath(__file__))
    tensor_path = os.path.join(current_dir, "..", "data", "processed", "training_tensor.pt")
    
    if not os.path.exists(tensor_path):
        print(f"❌ Error: {tensor_path} not found. Run dataset.py first!")
        return

    # Load the data and create a DataLoader
    data = torch.load(tensor_path)
    input_dim = data.shape[1]
    
    # Autoencoders reconstruct their own input, so X and Y are the same
    dataset = TensorDataset(data, data) 
    dataloader = DataLoader(dataset, batch_size=8, shuffle=True)

    print(f"✅ Loaded {len(data)} network events with {input_dim} dimensions.")

    # Initialize Model, Loss Function, and Optimizer
    model = ZeroTrustAutoencoder(input_dim)
    criterion = nn.MSELoss() # Mean Squared Error calculates reconstruction accuracy
    optimizer = optim.Adam(model.parameters(), lr=0.01)

    epochs = 100
    print(f"\n🚀 Commencing training for {epochs} epochs...\n")

    for epoch in range(epochs):
        total_loss = 0
        for batch_features, _ in dataloader:
            
            # 1. Forward Pass
            reconstructed = model(batch_features)
            
            # 2. Calculate Error (Loss)
            loss = criterion(reconstructed, batch_features)
            
            # 3. Backward Pass & Optimize
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            
        avg_loss = total_loss / len(dataloader)
        
        if (epoch + 1) % 10 == 0:
            print(f"Epoch [{epoch + 1}/{epochs}], Average Loss: {avg_loss:.6f}")

    # Save the trained model weights
    model_dir = os.path.join(current_dir, "..", "models")
    os.makedirs(model_dir, exist_ok=True)
    model_path = os.path.join(model_dir, "zerotrust_ae_v1.pth")
    
    torch.save(model.state_dict(), model_path)
    print(f"\n💾 Training complete! Model weights saved to {model_path}")

if __name__ == "__main__":
    train_model()