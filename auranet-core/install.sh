# step 1

helm dependency update

sleep 2
# step 2

helm install auranet . \
  --namespace auranet-namespace \
  --create-namespace


sleep 2

