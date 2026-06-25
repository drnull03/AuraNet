import argparse
import json
import sys
from kubernetes import client, config

def inject_trusted_label(label: str, namespace: str = "auranet-namespace"):
    """
    Connects to the K8s API, modifies the AuraNet ConfigMap in memory, 
    and patches the live cluster to trigger a hot-reload on all edge nodes.
    """
    try:
        # Loads your local ~/.kube/config (or service account if run inside a pod)
        config.load_kube_config()
        v1 = client.CoreV1Api()
        
        config_map_name = "auranet-engine-config"
        
        print(f"Connecting to Kubernetes API in namespace '{namespace}'...")
        
        cm = v1.read_namespaced_config_map(name=config_map_name, namespace=namespace)
        
        ai_config_str = cm.data.get('ai-config.json', '{}')
        ai_config = json.loads(ai_config_str)
        
        if "trustedIdentities" not in ai_config:
            ai_config["trustedIdentities"] = []
            
        if label in ai_config["trustedIdentities"]:
            print(f" The eBPF label '{label}' is already in the trust matrix. Exiting.")
            sys.exit(0)
            
        ai_config["trustedIdentities"].append(label)
        
        cm.data['ai-config.json'] = json.dumps(ai_config, indent=2)
        v1.patch_namespaced_config_map(name=config_map_name, namespace=namespace, body=cm)
        
        print(f"Successfully injected trusted identity: {label}")
        print(f"Kubernetes is propagating the update to all AuraNet edge agents. Hot-reload imminent.")

    except Exception as e:
        print(f"❌ Failed to update the cluster: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AuraNet Command Line Interface")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # The 'trust' command
    trust_parser = subparsers.add_parser("trust", help="Inject a new eBPF label into the Zero Trust matrix.")
    trust_parser.add_argument("--label", required=True, help="The exact K8s/eBPF label (e.g., k8s:app=payment-gateway)")
    trust_parser.add_argument("--namespace", default="auranet-namespace", help="The namespace AuraNet is deployed in")
    
    args = parser.parse_args()
    
    if args.command == "trust":
        inject_trusted_label(args.label, args.namespace)
    else:
        parser.print_help()
