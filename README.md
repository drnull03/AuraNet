<p align="center">
  <img src="./assets/logo.png" alt="AuraNet Logo" width="180"/>
</p>

<h1 align="center">AuraNet</h1>
<p align="center"><em>A Kubernetes-native, Zero Trust network security platform</em></p>

<p align="center">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"/>
  <img src="https://img.shields.io/badge/Kubernetes-native-blue.svg" alt="Kubernetes native"/>
  <img src="https://img.shields.io/badge/eBPF-powered-orange.svg" alt="eBPF powered"/>
  <img src="https://img.shields.io/badge/Windows-unsupported-red.svg" alt="Windows unsupported"/>
</p>

---

> Graduation project — 5th year Engineering Student at **HIAST**

---

## 📖 About AuraNet

Network security has never been an afterthought — it has evolved hand in hand with the networks it protects. For decades, the dominant approach was the **Perimeter Model**: fortify the external borders of a network and implicitly trust anything already inside them. As cyberattacks grew more sophisticated and cloud and distributed environments became the norm, this assumption stopped holding. In 2010, the **Zero Trust** model emerged as a response — trust is never granted simply because a device or user sits inside the network perimeter; instead, it is calculated and re-evaluated continuously.

Zero Trust was a genuine leap forward, but most current implementations still struggle with real technical challenges:

- **Privacy erosion**, caused by centralized collection and inspection of traffic to compute trust scores.
- **Performance overhead**, from the burden of continuous monitoring and inspection.
- **Static, unintelligent trust evaluation**, since most systems still rely on fixed rule sets rather than adaptive scoring.

**AuraNet** is an engineering response to these gaps. It combines:

- **eBPF** for ultra-fast, kernel-level network observability and enforcement.
- **Federated Learning** to drive intelligent, privacy-preserving, decentralized trust scoring.
- **Auto-Healing** — rather than stopping at detection and isolation of low-trust connections, AuraNet closes the security loop by *reacting*: it self-remediates faults and automatically rebuilds trust for compromised components.

What sets AuraNet apart from comparable projects is twofold: it treats Zero Trust networking as a **comprehensive problem** rather than a single narrow issue, and it goes beyond passive monitoring to **active, corrective response** — a meaningful step toward a scalable security ecosystem for modern, highly sensitive organizations.

---

<p align="center">
  <em>"And the very hairs of your head are all numbered. Do not fear therefore; you are of more value than many sparrows."</em><br/>
  — Matthew 10:30–31
</p>

<p align="center">✨ Hope this project goes well ✨</p>

---

## Documentation

Start here — this is the most important section if you want to actually understand the project.

| Resource | Location | Notes |
|---|---|---|
| **Main Report** ⭐ | `./docs/Report` | The primary reference. Covers the problem statement, implementation details, screenshots, and algorithms in full. **Read this first.** |
| Presentation | `./docs/Representation` | Slide deck presentation of the project. |
| Doxygen-generated docs | `./auranet_docs` | Auto-generated from source code. |
| SRS | ~~`./docs/SRS`~~ | **Deprecated** — do not use. The Software Requirements Specification now lives inside the Main Report. |
| Extra screenshots ("fun tours") | `./docs/more_images` | Linux symlinks to additional screenshots taken throughout development. |
| Obsidian notes | `./ObsidianNotes` | Personal notes written mostly *before* implementation began — useful for design intent and early thinking. |
| Report images | `./docs/Images` | Images extracted directly from the Main Report. |

---

##  Project Structure

```text
.
├── pulumi_IoC/                  # Infrastructure as Code (modern approach used in this project)
├── sample_workload_layer/       # Three sample systems written to demo AuraNet in action
│
├── auranet-autoheal/            # Auto-healing service implementation
├── auranet-bootstrap/           # Bootstrap service implementation
├── auranet-cli/                 # CLI tool
├── auranet-controller/          # Federated Learning controller implementation
├── auranet-core/                # Helm package (main install chart)
├── auranet-loader/              # eBPF ephemeral loader service
│   └── ebpf/                    # auranet-bpf implementation
├── auranet-ztc/                 # Zero Trust Controller (ZTC)
├── auranet-ui/                  # Dashboard implementation
├── auranet-agent/
│   ├── auranet-runtime/         # Runtime filter implementation
│   ├── auranet-engine/          # Engine filter implementation
│   └── chart/                   # Helm chart installing both filters above
│
├── PQC/                         # Post-Quantum Cryptography tests & microservices
│   └── auranet-encryption/      # PQC encryption microservice
│
├── Prepare_Images.sh            # Builds all Docker images in the project
├── CelebratingTheSmallWins/     # Screenshots the author is proud of 🎉
├── .vscode/                     # VS Code settings & extensions used during development
│
├── adaptablity_tests/           # (ignore for now — empty, used for demo)
├── attack/                      # (ignore for now — empty, used for demo)
├── assets/                      # Project logo and related assets
│
├── deprecated/ (root)           # Old CNI testing approach (pre-Cilium)
├── E2E_tests/                   # End-to-end tests
├── eBPF/                        # eBPF experiments — includes an attempt at cilium-bpf
├── expirementents/              # Miscellaneous tool experimentation throughout the project
├── ideas/                       # (empty — superseded by Obsidian notes)
├── stress_tests/                # System stress tests
├── scripts/                     # Dev-time bash scripts (safe to ignore)
│
├── AUTHORS                      # Authors and public contact emails
├── system-reuirement.md         # System requirements
├── releases/                    # auranet-core releases
├── policylibrary/                # Library of policies
├── project_tree.sh              # Generates the project tree
├── virtual-patches-library/     # Public virtual patches written by the author (partial set)
├── vps/                         # (empty — marks the start of the VPS migration)
├── monolith_training/           # Centralized ML training approach (pre-Federated Learning)
├── workload_dev_guide/
├── GEMINI.md                    # Notes for gemini-cli usage on this project
├── shoutout/                    # Shoutout to a VS Code extension that helped keep the author sane 🙏
├── thread_matrices/             # Example threat matrices written by the author
├── proofs/                      # Screenshots proving certain implementations (can be ignored)
│
├── IoC/                         # Deprecated — old IoC approach, pre-Pulumi
├── LICENSE
│
├── Resources/                   # Curated useful resources (partial, due to copyright)
├── System_CharacterizationAndInsights/  # Jupyter notebooks deriving results/charts from the system
├── CODE_OF_CONDUCT
├── g_test.txt                   # Marks the first use of gemini-cli
├── Doxyfile                     # Doxygen configuration
└── install/                     # Small install script (dev-only — not production)
```

> **Future implementation plans (planned, not yet built):**
> - Integrating an LLM with the auto-healing service
> - Multi-cloud support via Cilium
> - Post-Quantum encryption via `auranet-encryption` *(almost done)*

---

##  Tools Used

This chapter covers the core technologies adopted to build AuraNet, along with the reasoning behind each choice. Tools used specifically for simulation/infrastructure provisioning are covered separately in the *Environment & Simulation Setup* chapter, and packaging/testing tools are covered in the *System Packaging* and *Testing* chapters respectively.

### Infrastructure Frameworks
| Tool | Version | Why |
|---|---|---|
| **Kubernetes** | v1.36.1 | Used as the core engine and dependency of the system, chosen for the cloud-native properties it provides and the isolation guarantees of running workloads in containers — ensuring a vulnerability in one application doesn't compromise the host node or other applications. |
| **Cilium** | v1.19.3 | Runs on top of Kubernetes as the network control engine at the eBPF level, and is a core dependency of the system. Chosen for the advanced networking capabilities it provides, which simplify building a Zero Trust network architecture. |
| **SPIRE** | v1.19.3 (Cilium-integrated) | Provides workload identity and continuous identity verification — a cornerstone of Zero Trust networking. Chosen for its ease of integration with Kubernetes, being the identity framework recommended by Cilium, and its built-in support for mutual authentication via mTLS. |
| **Hubble** | v1.19.3 | Provides detailed network observability. Chosen because it ships natively with Cilium, guaranteeing seamless integration without adding complex external tooling. |

### Programming Languages
| Tool | Version | Why |
|---|---|---|
| **Node.js** | v24.16.0 | Used to write microservices that don't require machine learning, as a solid general-purpose language for microservice development. |
| **Python** | 3.12.3 | The primary language for microservices related to Federated Learning — the world's leading language for Deep Learning, with a rich ecosystem of libraries. |
| **C** | GCC 13.3.0 | The primary language for writing eBPF programs. While Rust is also an option for eBPF, C was chosen for the maturity of its surrounding tooling and ecosystem. |
| **Bash** | 5.2.21 | Used for small automation scripts to handle operational tasks and simplify infrastructure management. |
| **libbpf** | v1.7.0 | The core library used to write eBPF programs that monitor OS runtime behavior. Chosen as the official and most robust environment for this purpose. |
| **asyncio / aiohttp** | aiohttp v3.14.3, asyncio 3.14.6 | Core building blocks in Python for building asynchronous, non-blocking systems. |

### Machine Learning Tools
| Tool | Version | Why |
|---|---|---|
| **Flower** | 1.5.0 | The primary Python library used to implement Federated Learning. Enables a smooth transition from a centralized ML model to a distributed federated one without major code rewrites — chosen as the easiest and fastest path to this transition. |
| **PyTorch** | v13.13 | The most widely used Python library for building and training ML models. Chosen for its Dynamic Computational Graph, which offers high flexibility and easier debugging of complex models, along with its seamless integration with Python and strong support for Federated Learning research. |
| **NumPy** | 1.24.3 | The core Python library for scientific computing and multi-dimensional array operations. Used for high-performance computation on model weights, and for preparing and formatting data into arrays prior to processing and aggregation within the Federated Learning algorithm. |

### Messaging Tools
| Tool | Version | Why |
|---|---|---|
| **NATS** | server v2.14.2 | Despite the availability of more widely known messaging systems like RabbitMQ, NATS was chosen for being the best-suited option for asynchronous communication between microservices, with the strongest integration and compatibility with distributed Kubernetes environments. |

### Development Tools
| Tool | Version | Why |
|---|---|---|
| **Visual Studio Code** | 1.92.2 | The primary IDE for writing and editing source code. Chosen for being lightweight while offering excellent support for the range of languages used in the system (Python, C, Node.js) via a rich extension ecosystem, along with built-in terminal and Git integration and exceptional remote development support — which greatly simplified writing and testing code across different environments and servers. |
| **Git & GitHub** | git 2.43.0 | Core tools for source control, offering strong change-tracking and collaborative, secure version management. |
| **Doxygen** | 1.9.8 | Used to auto-generate project documentation. Chosen for its ease of use and prior hands-on experience with the tool. |
| **Curl** | 8.5.0 | Used to simulate and send requests to the system in order to collect data and build the dataset used to train the ML model centrally, before transitioning it into the Federated Learning phase. |
| **Next.js / React** | 19.0.1 | Used to build the frontend/dashboard, chosen for its ease of use and high efficiency in building interactive, smooth user interfaces. |

### Visualization Tools
| Tool | Version | Why |
|---|---|---|
| **Jupyter Notebook** | 7.5.7 | The primary environment for presenting and analyzing system results and ML model performance. |
| **Matplotlib** | 3.11.0 | Chosen alongside Jupyter for its strong ability to visually represent data through clear, easily interpretable charts. |

### Demo Tools
Three practical examples were built on top of AuraNet for demonstration purposes:

| Tool | Purpose |
|---|---|
| **SQLite** | Simulates a local, embedded database within demo applications. |
| **PostgreSQL** | An advanced relational database used to simulate complex data storage scenarios — allowing the system to be tested and evaluated in real storage environments that demand high reliability and efficient data handling. |
| **Python, JS, Go** | Standard, mainstream languages used to simulate the system's operation across multiple software environments and runtimes. |
| **FastAPI** (Python) | Chosen as one of the best and fastest options for building APIs for rapid experimentation and testing. |

---

## ⚠️ Note for Windows Users

**This project cannot run on Windows**, due to the limited support of `kind` on the platform.

---

##  Getting Started

### Option A — Full dev environment from scratch

> ⚠️ Warning: this is a **local development setup**, not intended for production use.

1. Build each Docker image using Pulumi, or run the helper script (heads up — this pulls down roughly **45GB**):
   ```bash
   ./Prepare_Images.sh
   ```
2. Install the prerequisites: **kind**, **Pulumi**, and **Helm**.
3. Bring the system up:
   ```bash
   cd ./pulumi_IoC
   make up-all
   ```
4. To tear it back down:
   ```bash
   make down-all
   ```

There is also a small helper script under `./install` for local testing — again, dev-only, not for production.

### Option B — You already have a Kubernetes cluster with Cilium running

```bash
git clone <this-repo>
cd auranet-core
helm dependency update
helm install auranet . \
  --namespace auranet-namespace \
  --create-namespace
```

---

##  Contributing

We welcome contributions from developers interested in decentralized communications, smart contracts, cryptography, and Web3 UI/UX.

Feel free to fork the repo, submit issues, or open pull requests. See the `CONTRIBUTORS` file for a list of everyone who helped build this project.

##  Code of Conduct

This project follows the same Code of Conduct as **Cilium**. See `CODE_OF_CONDUCT` for details.

## License

<p>
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="MIT License"/>
</p>

This project is licensed under the **MIT License** — see the [`LICENSE`](./LICENSE) file for details.