import torch
import sys
import os


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from model import ZeroTrustAutoencoder
import config

def test_model_initialization():
    """Test that the model boots up with the correct 13-dimensional input."""
    model = ZeroTrustAutoencoder(input_dim=config.INPUT_DIM)
    assert model is not None

def test_model_forward_pass_shape():
    """Test that a 13-dim input perfectly reconstructs into a 13-dim output."""
    model = ZeroTrustAutoencoder(input_dim=config.INPUT_DIM)
    
    # Create a dummy batch of 5 packets, each with 13 features
    dummy_input = torch.rand(5, 13) 
    
    output = model(dummy_input)
    
    # The output shape MUST match the input shape exactly
    assert output.shape == (5, 13), f"Expected shape (5, 13) but got {output.shape}"

def test_model_sigmoid_bounds():
    """Test that the decoder's Sigmoid function keeps all outputs between 0 and 1."""
    model = ZeroTrustAutoencoder(input_dim=config.INPUT_DIM)
    
    # Push extreme values (negative and highly positive) through the network
    extreme_input = torch.tensor([[-100.0] * 13, [100.0] * 13])
    
    output = model(extreme_input)
    
    # Check that absolutely no value escaped the 0.0 to 1.0 bounds
    assert torch.all(output >= 0.0), "Outputs fell below 0.0, Sigmoid failed!"
    assert torch.all(output <= 1.0), "Outputs exceeded 1.0, Sigmoid failed!"