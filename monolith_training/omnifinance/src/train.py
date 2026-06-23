import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader

import config
from model import ZeroTrustAutoencoder
from dataset import HubbleDataProcessor, HubbleDataset

def train_pipeline():
    print("🐝 [MLOps] Initializing OmniFinance Training Pipeline...")

    if not os.path.exists(config.TRAIN_DATA_PATH):
        print(f"❌ Error: Training data not found at {config.TRAIN_DATA_PATH}")
        return

    # 1. Process Data Dynamically In-Memory
    print("📊 [MLOps] Processing raw training telemetry on the fly...")
    processor = HubbleDataProcessor(config.TRAIN_DATA_PATH)
    processor.load_and_filter()
    processor.engineer_features()
    
    df = processor.get_dataframe()
    input_dim = df.shape[1]
    
    # 2. Convert to PyTorch Dataset
    torch_dataset = HubbleDataset(df)
    dataloader = DataLoader(torch_dataset, batch_size=config.BATCH_SIZE, shuffle=True)
    print(f"✅ [MLOps] Extracted {len(torch_dataset)} pure network events ({input_dim} dimensions).")

    # 3. Initialize Model using config parameters
    model = ZeroTrustAutoencoder(input_dim)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=config.LEARNING_RATE)

    # 4. Training Loop
    print(f"\n🚀 [MLOps] Commencing training for {config.EPOCHS} epochs...\n")
    for epoch in range(config.EPOCHS):
        total_loss = 0
        for batch_features, _ in dataloader:
            
            reconstructed = model(batch_features)
            loss = criterion(reconstructed, batch_features)
            
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            
        avg_loss = total_loss / len(dataloader)
        if (epoch + 1) % 10 == 0:
            print(f"Epoch [{epoch + 1}/{config.EPOCHS}], Average MSE Loss: {avg_loss:.6f}")

    # 5. Save the Brain
    os.makedirs(os.path.dirname(config.MODEL_WEIGHTS_PATH), exist_ok=True)
    torch.save(model.state_dict(), config.MODEL_WEIGHTS_PATH)
    print(f"\n💾 [MLOps] Training complete! Weights saved to {config.MODEL_WEIGHTS_PATH}")

if __name__ == "__main__":
    train_pipeline()