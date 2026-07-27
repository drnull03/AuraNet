# auranet-loader eBPF build
# Requires: clang >= 12, libbpf-dev, linux-headers
# we default to this only for debugging
CLANG      ?= clang
BPF_CFLAGS := -O2 -g -Wall -Wno-unused-value -Wno-pointer-sign \
               -Wno-compare-distinct-pointer-types \
               -target bpf \
               -D__TARGET_ARCH_x86

VMLINUX    ?= /sys/kernel/btf/vmlinux
LIBBPF_INC ?= /usr/include

SRC  = syscall_trace.bpf.c
OBJ  = syscall_trace.bpf.o
SKEL = syscall_trace.skel.h

.PHONY: all clean

all: $(OBJ)

$(OBJ): $(SRC)
	$(CLANG) $(BPF_CFLAGS) \
		-I$(LIBBPF_INC) \
		-c $< -o $@

# generate skeleton header (requires bpftool)
$(SKEL): $(OBJ)
	bpftool gen skeleton $< > $@

clean:
	rm -f $(OBJ) $(SKEL)
