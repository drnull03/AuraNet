import json
import subprocess
import numpy as np

import config

class HubbleStreamProcessor:
    def __init__(self):
        # Normalization constants (matching the monolithic processor)
        self.MAX_PATH_DEPTH = 10.0
        self.MAX_QUERY_PARAMS = 10.0
        self.MAX_HEADER_SIZE = 8192.0
        self.MAX_URL_LENGTH = 500.0

        # Method lookup sets for fast O(1) checks during live streaming
        self.valid_methods = {'GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS', ''}
        self.read_methods = {'GET', 'OPTIONS', 'HEAD'}
        self.write_methods = {'POST', 'PUT', 'DELETE', 'PATCH'}

        # Connect to the central Relay (Removed the --node flag to prevent the CLI crash)
        self.command = [
            "hubble", 
            "observe", 
            "--server", config.HUBBLE_RELAY_ADDRESS,
            "-f", 
            "-o", "json"
        ]

    def is_external_ip(self, ip_str):
        if not ip_str: 
            return 0.0
        if ip_str.startswith("10.") or ip_str.startswith("192.168.") or ip_str.startswith("172."):
            return 0.0
        return 1.0

    def process_event(self, event):
        """
        Filters and converts a single real-time packet into the 13-dim generic tensor.
        Returns None if the packet should be ignored based on our training rules.
        """
        # --- SOFTWARE-LEVEL NODE FILTERING ---
        event_node = event.get("node_name", "")
        if event_node != config.NODE_NAME:
            return None

        flow = event.get("flow", {})
        if not flow:
            return None

        verdict = flow.get("verdict", "")
        source_labels = flow.get("source", {}).get("labels", [])
        event_type = flow.get("event_type", {}).get("type", 0)
        drop_reason = flow.get("drop_reason_desc", "")

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

        traffic_direction = flow.get("traffic_direction", "UNKNOWN")
        ip_source = flow.get("IP", {}).get("source", "")

        http_data = l7.get("http", {}) if l7 else {}
        method = http_data.get("method", "")
        url = str(http_data.get("url", ""))
        status_code = http_data.get("code", 0)
        
        headers = http_data.get("headers", [])
        header_size = sum(len(h.get("key", "")) + len(h.get("value", "")) for h in headers)

        features = np.zeros(13, dtype=np.float32)

        # 1. is_inbound
        features[0] = 1.0 if traffic_direction == 'INGRESS' else 0.0
        
        # 2. is_outbound
        features[1] = 1.0 if traffic_direction == 'EGRESS' else 0.0
        
        # 3. is_external_ip
        features[2] = self.is_external_ip(ip_source)
        
        # 4. is_dropped
        features[3] = 1.0 if verdict == 'DROPPED' else 0.0
        
        # 5. is_unknown_method
        features[4] = 0.0 if method in self.valid_methods else 1.0
        
        # 6. is_http
        features[5] = 1.0 if is_http_l7 else 0.0
        
        # 7. is_read_method
        features[6] = 1.0 if method in self.read_methods else 0.0
        
        # 8. is_write_method
        features[7] = 1.0 if method in self.write_methods else 0.0
        
        # 9. url_path_depth
        path_depth = url.count('/')
        features[8] = min(path_depth / self.MAX_PATH_DEPTH, 1.0)
        
        # 10. query_param_count
        param_count = url.count('&') + 1 if '?' in url else 0
        features[9] = min(param_count / self.MAX_QUERY_PARAMS, 1.0)
        
        # 11. req_header_size
        features[10] = min(header_size / self.MAX_HEADER_SIZE, 1.0)
        
        # 12. url_length
        features[11] = min(len(url) / self.MAX_URL_LENGTH, 1.0)
        
        # 13. is_error_status
        features[12] = 1.0 if status_code >= 400 else 0.0

        return features

    def stream_traffic(self):
        """
        Continuously yields (raw_json, feature_array) for valid packets.
        """
        print(f"[Streamer] Connecting to Relay at {config.HUBBLE_RELAY_ADDRESS}...")
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
                
                # Apply filters and extract generic features
                feature_array = self.process_event(event)
                
                # If it passed all filters, yield the 13-dim array
                if feature_array is not None:
                    yield event, feature_array
                
            except json.JSONDecodeError:
                continue