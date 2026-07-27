#!/usr/bin/env python3
import argparse
import logging
import os
import sys

def parse_args():
    p = argparse.ArgumentParser(prog="auranet-loader")
    p.add_argument("--bpf-src", "-b",
        default=os.environ.get("AURANET_BPF_SRC", "/app/ebpf/syscall_trace.bpf.c"),
        help="Path to the eBPF .c source file")
    p.add_argument("--pid", "-p",
        type=int,
        default=int(os.environ.get("AURANET_PID", "0")) or None,
        help="Trace only this PID (0 = all)")
    p.add_argument("--syscalls", "-s",
        default=os.environ.get("AURANET_SYSCALLS", ""),
        help="Comma-separated syscall names to capture (empty = all)")
    p.add_argument("--log-level",
        default=os.environ.get("AURANET_LOG_LEVEL", "INFO"),
        choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    return p.parse_args()

def main():
    args = parse_args()

    logging.basicConfig(
        level=args.log_level,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    if os.geteuid() != 0:
        print("ERROR: must run as root (eBPF requires CAP_BPF / root)", file=sys.stderr)
        sys.exit(1)

    class Cfg:
        bpf_src         = args.bpf_src
        pid             = args.pid
        filter_syscalls = {s.strip() for s in args.syscalls.split(",") if s.strip()} or None

    from loader import AuranetLoader
    AuranetLoader(Cfg()).start()

if __name__ == "__main__":
    main()