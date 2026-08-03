kubectl delete ciliumnetworkpolicy bootstrap-allow-api-gateway-to-account-service -n default



cd ~/AuraNet/auranet-cli
source ./venv/bin/activate
python3 auranet-cli.py bootstrap-rules baseline.conf --namespace auranet-namespace --local-ui ../auranet-ui/naive.conf
