#include <stdio.h>
#include <unistd.h>
#include <sys/resource.h>
#include <bpf/libbpf.h>
#include "syscall_trace.skel.h"

#define BPF_FS_DIR "/sys/fs/bpf/auranet"

int main(int argc, char **argv)
{
    struct syscall_trace_bpf *skel;
    int err;

    // Bump RLIMIT_MEMLOCK to allow eBPF map creation
    struct rlimit r = {RLIM_INFINITY, RLIM_INFINITY};
    setrlimit(RLIMIT_MEMLOCK, &r);

    skel = syscall_trace_bpf__open_and_load();
    if (!skel) {
        fprintf(stderr, "Failed to open and load BPF skeleton\n");
        return 1;
    }

    err = syscall_trace_bpf__attach(skel);
    if (err) {
        fprintf(stderr, "Failed to attach BPF skeleton\n");
        syscall_trace_bpf__destroy(skel);
        return 1;
    }

    err = bpf_map__pin(skel->maps.events, BPF_FS_DIR "_events");
    if (err) {
        fprintf(stderr, "Failed to pin events map\n");
        goto cleanup;
    }

    err = bpf_link__pin(skel->links.handle_sys_enter, BPF_FS_DIR "_sys_enter");
    if (err) goto cleanup;

    err = bpf_link__pin(skel->links.handle_sys_exit, BPF_FS_DIR "_sys_exit");
    if (err) goto cleanup;

    printf("AuraNet eBPF successfully pinned to " BPF_FS_DIR "\n");
    return 0;

cleanup:
    syscall_trace_bpf__destroy(skel);
    return 1;
}