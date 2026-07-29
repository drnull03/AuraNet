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
    else:
        # Failsafe if run without a subcommand and no --version flag
        parser.print_help()





# add config option
# add stress test option 
# add restart option 
