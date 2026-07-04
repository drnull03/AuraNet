while true; do echo "Tunnel Active..."; kubectl port-forward svc/frontend-ui 8080:80 -n default; sleep 2; done
