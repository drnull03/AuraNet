# This image runs as an initContainer on EVERY node.
# It compiles the eBPF C source against the NODE'S OWN kernel headers
# (mounted from the host at /usr/src and /lib/modules) and writes
# syscall_trace.bpf.o into a shared emptyDir volume.
#
# Why compile on-node instead of shipping a pre-built .o?
#   eBPF bytecode is sensitive to kernel version and BTF layout.
#   Compiling on-node guarantees the object matches the running kernel
#   without needing BTF CO-RE (which requires a very recent toolchain).
FROM ubuntu:22.04

RUN apt-get update && apt-get install -y --no-install-recommends \
        clang \
        llvm \
        libbpf-dev \
        make \
        kmod \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY ebpf/syscall_trace.bpf.c .
COPY ebpf/Makefile .

# The entrypoint script:
#  1. Detects the running kernel version via /proc/version (host /proc mounted)
#  2. Locates kernel headers under /usr/src (host mount)
#  3. Runs clang to compile the eBPF object
#  4. Copies the .o to /output (shared emptyDir → loader container)
COPY scripts/build-ebpf.sh /usr/local/bin/build-ebpf.sh
RUN chmod +x /usr/local/bin/build-ebpf.sh

ENTRYPOINT ["/usr/local/bin/build-ebpf.sh"]
