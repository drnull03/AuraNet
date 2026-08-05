while true; do kubectl port-forward svc/demo-gateway 4000:80 --address 0.0.0.0 -n default; echo "Connection dropped, reconnecting..."; sleep 1; done
