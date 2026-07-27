#!/usr/bin/env python3
import ctypes
import json
import logging
import os
import signal
import struct
import sys
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger("auranet")

_STRUCT = struct.Struct(
    "<QIIIIqQQQQQQq16sB7x"
)
EVENT_SIZE = _STRUCT.size

from .syscall_names import SYSCALL_NAMES

class AuranetLoader:
    def __init__(self, cfg):
        self.cfg = cfg
        self._bpf = None
        self._running = True
        self._n = 0

    def start(self):
        bpf_src = Path(self.cfg.bpf_src)
        if not bpf_src.exists():
            log.error("eBPF source not found at %s", bpf_src)
            sys.exit(1)

        log.info("Compiling and loading eBPF source: %s", bpf_src)
        self._load_bpf(bpf_src)

        signal.signal(signal.SIGINT,  self._on_signal)
        signal.signal(signal.SIGTERM, self._on_signal)

        log.info("auranet-loader active (pid=%d). Streaming to stdout. Ctrl-C to stop.", os.getpid())
        self._poll_loop()

    def stop(self):
        self._running = False
        log.info("Stopped. Total events processed: %d", self._n)

    def _on_signal(self, *_):
        self.stop()

    def _load_bpf(self, src_path: Path):
        try:
            from bcc import BPF
        except ImportError:
            log.error("python3-bpfcc is not installed.")
            sys.exit(1)

        # BCC compiles the C code dynamically at runtime against the node's headers
        self._bpf = BPF(src_file=str(src_path))

        if self.cfg.pid:
            pid_map = self._bpf["pid_filter"]
            pid_map[ctypes.c_uint(0)] = ctypes.c_uint(self.cfg.pid)
            log.info("PID filter: %d", self.cfg.pid)

        self._bpf.attach_raw_tracepoint(tp="sys_enter", fn_name="handle_sys_enter")
        self._bpf.attach_raw_tracepoint(tp="sys_exit", fn_name="handle_sys_exit")
        log.info("Tracepoints attached: raw_tracepoint/sys_enter, sys_exit")

        self._bpf["events"].open_ring_buffer(self._on_event)

    def _poll_loop(self):
        while self._running:
            try:
                self._bpf.ring_buffer_poll(timeout=100)
            except KeyboardInterrupt:
                break
        self.stop()

    def _on_event(self, ctx, data, size):
        if size < EVENT_SIZE:
            return

        raw = bytes(ctypes.cast(data, ctypes.POINTER(ctypes.c_char * EVENT_SIZE)).contents)
        (ts_ns, pid, tgid, uid, gid, syscall_nr,
         a0, a1, a2, a3, a4, a5,
         ret, comm_b, is_exit) = _STRUCT.unpack(raw)

        comm = comm_b.rstrip(b"\x00").decode("utf-8", errors="replace")
        name = SYSCALL_NAMES.get(syscall_nr, f"unknown_{syscall_nr}")

        if self.cfg.filter_syscalls and name not in self.cfg.filter_syscalls:
            return

        ev: dict = {
            "ts":         datetime.fromtimestamp(ts_ns / 1e9, tz=timezone.utc).isoformat(),
            "ts_ns":      ts_ns,
            "type":       "exit" if is_exit else "enter",
            "pid":        pid,
            "tgid":       tgid,
            "uid":        uid,
            "gid":        gid,
            "comm":       comm,
            "syscall_nr": syscall_nr,
            "syscall":    name,
        }
        if is_exit:
            ev["ret"] = ret
        else:
            ev["args"] = [a0, a1, a2, a3, a4, a5]

        # Output directly to stdout instead of a log file
        print(json.dumps(ev, separators=(",", ":")), flush=True)
        self._n += 1