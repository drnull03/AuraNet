# ── auranet-loader Dockerfile ─────────────────────────────────────────────────
# Multi-stage build:
#   Stage 1 – compile the eBPF object (clang + libbpf-dev)
#   Stage 2 – minimal runtime image with Python + BCC
#
# The final image must run in privileged mode (or with CAP_BPF + CAP_SYS_ADMIN)
# and needs access to /sys/kernel/btf/vmlinux from the host.

# ────────────────────────────────────────────────────────────────────────────────
# Stage 1: eBPF compile
# ────────────────────────────────────────────────────────────────────────────────
FROM ubuntu:22.04 AS ebpf-builder

RUN apt-get update && apt-get install -y --no-install-recommends \
        clang \
        llvm \
        libbpf-dev \
        linux-headers-generic \
        make \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build/ebpf
COPY ebpf/ .

RUN make LIBBPF_INC=/usr/include

# ────────────────────────────────────────────────────────────────────────────────
# Stage 2: runtime
# ────────────────────────────────────────────────────────────────────────────────
FROM ubuntu:22.04 AS runtime

# BCC Python bindings
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 \
        python3-bpfcc \
        bpfcc-tools \
        linux-headers-generic \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy compiled eBPF object
COPY --from=ebpf-builder /build/ebpf/syscall_trace.bpf.o ./ebpf/

# Copy Python loader
COPY loader/ ./loader/

# Default output dir (override via env or helm values)
RUN mkdir -p /var/log/auranet

ENV AURANET_OUTPUT=/var/log/auranet/events.json \
    AURANET_LOG_LEVEL=INFO

ENTRYPOINT ["python3", "-m", "loader.main"]
