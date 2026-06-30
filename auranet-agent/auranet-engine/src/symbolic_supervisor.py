import config

class SymbolicSupervisor:
    def evaluate(self, raw_event):
        """
        Evaluates the raw Hubble packet against strict, deterministic Zero Trust rules.
        Returns 'Safe' if an override condition is met, otherwise 'Unknown' (to pass to AI),
        or a specific symbolic threat signature if a naive structural anomaly is detected.
        """
        source_labels = raw_event.get("flow", {}).get("source", {}).get("labels", [])
        trusted_identities = config.ai.TRUSTED_IDENTITIES
        
        # RULE 1: Cryptographic Identity Override
        for label in source_labels:
            if label in trusted_identities:
                return "Safe"

        l7_data = raw_event.get("flow", {}).get("l7", {})
        if l7_data and l7_data.get("type") == "REQUEST":
            http_data = l7_data.get("http", {})
            url = str(http_data.get("url", ""))
            method = str(http_data.get("method", ""))
            protocol = str(http_data.get("protocol", ""))
            headers = http_data.get("headers", [])

            

            if len(url) > 512:
                return "symbolic_uri_too_large"

            if "%00" in url or "\x00" in url:
                return "symbolic_null_byte_evasion"

            if url.count("/") > 15:
                return "symbolic_excessive_path_depth"

            if url.count("&") > 50:
                return "symbolic_excessive_query_params"

            if url.count("%") > 20:
                return "symbolic_excessive_url_encoding"

            # NEW: Non-ASCII / Binary Payload in URL
            # Standard URIs should be printable ASCII. Raw binary bytes indicate 
            # shellcode injection or memory corruption attempts.
            if any(ord(c) > 127 for c in url):
                return "symbolic_non_ascii_url"

            

            if method in ["TRACE", "TRACK", "CONNECT"]:
                return "symbolic_banned_method"

            # NEW: Anomalous Method Length
            # Valid HTTP methods (GET, POST, OPTIONS) are short. 
            # Fuzzers try to overflow method parsers by sending 50+ byte strings.
            if len(method) > 15:
                return "symbolic_anomalous_method_length"

            
            
            total_header_size = 0
            header_counts = {}
            content_length = 0

            # NEW: Excessive Header Count (Memory Exhaustion / Slowloris)
            # Instead of one massive header, attackers send hundreds of tiny ones 
            # to exhaust backend dictionary allocations.
            if len(headers) > 50:
                return "symbolic_excessive_header_count"

            for h in headers:
                key = h.get("key", "").lower()
                val = str(h.get("value", ""))
                total_header_size += len(key) + len(val)
                
                header_counts[key] = header_counts.get(key, 0) + 1
                
                if key == "content-length":
                    try:
                        content_length = int(val)
                    except ValueError:
                        pass

            if total_header_size > 8192:
                return "symbolic_massive_headers"

            if "host" not in header_counts and "HTTP/1.1" in protocol:
                return "symbolic_missing_host_header"

            
            # Legitimate browsers, APIs, and microservices almost universally declare a User-Agent.
            # Lazy botnets, curl scripts, and naive scanners frequently omit it entirely.
            if "user-agent" not in header_counts:
                return "symbolic_missing_user_agent"

            if method == "GET" and content_length > 0:
                return "symbolic_get_with_body"

            if header_counts.get("host", 0) > 1 or header_counts.get("content-length", 0) > 1:
                return "symbolic_duplicate_critical_headers"

            if "content-length" in header_counts and "transfer-encoding" in header_counts:
                return "symbolic_http_desync_attempt"

        return "Unknown"