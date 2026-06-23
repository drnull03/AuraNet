# AuraNet Developer Guide

This document outlines the mandatory architectural and development standards for applications deployed within the AuraNet environment. All developers must adhere to these principles to maintain the integrity of our Zero Trust Architecture.

## 1. Kubernetes Workload Standards

AuraNet strictly follows Kubernetes native patterns to ensure scalability, reliability, and maintainability. Developers are required to adhere to the official Kubernetes development guidelines.

### Stateless Applications
The majority of workloads in AuraNet should be designed to be stateless.
* **Implementation:** All stateless applications must be deployed using Kubernetes `Deployments`.
* **Rationale:** Statelessness allows for horizontal auto-scaling and seamless rolling updates, which are core requirements for the AuraNet infrastructure.

### Stateful Applications
When persistent storage or stable network identifiers are required, developers must utilize stateful patterns.
* **Implementation:** All stateful applications must be deployed using Kubernetes `StatefulSets`.
* **Rationale:** This ensures that pods have stable, unique network identifiers and persistent disk storage that survives rescheduling.

## 2. Security and Authentication Policy

AuraNet implements a Zero Trust model at the infrastructure level. To maintain this architecture, developers must strictly adhere to the following rules regarding application security.

### Prohibition of Application-Level Security
Developers are strictly prohibited from implementing custom authentication, authorization, or encryption logic within their application code.

### Rationale
* **Infrastructure-Level Controls:** AuraNet manages authentication, mTLS encryption, and authorization transparently via the service mesh and infrastructure sidecars.
* **Microsegmentation Integrity:** Implementing these features at the application level bypasses infrastructure visibility. If an application handles its own security, AuraNet cannot perform granular microsegmentation or inspect HTTP-level traffic for policy enforcement.
* **Policy Violation:** Any attempt to implement custom auth/encryption mechanisms will break the Zero Trust tenant model and will result in the application failing security compliance reviews.

## 3. Summary of Compliance

| Feature | Requirement | Deployment Type |
| :--- | :--- | :--- |
| Stateless Workload | Mandatory | Deployment |
| Stateful Workload | Permitted | StatefulSet |
| Auth/Encryption | Prohibited | N/A (Handled by Infra) |

By following these guidelines, you ensure that your services are compatible with the AuraNet self-healing Zero Trust architecture and contribute to a secure, observable, and resilient distributed system.
