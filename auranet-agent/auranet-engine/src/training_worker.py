import torch
import torch.nn as nn
import torch.optim as optim
import asyncio
import copy

import config

async def run_local_training(model, benign_buffer, buffer_lock, global_state):
    """
    Worker B: Wakes up every 2 minutes, locks the buffer, drains the data,
    and runs local FedProx training to adapt to new baseline traffic.
    """
    
    optimizer = optim.Adam(model.parameters(), lr=config.ai.LEARNING_RATE)
    criterion = nn.MSELoss()
    
    # The 'mu' parameter for FedProx. Controls how strictly the local model 
    # is tethered to the global master weights.
    # TODO later diaa might change this to see the best value
    proximal_mu = 0.1 

    print(f"[Worker B] Local FedProx Trainer initialized. Cadence: {config.ai.LOCAL_TRAIN_INTERVAL_SEC}s\n")

    while True:
        # Throttle: Go to sleep for 2 minutes
        await asyncio.sleep(config.ai.LOCAL_TRAIN_INTERVAL_SEC)
        
        # Safely extract and clear the buffer
        # mutex lock in python are super easy damn
        with buffer_lock:
            if len(benign_buffer) == 0:
                print("[Worker B] Buffer empty. Skipping training round.")
                continue
                
            # Copy the data out and instantly clear the queue so Worker A can keep working
            training_data = copy.deepcopy(benign_buffer)
            benign_buffer.clear()
            
        print(f"\n[Worker B] Waking up! Training on {len(training_data)} new benign packets...")

        # Convert the batch into a PyTorch Tensor
        x_train = torch.FloatTensor(training_data)
        
        # Get the latest global weights (updated by Worker C every 10 mins)
        master_weights = global_state.get("master_weights", None)
        
        # Switch model to training mode
        model.train()
        
        # The Local Epoch Loop
        for epoch in range(config.LOCAL_EPOCHS):
            optimizer.zero_grad()
            
            # Forward pass
            reconstructed = model(x_train)
            
            # Standard autoencoder loss
            loss = criterion(reconstructed, x_train)
            
            # FEDPROX PROXIMAL PENALTY
            # If we have received global weights from the Controller, apply the mathematical tether
            if master_weights is not None:
                proximal_term = 0.0
                for local_param, global_param in zip(model.parameters(), master_weights):
                    # Calculate the Euclidean distance between local and global weights
                    proximal_term += ((local_param - global_param).norm(2)) ** 2
                
                # Add the penalty to the standard loss
                loss += (proximal_mu / 2) * proximal_term

            # Backpropagation
            loss.backward()
            optimizer.step()

        # Switch back to evaluation mode for Worker A
        model.eval()
        print(f"[Worker B]  Local training complete. Final Loss: {loss.item():.6f}. Going back to sleep.\n")