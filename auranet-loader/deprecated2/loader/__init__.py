/**
 * @file __init__.py
 * @brief AuraNet userspace eBPF ring-buffer consumer.
 *
 * This module implements the userspace loader component of AuraNet's
 * kernel telemetry pipeline.
 *
 * The loader is responsible for:
 * - Loading a pre-compiled eBPF ELF object generated during node initialization.
 * - Attaching raw kernel tracepoints for syscall monitoring.
 * - Receiving kernel events through a high-performance BPF ring buffer.
 * - Decoding binary syscall events into structured JSON records.
 * - Persisting telemetry events using JSON Lines format.
 *
 * The component runs as a node-level daemon and acts as the bridge between
 * kernel-space eBPF programs and userspace security analysis components.
 *
 * Data flow:
 *
 * Kernel Syscalls
 *        |
 *        v
 * eBPF Raw Tracepoints
 *        |
 *        v
 * BPF Ring Buffer
 *        |
 *        v
 * AuraNet Loader
 *        |
 *        v
 * JSON Event Stream
 *
 * @note The eBPF object is expected to be pre-compiled by an initContainer.
 *       The loader does not compile eBPF source code at runtime.
 */
#!/usr/bin/env python3
"""
auranet-loader – userspace ring-buffer consumer.

Loads a PRE-COMPILED eBPF object (built on-node by the initContainer),
attaches raw tracepoints, drains the ring buffer, and writes JSON-lines.
"""

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

#
# struct syscall_event {
#     u64 timestamp_ns;          +0   (8)
#     u32 pid;                   +8   (4)
#     u32 tgid;                  +12  (4)
#     u32 uid;                   +16  (4)
#     u32 gid;                   +20  (4)
#     s64 syscall_nr;            +24  (8)  — pad to 8-byte align
#     u64 args[6];               +32  (48)
#     s64 ret;                   +80  (8)
#     char comm[16];             +88  (16)
#     u8  is_exit;               +104 (1)
#     u8  _pad[7];               +105 (7)
# }                              = 112 bytes total

/**
 * @brief Binary layout of syscall events exchanged between eBPF and userspace.
 *
 * This structure must exactly match the C structure defined inside the
 * eBPF kernel program.
 *
 * The format uses:
 * - Little endian encoding.
 * - Fixed-size fields.
 * - Explicit padding for kernel alignment compatibility.
 *
 * Total size:
 * 112 bytes
 */
_STRUCT = struct.Struct(
    "<"         # little-endian
    "Q"         # timestamp_ns  u64
    "I"         # pid           u32
    "I"         # tgid          u32
    "I"         # uid           u32
    "I"         # gid           u32
    "q"         # syscall_nr    s64
    "QQQQQQ"    # args[0..5]    6×u64
    "q"         # ret           s64
    "16s"       # comm          char[16]
    "B"         # is_exit       u8
    "7x"        # _pad[7]
)
/**
 * @brief Size of a single syscall event structure in bytes.
 *
 * Used to validate received ring-buffer events before decoding.
 */
EVENT_SIZE = _STRUCT.size   # 112



from .syscall_names import SYSCALL_NAMES

/**
 * @class AuranetLoader
 * @brief Main userspace controller for AuraNet eBPF telemetry collection.
 *
 * This class manages the complete lifecycle of the loader:
 *
 * Initialization:
 * - Validates eBPF object availability.
 * - Loads the compiled eBPF program.
 *
 * Runtime:
 * - Attaches syscall tracepoints.
 * - Opens the ring buffer.
 * - Continuously consumes kernel events.
 * - Converts binary events into JSON telemetry.
 *
 * Shutdown:
 * - Handles termination signals.
 * - Flushes output streams.
 * - Releases resources.
 *
 * @note This component runs with elevated privileges because eBPF programs
 *       require kernel-level access.
 */
class AuranetLoader:
    /**
 * @brief Initializes the AuraNet loader instance.
 *
 * @param cfg Runtime configuration object containing:
 * - eBPF object path.
 * - Output path.
 * - PID filtering options.
 * - Syscall filtering options.
 * - Logging preferences.
 */
    def __init__(self, cfg):
        self.cfg = cfg
        self._bpf = None
        self._running = True
        self._out = None
        self._n = 0         # events written counter

/**
 * @brief Starts the eBPF telemetry collection pipeline.
 *
 * Performs:
 * - eBPF object validation.
 * - Kernel program loading.
 * - Output file initialization.
 * - Signal handler registration.
 * - Ring-buffer polling startup.
 *
 * @return None
 */
    def start(self):
        bpf_obj = Path(self.cfg.bpf_obj)
        if not bpf_obj.exists():
            log.error(
                "eBPF object not found at %s — did the builder initContainer finish?",
                bpf_obj,
            )
            sys.exit(1)

        log.info("Loading pre-compiled eBPF object: %s", bpf_obj)
        self._load_bpf(bpf_obj)

        out = Path(self.cfg.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        self._out = open(out, "a", buffering=1)   # line-buffered
        log.info("Writing events → %s", out)

        signal.signal(signal.SIGINT,  self._on_signal)
        signal.signal(signal.SIGTERM, self._on_signal)

        log.info("auranet-loader active (pid=%d). Ctrl-C or SIGTERM to stop.", os.getpid())
        self._poll_loop()
/**
 * @brief Stops the loader gracefully.
 *
 * Performs:
 * - Stops polling loop.
 * - Flushes pending events.
 * - Closes output streams.
 * - Reports total collected events.
 */
    def stop(self):
        self._running = False
        if self._out:
            self._out.flush()
            self._out.close()
        log.info("Stopped. Total events written: %d", self._n)


    def _on_signal(self, *_):
        self.stop()
/**
 * @brief Loads and attaches the precompiled eBPF program.
 *
 * Operations:
 * - Loads ELF eBPF object using BCC.
 * - Applies optional PID filtering.
 * - Attaches syscall entry and exit tracepoints.
 * - Registers the ring-buffer callback.
 *
 * @param obj_path Path to compiled eBPF object file.
 *
 * @exception ImportError
 * Raised when BCC userspace bindings are unavailable.
 */
    def _load_bpf(self, obj_path: Path):
        """Load the compiled .o and attach raw tracepoints."""
        try:
            from bcc import BPF
        except ImportError:
            log.error("python3-bpfcc is not installed. "
                      "Install via: apt-get install python3-bpfcc")
            sys.exit(1)

        # BCC can load from a pre-compiled ELF object via the src_file= param
        # when combined with the object= kwarg for loading .o directly.
        # We use the object= path introduced in recent BCC versions.
        try:
            self._bpf = BPF(object=str(obj_path))
        except Exception:
            # Older BCC: fall back to src_file (re-compiles from source)
            log.warning(
                "BCC object= load failed, falling back to src_file "
                "(requires C source alongside the .o). Error will follow."
            )
            raise

        # Apply PID filter before attaching so first events aren't missed
        if self.cfg.pid:
            pid_map = self._bpf["pid_filter"]
            pid_map[ctypes.c_uint(0)] = ctypes.c_uint(self.cfg.pid)
            log.info("PID filter: %d", self.cfg.pid)

        self._bpf.attach_raw_tracepoint(
            tp="sys_enter", fn_name="handle_sys_enter"
        )
        self._bpf.attach_raw_tracepoint(
            tp="sys_exit", fn_name="handle_sys_exit"
        )
        log.info("Tracepoints attached: raw_tracepoint/sys_enter, sys_exit")

        self._bpf["events"].open_ring_buffer(self._on_event)

/**
 * @brief Continuously consumes events from the BPF ring buffer.
 *
 * The polling loop:
 * - Waits for kernel events.
 * - Dispatches events to the decoder callback.
 * - Performs optional output rotation.
 */
    def _poll_loop(self):
        while self._running:
            try:
                self._bpf.ring_buffer_poll(timeout=100)
                if self.cfg.rotate_mb and self._should_rotate():
                    self._rotate()
            except KeyboardInterrupt:
                break
        self.stop()
/**
 * @brief Checks whether output rotation is required.
 *
 * @return True if current log size exceeds configured limit.
 */
    def _should_rotate(self) -> bool:
        try:
            return os.path.getsize(self.cfg.output) > self.cfg.rotate_mb * 1_048_576
        except FileNotFoundError:
            return False
/**
 * @brief Rotates the telemetry output file.
 *
 * Creates a timestamped archive and continues writing into
 * a fresh JSON-lines file.
 */
    def _rotate(self):
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        rotated = f"{self.cfg.output}.{ts}"
        os.rename(self.cfg.output, rotated)
        self._out.close()
        self._out = open(self.cfg.output, "a", buffering=1)
        log.info("Rotated → %s", rotated)
/**
 * @brief Decodes and processes a single ring-buffer event.
 *
 * Converts raw binary kernel data into a structured JSON object.
 *
 * Processing steps:
 * - Validate event size.
 * - Deserialize binary structure.
 * - Resolve syscall number to syscall name.
 * - Apply syscall filtering.
 * - Serialize event as JSON.
 *
 * @param ctx BPF callback context.
 * @param data Raw event memory pointer.
 * @param size Received event size.
 */
    def _on_event(self, ctx, data, size):
        if size < EVENT_SIZE:
            log.debug("Short event ignored (%d < %d bytes)", size, EVENT_SIZE)
            return

        raw = bytes(
            ctypes.cast(data, ctypes.POINTER(ctypes.c_char * EVENT_SIZE)).contents
        )
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

        self._out.write(json.dumps(ev, separators=(",", ":")) + "\n")
        self._n += 1

        if self.cfg.verbose:
            tag = "EXIT" if is_exit else "ENTR"
            r = f" ret={ret}" if is_exit else ""
            print(f"[{tag}] tgid={tgid:6d} {comm:16s} {name}{r}", file=sys.stderr)
