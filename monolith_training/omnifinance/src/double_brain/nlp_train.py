import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader

from nlp_dataset import NlpDataset
from nlp_model import UrlNlpAutoencoder

def train_nlp_pipeline():
    print("🧠 [NLP] Booting Brain B (LSTM Payload Engine)...")
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    tensor_path = os.path.join(current_dir, "../../data/processed/nlp/nlp_train_tensor.pt")
    weights_path = os.path.join(current_dir, "../../models/omnifinance/nlp_ae_v1.pth")
    
    if not os.path.exists(tensor_path):
        print(f"❌ Error: Tensor not found at {tensor_path}")
        return

    tensor_data = torch.load(tensor_path)
    dataset = NlpDataset(tensor_data)
    dataloader = DataLoader(dataset, batch_size=16, shuffle=True)
    
    model = UrlNlpAutoencoder(vocab_size=128, seq_length=150)
    
    # We use CrossEntropy for classification. ignore_index=0 tells the model 
    # not to punish itself for messing up the padding zeroes.
    criterion = nn.CrossEntropyLoss(ignore_index=0) 
    optimizer = optim.Adam(model.parameters(), lr=0.005)

    epochs = 50
    print(f"\n🚀 Training LSTM Autoencoder for {epochs} epochs...\n")
    
    for epoch in range(epochs):
        total_loss = 0
        for batch_targets, _ in dataloader:
            
            optimizer.zero_grad()
            logits = model(batch_targets)
            
            # CrossEntropy requires logits shape: (batch_size, num_classes, seq_length)
            # and targets shape: (batch_size, seq_length)
            logits = logits.transpose(1, 2) 
            
            loss = criterion(logits, batch_targets)
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            
        avg_loss = total_loss / len(dataloader)
        if (epoch + 1) % 5 == 0:
            print(f"Epoch [{epoch + 1}/{epochs}], CrossEntropy Loss: {avg_loss:.4f}")

    os.makedirs(os.path.dirname(weights_path), exist_ok=True)
    torch.save(model.state_dict(), weights_path)
    print(f"\n💾 NLP Training complete! Weights saved to {weights_path}")

if __name__ == "__main__":
    train_nlp_pipeline()