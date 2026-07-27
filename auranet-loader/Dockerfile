# Stage 1: Build Environment
FROM ubuntu:22.04 AS builder

RUN apt-get update && apt-get install -y \
    clang \
    llvm \
    libbpf-dev \
    make \
    linux-tools-common \
    linux-tools-generic \
    bpftool

WORKDIR /build
COPY ebpf/ ./ebpf/

WORKDIR /build/ebpf
# Generate vmlinux and build the installer
RUN make all

# Stage 2: Minimal Runtime
FROM ubuntu:22.04

WORKDIR /app
COPY --from=builder /build/ebpf/auranet-installer .

# Run the installer, then sleep infinity so the DaemonSet pod stays "Running"
ENTRYPOINT ["/bin/sh", "-c", "rm -f /sys/fs/bpf/auranet* && ./auranet-installer && echo 'Monitoring active...' && sleep infinity"]