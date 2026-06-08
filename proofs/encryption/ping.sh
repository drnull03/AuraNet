kubectl run secure-test --image=busybox -n default --restart=Never -- ping -c 4 8.8.8.8
