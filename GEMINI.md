# AuraNet - Project Context

## Overview

It is an IT engineering project The official title of the project is """AuraNet"  Autonomous Self-Healing Zero Trust Architecture using eBPF and Federated Learning""


AuraNet is an autonomous, self-healing Zero Trust Architecture (ZTA) operating at the kernel level. It is built on Kubernetes, utilizes  cryptographic identity (SPIFFE/SPIRE), and relies heavily on observability orchestrated through eBPF and Cilium.
The Prject Also uses Tetragon for runtime monitoring for achieveing zero trust.

The AI model that we are gonna build later with flower and python it is a nurosymbolic AI the symbolic part is an autoencoder we will also be using fedPox as an aggregator algo

the zero trust scoring algorithim should be a contextual algorithim 

The AI should read eBPF and make a decision using a shadow stream that means it will usually miss the first packet 
this design decision was made as trade of to preformance


## Boundaries (ignore these files)
* **`/eBPF`**: We Will Not deal with this right now 
* **`/IoC` it is a deprecated way to handle infra as code
* **`/shadowAuraNet`**: It is a private folder 
* **`/proofs`**: as it is  meant for the professors to see the work
* **`/docs` & `/Report`**: Academic documentation, architectural diagrams, and the graduation project reporting materials.
* **`/vps` & `/configs`**: Remote deployment manifests and server configurations.
* **`CelebratingTheSmallWins`**: A continuous log of successful debugging milestones, resolved race conditions, and project victories. 
* **`assets`**: just contain the logo for the project 
* **`deprecated`**: contains deprecated meterials
* **`g_test.txt`**: personal file don't touch it
* **`TODO`**: can be safely ignored
* **`AUTHORS`**: contain the author name
* **`CONTRIBUTORS`**: contain name of contributors 
* **`CODE_OF_CONDUCT`**: contain the code of conduct
* **`LICENESE`**: contain the license of the project

## Architucture of the project so far 

we are using pulumi as infra as code 
we divided the project into 4 layers
1. layer 1: kind cluster cilium ,tetragon and hubble 
2. layer 2: SPIRE and identity integration
3. layer 3: Our own custom custom auranet agent (it is divided into multiple components the zero trust controller,inference engine,Ml agent,central aggregator, it will also read naive policy rules and apply them)
4. layer 4: this is the plugable layer it should deploy some sample pods representing the company workload infrastructure  