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
1. layer 1: kind cluster cilium ,tetragon and hubble  And SPIRE
2. layer 2: Our own custom custom auranet agent (it is divided into multiple components the zero trust controller,inference engine,Ml agent,central aggregator, it will also read naive policy rules and apply them)
3. layer 3: this is the plugable layer it should deploy some sample pods representing the company workload infrastructure  



##  Notes For the AI
1.don't specify versions in pulumi let helm download the latest version

## What We are Building 
okay this session if for building auranet 5th year graduation project """AuraNet"  Autonomous Self-Healing Zero Trust Architecture using eBPF and Federated Learning"" my current setup i have pulumi i already have a kind cluster running 3 nodes cilium setup with SPIFFE and SPIRE and tetragon this layer 1 the arch layer this is done now we should build together layer 2 and layer 3 layer 2  is auranet layer and layer three is sample workload layer (plugable layer) layer 2 should have the following 1.auranet controller (it plays as aggregator for the ml model ) 2. auranet-agent a deamon set running on every node the auranet-agent consist of the following 1.inference-engine : runing autoencoder model 2. learning-engine for learning and sending to the aggregator 3.zero-trust-controller for the contextual or scoring based algo 4.auranet runtime (this uses tetragon and some public of known bad behaviours to block the process using tracing policies 5-auranet bootstrap this read two file a configuration file for configuring auranet for example i can turn on inferenceOnly setting which stops the learning the second file is a file the define naive unallowed connection for example front end isn't allowed to talk to database directly  it convert this file to cilium policies 6.an autohealing component here are notes on the AI 1. we should  nurosymbolic AI for offering some controller env 2. the ai should not be blocking we should have a shadow stream which means we don't execute the inference engine on every request the inference engine run on logs and apply cilium network policy (thus achieving immuntisation and lateral movement isolation and maybe restart pod)
