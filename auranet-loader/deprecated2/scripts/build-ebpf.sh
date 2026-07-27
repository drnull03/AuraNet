#!/usr/bin/env bash
# Runs inside the builder initContainer on each Kubernetes node.
# Detects the host kernel version, finds the right headers, compiles the eBPF
# object, and drops it into /output (a shared emptyDir volume).
set -euo pipefail

OUTPUT_DIR="${OUTPUT_DIR:-/output}"
SRC_FILE="/build/syscall_trace.bpf.c"
OBJ_FILE="${OUTPUT_DIR}/syscall_trace.bpf.o"

# /proc is mounted from the host so uname -r reflects the real kernel
KVER=$(uname -r)
echo "[auranet-builder] Kernel version: ${KVER}"

# Locate kernel headers
# The DaemonSet mounts /lib/modules and /usr/src from the host.
# Standard header locations (in priority order):
HEADER_PATHS=(
    "/usr/src/linux-headers-${KVER}/include"
    "/usr/src/kernels/${KVER}/include"
    "/lib/modules/${KVER}/build/include"
    "/usr/src/linux-headers-${KVER%-*}-common/include"
)

KERNEL_HEADERS=""
for p in "${HEADER_PATHS[@]}"; do
    if [ -d "$p" ]; then
        KERNEL_HEADERS="$p"
        echo "[auranet-builder] Using kernel headers: ${KERNEL_HEADERS}"
        break
    fi
done

# Also check for the build symlink
BUILD_LINK="/lib/modules/${KVER}/build"
if [ -z "${KERNEL_HEADERS}" ] && [ -d "${BUILD_LINK}" ]; then
    KERNEL_HEADERS="${BUILD_LINK}/include"
    echo "[auranet-builder] Using build symlink headers: ${KERNEL_HEADERS}"
fi

if [ -z "${KERNEL_HEADERS}" ]; then
    echo "[auranet-builder] ERROR: Cannot find kernel headers for ${KVER}"
    echo "[auranet-builder] Searched:"
    for p in "${HEADER_PATHS[@]}"; do echo "  $p"; done
    echo "[auranet-builder] Make sure you have linux-headers-${KVER} installed on the node"
    echo "[auranet-builder] or set hostPath mounts in the Helm values."
    exit 1
fi

# Locate arch-specific headers 
ARCH=$(uname -m)
case "${ARCH}" in
    x86_64)  BPF_ARCH="x86" ;;
    aarch64) BPF_ARCH="arm64" ;;
    *)
        echo "[auranet-builder] WARNING: Unsupported arch ${ARCH}, defaulting to x86"
        BPF_ARCH="x86"
        ;;
esac
echo "[auranet-builder] Architecture: ${ARCH} → BPF arch: ${BPF_ARCH}"

# Arch-specific includes (asm/ptrace.h etc.)
ARCH_INC_CANDIDATES=(
    "/usr/src/linux-headers-${KVER}/arch/${BPF_ARCH}/include"
    "/usr/src/linux-headers-${KVER%-*}-common/arch/${BPF_ARCH}/include"
    "/lib/modules/${KVER}/build/arch/${BPF_ARCH}/include"
)
ARCH_HEADERS=""
for p in "${ARCH_INC_CANDIDATES[@]}"; do
    if [ -d "$p" ]; then
        ARCH_HEADERS="$p"
        break
    fi
done

#  Prepare output directory 
mkdir -p "${OUTPUT_DIR}"

#  Compile eBPF object 
CLANG="${CLANG:-clang}"
EXTRA_CFLAGS="${EXTRA_CFLAGS:-}"

CFLAGS=(
    -O2
    -g
    -Wall
    -Wno-unused-value
    -Wno-pointer-sign
    -Wno-compare-distinct-pointer-types
    -target bpf
    -D__TARGET_ARCH_${BPF_ARCH}
    -D__KERNEL__
    -DKBUILD_MODNAME='"auranet"'
    -I/usr/include
    -I/usr/include/bpf
    -I"${KERNEL_HEADERS}"
)

if [ -n "${ARCH_HEADERS}" ]; then
    CFLAGS+=(-I"${ARCH_HEADERS}")
    # Generated headers (autoconf.h, etc.)
    GENERATED="${ARCH_HEADERS/include/include\/generated}"
    [ -d "${GENERATED}" ] && CFLAGS+=(-I"${GENERATED}")
fi

# Include generated uapi headers if available
UAPI="${KERNEL_HEADERS}/uapi"
[ -d "${UAPI}" ] && CFLAGS+=(-I"${UAPI}")

echo "[auranet-builder] Running clang..."
echo "[auranet-builder] ${CLANG} ${CFLAGS[*]} -c ${SRC_FILE} -o ${OBJ_FILE}"

"${CLANG}" "${CFLAGS[@]}" ${EXTRA_CFLAGS} -c "${SRC_FILE}" -o "${OBJ_FILE}"

echo "[auranet-builder] ✓ Compiled: ${OBJ_FILE}"
ls -lh "${OBJ_FILE}"

# Verify it's a valid BPF ELF 
file "${OBJ_FILE}" | grep -q "ELF" && \
    echo "[auranet-builder] Verified: valid ELF object" || \
    (echo "[auranet-builder] ERROR: output is not an ELF file"; exit 1)

echo "[auranet-builder] Build complete. Loader container can now start."
