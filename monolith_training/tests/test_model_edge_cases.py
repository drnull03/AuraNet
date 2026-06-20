import unittest
import torch
import sys
import os

# Add the src directory to the path so we can import the model
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from model import ZeroTrustAutoencoder

class TestZeroTrustAutoencoderEdgeCases(unittest.TestCase):
    def setUp(self):
        """
        Runs before every single test.
        Initializes a fresh model with our expected 9 input dimensions.
        """
        self.input_dim = 9
        self.model = ZeroTrustAutoencoder(self.input_dim)
        self.model.eval() # Set to inference mode

    def test_wrong_input_shape_raises_error(self):
        """EDGE CASE 1: What if upstream feature engineering breaks and sends 8 features?"""
        print("\n[Test] Passing 8 features instead of 9...")
        
        wrong_shape_tensor = torch.randn(1, 8)
        
        # We EXPECT PyTorch to throw a RuntimeError about matrix multiplication dimensions
        with self.assertRaises(RuntimeError):
            self.model(wrong_shape_tensor)
            
    def test_wrong_data_type_raises_error(self):
        """EDGE CASE 2: What if we pass Integers instead of Floats?"""
        print("[Test] Passing Integer tensor instead of Float tensor...")
        
        # PyTorch Linear layers require float32. Passing int64 should crash.
        int_tensor = torch.randint(0, 2, (1, 9))
        
        # We expect this to fail due to a type mismatch
        with self.assertRaises(Exception):
            self.model(int_tensor)

    def test_extreme_values_and_nans(self):
        """EDGE CASE 3: What if the telemetry gets corrupted with Infinity or NaN?"""
        print("[Test] Passing Infinity and NaN values...")
        
        extreme_tensor = torch.tensor([[float('nan'), float('inf'), -float('inf'), 0.0, 1.0, 1.0, 0.0, 1.0, 0.0]])
        output = self.model(extreme_tensor)
        
        # The model shouldn't hard-crash the server, but the output should mathematically be NaN
        self.assertTrue(torch.isnan(output).any().item())

    def test_empty_batch_processing(self):
        """EDGE CASE 4: What if the SOAR pipeline is empty and passes 0 packets?"""
        print("[Test] Passing an empty batch of size 0...")
        
        empty_tensor = torch.empty((0, 9))
        output = self.model(empty_tensor)
        
        # The model should cleanly process nothing and return an empty tensor of the same shape
        self.assertEqual(output.shape, (0, 9))

    def test_sigmoid_output_bounds_guarantee(self):
        """
        EDGE CASE 5: The Mathematical Guarantee.
        Because our last layer is nn.Sigmoid(), the output MUST strictly be between 0.0 and 1.0,
        even if we feed it astronomical input numbers.
        """
        print("[Test] Blasting the model with astronomical numbers to test Sigmoid bounds...")
        
        crazy_tensor = torch.tensor([[999999.0, -999999.0, 1e10, -1e10, 500.0, -500.0, 0.0, 1.0, -1.0]])
        output = self.model(crazy_tensor)
        
        # Assert every single output value is >= 0.0
        self.assertTrue(torch.all(output >= 0.0).item())
        
        # Assert every single output value is <= 1.0
        self.assertTrue(torch.all(output <= 1.0).item())
        
    def test_gradient_flow_sanity(self):
        """EDGE CASE 6: Does the model actually learn, or are the layers frozen?"""
        print("[Test] Checking if gradients flow backwards (proving it can learn)...")
        
        self.model.train() # Switch to training mode for this test
        dummy_input = torch.randn(1, 9)
        dummy_target = torch.randn(1, 9)
        
        criterion = torch.nn.MSELoss()
        output = self.model(dummy_input)
        loss = criterion(output, dummy_target)
        loss.backward()
        
        # Assert that the very first layer in our encoder received a gradient update
        # If this is None, our network is broken and incapable of learning!
        self.assertIsNotNone(self.model.encoder[0].weight.grad)

if __name__ == '__main__':
    # Run the tests with verbose output
    unittest.main(verbosity=2)
