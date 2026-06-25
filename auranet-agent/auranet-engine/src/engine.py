import asyncio
import threading
import time

import config
from model import ZeroTrustAutoencoder
from inference_worker import run_inference_pipeline
from training_worker import run_local_training
from fl_client import start_fl_client

def run_background_workers(model, benign_buffer, buffer_lock, global_state):
    """Creates an isolated asyncio event loop for background workers."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # ALWAYS schedule Worker A (Inference)
    tasks = [loop.create_task(run_inference_pipeline(model, benign_buffer, buffer_lock))]
    
    # ONLY schedule Worker B (Training) if learning is enabled
    if config.ai.LEARNING_ENGINE:
        tasks.append(loop.create_task(run_local_training(model, benign_buffer, buffer_lock, global_state)))
    
    try:
        loop.run_until_complete(asyncio.gather(*tasks))
    except Exception as e:
        print(f"[Engine] ❌ Background workers crashed: {e}")
    finally:
        loop.close()

if __name__ == "__main__":
    print(f"Booting AuraNet Engine for {config.NODE_NAME}")

    model = ZeroTrustAutoencoder(input_dim=config.ai.INPUT_DIM)
    model.eval() 
    
    benign_buffer = []
    global_state = {
        "master_weights": None,
        "is_initialized": False
    }
    
    buffer_lock = threading.Lock()
    model_lock = threading.Lock()

    print("[Engine]Spinning up Async Background Thread...")
    bg_thread = threading.Thread(
        target=run_background_workers,
        args=(model, benign_buffer, buffer_lock, global_state),
        daemon=True 
    )
    bg_thread.start()

    if config.ai.LEARNING_ENGINE:
        try:
            start_fl_client(model, model_lock, global_state)
        except KeyboardInterrupt:
            print("\n[Engine] 🛑 Keyboard Interrupt detected. Shutting down...")
        except Exception as e:
            print(f"\n[Engine] ❌ FL Client crashed: {e}")
    else:
        print("\n[Engine] 🛑 LEARNING_ENGINE is False. Running in INFERENCE-ONLY mode.")
        print("[Engine] ⚠️ Local Training and Federated Learning are DISABLED.")
        try:
            # Keep the main thread alive so Worker A can keep streaming
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            print("\n[Engine] 🛑 Keyboard Interrupt detected. Shutting down...")