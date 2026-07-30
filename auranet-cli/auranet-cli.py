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
import tempfile

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

def update_controller_config(updates: dict, release_name: str, chart_path: str, namespace: str):
    """
    Dynamically updates AuraNet Controller FL parameters using Helm overrides.
    """
    cmd = ["helm", "upgrade", release_name, chart_path, "-n", namespace, "--reuse-values"]
    
    count = 0
    for key, val in updates.items():
        if val is not None:
            cmd.extend(["--set", f"appConfig.{key}={val}"])
            count += 1
            
    if count == 0:
        print("⚠️  No configuration values provided. Pass at least one flag (e.g., --proximal-mu).")
        sys.exit(0)

    print(f"⚙️  Applying {count} configuration updates to AuraNet Controller...")
    _run(cmd)
    print("✅ Controller configuration updated. Watchdog hot-reload triggered.")

def update_runtime_threats(file_path: str, release_name: str, chart_path: str, namespace: str):
    """
    Reads a raw THREAT_MAP.conf file, formats it into a Helm values structure, 
    and updates the AuraNet Runtime eBPF agent.
    """
    if not os.path.exists(file_path):
        print(f"❌ Error: File '{file_path}' not found.")
        sys.exit(1)

    with open(file_path, 'r') as f:
        content = f.read()

    # Format as a Helm multiline string under the 'runtime' dictionary key
    yaml_content = "runtime:\n  threatMapConf: |-\n"
    for line in content.split('\n'):
        yaml_content += f"    {line}\n"
        
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
        tmp.write(yaml_content)
        tmp_path = tmp.name

    try:
        print("🚀 Pushing updated Threat Map to AuraNet Runtime...")
        _run(["helm", "upgrade", release_name, chart_path, "-n", namespace, "--reuse-values", "-f", tmp_path])
        print("✅ Runtime Threat Map updated successfully. Hot-reload triggered.")
    finally:
        os.remove(tmp_path)


def update_engine_config(updates: dict, release_name: str, chart_path: str, namespace: str):
    """
    Dynamically updates AuraNet Engine AI parameters using a dictionary of overrides.
    """
    cmd = ["helm", "upgrade", release_name, chart_path, "-n", namespace, "--reuse-values"]
    
    count = 0
    for key, val in updates.items():
        if val is not None:
            cmd.extend(["--set", f"engine.aiConfig.{key}={val}"])
            count += 1
            
    if count == 0:
        print(" No configuration values provided. Pass at least one flag (e.g., --learning-rate).")
        sys.exit(0)

    print(f" Applying {count} AI configuration updates to AuraNet Engine...")
    _run(cmd)
    print("✅ Engine configuration updated. AI hot-reload triggered.")





def update_threat_matrix(file_path: str, namespace: str):
    """
    Reads a raw threat_matrix.conf file, formats it into a Helm values.yaml structure, 
    and updates both AutoHeal and ZTC simultaneously to prevent synchronization drift.
    """
    if not os.path.exists(file_path):
        print(f"❌ Error: File '{file_path}' not found.")
        sys.exit(1)

    with open(file_path, 'r') as f:
        content = f.read()

    # Format as a Helm multiline string (matching the format in values.yaml)
    yaml_content = "threatMatrix: |-\n"
    for line in content.split('\n'):
        yaml_content += f"  {line}\n"
        
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
        tmp.write(yaml_content)
        tmp_path = tmp.name

    try:
        print("Pushing synchronized Threat Matrix to AuraNet AutoHeal...")
        _run(["helm", "upgrade", "auranet-autoheal", "../auranet-autoheal/chart", "-n", namespace, "--reuse-values", "-f", tmp_path])
        
        print("\nPushing synchronized Threat Matrix to AuraNet ZTC...")
        _run(["helm", "upgrade", "auranet-ztc", "../auranet-ztc/chart", "-n", namespace, "--reuse-values", "-f", tmp_path])
        
        print("\nThreat Matrix synchronized successfully. Hot-reload triggered on both microservices.")
    finally:
        os.remove(tmp_path)


def update_ztc_config(window_time: str, threshold: str, namespace: str):
    """
    Updates the ZTC sliding window and trust threshold parameters.
    """
    cmd = ["helm", "upgrade", "auranet-ztc", "../auranet-ztc/chart", "-n", namespace, "--reuse-values"]
    
    updates = 0
    if window_time:
        cmd.extend(["--set", f"ztcConfig.windowTimeMs={window_time}"])
        updates += 1
    if threshold:
        cmd.extend(["--set", f"ztcConfig.trustThreshold={threshold}"])
        updates += 1
        
    if updates == 0:
        print("⚠️  No configuration values provided to update. Use --window-time or --threshold.")
        sys.exit(0)

    print(f"⚙️  Applying {updates} configuration updates to AuraNet ZTC...")
    _run(cmd)
    print("✅ ZTC configuration updated. Hot-reload triggered.")




def update_bootstrap_rules(file_path: str, namespace: str):
    """
    Reads a local configuration file, validates the rule syntax, 
    and applies it via Helm to both the bootstrap job and the UI topology.
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
        # Skip empty lines and comments
        if not trimmed or trimmed.startswith('#'):
            continue
        
        if not rule_pattern.match(trimmed):
            print(f"❌ Validation Error on line {i+1}: '{trimmed}' is invalid.")
            print("   Expected format: '1.source-app -> destination-app:port'")
            sys.exit(1)
            
        valid_rules += 1

    if valid_rules == 0:
        print("⚠️  Warning: No valid rules found in the file. Exiting.")
        sys.exit(0)

    print(f"✅ Validated {valid_rules} rules locally. Synchronizing cluster...")

    # Create temporary YAML for Bootstrap (uses naiveConf)
    boot_yaml = "naiveConf: |-\n"
    for line in lines:
        boot_yaml += f"  {line}\n"
        
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp_boot:
        tmp_boot.write(boot_yaml)
        boot_path = tmp_boot.name

    # Create temporary YAML for UI (uses topologyConfig)
    ui_yaml = "topologyConfig: |-\n"
    for line in lines:
        ui_yaml += f"  {line}\n"
        
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp_ui:
        tmp_ui.write(ui_yaml)
        ui_path = tmp_ui.name

    try:
        print(" Pushing rules to AuraNet Bootstrap...")
        _run(["helm", "upgrade", "auranet-bootstrap-chart", "../auranet-bootstrap/chart", "-n", namespace, "--reuse-values", "-f", boot_path])
        
        print("\n Pushing rules to AuraNet UI...")
        _run(["helm", "upgrade", "auranet-ui", "../auranet-ui/chart", "-n", namespace, "--reuse-values", "-f", ui_path])
        
        print("\n✅ Topology synchronized successfully across Bootstrap and UI.")
    finally:
        os.remove(boot_path)
        os.remove(ui_path)

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
    # The 'bootstrap-rules' command
    bootstrap_parser = subparsers.add_parser("bootstrap-rules", help="Update naive.conf network policies for both Bootstrap and UI.")
    bootstrap_parser.add_argument("file", help="Path to the local .conf file containing the new rules")
    bootstrap_parser.add_argument("--namespace", default="auranet-namespace", help="The namespace the services run in")

    # The 'threat-matrix' command
    threat_parser = subparsers.add_parser("threat-matrix", help="Update the Threat Matrix for both AutoHeal and ZTC simultaneously.")
    threat_parser.add_argument("file", help="Path to the local threat_matrix.conf file")
    threat_parser.add_argument("--namespace", default="auranet-namespace", help="The namespace the services run in")

    # The 'ztc-config' command
    ztc_config_parser = subparsers.add_parser("ztc-config", help="Update the ZTC sliding window and quarantine threshold.")
    ztc_config_parser.add_argument("--window-time", help="New sliding window time in milliseconds (e.g., 600000 for 10 mins)")
    ztc_config_parser.add_argument("--threshold", help="New trust score threshold for quarantine (e.g., 10)")
    ztc_config_parser.add_argument("--namespace", default="auranet-namespace", help="The namespace the ZTC runs in")

    # The 'runtime-threats' command
    runtime_parser = subparsers.add_parser("runtime-threats", help="Update the Runtime eBPF Threat Map from a local file.")
    runtime_parser.add_argument("file", help="Path to the local THREAT_MAP.conf file")
    runtime_parser.add_argument("--release-name", default="auranet-agent", help="Helm release name for the agent deployment")
    runtime_parser.add_argument("--chart-path", default="../auranet-agent/chart", help="Path to the local auranet-agent Helm chart")
    runtime_parser.add_argument("--namespace", default="auranet-namespace", help="The namespace the agent runs in")

    # The 'engine-config' command
    # The 'engine-config' command
    engine_parser = subparsers.add_parser("engine-config", help="Update the AuraNet Engine AI parameters.")
    engine_parser.add_argument("--input-dim", dest="inputDim", help="New input dimension (e.g., 13)")
    engine_parser.add_argument("--tripwire", dest="tripwireThreshold", help="New base tripwire threshold (e.g., 0.08)")
    engine_parser.add_argument("--train-interval", dest="localTrainIntervalSec", help="Local training interval in seconds (e.g., 120)")
    engine_parser.add_argument("--max-buffer", dest="maxBufferSize", help="Max benign traffic buffer size (e.g., 5000)")
    engine_parser.add_argument("--epochs", dest="localEpochs", help="Local training epochs (e.g., 5)")
    engine_parser.add_argument("--learning-rate", dest="learningRate", help="New FedProx learning rate (e.g., 0.005)")
    engine_parser.add_argument("--nlp-tripwire", dest="nlpTripwire", help="New NLP URL threshold (e.g., 2.0)")
    engine_parser.add_argument("--nlp-body-tripwire", dest="nlpBodyTripwire", help="New NLP Body threshold (e.g., 2.0)")
    engine_parser.add_argument("--z-score", dest="zScoreThreshold", help="New dynamic Z-Score threshold (e.g., 3.0)")
    engine_parser.add_argument("--z-score-window", dest="zScoreWindowSize", help="Window size for Z-score calculation (e.g., 1000)")
    engine_parser.add_argument("--third-brain", dest="thirdBrain", help="Toggle third brain (true or false)")
    
    engine_parser.add_argument("--release-name", default="auranet-agent", help="Helm release name for the agent deployment")
    engine_parser.add_argument("--chart-path", default="../auranet-agent/chart", help="Path to the local auranet-agent Helm chart")
    engine_parser.add_argument("--namespace", default="auranet-namespace", help="The namespace the agent runs in")


    # The 'controller-config' command
    controller_parser = subparsers.add_parser("controller-config", help="Update the AuraNet Controller FL parameters.")
    controller_parser.add_argument("--fl-rounds", dest="fl_rounds", help="Total number of federated learning rounds (e.g., 1000)")
    controller_parser.add_argument("--min-clients", dest="min_available_clients", help="Minimum clients required to start a round (e.g., 2)")
    controller_parser.add_argument("--fraction-fit", dest="fraction_fit", help="Fraction of clients sampled per round (e.g., 1.0)")
    controller_parser.add_argument("--round-timeout", dest="round_timeout_seconds", help="Aggregation delay between rounds in seconds (e.g., 600)")
    controller_parser.add_argument("--proximal-mu", dest="proximal_mu", help="Proximal penalty mu value for FedProx (e.g., 0.1)")
    
    controller_parser.add_argument("--release-name", default="auranet-controller", help="Helm release name for the controller deployment")
    controller_parser.add_argument("--chart-path", default="../auranet-controller/chart", help="Path to the local auranet-controller Helm chart")
    controller_parser.add_argument("--namespace", default="auranet-namespace", help="The namespace the controller runs in")

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
            namespace=args.namespace
        )

    elif args.command == "threat-matrix":
        update_threat_matrix(args.file, args.namespace)
    elif args.command == "ztc-config":
        update_ztc_config(args.window_time, args.threshold, args.namespace)

    elif args.command == "runtime-threats":
        update_runtime_threats(
            file_path=args.file,
            release_name=args.release_name,
            chart_path=args.chart_path,
            namespace=args.namespace
        )
    elif args.command == "engine-config":
        # Define the exact YAML keys we want to check
        config_keys = [
            "inputDim", "tripwireThreshold", "localTrainIntervalSec", "maxBufferSize", 
            "localEpochs", "learningRate", "nlpTripwire", "nlpBodyTripwire", 
            "zScoreThreshold", "zScoreWindowSize", "thirdBrain"
        ]
        
        # Build a dictionary of only the arguments the user provided
        updates = {key: getattr(args, key) for key in config_keys if getattr(args, key) is not None}
        
        update_engine_config(
            updates=updates,
            release_name=args.release_name,
            chart_path=args.chart_path,
            namespace=args.namespace
        )
    elif args.command == "controller-config":
        config_keys = [
            "fl_rounds", "min_available_clients", "fraction_fit", 
            "round_timeout_seconds", "proximal_mu"
        ]
        
        updates = {key: getattr(args, key) for key in config_keys if getattr(args, key) is not None}
        
        update_controller_config(
            updates=updates,
            release_name=args.release_name,
            chart_path=args.chart_path,
            namespace=args.namespace
        )

    else:
        # Failsafe if run without a subcommand and no --version flag
        parser.print_help()










#auranet-cli inject  ./model.pt