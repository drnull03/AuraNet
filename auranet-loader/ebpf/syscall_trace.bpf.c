// SPDX-License-Identifier: GPL-2.0
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include <bpf/bpf_core_read.h>

#define TASK_COMM_LEN   16
#define MAX_STR_LEN     256
#define RING_BUF_BYTES  (1 << 22) // 4 MiB

// Updated struct to hold strings instead of raw pointers
struct syscall_event {
    __u64 timestamp_ns;
    __u32 pid;
    __u32 tgid;
    __u32 uid;
    __u32 gid;
    __s64 syscall_nr;
    __s64 ret;
    char  comm[TASK_COMM_LEN];
    //changed this to make auranet-runtime easier to work this 
    char  str_arg[MAX_STR_LEN]; // Holds the binary or file path
    __u8  is_exit;
    __u8  _pad[7];
};

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, RING_BUF_BYTES);
} events SEC(".maps");

static __always_inline void fill_common(struct syscall_event *ev, __u64 id, __s64 nr)
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
    __u64 id = bpf_get_current_pid_tgid();
    __s64 syscall_nr = (__s64)ctx->args[1];

    // added a filter here for the demo this is not necessary and for demo purposes
    if (syscall_nr != 2 && syscall_nr != 59 && syscall_nr != 257 && syscall_nr != 322) {
        return 0;
    }

    struct syscall_event *ev = bpf_ringbuf_reserve(&events, sizeof(*ev), 0);
    if (!ev) return 0;

    fill_common(ev, id, syscall_nr);
    ev->is_exit = 0;
    ev->ret = 0;
    
    // Zero out the string buffer and padding
    __builtin_memset(ev->str_arg, 0, sizeof(ev->str_arg));
    __builtin_memset(ev->_pad, 0, sizeof(ev->_pad));

    struct pt_regs *regs = (struct pt_regs *)ctx->args[0];
    const char *arg_ptr = NULL;

    // Identify which argument holds the string pointer
    if (syscall_nr == 2 || syscall_nr == 59) {
        arg_ptr = (const char *)PT_REGS_PARM1_CORE_SYSCALL(regs);
    } else if (syscall_nr == 257 || syscall_nr == 322) {
        arg_ptr = (const char *)PT_REGS_PARM2_CORE_SYSCALL(regs);
    }

    //  Extract the string from userspace memory
    //bpf_proble_read_user_str is a kernel function
    if (arg_ptr) {
        bpf_probe_read_user_str(ev->str_arg, sizeof(ev->str_arg), arg_ptr);
    }

    bpf_ringbuf_submit(ev, 0);
    return 0;
}

char _license[] SEC("license") = "GPL";














































/*// SPDX-License-Identifier: GPL-2.0
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include <bpf/bpf_core_read.h>

#define TASK_COMM_LEN   16
#define MAX_ARGS        6
#define RING_BUF_BYTES  (1 << 22) // 4 MiB

struct syscall_event {
    __u64 timestamp_ns;
    __u32 pid;
    __u32 tgid;
    __u32 uid;
    __u32 gid;
    __s64 syscall_nr;
    __u64 args[MAX_ARGS];
    __s64 ret;
    char  comm[TASK_COMM_LEN];
    __u8  is_exit;
    __u8  _pad[7];
};

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, RING_BUF_BYTES);
} events SEC(".maps");

static __always_inline void fill_common(struct syscall_event *ev, __u64 id, __s64 nr)
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
int BPF_PROG(handle_sys_enter, struct pt_regs *regs, long id)
{
    struct syscall_event *ev = bpf_ringbuf_reserve(&events, sizeof(*ev), 0);
    if (!ev) return 0;

    fill_common(ev, bpf_get_current_pid_tgid(), id);
    
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
int BPF_PROG(handle_sys_exit, struct pt_regs *regs, long ret)
{
    long id = 0; // Capture syscall ID logic here if needed
    struct syscall_event *ev = bpf_ringbuf_reserve(&events, sizeof(*ev), 0);
    if (!ev) return 0;

    fill_common(ev, bpf_get_current_pid_tgid(), id);

    __builtin_memset(ev->args, 0, sizeof(ev->args));
    ev->ret     = ret;
    ev->is_exit = 1;
    __builtin_memset(ev->_pad, 0, sizeof(ev->_pad));

    bpf_ringbuf_submit(ev, 0);
    return 0;
}

char _license[] SEC("license") = "GPL";*/