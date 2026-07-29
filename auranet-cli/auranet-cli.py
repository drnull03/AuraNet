#!/usr/bin/env python3
"""
@file auranet-cli.py
@brief AuraNet Command Line Interface.

Provides administrative commands for managing AuraNet deployments,
including installing and uninstalling core components, managing trusted
eBPF identities, and updating Zero Trust configuration through the
Kubernetes API.
"""

import argparse
import json
import subprocess
import sys
from kubernetes import client, config
import os
import re

VERSION='v1.0.0'





# Bold Cyan ASCII Logo
LOGO = r"""[1;36m                                                                                            
                                          .+=.        .=+.                                          
                                           .*@-      -@#.                                           
                                            .#@+#%%#+@#.                                            
                       ..-==+***++==:.     .:%@%++++%@%:.     .:==++***+==-..                       
                     -*@@%#*++++++*%@@*-.  :#@=      =@%:  .-*@@%*++++++*#%@@*-                     
                     .*@%:        ...-+@*..*@%        %@#..*@+-...        .#@*.                     
                      .+@%-.  ..........-: +%@.      .@%+ .-..........  .-#@+.                      
                        :#@#-...-*******=  .*@%-.  .-%@#.  =*******-...:#@#:.                       
                         .:#@%%@%==-.. ..   .-%@@%%@@%-.   .....:==%@%%@#-.                         
                         .-%@%+@@@%####%*   .. .:--:....   *%####%@@@+%@%=.                         
                        .#@#-.  ...:::.  .=##############=.  .:::...  .-#@#:.                       
                       :%%+.           .*%@@@@@@@@@@@@@@@@%*..          .+%%:                       
                      .@@@%#-.......+%%@@*..            ..*@@%%+:......-#%@@@.                      
                        .:+@@@@@@%@@@@:..  .=++++++++++=.  ..:@@@@@@@@@@@*:..                       
                                        .*@@@@@@@@@@@@@@@@*:                                        
                                 .+=  .@@@*:.          ..*@@@:  =*.                                 
                                .=@=  -@%==================#@-  =@=.                                
                                .=@=  =@@%%%%%%%%%%%%%%%%%%@@+  -@+.                                
                                .=@=  -@# ...          ... *@=  =@+.                                
                                .=@=. .@%+================+%@: .=@=.                                
                                .-@#:  *@%####*######*####%@#. :#@=.                                
                                 .+@=. :%@+.            .+@%:..=@*.                                 
                              ....-%@-..:#@*============*@%-..-@%=....                              
                                  .=%@= .:*@@@********@@@*:. -@%=.                                  
                                  ..-%@*. .-#@@+-  -+@@#-. .+@%=..                                  
                                  .. .*@%=. .:+@@%%@@+:. .=%@*. ..                                  
                                      .:#@%+.  .:==:.. .+%@#-.                                      
                                       ..:#@@#+      +#@@#:..                                       
                                          ..-#@@%**%@@%-..                                          
                                             ..:=##=:..                                             
                                                 ..                                                                                                                                       
[0m"""  


def print_logo():
    print(LOGO)



def update_bootstrap_rules(file_path: str, release_name: str, chart_path: str, namespace: str):
    """
    Reads a local configuration file, validates the rule syntax, 
    and applies it via a Helm upgrade to trigger the bootstrap Job.
    """
    if not os.path.exists(file_path):
        print(f"❌ Error: File '{file_path}' not found.")
        sys.exit(1)

    with open(file_path, 'r') as f:
        content = f.read()

    lines = content.split('\n')
    # Exact regex match from your index.js parsing logic
    rule_pattern = re.compile(r"^\d+\.\s*([a-zA-Z0-9-]+)\s*->\s*([a-zA-Z0-9-]+):(\d+)$")

    valid_rules = 0
    for i, line in enumerate(lines):
        trimmed = line.strip()
        if not trimmed:
            continue
        
        if not rule_pattern.match(trimmed):
            print(f"❌ Validation Error on line {i+1}: '{trimmed}' is invalid.")
            print("   Expected format: '1.source-app -> destination-app:port'")
            sys.exit(1)
            
        valid_rules += 1

    if valid_rules == 0:
        print("⚠️  Warning: No valid rules found in the file. Exiting.")
        sys.exit(0)

    print(f"✅ Validated {valid_rules} rules locally. Applying to cluster via Helm...")

    # Uses subprocess to safely pass the multi-line string directly to Helm
    cmd = [
        "helm", "upgrade", release_name, chart_path,
        "-n", namespace,
        "--reuse-values",
        "--set", f"naiveConf={content}"
    ]
    _run(cmd)
    print("✅ Bootstrap rules updated. Kubernetes is recreating the Job.")



def run_stress_test(test_type: str):
    """
    Executes a stress test script from the ../stress_tests directory.
    """
    # Map the CLI argument to your specific file names
    file_map = {
        "light": "light_load.js",
        "spike": "spike_load.js",
        "soak": "soak_test.js",
        "wave": "wave_test.js",
        "breakpoint": "breakpoint_test.js"
    }
    
    file_path = f"../stress_tests/{file_map[test_type]}"
    
    print(f"🚀 Initiating '{test_type}' stress test...")
    # Assuming k6 is your runner. Change to ["node", file_path] if using standard Node.js
    cmd = ["k6", "run", file_path]
    _run(cmd)
    print(f"✅ Stress test '{test_type}' completed successfully.")





def restart_workload(workload: str, namespace: str = "default"):
    """
    Restarts a Kubernetes deployment using kubectl rollout restart.
    """
    print(f"Restarting deployment '{workload}' in namespace '{namespace}'...")
    cmd = ["kubectl", "rollout", "restart", f"deployment/{workload}", "-n", namespace]
    _run(cmd)
    print(f"✅ Successfully triggered restart for deployment '{workload}'.")





def inject_trusted_label(label: str, namespace: str = "auranet-namespace"):
    """
    Connects to the K8s API, modifies the AuraNet ConfigMap in memory,
    and patches the live cluster to trigger a hot-reload on all edge nodes.
    """
    try:
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
            print(f"⚠️  The eBPF label '{label}' is already in the trust matrix. Exiting.")
            sys.exit(0)

        ai_config["trustedIdentities"].append(label)

        cm.data['ai-config.json'] = json.dumps(ai_config, indent=2)
        v1.patch_namespaced_config_map(name=config_map_name, namespace=namespace, body=cm)

        print(f"✅ Successfully injected trusted identity: {label}")
        print(f"Kubernetes is propagating the update to all AuraNet edge agents. Hot-reload imminent.")

    except Exception as e:
        print(f"❌ Failed to update the cluster: {e}")
        sys.exit(1)


def remove_trusted_label(label: str, namespace: str = "auranet-namespace"):
    """
    Removes an existing eBPF label from the ConfigMap trust matrix to revoke immunity.
    """
    try:
        config.load_kube_config()
        v1 = client.CoreV1Api()
        config_map_name = "auranet-engine-config"

        print(f"Connecting to Kubernetes API in namespace '{namespace}'...")

        cm = v1.read_namespaced_config_map(name=config_map_name, namespace=namespace)
        ai_config_str = cm.data.get('ai-config.json', '{}')
        ai_config = json.loads(ai_config_str)

        if "trustedIdentities" not in ai_config or label not in ai_config["trustedIdentities"]:
            print(f"The eBPF label '{label}' is not currently in the trust matrix. Exiting.")
            sys.exit(0)

        ai_config["trustedIdentities"].remove(label)

        cm.data['ai-config.json'] = json.dumps(ai_config, indent=2)
        v1.patch_namespaced_config_map(name=config_map_name, namespace=namespace, body=cm)

        print(f"✅ Successfully revoked trusted identity: {label}")
        print(f"Kubernetes is propagating the update. The AI will now evaluate this workload.")

    except Exception as e:
        print(f"❌ Failed to update the cluster: {e}")
        sys.exit(1)


def _run(cmd: list[str]):
    """Run a subprocess command, streaming output, and exit on failure."""
    print(f"$ {' '.join(cmd)}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"❌ Command failed with exit code {result.returncode}: {' '.join(cmd)}")
        sys.exit(result.returncode)


def install_encryption(release_name: str, chart_path: str, namespace: str, create_namespace: bool):
    """
    Installs the auranet-encryption Helm deployment.
    """
    print(f"Installing '{release_name}' Helm release from '{chart_path}'...")
    cmd = ["helm", "install", release_name, chart_path, "-n", namespace]
    if create_namespace:
        cmd.append("--create-namespace")
    
    _run(cmd)
    print("✅ auranet-encryption Helm release installed.")


def uninstall_encryption(release_name: str, namespace: str):
    """
    Uninstalls the auranet-encryption Helm deployment.
    """
    print(f"Uninstalling '{release_name}' Helm release from namespace '{namespace}'...")
    cmd = ["helm", "uninstall", release_name, "-n", namespace]
    _run(cmd)
    print("✅ auranet-encryption Helm release uninstalled.")


def install_core(release_name: str, chart_path: str, namespace: str,
                  create_namespace: bool, values_file: str | None):
    """
    Installs the auranet-core Helm chart.
    """
    print(f"Installing Helm release '{release_name}' from local chart '{chart_path}'...")

    cmd = ["helm", "install", release_name, chart_path, "-n", namespace]
    if create_namespace:
        cmd.append("--create-namespace")
    if values_file:
        cmd.extend(["-f", values_file])

    _run(cmd)
    print(f"✅ auranet-core installed as Helm release '{release_name}' in namespace '{namespace}'.")


def uninstall_core(release_name: str, namespace: str):
    """
    Uninstalls the auranet-core Helm release.
    """
    print(f"Uninstalling Helm release '{release_name}' from namespace '{namespace}'...")
    cmd = ["helm", "uninstall", release_name, "-n", namespace]
    _run(cmd)
    print(f"✅ auranet-core Helm release '{release_name}' uninstalled.")


if __name__ == "__main__":
    print_logo()
    parser = argparse.ArgumentParser(
        prog="auranet-cli",
        description="AuraNet Command Line Interface",
    )
    
    # Adding the version flag with Bold Cyan ANSI color codes
    parser.add_argument(
        "-v", "--version", 
        action="version", 
        version=f"\033[1;36mAuraNet CLI {VERSION}\033[0m"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # The 'trust' command
    trust_parser = subparsers.add_parser("trust", help="Inject a new eBPF label into the Zero Trust matrix.")
    trust_parser.add_argument("--label", required=True, help="The exact K8s/eBPF label (e.g., k8s:app=payment-gateway)")
    trust_parser.add_argument("--namespace", default="auranet-namespace", help="The namespace AuraNet is deployed in")

    # The 'untrust' command
    untrust_parser = subparsers.add_parser("untrust", help="Revoke an eBPF label from the Zero Trust matrix.")
    untrust_parser.add_argument("--label", required=True, help="The exact K8s/eBPF label to remove")
    untrust_parser.add_argument("--namespace", default="auranet-namespace", help="The namespace AuraNet is deployed in")

    # The 'install' command
    install_parser = subparsers.add_parser("install", help="Install auranet components via Helm.")
    install_parser.add_argument("--chart-path", default="../auranet-core/chart",
                                 help="Path to the local auranet-core Helm chart directory")
    install_parser.add_argument("--release-name", default="auranet-core",
                                 help="Helm release name to use for the core deployment")
    install_parser.add_argument("--namespace", default="auranet-namespace",
                                 help="The namespace to install AuraNet into")
    install_parser.add_argument("--create-namespace", action="store_true",
                                 help="Create the namespace if it doesn't already exist")
    install_parser.add_argument("--values", dest="values_file", default=None,
                                 help="Optional Helm values file to pass with -f")
    install_parser.add_argument("--encryption", action="store_true",
                                 help="Install ONLY the encryption chart, skipping the core chart")
    install_parser.add_argument("--encryption-path", default="../PQC/auranet-encryption/",
                                 help="Path to the local auranet-encryption Helm chart directory")
    install_parser.add_argument("--encryption-release-name", default="auranet-encryption",
                                 help="Helm release name for the encryption deployment")

    # The 'uninstall' command
    uninstall_parser = subparsers.add_parser("uninstall", help="Uninstall auranet components via Helm.")
    uninstall_parser.add_argument("--release-name", default="auranet-core",
                                   help="Helm release name for the core deployment to uninstall")
    uninstall_parser.add_argument("--namespace", default="auranet-namespace",
                                   help="The namespace AuraNet is deployed in")
    uninstall_parser.add_argument("--encryption", action="store_true",
                                   help="Uninstall ONLY the encryption chart, skipping the core chart")
    uninstall_parser.add_argument("--encryption-release-name", default="auranet-encryption",
                                   help="Helm release name for the encryption deployment to uninstall")


    # The 'restart' command
    restart_parser = subparsers.add_parser("restart", help="Restart a Kubernetes deployment.")
    restart_parser.add_argument("--workload", required=True, help="The name of the deployment to restart (e.g., frontend-ui)")
    restart_parser.add_argument("--namespace", default="default", help="The namespace of the deployment (defaults to 'default')")


    # The 'stress' command
    stress_parser = subparsers.add_parser("stress", help="Run system stress tests against the cluster.")
    stress_parser.add_argument(
        "--type", 
        required=True, 
        choices=["light", "spike", "soak", "wave", "breakpoint"], 
        help="The type of stress test to execute."
    )

    # The 'bootstrap-rules' command
    bootstrap_parser = subparsers.add_parser("bootstrap-rules", help="Update naive.conf network policies from a local file.")
    bootstrap_parser.add_argument("file", help="Path to the local .conf file containing the new rules")
    bootstrap_parser.add_argument("--release-name", default="auranet-bootstrap-chart", help="Helm release name for the bootstrap deployment")
    bootstrap_parser.add_argument("--chart-path", default="../auranet-bootstrap/chart", help="Path to the local bootstrap Helm chart")
    bootstrap_parser.add_argument("--namespace", default="auranet-namespace", help="The namespace the bootstrap job runs in")

    args = parser.parse_args()

    if args.command == "trust":
        inject_trusted_label(args.label, args.namespace)
    elif args.command == "untrust":
        remove_trusted_label(args.label, args.namespace)
    elif args.command == "install":
        # Decoupled installation logic
        if args.encryption:
            install_encryption(
                release_name=args.encryption_release_name,
                chart_path=args.encryption_path,
                namespace=args.namespace,
                create_namespace=args.create_namespace
            )
        else:
            install_core(
                release_name=args.release_name,
                chart_path=args.chart_path,
                namespace=args.namespace,
                create_namespace=args.create_namespace,
                values_file=args.values_file
            )
    elif args.command == "uninstall":
        # Decoupled uninstallation logic
        if args.encryption:
            uninstall_encryption(
                release_name=args.encryption_release_name,
                namespace=args.namespace
            )
        else:
            uninstall_core(
                release_name=args.release_name,
                namespace=args.namespace
            )
    elif args.command == "restart":
        restart_workload(args.workload, args.namespace)


    elif args.command == "stress":
        run_stress_test(args.type)

    elif args.command == "bootstrap-rules":
        update_bootstrap_rules(
            file_path=args.file,
            release_name=args.release_name,
            chart_path=args.chart_path,
            namespace=args.namespace
        )

    else:
        # Failsafe if run without a subcommand and no --version flag
        parser.print_help()









#auranet-cli  install --config naive.conf
#auranet-cli inject  ./model.pt