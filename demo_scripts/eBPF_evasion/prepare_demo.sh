#!/bin/bash

echo "[*] Preparing environment for video capture..."

#  Dynamically locate the frontend pod
POD_NAME=$(kubectl get pods -n default --no-headers | grep ^frontend-ui | awk '{print $1}' | head -n 1)

if [ -z "$POD_NAME" ]; then
    echo "[-] Error: Could not find a pod starting with 'frontend-ui'."
    exit 1
fi

echo "[+] Found target pod: $POD_NAME"
echo "[*] Installing strace and perl silently (takes a few seconds)..."

# Install dependencies silently so it doesn't clutter the screen
kubectl exec -i "$POD_NAME" -- /bin/sh -c "apk update >/dev/null 2>&1 && apk add strace perl >/dev/null 2>&1"

#  Generate the command and use Kitty's OSC 52 integration to copy it to your local clipboard
# We base64 encode the payload as required by the OSC 52 protocol
#command for listing eBPF program using the bpf() syscall directly
COMMAND="strace -e bpf perl -e '\$attr = \"\\0\" x 128; syscall(321, 11, \$attr, 128)'"
B64_CMD=$(printf "%s" "$COMMAND" | base64 | tr -d '\n')

# Send the escape sequence to Kitty
printf "\033]52;c;%s\007" "$B64_CMD"

echo "[+] The command is now in your local clipboard!"
echo "[*] Dropping you into the pod. Press Paste when ready..."
sleep 2

#  Clear the screen for a clean video start and enter the pod interactively
kubectl exec -it "$POD_NAME" -- /bin/sh
