/**
 * @file event.py
 * @brief Typed representation of AuraNet syscall telemetry events.
 *
 * Provides a strongly typed Python representation of syscall events.
 *
 * This dataclass is currently optional and reserved for future extensions
 * requiring object-oriented event manipulation.
 */

# can be ignored for now

from dataclasses import dataclass, field
from typing import List, Optional

/**
 * @class SyscallEvent
 * @brief Represents a decoded Linux syscall event.
 *
 * Stores metadata collected from kernel tracepoints including:
 *
 * - Process identity.
 * - User and group information.
 * - Syscall identifier.
 * - Syscall arguments.
 * - Return values.
 *
 * This object provides a structured representation before conversion
 * into external telemetry formats.
 */
@dataclass
class SyscallEvent:
    timestamp_ns: int
    event_type: str          # "sys_enter" | "sys_exit"
    pid: int
    tgid: int
    uid: int
    gid: int
    comm: str
    syscall_nr: int
    syscall_name: str
    args: List[int] = field(default_factory=list)
    ret: Optional[int] = None
/**
 * @brief Converts the syscall event into a JSON-compatible dictionary.
 *
 * The output format separates syscall metadata from syscall-specific
 * information:
 *
 * sys_enter:
 * - Includes syscall arguments.
 *
 * sys_exit:
 * - Includes syscall return value.
 *
 * @return Dictionary representation of the event.
 */
    def to_dict(self) -> dict:
        d: dict = {
            "timestamp_ns": self.timestamp_ns,
            "event_type":   self.event_type,
            "pid":  self.pid,
            "tgid": self.tgid,
            "uid":  self.uid,
            "gid":  self.gid,
            "comm": self.comm,
            "syscall": {
                "nr":   self.syscall_nr,
                "name": self.syscall_name,
            },
        }
        if self.event_type == "sys_enter":
            d["args"] = self.args
        else:
            d["ret"] = self.ret
        return d
