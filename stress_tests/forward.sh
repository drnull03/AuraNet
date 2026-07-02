while true; do echo "Tunnel Active..."; kubectl port-forward svc/api-gateway 10000:80 -n default; sleep 2; done
