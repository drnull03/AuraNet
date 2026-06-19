import os
import torch
import torch.nn as nn

# Import our MLOps modules
import config
from model import ZeroTrustAutoencoder

def test_single_packet(name, features):
    """
    Takes a 9-dimensional list of features, feeds it to the trained Autoencoder,
    and calculates the Mean Squared Error (MSE).
    """
    print(f"\n Testing Scenario: {name} ")
    
    if not os.path.exists(config.MODEL_WEIGHTS_PATH):
        print(f"❌ Error: Model weights not found at {config.MODEL_WEIGHTS_PATH}")
        return

    # load the Brain
    input_dim = 9
    model = ZeroTrustAutoencoder(input_dim)
    model.load_state_dict(torch.load(config.MODEL_WEIGHTS_PATH))
    model.eval() # Set to evaluation mode
    criterion = nn.MSELoss()

    # Convert our list of numbers into a PyTorch Tensor
    # We wrap it in an extra bracket to simulate a "batch size of 1"
    row_tensor = torch.FloatTensor([features])

    # 3. Ask the AI to reconstruct it
    with torch.no_grad():
        reconstructed = model(row_tensor)
        mse_loss = criterion(reconstructed, row_tensor).item()

    # 4. Evaluate the result against the Tripwire Threshold
    print(f"Input Vector: {features}")
    print(f"MSE Score:    {mse_loss:.6f}")
    
    if mse_loss > config.TRIPWIRE_THRESHOLD:
        print(f"🚨 ANOMALY DETECTED! (Exceeded {config.TRIPWIRE_THRESHOLD})")
    else:
        print(f"✅ NORMAL TRAFFIC (Below {config.TRIPWIRE_THRESHOLD})")

if __name__ == "__main__":
    # -------------------------------------------------------------------------
    # Feature Index Guide (Based on dataset.py):
    # [0] is_dropped
    # [1] is_valid_path (1.0 = valid path like /customers/1)
    # [2] is_get        (1.0 = GET request)
    # [3] is_post       (1.0 = POST request)
    # [4] is_delete     (1.0 = DELETE request)
    # [5] src_is_retail (1.0 = retail-dashboard)
    # [6] src_is_invest (1.0 = investment-dashboard)
    # [7] dst_is_api    (1.0 = customer-api)
    # [8] dst_is_vault  (1.0 = vault-db)
    # -------------------------------------------------------------------------

    # test 1: normal  test near zero mse
    # Retail Dashboard -> GET /customers/1
    normal_get = [0.0, 1.0, 1.0, 0.0, 0.0, 1.0, 0.0, 1.0, 0.0]
    test_single_packet("Authorized GET Request", normal_get)

    # test 2: generating a delete
    # Retail Dashboard -> DELETE /customers/1
    malicious_delete = [0.0, 1.0, 0.0, 0.0, 1.0, 1.0, 0.0, 1.0, 0.0]
    test_single_packet("Malicious DELETE Request", malicious_delete)
    
    # TEST 3: What if the Investment Dashboard successfully bypassed Cilium?
    # Investment Dashboard -> GET /customers/1 (BUT is_dropped is 0.0 instead of 1.0!)
    bypassed_invest = [0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0]
    test_single_packet("Investment Dashboard Bypass", bypassed_invest)