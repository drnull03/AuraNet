import os
from unittest import mock
import flwr as fl
from src.server import get_genesis_parameters

@mock.patch('src.server.os.path.exists')
@mock.patch('src.server.torch.load')
def test_genesis_parameters_fallback(mock_torch_load, mock_path_exists):
    """
    Tests that the server safely initializes a fresh neural network 
    if the pre-trained monolith weights file is missing.
    """
    # Force the file-check to return False (Simulating a fresh deployment)
    mock_path_exists.return_value = False

    # Execute the warm start logic
    params = get_genesis_parameters()

    # Assertions
    assert isinstance(params, fl.common.Parameters), "Failed to return Flower Parameters object"
    assert len(params.tensors) > 0, "Genesis parameters are empty"
    
    # Ensure torch.load was never actually called since the file doesn't exist
    mock_torch_load.assert_not_called()import os
from unittest import mock
import flwr as fl
from src.server import get_genesis_parameters

@mock.patch('src.server.os.path.exists')
@mock.patch('src.server.torch.load')
def test_genesis_parameters_fallback(mock_torch_load, mock_path_exists):
    """
    Tests that the server safely initializes a fresh neural network 
    if the pre-trained monolith weights file is missing.
    """
    # Force the file-check to return False (Simulating a fresh deployment)
    mock_path_exists.return_value = False

    # Execute the warm start logic
    params = get_genesis_parameters()

    # Assertions
    assert isinstance(params, fl.common.Parameters), "Failed to return Flower Parameters object"
    assert len(params.tensors) > 0, "Genesis parameters are empty"
    
    # Ensure torch.load was never actually called since the file doesn't exist
    mock_torch_load.assert_not_called()
