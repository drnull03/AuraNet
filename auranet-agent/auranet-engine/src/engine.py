import asyncio
import threading
import time

import config
from model import ZeroTrustAutoencoder
from nlp_model import UrlNlpAutoencoder  # <-- Import Brain B
from inference_worker import run_inference_pipeline
from training_worker import run_local_training
from fl_client import start_fl_client

def run_background_workers(brain_a, brain_b, benign_buffer, buffer_lock, global_state):
    """Creates an isolated asyncio event loop for background workers."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Schedule Worker A (Inference) with BOTH brains
    tasks = [loop.create_task(run_inference_pipeline(brain_a, brain_b, benign_buffer, buffer_lock))]
    
    # Worker B (Training) only federates Brain A (Tabular). Brain B is static.
    if config.ai.LEARNING_ENGINE:
        tasks.append(loop.create_task(run_local_training(brain_a, benign_buffer, buffer_lock, global_state)))
    
    try:
        loop.run_until_complete(asyncio.gather(*tasks))
    except Exception as e:
        print(f"[Engine] ❌ Background workers crashed: {e}")
    finally:
        loop.close()

if __name__ == "__main__":
    print(f"Booting AuraNet Engine for {config.NODE_NAME}")

    # Initialize Brain A (Behavioral)
    brain_a = ZeroTrustAutoencoder(input_dim=config.ai.INPUT_DIM)
    brain_a.eval() 
    
    # Initialize Brain B (Grammatical)
    brain_b = UrlNlpAutoencoder(vocab_size=128, seq_length=150)
    if os.path.exists(config.NLP_WEIGHTS_PATH):
        print(f"[Engine] Loading pre-trained Brain B (NLP) weights from {config.NLP_WEIGHTS_PATH}...")
        # weights_only=True is a PyTorch security best practice to prevent pickle exploits
        brain_b.load_state_dict(torch.load(config.NLP_WEIGHTS_PATH, weights_only=True))
    else:
        print(f"[Engine] WARNING: NLP weights not found at {config.NLP_WEIGHTS_PATH}.")
        print(f"[Engine] Brain B is untrained! Neural parsing will be highly erratic.")
        
    
    brain_b.eval()

    benign_buffer = []
    global_state = {
        "master_weights": None,
        "is_initialized": False
    }
    
    buffer_lock = threading.Lock()
    model_lock = threading.Lock()

    print("[Engine] Spinning up Async Background Thread...")
    bg_thread = threading.Thread(
        target=run_background_workers,
        args=(brain_a, brain_b, benign_buffer, buffer_lock, global_state),
        daemon=True 
    )
    bg_thread.start()

    if config.ai.LEARNING_ENGINE:
        try:
            start_fl_client(brain_a, model_lock, global_state)
        except KeyboardInterrupt:
            print("\n[Engine] 🛑 Keyboard Interrupt detected. Shutting down...")
        except Exception as e:
            print(f"\n[Engine] ❌ FL Client crashed: {e}")
    else:
        print("\n[Engine] 🛑 LEARNING_ENGINE is False. Running in INFERENCE-ONLY mode.")
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            print("\n[Engine] 🛑 Keyboard Interrupt detected. Shutting down...")