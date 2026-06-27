#!/usr/bin/env python3
"""auranet-loader CLI – configurable via flags or env vars."""

import argparse
import logging
import os
import sys


def parse_args():
    p = argparse.ArgumentParser(
        prog="auranet-loader",
        description="Lightweight eBPF syscall tracer (loads pre-compiled BPF object)",
    )
    p.add_argument("--bpf-obj", "-b",
        default=os.environ.get("AURANET_BPF_OBJ", "/ebpf/syscall_trace.bpf.o"),
        help="Path to the compiled eBPF .o file (written by the builder initContainer)")
    # this gonna change to the same tetragon path to make it switchable 
    p.add_argument("--output", "-o",
        default=os.environ.get("AURANET_OUTPUT", "/var/log/auranet/events.json"),
        help="Output JSON-lines file")
    p.add_argument("--pid", "-p",
        type=int,
        default=int(os.environ.get("AURANET_PID", "0")) or None,
        help="Trace only this PID (0 = all)")
    p.add_argument("--syscalls", "-s",
        default=os.environ.get("AURANET_SYSCALLS", ""),
        help="Comma-separated syscall names to capture (empty = all)")
    p.add_argument("--rotate-mb",
        type=float,
        default=float(os.environ.get("AURANET_ROTATE_MB", "0")) or None,
        help="Rotate output file at this size in MB")
    p.add_argument("--log-level",
        default=os.environ.get("AURANET_LOG_LEVEL", "INFO"),
        choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    p.add_argument("--verbose", "-v",
        action="store_true",
        default=os.environ.get("AURANET_VERBOSE", "").lower() in ("1","true","yes"),
        help="Print events to stderr as they arrive")
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
        bpf_obj         = args.bpf_obj
        output          = args.output
        pid             = args.pid
        filter_syscalls = {s.strip() for s in args.syscalls.split(",") if s.strip()} or None
        rotate_mb       = args.rotate_mb
        verbose         = args.verbose

    from loader import AuranetLoader
    AuranetLoader(Cfg()).start()


if __name__ == "__main__":
    main()
