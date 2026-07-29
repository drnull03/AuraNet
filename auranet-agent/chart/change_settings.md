Changing Settings Using HelmHelm provides two primary ways to override the default settings defined in your values.yaml file during deployment or upgrades.  Method A: Using the --set Flag (For Quick Changes)You can override individual values directly from the command line using dot notation. This is ideal for quickly tuning AI thresholds or testing parameters.To change the tripwireThreshold and localEpochs for the engine:  Bashhelm upgrade --install auranet-agent ./auranet-agent \
  --namespace auranet-namespace \
  --set engine.aiConfig.tripwireThreshold=0.08 \
  --set engine.aiConfig.localEpochs=10
To update a specific string in the threat map:  Bashhelm upgrade --install auranet-agent ./auranet-agent \
  --namespace auranet-namespace \
  --set runtime.image.tag=v2 \
  --set engine.aiConfig.learningRate=0.005
Method B: Using a Custom YAML File (For Permanent Overrides)For larger changes—like completely replacing the threatMapConf or updating the trustedIdentities list—it is much cleaner to create a separate YAML file containing only your overrides.  1. Create a file named custom-values.yaml:YAML# custom-values.yaml
engine:
  aiConfig:
    tripwireThreshold: 0.10
    trustedIdentities:
      - "k8s:app=gitlab-runner"
      - "k8s:app=auranet-controller"
      - "k8s:app=new-trusted-service"

runtime:
  threatMapConf: |
    # Add your custom signatures here
    nmap=nmap_scan_detected
    /etc/shadow=unauthorized_file_read
    /new/custom/path=custom_alert
2. Apply it using the -f flag:Bashhelm upgrade --install auranet-agent ./auranet-agent \
  --namespace auranet-namespace \
  -f custom-values.yaml
Because of the hot-reloading watchers built into both Python microservices, running this helm upgrade command will seamlessly update the mounted ConfigMaps inside the pods. The Python scripts will detect the updated files within a minute or two and apply the new threat rules and learning rates automatically without dropping any network traffic.