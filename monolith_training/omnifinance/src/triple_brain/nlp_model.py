import torch
import torch.nn as nn


# the same as the url one 
# the exact same
class UrlNlpAutoencoder(nn.Module):
    def __init__(self, vocab_size=128, embedding_dim=16, hidden_dim=32, seq_length=150):
        super(UrlNlpAutoencoder, self).__init__()
        self.seq_length = seq_length
        
        # 1. EMBEDDING
        self.embedding = nn.Embedding(num_embeddings=vocab_size, embedding_dim=embedding_dim, padding_idx=0)
        
        # 2. ENCODER
        self.encoder_lstm = nn.LSTM(input_size=embedding_dim, hidden_size=hidden_dim, batch_first=True)
        
        # 3. DECODER
        self.decoder_lstm = nn.LSTM(input_size=hidden_dim, hidden_size=hidden_dim, batch_first=True)
        
        # 4. OUTPUT MAPPER
        self.fc_out = nn.Linear(hidden_dim, vocab_size)

    def forward(self, x):
        embedded = self.embedding(x)
        _, (hidden, _) = self.encoder_lstm(embedded) 
        
        hidden = hidden.squeeze(0) 
        decoder_input = hidden.unsqueeze(1).repeat(1, self.seq_length, 1) 
        
        decoder_out, _ = self.decoder_lstm(decoder_input) 
        logits = self.fc_out(decoder_out) 
        
        # We output raw logits. The CrossEntropyLoss function will handle the Softmax math internally.
        return logits