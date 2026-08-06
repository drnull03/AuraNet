import os
import sys
import pytest
from unittest.mock import MagicMock

# 1. Inject a mock 'config' module so the import doesn't fail
mock_config = MagicMock()
mock_config.ai.TRUSTED_IDENTITIES = ["k8s:app=trusted-admin"]
sys.modules['config'] = mock_config

# Ensure Python can locate the engine modules in src/
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from symbolic_supervisor import SymbolicSupervisor


@pytest.fixture
def supervisor():
    return SymbolicSupervisor()


def create_mock_event(labels=None, url="/api/v1/data", method="GET", protocol="HTTP/1.1", headers=None):
    """Helper function to build valid Hubble JSON flow events."""
    if labels is None:
        labels = ["k8s:app=untrusted-app"]
    
    # Supply default valid headers so we don't accidentally trigger missing header rules
    if headers is None:
        headers = [
            {"key": "Host", "value": "api.local"},
            {"key": "User-Agent", "value": "Mozilla/5.0"}
        ]

    return {
        "flow": {
            "source": {"labels": labels},
            "l7": {
                "type": "REQUEST",
                "http": {
                    "url": url,
                    "method": method,
                    "protocol": protocol,
                    "headers": headers
                }
            }
        }
    }



def test_rule_cryptographic_identity_override(supervisor):
    """RULE 1: Cryptographic Identity Override"""
    event = create_mock_event(labels=["k8s:app=trusted-admin"])
    # Even if we send a bad method, the trusted identity overrides it
    event["flow"]["l7"]["http"]["method"] = "TRACE"
    
    assert supervisor.evaluate(event) == "Safe"


def test_rule_uri_too_large(supervisor):
    """RULE 2: URI length exceeds 512 characters"""
    massive_url = "/" + ("A" * 513)
    event = create_mock_event(url=massive_url)
    assert supervisor.evaluate(event) == "symbolic_uri_too_large"


def test_rule_null_byte_evasion(supervisor):
    """RULE 3: URL contains null bytes (%00 or \x00)"""
    event_hex = create_mock_event(url="/api/users?id=1%00")
    event_raw = create_mock_event(url="/api/users?id=1\x00")
    
    assert supervisor.evaluate(event_hex) == "symbolic_null_byte_evasion"
    assert supervisor.evaluate(event_raw) == "symbolic_null_byte_evasion"


def test_rule_excessive_path_depth(supervisor):
    """RULE 4: URL contains more than 15 slashes"""
    deep_url = "/" + "/".join(["path"] * 16)
    event = create_mock_event(url=deep_url)
    assert supervisor.evaluate(event) == "symbolic_excessive_path_depth"


def test_rule_excessive_query_params(supervisor):
    """RULE 5: URL contains more than 50 ampersands"""
    # Joining 52 items creates exactly 51 ampersands, triggering the > 50 rule
    heavy_query_url = "/api/data?" + "&".join(["q=1"] * 52)
    event = create_mock_event(url=heavy_query_url)
    assert supervisor.evaluate(event) == "symbolic_excessive_query_params"


def test_rule_excessive_url_encoding(supervisor):
    """RULE 6: URL contains more than 20 percent signs"""
    encoded_url = "/api/view?payload=" + ("%20" * 21)
    event = create_mock_event(url=encoded_url)
    assert supervisor.evaluate(event) == "symbolic_excessive_url_encoding"


def test_rule_non_ascii_url(supervisor):
    """RULE 7: URL contains non-printable raw binary bytes"""
    binary_url = "/api/upload/" + chr(150) + chr(200)
    event = create_mock_event(url=binary_url)
    assert supervisor.evaluate(event) == "symbolic_non_ascii_url"


def test_rule_banned_method(supervisor):
    """RULE 8: Use of TRACE, TRACK, or CONNECT methods"""
    for bad_method in ["TRACE", "TRACK", "CONNECT"]:
        event = create_mock_event(method=bad_method)
        assert supervisor.evaluate(event) == "symbolic_banned_method"


def test_rule_anomalous_method_length(supervisor):
    """RULE 9: HTTP method string exceeds 15 characters"""
    event = create_mock_event(method="SUPERLONGMETHODNAME")
    assert supervisor.evaluate(event) == "symbolic_anomalous_method_length"


def test_rule_excessive_header_count(supervisor):
    """RULE 10: More than 50 HTTP headers provided"""
    headers = [{"key": f"X-Header-{i}", "value": "val"} for i in range(51)]
    event = create_mock_event(headers=headers)
    assert supervisor.evaluate(event) == "symbolic_excessive_header_count"


def test_rule_massive_headers(supervisor):
    """RULE 11: Total header size exceeds 8192 bytes"""
    headers = [
        {"key": "Host", "value": "api.local"},
        {"key": "User-Agent", "value": "Mozilla/5.0"},
        {"key": "X-Payload", "value": "A" * 8193}
    ]
    event = create_mock_event(headers=headers)
    assert supervisor.evaluate(event) == "symbolic_massive_headers"


def test_rule_missing_host_header(supervisor):
    """RULE 12: HTTP/1.1 protocol used without a Host header"""
    headers = [{"key": "User-Agent", "value": "Mozilla/5.0"}] # No host
    event = create_mock_event(protocol="HTTP/1.1", headers=headers)
    assert supervisor.evaluate(event) == "symbolic_missing_host_header"


def test_rule_missing_user_agent(supervisor):
    """RULE 13: Request lacks a User-Agent header"""
    headers = [{"key": "Host", "value": "api.local"}] # No user-agent
    event = create_mock_event(headers=headers)
    assert supervisor.evaluate(event) == "symbolic_missing_user_agent"


def test_rule_get_with_body(supervisor):
    """RULE 14: GET request contains a Content-Length greater than 0"""
    headers = [
        {"key": "Host", "value": "api.local"},
        {"key": "User-Agent", "value": "Mozilla/5.0"},
        {"key": "Content-Length", "value": "100"}
    ]
    event = create_mock_event(method="GET", headers=headers)
    assert supervisor.evaluate(event) == "symbolic_get_with_body"


def test_rule_duplicate_critical_headers(supervisor):
    """RULE 15: Multiple Host or Content-Length headers provided"""
    # Test duplicate Host
    headers_dup_host = [
        {"key": "Host", "value": "api.local"},
        {"key": "Host", "value": "evil.local"},
        {"key": "User-Agent", "value": "Mozilla/5.0"}
    ]
    event_host = create_mock_event(headers=headers_dup_host)
    assert supervisor.evaluate(event_host) == "symbolic_duplicate_critical_headers"

    # Test duplicate Content-Length
    headers_dup_cl = [
        {"key": "Host", "value": "api.local"},
        {"key": "User-Agent", "value": "Mozilla/5.0"},
        {"key": "Content-Length", "value": "50"},
        {"key": "content-length", "value": "100"}  # Supervisor uses .lower()
    ]
    # We MUST explicitly set the method to POST so we don't accidentally 
    # trigger the 'symbolic_get_with_body' rule that comes earlier in the supervisor.
    event_cl = create_mock_event(method="POST", headers=headers_dup_cl)
    assert supervisor.evaluate(event_cl) == "symbolic_duplicate_critical_headers"

def test_rule_http_desync_attempt(supervisor):
    """RULE 16: Both Content-Length and Transfer-Encoding are present"""
    headers = [
        {"key": "Host", "value": "api.local"},
        {"key": "User-Agent", "value": "Mozilla/5.0"},
        {"key": "Content-Length", "value": "50"},
        {"key": "Transfer-Encoding", "value": "chunked"}
    ]
    event = create_mock_event(method="POST", headers=headers)
    assert supervisor.evaluate(event) == "symbolic_http_desync_attempt"


def test_rule_benign_traffic_is_unknown(supervisor):
    """RULE 17: Normal, safe traffic should return 'Unknown' to pass to the AI"""
    event = create_mock_event()
    assert supervisor.evaluate(event) == "Unknown"
