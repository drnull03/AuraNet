CLANG := clang
BPFTOOL := bpftool
CFLAGS := -g -O2 -Wall

ARCH := $(shell uname -m | sed 's/x86_64/x86/' | sed 's/aarch64/arm64/')

.PHONY: all clean

all: auranet-installer

# Generate vmlinux.h from the host kernel
vmlinux.h:
	$(BPFTOOL) btf dump file /sys/kernel/btf/vmlinux format c > vmlinux.h

# Compile eBPF source into object file
syscall_trace.bpf.o: syscall_trace.bpf.c vmlinux.h
	$(CLANG) -g -O2 -target bpf -D__TARGET_ARCH_$(ARCH) -c syscall_trace.bpf.c -o $@

# Generate the C skeleton header
syscall_trace.skel.h: syscall_trace.bpf.o
	$(BPFTOOL) gen skeleton $< > $@

# Compile the C loader binary
auranet-installer: loader.c syscall_trace.skel.h
	$(CLANG) $(CFLAGS) -o $@ loader.c -lbpf -lelf -lz

clean:
	rm -f *.o *.skel.h vmlinux.h auranet-installer