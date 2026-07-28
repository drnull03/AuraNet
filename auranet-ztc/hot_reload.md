
**Step A: Create  custom file**
Create a file named `my-custom-matrix.yaml` anywhere on your local machine. Define your `threatMatrix` multiline string block exactly how you want it.

```yaml
# my-custom-matrix.yaml
threatMatrix: |-
  # === My Custom AI Threats ===
  symbolic_null_byte_evasion=100
  custom_banned_method=90

  # === My Custom Runtime Threats ===
  nc_execution=85
  unauthorized_file_read=95
  unknown_anomaly=50

ztcConfig:
  windowTimeMs: 600000
  trustThreshold: 10

```

**Step B: Install using the file**


```bash
helm install auranet-ztc ./chart -f my-custom-matrix.yaml

```

### 2. Hot-Reloading a New Matrix Later On

Once the controller is actively running and processing NATS messages, you may decide you need to tweak a score (e.g., lowering `nc_execution` to `60`) or add a brand new threat signature without restarting the pod.

**Step A: Edit  custom file**
Open `my-custom-matrix.yaml` and update the values.

```yaml
# my-custom-matrix.yaml
threatMatrix: |-
  # === My Custom AI Threats ===
  symbolic_null_byte_evasion=100
  custom_banned_method=90

  # === My Custom Runtime Threats ===
  nc_execution=60               # <-- Changed score
  brand_new_attack_vector=100   # <-- Added new signature
  unauthorized_file_read=95
  unknown_anomaly=50

ztcConfig:
  windowTimeMs: 600000
  trustThreshold: 10

```

**Step B: Trigger the hot reload**
Use the `helm upgrade` command, passing that exact same file again.

```bash
helm upgrade auranet-ztc ./chart -f my-custom-matrix.yaml

```

**What happens?:**

1. Helm updates the ConfigMap in Kubernetes.
2. The `kubelet` performs the atomic `..data` symlink swap in the pod's `/etc/auranet/config/` directory.
3. Your Node.js `fs.watch()` detects the swap.
4. `getThreatMatrix()` is executed, parsing the new multiline string and updating `matrixState.current`.
5. The next packet processed by `calculateDeduction()` immediately uses the new scores and signatures.



or one can do this command
helm upgrade auranet-ztc ./chart \
  --reuse-values \
  --set threatMatrix="nc_execution=60\nreverse_shell_detected=100\nunknown_anomaly=30"





#FOMBD