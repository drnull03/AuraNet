# AuraNet Core: Umbrella Helm Chart

This repository contains the Umbrella Helm Chart for the complete AuraNet Zero Trust System. By leveraging an umbrella architecture, you can deploy, manage, and configure the entire decentralized network of microservices through a single `helm` command.

## Architecture

The `auranet-core` chart wraps the following nested subcharts:

* `auranet-agent` (Contains both the `auranet-engine` AI and `auranet-runtime` eBPF forwarder)
* `auranet-controller` (Federated Learning Aggregator)
* `auranet-ztc` (Zero Trust Controller)
* `autoheal` (SOAR & Remediation)
* `auranet-bootstrap-chart` (Naive Network Policies)
* `auranet-loader` (eBPF map loader)
* `auranet-ui` (Dashboard)

---

## Standard Installation

Before installing the system for the first time, you must build the internal chart dependencies.

**1. Update the dependencies:**

```bash
helm dependency update

```

*(This pulls the local `file://../` references into the `charts/` directory).*

**2. Install the full suite:**

```bash
helm install auranet . --namespace auranet-namespace --create-namespace

```

---

## Configuration & Live Modifications

You **do not** need to edit the umbrella's `values.yaml` file to change settings in the subcharts. Helm dynamically routes configurations down to the microservices based on the subchart name prefix.

You can modify these on the fly using `--set` for quick tweaks, or by passing a custom `-f custom-values.yaml` file for larger multi-line configurations. Because the Python microservices use `watchdog` and `fs.watch`, modifying these values via Helm will trigger **instant hot-reloads** across the cluster without dropping traffic.

### 1. AuraNet Agent (AI Engine & eBPF Runtime)

Because the Engine and Runtime are bundled inside the `auranet-agent` subchart, their configurations are nested under `auranet-agent.engine` and `auranet-agent.runtime`.

**Example: Tuning AI Learning Parameters**

```bash
helm upgrade --install auranet . \
  --namespace auranet-namespace \
  --set auranet-agent.engine.aiConfig.learningRate=0.005 \
  --set auranet-agent.engine.aiConfig.tripwireThreshold=0.08 \
  --set auranet-agent.engine.aiConfig.zScoreThreshold=2.5

```

**Example: Updating the eBPF Threat Map**
For multi-line strings, passing a custom YAML file is much cleaner than using `--set`.
Create a `custom-runtime.yaml`:

```yaml
auranet-agent:
  runtime:
    threatMapConf: |-
      nc=nc_execution
      bash=reverse_shell_detected
      nmap=nmap_scan_detected
      /custom/malware/path=suspicious_binary_download

```

Deploy the update:

```bash
helm upgrade --install auranet . -n auranet-namespace -f custom-runtime.yaml

```

### 2. AutoHeal & ZTC (Synchronizing the Threat Matrix)

Both the ZTC and the AutoHeal services rely on the exact same Threat Matrix. You can update both subcharts simultaneously by defining their respective keys in a single file.

Create a `custom-matrix.yaml`:

```yaml
# Target the ZTC subchart
auranet-ztc:
  threatMatrix: |-
    nc_execution=85
    privilege_escalation=100
    unknown_anomaly=45
  ztcConfig:
    windowTimeMs: 300000  # 5 minutes
    trustThreshold: 15

# Target the AutoHeal subchart
autoheal:
  threatMatrix: |-
    nc_execution=85
    privilege_escalation=100
    unknown_anomaly=45

```

Deploy the synchronized update:

```bash
helm upgrade --install auranet . -n auranet-namespace -f custom-matrix.yaml

```

### 3. AuraNet Bootstrap (Naive Policies)

The bootstrap job runs once upon deployment or upgrade. Updating the `naiveConf` will trigger Kubernetes to delete the old Job and spin up a new one to apply the Cilium policies.

**Example: Adding a new L7 path**

```bash
helm upgrade --install auranet . \
  --namespace auranet-namespace \
  --set auranet-bootstrap-chart.naiveConf="1.frontend-ui -> api-gateway:8080\n2.api-gateway -> database:5432"

```

### 4. AuraNet Controller (Federated Learning)

The centralized FL controller monitors its ConfigMap for changes to federated training rules.

**Example: Adjusting FedProx & Round Timeouts**

```bash
helm upgrade --install auranet . \
  --namespace auranet-namespace \
  --set auranet-controller.appConfig.fl_rounds=2000 \
  --set auranet-controller.appConfig.proximal_mu=0.15 \
  --set auranet-controller.appConfig.round_timeout_seconds=300

```

### 5. AuraNet Loader

If you need to debug eBPF map initializations or change log rotation metrics.

**Example: Enabling Debug Mode**

```bash
helm upgrade --install auranet . \
  --namespace auranet-namespace \
  --set auranet-loader.config.logLevel=DEBUG \
  --set auranet-loader.config.rotateMb=50

```

---

##  Uninstallation

To completely tear down the AuraNet system, delete the umbrella release. The Bootstrap cleanup job will automatically wipe all associated Cilium Network Policies before the pods terminate.

```bash
helm uninstall auranet --namespace auranet-namespace

```