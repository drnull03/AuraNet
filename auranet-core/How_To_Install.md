## Packaging and Installation
Before installing, Helm needs to link the dependencies defined in your Chart.yaml.

Step 1: Update Dependencies
Navigate to your auranet-core directory and run:

```helm dependency update```
This command reads the file:// paths and pulls the subcharts into an internal charts/ folder inside auranet-core.

Step 2: Install the Umbrella Chart
You want all of these deployed into the auranet-namespace. Run the install command, ensuring the namespace is created if it doesn't exist:


```helm install my-auranet-release . \
  --namespace auranet-namespace \
  --create-namespace```
## Modifying Arguments During Installation
The power of the umbrella chart is that you don't need to touch the subchart files to change their behavior. You can override any nested value directly from the CLI using the --set flag during installation or upgrades.

Example: Tuning Ai Engine Parameters
If you want to deploy the system but test a more aggressive learning rate and a lower tripwire threshold for the Ai engine, you target the keys as they are nested in the auranet-agent block:

```
helm install my-auranet-release . \
  --namespace auranet-namespace \
  --set auranet-agent.engine.aiConfig.learningRate=0.005 \
  --set auranet-agent.engine.aiConfig.tripwireThreshold=0.02 ```
Example: Modifying the Loader Configuration
If you need to change the eBPF loader's log level to debug a syscall issue, you can inject that override simultaneously:


```helm upgrade --install my-auranet-release . \
  --namespace auranet-namespace \
  --set auranet-loader.config.logLevel=DEBUG \
  --set auranet-loader.config.rotateMb=50```


setting the configuration matrix

```helm install my-auranet-release . \
  --namespace auranet-namespace \
  --set-file autoheal.threatMatrix=./custom-threat-map.conf```


## Injecting via a Custom Values File
If you have multiple environments (e.g., development vs. production) and want to keep things organized without cluttering the umbrella chart's default values.yaml, you can create external YAML files and pass them during installation.

1. Create a production-values.yaml file:

YAML
auranet-agent:
  runtime:
    threatMapConf: |-
      nc=nc_execution
      bash=reverse_shell_detected
      custom_malware=immediate_kill

autoheal:
  threatMatrix: |-
    nc_execution=100
    reverse_shell_detected=100
2. Pass the file using -f or --values:

Bash
helm install my-auranet-release . \
  --namespace auranet-namespace \
  -f production-values.yaml
Helm will take the overrides from production-values.yaml, merge them with the umbrella's values.yaml, and push the final computed values down to the respective auranet-agent and autoheal subcharts.
