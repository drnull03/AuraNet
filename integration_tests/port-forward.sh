kubectl port-forward svc/api-gateway 8080:80 -n default &
kubectl port-forward svc/auranet-nats-broker 4222:4222 -n auranet-namespace &
