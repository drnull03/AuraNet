import asyncio
import threading

import config
from model import ZeroTrustAutoencoder
from inference_worker import run_inference_pipeline
from training_worker import run_local_training
from fl_client import start_fl_client

def run_background_workers(model, benign_buffer, buffer_lock, global_state):
    """
    Creates an isolated asyncio event loop to run Worker A (Inference) 
    and Worker B (Local Training) concurrently on a background thread.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Schedule Worker A and Worker B
    inference_task = loop.create_task(run_inference_pipeline(model, benign_buffer, buffer_lock))
    training_task = loop.create_task(run_local_training(model, benign_buffer, buffer_lock, global_state))
    
    try:
        # Run both async loops forever
        loop.run_until_complete(asyncio.gather(inference_task, training_task))
    except Exception as e:
        print(f"[Engine] ❌ Background workers crashed: {e}")
    finally:
        loop.close()

if __name__ == "__main__":
    print(f"🚀 Booting AuraNet Engine for Workload: {config.WORKLOAD_NAME}")
    print("====")

    # Initialize Shared Global State
    # Using the 13->16->8->4 
    model = ZeroTrustAutoencoder(input_dim=config.INPUT_DIM)
    model.eval()  # Default to evaluation mode so Worker A can start streaming instantly
    
    benign_buffer = []
    global_state = {"master_weights": None}
    
    # Initialize Thread Locks for Memory Safety
    buffer_lock = threading.Lock()
    model_lock = threading.Lock()

    # fire up worker A and B
    print("[Engine]  Spinning up Async Background Thread for AI & Streaming.")
    bg_thread = threading.Thread(
        target=run_background_workers,
        args=(model, benign_buffer, buffer_lock, global_state),
        daemon=True  # Ensures this thread dies automatically if the main program exits
    )
    bg_thread.start()

    # Spin up Worker C in the main thread
    # The Flower client will block here indefinitely, listening for the central controller
    try:
        start_fl_client(model, model_lock, global_state)
    except KeyboardInterrupt:
        print("\n[Engine] 🛑 Keyboard Interrupt detected. Shutting down AuraNet Agent...")
    except Exception as e:
        print(f"\n[Engine] ❌ FL Client crashed: {e}")