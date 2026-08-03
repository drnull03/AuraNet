helm uninstall auranet-bootstrap -n auranet-namespace
sleep 2

helm install auranet-bootstrap ../../../auranet-bootstrap/chart -n auranet-namespace
