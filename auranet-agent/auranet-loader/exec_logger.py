#!/usr/bin/env python3
from bcc import BPF
import time

bpf_text = """
#include <uapi/linux/ptrace.h>
#include <linux/sched.h>

// Define the structure for the data we will send to user space
struct data_t {
    u32 pid;
    char comm[TASK_COMM_LEN];
    char fname[256];
};

// Define a perf ring buffer to send events to Python
BPF_PERF_OUTPUT(events);

// Attach to the execve tracepoint
TRACEPOINT_PROBE(syscalls, sys_enter_execve) {
    struct data_t data = {};
    
    // Get Process ID
    data.pid = bpf_get_current_pid_tgid() >> 32;
    
    // Get the name of the current process calling execve
    bpf_get_current_comm(&data.comm, sizeof(data.comm));
    
    // Get the filename being executed from the tracepoint arguments
    bpf_probe_read_user_str(&data.fname, sizeof(data.fname), args->filename);
    
    // Submit the data to user space
    events.perf_submit(args, &data, sizeof(data));
    return 0;
}
"""

b = BPF(text=bpf_text)

log_filename = "execve_logs.txt"

print(f"Tracing execve... Logging to {log_filename}. Press Ctrl+C to stop.")

with open(log_filename, "a") as log_file:
    # Write a header if the file is new
    log_file.write(f"{'TIME':<20} {'PID':<10} {'PARENT_COMM':<20} {'EXECUTABLE'}\n")

    # Callback function to handle incoming eBPF events
    def print_event(cpu, data, size):
        event = b["events"].event(data)
        
        # Decode byte strings to standard strings
        comm = event.comm.decode('utf-8', 'replace')
        fname = event.fname.decode('utf-8', 'replace')
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Format the log line
        log_line = f"{current_time:<20} {event.pid:<10} {comm:<20} {fname}"
        
        # Print to console (optional) and write to file
        print(log_line)
        log_file.write(log_line + "\n")
        log_file.flush() # Ensure it writes immediately

    # Open the perf buffer and bind the callback
    b["events"].open_perf_buffer(print_event)

    try:
        while True:
            b.perf_buffer_poll()
    except KeyboardInterrupt:
        print("\nExiting and closing log file.")
        exit()
