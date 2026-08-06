import os
import json
import torch
import torch.nn as nn
import numpy as np

from nlp_model import BodyNlpAutoencoder


def evaluate_nlp_pipeline():
    print("[NLP] Initializing Brain C Evaluation Engine...")

    current_dir = os.path.dirname(os.path.abspath(__file__))

    tensor_path = os.path.join(
        current_dir,
        "../../data/processed/nlp/body/nlp_test_tensor.pt"
    )

    weights_path = os.path.join(
        current_dir,
        "../../models/omnifinance/nlp_ae_v1.pth"
    )

    json_test = os.path.join(
        current_dir,
        "../../data/raw/body/hubble_testing_data.json"
    )

    if not os.path.exists(tensor_path) or not os.path.exists(weights_path):
        print("❌ Error: Missing tensor or model weights. Run nlp_dataset.py and nlp_train.py first.")
        return

    # Load model
    model = BodyNlpAutoencoder(vocab_size=128, seq_length=150)
    model.load_state_dict(torch.load(weights_path))
    model.eval()

    criterion = nn.CrossEntropyLoss(ignore_index=0, reduction="none")

    # Load tensor
    test_tensor = torch.load(tensor_path)

    # Extract HTTP request bodies for display
    bodies = []

    with open(json_test, "r") as f:
        for line in f:
            if not line.strip():
                continue

            try:
                event = json.loads(line)
                l7 = event.get("flow", {}).get("l7", {})

                if not l7 or l7.get("type") == "RESPONSE":
                    continue

                body = l7.get("http", {}).get("body", "")

                if body:
                    bodies.append(body)

            except Exception:
                continue

    print(f"\n[NLP] Scanning {len(bodies)} HTTP Bodies for Grammatical Anomalies...\n")
    print(f"{'LOSS':<8} | {'CONTEXT (BODY)'}")
    print("=" * 100)

    losses = []

    # Evaluate each body
    for i in range(len(test_tensor)):
        row_tensor = test_tensor[i].unsqueeze(0)
        body_string = bodies[i]

        with torch.no_grad():
            logits = model(row_tensor)
            logits = logits.transpose(1, 2)

            char_losses = criterion(logits, row_tensor)

            mask = row_tensor != 0

            if mask.sum().item() > 0:
                seq_loss = char_losses.sum().item() / mask.sum().item()
            else:
                seq_loss = 0.0

        losses.append(seq_loss)

        alert_flag = "🚨" if seq_loss > 2.0 else "  "

        display_body = (
            body_string[:70] + "..."
            if len(body_string) > 70
            else body_string
        )

        print(f"{alert_flag} {seq_loss:.4f} | {display_body}")

    print("=" * 100)

    if losses:
        mean_loss = np.mean(losses)
        p95 = np.percentile(losses, 95)
        p99 = np.percentile(losses, 99)

        print("\n[NLP] Threshold Discovery Complete.")
        print(f"   Total Bodies Inspected: {len(losses)}")
        print(f"   Mean Loss (Normal):   {mean_loss:.4f}")
        print(f"   95th Percentile:      {p95:.4f}")
        print(f"   99th Percentile:      {p99:.4f}")


if __name__ == "__main__":
    evaluate_nlp_pipeline()