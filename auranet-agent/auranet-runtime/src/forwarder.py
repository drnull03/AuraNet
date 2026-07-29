#!/usr/bin/env python3
import asyncio
import ctypes
import json
import os
import re
import ssl
import struct
import time
import urllib.request
from nats.aio.client import Client as NATS

#  Configuration 
MAP_PATH = os.environ.get("MAP_PATH", "/sys/fs/bpf/auranet_events")
NATS_URL = os.environ.get("NATS_URL", "nats://auranet-nats-broker.auranet-messaging.svc.cluster.local:4222")
THREAT_MAP_PATH = os.environ.get("THREAT_MAP_PATH", "/etc/auranet/runtime/THREAT_MAP.conf")
NODE_NAME = os.environ.get("NODE_NAME", "")

# eBPF Struct Definition 
EVENT_STRUCT = struct.Struct("<QIIIIqq16s256sB7x")
EVENT_SIZE = EVENT_STRUCT.size

# Global State & Caches
THREAT_MAP = {}
recent_alerts = {}
POD_CACHE = {}          # Maps container_id -> {"pod_name": ..., "namespace": ..., "workload": ...}
LAST_CACHE_REFRESH = 0
CACHE_TTL_SEC = 15
DEDUPE_WINDOW_MS = 2000

# Regex patterns for extracting 64-hex container IDs from /proc/{pid}/cgroup
CONTAINER_ID_REGEX = re.compile(r'([a-f0-9]{64})')

#  Load Threat Map 
def load_threat_map():
    global THREAT_MAP
    try:
        new_map = {}
        with open(THREAT_MAP_PATH, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, val = line.split('=', 1)
                        new_map[key.strip()] = val.strip()
        THREAT_MAP = new_map
        print(f"[Runtime Forwarder] Loaded {len(THREAT_MAP)} threat signatures.")
    except Exception as e:
        print(f"[Runtime Forwarder] Warning: Failed to load Threat Map: {e}")



async def watch_threat_map():
    """Polls the Threat Map configuration file for changes."""
    last_mtime = 0
    while True:
        try:
            # Resolve the real path to handle Kubernetes symlink updates
            real_path = os.path.realpath(THREAT_MAP_PATH)
            current_mtime = os.path.getmtime(real_path)
            
            if last_mtime != 0 and current_mtime != last_mtime:
                print(f"[Runtime Forwarder] ConfigMap update detected at {THREAT_MAP_PATH}. Reloading...")
                load_threat_map()
                
            last_mtime = current_mtime
        except OSError:
            pass # File might be temporarily unavailable during atomic swap
            
        await asyncio.sleep(5) # Check every 5 seconds

# Real Kubernetes API Metadata Sync 
def refresh_k8s_pod_cache():
    """Queries the local Kubernetes API server to build a container_id -> pod/workload map."""
    global POD_CACHE, LAST_CACHE_REFRESH
    now = time.time()
    if now - LAST_CACHE_REFRESH < CACHE_TTL_SEC:
        return

    sa_token_path = "/var/run/secrets/kubernetes.io/serviceaccount/token"
    ca_cert_path = "/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"

    if not os.path.exists(sa_token_path):
        # Running outside cluster / no service account mounted
        return

    try:
        with open(sa_token_path, 'r') as f:
            token = f.read().strip()

        # Query API server for pods running on THIS node
        url = "https://kubernetes.default.svc/api/v1/pods"
        if NODE_NAME:
            url += f"?fieldSelector=spec.nodeName={NODE_NAME}"

        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
        
        ssl_ctx = ssl.create_default_context(cafile=ca_cert_path)
        with urllib.request.urlopen(req, context=ssl_ctx, timeout=5) as resp:
            data = json.loads(resp.read().decode())

        new_cache = {}
        for pod in data.get("items", []):
            pod_name = pod["metadata"]["name"]
            namespace = pod["metadata"]["namespace"]

            # Derive Workload Name from OwnerReferences or Labels
            workload = "unknown-workload"
            owner_refs = pod["metadata"].get("ownerReferences", [])
            if owner_refs:
                workload = owner_refs[0]["name"]
                # Strip deployment hash suffix if owned by a ReplicaSet (e.g. loan-service-7f8d9b -> loan-service)
                if owner_refs[0]["kind"] == "ReplicaSet" and "-" in workload:
                    workload = "-".join(workload.split("-")[:-1])
            else:
                labels = pod["metadata"].get("labels", {})
                workload = labels.get("app") or labels.get("app.kubernetes.io/name") or pod_name

            # Map all Container IDs in this pod to metadata
            container_statuses = pod.get("status", {}).get("containerStatuses", [])
            for c_status in container_statuses:
                container_id_raw = c_status.get("containerID", "")
                if container_id_raw:
                    # Strip protocol prefix (e.g. containerd://<hash> or docker://<hash>)
                    c_id = container_id_raw.split("//")[-1]
                    new_cache[c_id] = {
                        "pod_name": pod_name,
                        "namespace": namespace,
                        "workload": workload
                    }

        POD_CACHE = new_cache
        LAST_CACHE_REFRESH = now
    except Exception as e:
        print(f"[Runtime Forwarder] K8s API Sync Warning: {e}")

#  Real Process PID to Workload Resolver 
def resolve_k8s_context(pid):
    """
    Reads /proc/{pid}/cgroup to extract the real Container ID.
    Queries the K8s API cache for matching Pod & Workload names.
    Falls back to generic defaults if unmapped or host process.
    """
    cgroup_path = f"/proc/{pid}/cgroup"
    container_id = None

    if os.path.exists(cgroup_path):
        try:
            with open(cgroup_path, "r") as f:
                content = f.read()
                match = CONTAINER_ID_REGEX.search(content)
                if match:
                    container_id = match.group(1)
        except Exception:
            pass

    if container_id:
        # Check cache
        if container_id not in POD_CACHE:
            refresh_k8s_pod_cache()

        if container_id in POD_CACHE:
            meta = POD_CACHE[container_id]
            return meta["pod_name"], meta["namespace"], meta["workload"]

    # Generic Fallbacks for host processes or unmapped containers
    return f"host-pid-{pid}", "default", "unknown-workload"

# Threat Publisher 
async def publish_threat(nc, pid, threat_signature, context):
    now = time.time() * 1000
    
    pod_name, namespace, workload = resolve_k8s_context(pid)

    # Filter out system namespaces 
    if namespace in ("kube-system", "auranet-namespace"):
        return

    alert_key = f"{pod_name}-{threat_signature}-{context}"

    if alert_key in recent_alerts and (now - recent_alerts[alert_key] < DEDUPE_WINDOW_MS):
        return

    recent_alerts[alert_key] = now
    if len(recent_alerts) > 1000:
        recent_alerts.clear()

    payload = {
        "source": "runtime_ebpf",
        "threat": threat_signature,
        "context": context,
        "timestamp": now,
        "pod": pod_name,
        "namespace": namespace
    }

    subject = f"auranet.events.runtime.{workload}"
    print(f"🚨 [THREAT DETECTED] Pod: {pod_name} ({workload}) -> {threat_signature}")
    print(f"   Publishing to Subject: {subject}")

    await nc.publish(subject, json.dumps(payload).encode())

#  Event Processor 
def process_event(data, nc, loop):
    unpacked = EVENT_STRUCT.unpack(data)

    pid = unpacked[1]
    syscall_nr = unpacked[5]
    comm = unpacked[7].rstrip(b'\x00').decode('utf-8', errors='replace')
    str_arg = unpacked[8].rstrip(b'\x00').decode('utf-8', errors='replace')

    threat_signature = None
    action_context = ""

    # execve (59) or execveat (322)
    if syscall_nr in (59, 322):
        binary = str_arg.split('/')[-1]
        threat_signature = THREAT_MAP.get(binary)
        action_context = f"Executed binary: {binary}"

    # open (2) or openat (257)
    elif syscall_nr in (2, 257):
        file_name = str_arg.split('/')[-1]
        threat_signature = (THREAT_MAP.get(str_arg) or 
                            THREAT_MAP.get(file_name) or 
                            ('k8s_token_theft' if 'token' in str_arg else None) or
                            ('ssh_key_access' if '.ssh' in str_arg else None))
        action_context = f"Accessed file: {str_arg}"

    if threat_signature:
        asyncio.run_coroutine_threadsafe(publish_threat(nc, pid, threat_signature, action_context), loop)

# Main Runner 
async def main():
    load_threat_map()
    refresh_k8s_pod_cache()

    loop = asyncio.get_running_loop()
    loop.create_task(watch_threat_map())

    nc = NATS()
    print(f"[Runtime Forwarder] Connecting to NATS at {NATS_URL}...")
    await nc.connect(servers=[NATS_URL])
    print("[Runtime Forwarder] Connected to NATS!")

    libbpf = ctypes.CDLL("libbpf.so.0")

    libbpf.bpf_obj_get.argtypes = [ctypes.c_char_p]
    libbpf.bpf_obj_get.restype = ctypes.c_int

    RINGBUFFER_CALLBACK = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t)
    libbpf.ring_buffer__new.argtypes = [ctypes.c_int, RINGBUFFER_CALLBACK, ctypes.c_void_p, ctypes.c_void_p]
    libbpf.ring_buffer__new.restype = ctypes.c_void_p

    libbpf.ring_buffer__poll.argtypes = [ctypes.c_void_p, ctypes.c_int]
    libbpf.ring_buffer__poll.restype = ctypes.c_int

    map_fd = libbpf.bpf_obj_get(MAP_PATH.encode('utf-8'))
    if map_fd < 0:
        print(f"CRITICAL: Failed to get pinned map at {MAP_PATH}. Did auranet-loader run?")
        exit(1)

    loop = asyncio.get_running_loop()
    def ring_buffer_callback(ctx, data, size):
        if size == EVENT_SIZE:
            raw_bytes = ctypes.string_at(data, size)
            process_event(raw_bytes, nc, loop)
        return 0

    c_callback = RINGBUFFER_CALLBACK(ring_buffer_callback)
    rb = libbpf.ring_buffer__new(map_fd, c_callback, None, None)
    if not rb:
        print("CRITICAL: Failed to create ring buffer object.")
        exit(1)

    print(f"[Runtime Forwarder] Actively polling pinned eBPF map: {MAP_PATH}\n")

    try:
        while True:
            libbpf.ring_buffer__poll(rb, 100)
            await asyncio.sleep(0.01)
    except KeyboardInterrupt:
        print("\n[Runtime Forwarder] Shutting down...")
    finally:
        await nc.close()

if __name__ == '__main__':
    asyncio.run(main())