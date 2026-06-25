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
        
        # RULE 1: Cryptographic Identity Override
        # If the Linux kernel proves this packet came from a trusted system component,
        # we override the AI to prevent it from blocking legitimate updates.
        for label in source_labels:
            if label in trusted_identities:
                return "Safe"
                
        return "Unknown"