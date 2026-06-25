import pytest
import torch
import time
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from model import ZeroTrustAutoencoder
import config

def test_inference_throughput_meltdown():
    """
    STRESS TEST: Blasts 100,000 packets through the AI sequentially to find the absolute
    ceiling of packets-per-second (PPS) the edge node can handle in real-time.
    """
    model = ZeroTrustAutoencoder(input_dim=config.ai.INPUT_DIM)
    model.eval()
    
    num_packets = 100_000
    # Pre-generate a massive tensor representing 100k random network packets
    dummy_stream = torch.rand(num_packets, 1, config.ai.INPUT_DIM)
    
    print(f"\n[Chaos] Unleashing {num_packets:,} packets into the neural network...")
    
    start_time = time.time()
    
    # Fire them sequentially, exactly like the Hubble stream generator would
    with torch.no_grad():
        for i in range(num_packets):
            _ = model(dummy_stream[i])
            
    end_time = time.time()
    duration = end_time - start_time
    packets_per_second = num_packets / duration
    
    print(f"\n================ STRESS TEST RESULTS ================")
    print(f" Processed:  {num_packets:,} packets")
    print(f" Time:       {duration:.4f} seconds")
    print(f" Throughput: {packets_per_second:,.2f} packets/sec")
    print(f"=====================================================")
    
    assert packets_per_second > 5000, "Node CPU is too slow to survive a DDoS!"
