# How to Update naive.conf via Helm
Because naive.conf is represented by the naiveConf multiline string in values.yaml, there is  two ways to execute this from the command line depending on how many rules we are adding.  
Approach A: The Custom Values File , if you are adding multiple network flows, doing it via a YAML file is the safest approach to prevent formatting errors.1. Create a file named new-rules.yaml:YAMLnaiveConf: |
  1.retail-dashboard -> customer-api:8000
  2.api-gateway -> account-service:5000
  3.loan-service -> finance-db:5432
Run the Helm upgrade 
```helm upgrade auranet-bootstrap-chart ./chart -f new-rules.yaml```
Approach B: The Pure CLI --set (For Quick One-Liners)If you only need to inject a single rule (or are comfortable using \n for line breaks in your terminal), you can bypass the file entirely and use --set.Since naiveConf expects a string, you can overwrite it directly:  
```helm upgrade auranet-bootstrap-chart ./chart \
  --reuse-values \
  --set naiveConf="1.frontend-ui -> api-gateway:8080"```
What happens next in the cluster:Helm updates the ConfigMap.Helm deletes the old auranet-bootstrap Job.  Helm creates a new Job.  The new pod boots up, reads the new naiveConf, generates the Cilium policy for frontend-ui -> api-gateway:8080, prints the success log, and exits cleanly.