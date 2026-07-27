// SPDX-License-Identifier: GPL-2.0
// auranet-loader: for debugging purposes
// Built on-node by the builder initContainer against the node's own kernel headers.

#include <linux/bpf.h>
#include <linux/ptrace.h>
#include <linux/sched.h>
#include <linux/types.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include <bpf/bpf_core_read.h>
//this version only detect two syscalls and that is enough for the demo 
//for more syscalls one can refer a different version of this file 

#define TASK_COMM_LEN   16
#define MAX_ARGS        6
// Ring-buffer capacity (bytes).  Must be a power of 2 and multiple of page size.
#define RING_BUF_BYTES  (1 << 22)   // 4 MiB

struct syscall_event {
    __u64 timestamp_ns;
    __u32 pid;
    __u32 tgid;
    __u32 uid;
    __u32 gid;
    __s64 syscall_nr;
    __u64 args[MAX_ARGS];   // only valid on sys_enter events
    __s64 ret;              // only valid on sys_exit events
    char  comm[TASK_COMM_LEN];
    __u8  is_exit;          // 0 = enter, 1 = exit
    __u8  _pad[7];
};


struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, RING_BUF_BYTES);
} events SEC(".maps");

// PID allowlist: if pid_filter[0] != 0, only that TGID is traced.
// Written from Python userspace after program load.
struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __uint(max_entries, 1);
    __type(key,   __u32);
    __type(value, __u32);
} pid_filter SEC(".maps");


static __always_inline int should_trace(__u32 tgid)
{
    __u32 key = 0;
    __u32 *fp = bpf_map_lookup_elem(&pid_filter, &key);
    if (fp && *fp != 0 && *fp != tgid)
        return 0;
    return 1;
}

static __always_inline void fill_common(struct syscall_event *ev,
                                        __u64 id, __s64 nr)
{
    __u64 uid_gid = bpf_get_current_uid_gid();
    ev->timestamp_ns = bpf_ktime_get_ns();
    ev->pid          = (__u32)id;
    ev->tgid         = (__u32)(id >> 32);
    ev->uid          = (__u32)uid_gid;
    ev->gid          = (__u32)(uid_gid >> 32);
    ev->syscall_nr   = nr;
    bpf_get_current_comm(ev->comm, sizeof(ev->comm));
}


SEC("raw_tracepoint/sys_enter")
int handle_sys_enter(struct bpf_raw_tracepoint_args *ctx)
{
    __u64 id   = bpf_get_current_pid_tgid();
    __u32 tgid = (__u32)(id >> 32);
    if (!should_trace(tgid)) return 0;

    struct syscall_event *ev =
        bpf_ringbuf_reserve(&events, sizeof(*ev), 0);
    if (!ev) return 0;

    // ctx->args[0] = pt_regs*, ctx->args[1] = syscall nr
    struct pt_regs *regs = (struct pt_regs *)ctx->args[0];
    fill_common(ev, id, (__s64)ctx->args[1]);

    ev->args[0] = PT_REGS_PARM1_CORE_SYSCALL(regs);
    ev->args[1] = PT_REGS_PARM2_CORE_SYSCALL(regs);
    ev->args[2] = PT_REGS_PARM3_CORE_SYSCALL(regs);
    ev->args[3] = PT_REGS_PARM4_CORE_SYSCALL(regs);
    ev->args[4] = PT_REGS_PARM5_CORE_SYSCALL(regs);
    ev->args[5] = PT_REGS_PARM6_CORE_SYSCALL(regs);
    ev->ret     = 0;
    ev->is_exit = 0;
    __builtin_memset(ev->_pad, 0, sizeof(ev->_pad));

    bpf_ringbuf_submit(ev, 0);
    return 0;
}


SEC("raw_tracepoint/sys_exit")
int handle_sys_exit(struct bpf_raw_tracepoint_args *ctx)
{
    __u64 id   = bpf_get_current_pid_tgid();
    __u32 tgid = (__u32)(id >> 32);
    if (!should_trace(tgid)) return 0;

    struct syscall_event *ev =
        bpf_ringbuf_reserve(&events, sizeof(*ev), 0);
    if (!ev) return 0;

    struct pt_regs *regs = (struct pt_regs *)ctx->args[0];
    fill_common(ev, id, (__s64)ctx->args[1]);

    __builtin_memset(ev->args, 0, sizeof(ev->args));
    ev->ret     = (__s64)PT_REGS_RC_CORE(regs);
    ev->is_exit = 1;
    __builtin_memset(ev->_pad, 0, sizeof(ev->_pad));

    bpf_ringbuf_submit(ev, 0);
    return 0;
}

char _license[] SEC("license") = "GPL";
