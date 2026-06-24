import json
import re
import subprocess
import numpy as np

import config

class HubbleStreamProcessor:
    def __init__(self):
        # Compile the regexes once during boot to save CPU cycles during live streaming
        self.acc_regex = re.compile(r"^.*/api/accounts\?id=[0-9]+$")
        self.loan_regex = re.compile(r"^.*/api/loans/export\?id=L-[0-9]+$")
        
        # Connect to the central Relay, but apply server-side filtering for THIS specific node
        self.command = [
            "hubble", 
            "observe", 
            "--server", config.HUBBLE_RELAY_ADDRESS,
            "--node", config.NODE_NAME,
            "-f", 
            "-o", "json"
        ]

    def extract_app_label(self, labels):
        """Identical to monolithic dataset logic."""
        if not labels:
            return "unknown"
        for label in labels:
            if label.startswith("k8s:app="):
                return label.split("=")[1]
        return "unknown"

    def process_event(self, event):
        """
        Filters and converts a single real-time packet into the 13-dim tensor.
        Returns None if the packet should be ignored based on our training rules.
        """
        flow = event.get("flow", {})
        if not flow:
            return None

        verdict = flow.get("verdict", "")
        source_labels = flow.get("source", {}).get("labels", [])
        event_type = flow.get("event_type", {}).get("type", 0)
        drop_reason = flow.get("drop_reason_desc", "")

        # MONOLITHIC FILTERING RULES
        
        if "reserved:host" in source_labels:
            return None
        
        # Prevent Double-Logging
        if verdict == "DROPPED" and event_type != 1:
            return None
            
        # IGNORE SPIRE mTLS HANDSHAKE DROPS
        if verdict == "DROPPED" and drop_reason == "AUTH_REQUIRED":
            return None

        l7 = flow.get("l7", {})
        
        raw_port = flow.get("destination", {}).get("port")
        try:
            dst_port = int(raw_port) if raw_port else 0
        except ValueError:
            dst_port = 0

        tcp_flags = flow.get("l4", {}).get("TCP", {}).get("flags", {})
        is_syn = tcp_flags.get("SYN", False)
        is_ack = tcp_flags.get("ACK", False)
        
        # IGNORE L7 RESPONSES
        if l7 and l7.get("type") == "RESPONSE":
            return None

        is_http_l7 = verdict == "FORWARDED" and l7 and "http" in l7
        is_db_l4 = verdict == "FORWARDED" and dst_port == 5432 and is_syn and not is_ack
        
        # Keep Drops, HTTP, OR Database TCP (L4)
        if not (verdict == "DROPPED" or is_http_l7 or is_db_l4):
            return None

        #  FEATURE ENGINEERING (Strict 13-Dim Match)
        src_app = self.extract_app_label(source_labels)
        dst_app = self.extract_app_label(flow.get("destination", {}).get("labels", []))
        
        http_data = l7.get("http", {}) if l7 else {}
        method = http_data.get("method", "NONE")
        url = http_data.get("url", "NONE")

        features = np.zeros(13, dtype=np.float32)

        # Target Label (Index 0)
        features[0] = 1.0 if verdict == 'DROPPED' else 0.0
        
        # Path Validations (Index 1, 2)
        features[1] = 1.0 if self.acc_regex.match(str(url)) else 0.0
        features[2] = 1.0 if self.loan_regex.match(str(url)) else 0.0
        
        # Request Types (Index 3, 4)
        features[3] = 1.0 if method == 'GET' else 0.0
        features[4] = 1.0 if dst_port == 5432 else 0.0
        
        # Source Pod Matrix (Index 5, 6, 7, 8)
        features[5] = 1.0 if src_app == 'frontend-ui' else 0.0
        features[6] = 1.0 if src_app == 'api-gateway' else 0.0
        features[7] = 1.0 if src_app == 'account-service' else 0.0
        features[8] = 1.0 if src_app == 'loan-service' else 0.0
        
        # Destination Pod Matrix (Index 9, 10, 11, 12)
        features[9] = 1.0 if dst_app == 'api-gateway' else 0.0
        features[10] = 1.0 if dst_app == 'account-service' else 0.0
        features[11] = 1.0 if dst_app == 'loan-service' else 0.0
        features[12] = 1.0 if dst_app == 'finance-db' else 0.0

        return features

    def stream_traffic(self):
        """
        Continuously yields (raw_json, feature_array) for valid packets.
        """
        print(f"[Streamer]  Connecting to Relay at {config.HUBBLE_RELAY_ADDRESS} for node {config.NODE_NAME}...")
        process = subprocess.Popen(
            self.command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        for line in process.stdout:
            line = line.strip()
            if not line:
                continue
                
            try:
                event = json.loads(line)
                
                # Apply monolithic filters and extract features
                feature_array = self.process_event(event)
                
                # If it passed all filters, send it to the AI for inference
                if feature_array is not None:
                    yield event, feature_array
                
            except json.JSONDecodeError:
                continue