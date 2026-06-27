"""Typed event dataclass (optional – used for future extensions)."""

from dataclasses import dataclass, field
from typing import List, Optional


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
