# AuraNet Threat Matrices Database

This directory contains pre-configured threat severity matrices for the AuraNet Zero Trust Controller. 

These configuration files (`.conf`) map specific AI-detected anomalies and runtime events to numerical penalty scores (1-100). When a workload's trust score drops below the quarantine threshold, the AutoHeal pipeline is triggered.

## Architectural Warning: Context is Everything

**There is no such thing as a "perfect" universal threat matrix.** The choice of penalties is completely application-dependent. A severity score that works flawlessly for a highly-secured banking microservice might cause catastrophic false-positive quarantines in a public-facing e-commerce API during a Black Friday sale. 

Developers and security engineers **must** choose, tune, and stress-test their own threat matrix based on:
1. The acceptable risk tolerance of the specific application.
2. The natural "noise" and baseline behavior of the network traffic.
3. Penetration testing results against the specific cluster environment.

Use the samples below as starting points, but always calibrate them to your cluster's reality.

---

## Sample Matrices

### 1. `01-auranet-balanced-default.conf`
**Use Case:** The standard baseline. Balances strict enforcement for obvious breaches with moderate tolerance for AI-perceived anomalies to prevent false positives.

```ini
# === Neurosymbolic AI Threats ===
symbolic_null_byte_evasion=100
symbolic_uri_too_large=80
symbolic_banned_method=60
l7_payload_anomaly=90
l7_body_anomaly=90
network_behavior_anomaly=40

# === Tetragon Runtime Threats ===
nc_execution=70
unauthorized_file_read=60
privilege_escalation=100
unexpected_outbound_traffic=50

# === Fallback ===
unknown_anomaly=30
