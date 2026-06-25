import config

class SymbolicSupervisor:
    def evaluate(self, raw_event):
        """
        Evaluates the raw Hubble packet against strict, deterministic Zero Trust rules.
        Returns 'Safe' if an override condition is met, otherwise 'Unknown'.
        """
        # Extract the kernel-verified source labels from the Hubble event
        
        # SPIRE and SPIFFE trust is used here 


        # the trust flow work as follows
        # we trust in auranet ->  k8s api -> SPIRE and SPIFFE -> programmer newly injected workload
        #in other words we trust auranet thus we trust the programmer 
        # in production we use TPM we used PSAT here but it is bascially the same thing
        source_labels = raw_event.get("flow", {}).get("source", {}).get("labels", [])
        
        
        trusted_identities = config.ai.TRUSTED_IDENTITIES
        

        # might be the only rule we add thus this is not enough to call nuro-symbolic AI 
        # we will see how this goes

        # RULE 1: Cryptographic Identity Override
        # If the Linux kernel proves this packet came from a trusted system component,
        # we override the AI to prevent it from blocking legitimate updates.
        for label in source_labels:
            if label in trusted_identities:
                return "Safe"

        l7_data = raw_event.get("flow", {}).get("l7", {})
        if l7_data and l7_data.get("type") == "REQUEST":
            http_data = l7_data.get("http", {})
            url = http_data.get("url", "")
            method = http_data.get("method", "")

            # Rule 1: Massive URI/URL (Buffer Overflow / Massive Injection)
            # 2048 characters is the standard max limit for safe URLs
            if len(url) > 1024:
                return "symbolic_uri_too_large"

            # Rule 2: Path Traversal Attempts
            if "../" in url or "%2e%2e%2f" in url.lower():
                return "symbolic_path_traversal"

            # Rule 3: Banned/Dangerous HTTP Methods
            if method in ["TRACE", "TRACK", "CONNECT"]:
                return "symbolic_banned_method"
                
        return "Unknown"




