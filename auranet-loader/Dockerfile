# ── auranet-loader Dockerfile ─────────────────────────────────────────────────
# Single-stage image: Compiles and runs the eBPF program at runtime via BCC.
FROM ubuntu:22.04

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 \
        python3-bpfcc \
        bpfcc-tools \
        clang \
        llvm \
        libbpf-dev \
        make \
        kmod \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the eBPF C source (no pre-compilation)
COPY ebpf/ ./ebpf/

# Copy the Python loader
COPY loader/ ./loader/

ENV AURANET_LOG_LEVEL=INFO \
    AURANET_BPF_SRC=/app/ebpf/syscall_trace.bpf.c

ENTRYPOINT ["python3", "-m", "loader.main"]