#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from kubernetes import client, config


# ---------------------------------------------------------------------------
# Existing trust-matrix commands
# ---------------------------------------------------------------------------

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

        # Remove the immunity label
        ai_config["trustedIdentities"].remove(label)

        cm.data['ai-config.json'] = json.dumps(ai_config, indent=2)
        v1.patch_namespaced_config_map(name=config_map_name, namespace=namespace, body=cm)

        print(f" Successfully revoked trusted identity: {label}")
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


def apply_encryption_chart(chart_path: str, namespace: str):
    """
    Applies the auranet-encryption chart directly via kubectl, since it is a
    plain set of Kubernetes manifests and is NOT packaged as a Helm chart.
    """
    print(f"Applying auranet-encryption manifests from '{chart_path}' (kubectl, not Helm)...")
    cmd = ["kubectl", "apply", "-f", chart_path, "-n", namespace]
    _run(cmd)
    print("✅ auranet-encryption manifests applied.")


def delete_encryption_chart(chart_path: str, namespace: str):
    """
    Removes the auranet-encryption manifests via kubectl delete.
    """
    print(f"Deleting auranet-encryption manifests from '{chart_path}' (kubectl, not Helm)...")
    cmd = ["kubectl", "delete", "-f", chart_path, "-n", namespace, "--ignore-not-found"]
    _run(cmd)
    print("✅ auranet-encryption manifests removed.")


def install_core(release_name: str, chart_path: str, namespace: str,
                  create_namespace: bool, values_file: str | None,
                  encryption: bool, encryption_path: str):
    """
    Installs the auranet-core chart (a local, unpackaged Helm chart directory)
    using `helm install`.
    """
    print(f"Installing Helm release '{release_name}' from local chart '{chart_path}'...")

    cmd = ["helm", "install", release_name, chart_path, "-n", namespace]
    if create_namespace:
        cmd.append("--create-namespace")
    if values_file:
        cmd.extend(["-f", values_file])

    _run(cmd)
    print(f"✅ auranet-core installed as Helm release '{release_name}' in namespace '{namespace}'.")

    if encryption:
        apply_encryption_chart(encryption_path, namespace)


def uninstall_core(release_name: str, namespace: str, encryption: bool, encryption_path: str):
    """
    Uninstalls the auranet-core Helm release.
    """
    print(f"Uninstalling Helm release '{release_name}' from namespace '{namespace}'...")
    cmd = ["helm", "uninstall", release_name, "-n", namespace]
    _run(cmd)
    print(f"✅ auranet-core Helm release '{release_name}' uninstalled.")

    if encryption:
        delete_encryption_chart(encryption_path, namespace)




if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="auranet-cli",
        description="AuraNet Command Line Interface",
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
    install_parser = subparsers.add_parser("install", help="Install the auranet-core chart via Helm (local chart).")
    install_parser.add_argument("--chart-path", default="../auranet-core/chart",
                                 help="Path to the local auranet-core Helm chart directory")
    install_parser.add_argument("--release-name", default="auranet-core",
                                 help="Helm release name to use")
    install_parser.add_argument("--namespace", default="auranet-namespace",
                                 help="The namespace to install AuraNet into")
    install_parser.add_argument("--create-namespace", action="store_true",
                                 help="Create the namespace if it doesn't already exist")
    install_parser.add_argument("--values", dest="values_file", default=None,
                                 help="Optional Helm values file to pass with -f")
    install_parser.add_argument("--encryption", action="store_true",
                                 help="Also apply the auranet-encryption manifests (kubectl, not Helm)")
    install_parser.add_argument("--encryption-path", default="./charts/auranet-encryption",
                                 help="Path to the local auranet-encryption manifests directory")

    # The 'uninstall' command
    uninstall_parser = subparsers.add_parser("uninstall", help="Uninstall the auranet-core Helm release.")
    uninstall_parser.add_argument("--release-name", default="auranet-core",
                                   help="Helm release name to uninstall")
    uninstall_parser.add_argument("--namespace", default="auranet-namespace",
                                   help="The namespace AuraNet is deployed in")
    uninstall_parser.add_argument("--encryption", action="store_true",
                                   help="Also remove the auranet-encryption manifests (kubectl, not Helm)")
    uninstall_parser.add_argument("--encryption-path", default="../auranet-encryption/charts",
                                   help="Path to the local auranet-encryption manifests directory")

    args = parser.parse_args()

    if args.command == "trust":
        inject_trusted_label(args.label, args.namespace)
    elif args.command == "untrust":
        remove_trusted_label(args.label, args.namespace)
    elif args.command == "install":
        install_core(
            release_name=args.release_name,
            chart_path=args.chart_path,
            namespace=args.namespace,
            create_namespace=args.create_namespace,
            values_file=args.values_file,
            encryption=args.encryption,
            encryption_path=args.encryption_path,
        )
    elif args.command == "uninstall":
        uninstall_core(
            release_name=args.release_name,
            namespace=args.namespace,
            encryption=args.encryption,
            encryption_path=args.encryption_path,
        )
    else:
        parser.print_help()
