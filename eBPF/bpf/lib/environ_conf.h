// SPDX-License-Identifier: (GPL-2.0-only OR BSD-2-Clause)
/* Copyright Authors of aura */

#ifndef __ENVIRON_CONF_
#define __ENVIRON_CONF_

/* bpf runtime log levels that follow Golang logrus levels
 * https://pkg.go.dev/github.com/sirupsen/logrus#Level
 */
enum {
	LOG_ERROR_LEVEL = 2,
	LOG_WARN_LEVEL = 3,
	LOG_INFO_LEVEL = 4,
	LOG_DEBUG_LEVEL = 5,
	LOG_TRACE_LEVEL = 6,
};

/* aura runtime configuration */
struct auragon_conf {
	__u32 loglevel; /* aura log level */
	__u32 pid; /* aura pid for debugging purpose */
	__u32 nspid; /* aura pid in namespace for debugging purpose */
	__u32 tg_cgrp_hierarchy; /* aura tracked hierarchy ID */
	__u32 tg_cgrpv1_subsys_idx; /* aura tracked cgroupv1 subsystem state index at compile time */
	__u32 tg_cgrp_level; /* aura cgroup level */
	__u64 tg_cgrpid; /* aura current cgroup ID to avoid filtering blocking itself */
	__u64 cgrp_fs_magic; /* Cgroupv1 or Cgroupv2 */
	__u8 use_perf_ring_buf; /* Use perf ring buffer rather than the bpf ring buffer */
	__u8 pad[7];
}; // All fields aligned so no 'packed' attribute.

/* aura runtime configuration storage.
 * Set from userspace during startup and environment discovery
 * only, bpf part is read-only.
 */
struct {
	__uint(type, BPF_MAP_TYPE_ARRAY);
	__uint(max_entries, 1);
	__type(key, __u32);
	__type(value, struct auragon_conf);
} tg_conf_map SEC(".maps");

#endif // __ENVIRON_CONF_
