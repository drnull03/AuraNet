import unittest
import os

class MockAIConfig:
    TRUSTED_IDENTITIES = ["k8s:app=auranet-controller", "k8s:app=gitlab-runner"]

class MockConfig:
    ai = MockAIConfig()

# Inject the mock config into the global namespace for the supervisor to use
import sys
sys.modules['config'] = MockConfig()

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from symbolic_supervisor import SymbolicSupervisor 


class TestSymbolicSupervisor(unittest.TestCase):
    def setUp(self):
        self.supervisor = SymbolicSupervisor()
        # A set of standard headers that mimic legitimate traffic
        self.valid_headers = [
            {"key": "Host", "value": "account-service.default.svc.cluster.local"},
            {"key": "User-Agent", "value": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
            {"key": "Accept", "value": "application/json"}
        ]

    def create_mock_event(self, method="GET", url="/api/v1/health", protocol="HTTP/1.1", headers=None, labels=None):
        """Helper to quickly generate Hubble JSON payloads for testing."""
        if headers is None:
            headers = self.valid_headers
        if labels is None:
            labels = ["k8s:app=frontend-ui"]
            
        return {
            "flow": {
                "source": {"labels": labels},
                "l7": {
                    "type": "REQUEST",
                    "http": {
                        "method": method,
                        "url": url,
                        "protocol": protocol,
                        "headers": headers
                    }
                }
            }
        }

    def test_legitimate_traffic_is_unknown(self):
        """Benign traffic should return 'Unknown' so it gets passed to the AI."""
        event = self.create_mock_event()
        result = self.supervisor.evaluate(event)
        self.assertEqual(result, "Unknown")

    def test_cryptographic_override(self):
        """Traffic from highly trusted internal components bypasses inspection."""
        event = self.create_mock_event(labels=["k8s:app=auranet-controller"])
        result = self.supervisor.evaluate(event)
        self.assertEqual(result, "Safe")

    def test_uri_too_large(self):
        event = self.create_mock_event(url="/" + "A" * 600)
        result = self.supervisor.evaluate(event)
        self.assertEqual(result, "symbolic_uri_too_large")

    def test_null_byte_evasion(self):
        event = self.create_mock_event(url="/api/users?id=5%00drop")
        result = self.supervisor.evaluate(event)
        self.assertEqual(result, "symbolic_null_byte_evasion")

    def test_excessive_path_depth(self):
        event = self.create_mock_event(url="/api/v1/a/b/c/d/e/f/g/h/i/j/k/l/m/n/o/p/q")
        result = self.supervisor.evaluate(event)
        self.assertEqual(result, "symbolic_excessive_path_depth")

    def test_excessive_query_params(self):
        event = self.create_mock_event(url="/api/data?" + "&".join(["a=1"] * 55))
        result = self.supervisor.evaluate(event)
        self.assertEqual(result, "symbolic_excessive_query_params")

    def test_excessive_url_encoding(self):
        event = self.create_mock_event(url="/api/view?payload=%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20")
        result = self.supervisor.evaluate(event)
        self.assertEqual(result, "symbolic_excessive_url_encoding")

    def test_non_ascii_url(self):
        # Injecting raw hex/binary bytes directly into the URL path
        event = self.create_mock_event(url="/api/upload/" + chr(255) + chr(200))
        result = self.supervisor.evaluate(event)
        self.assertEqual(result, "symbolic_non_ascii_url")

    def test_banned_method(self):
        event = self.create_mock_event(method="TRACE")
        result = self.supervisor.evaluate(event)
        self.assertEqual(result, "symbolic_banned_method")

    def test_anomalous_method_length(self):
        event = self.create_mock_event(method="SUPERLONGMETHODNAMEFORFUZZING")
        result = self.supervisor.evaluate(event)
        self.assertEqual(result, "symbolic_anomalous_method_length")

    def test_excessive_header_count(self):
        # Create 55 tiny junk headers
        junk_headers = [{"key": f"X-Junk-{i}", "value": "1"} for i in range(55)]
        event = self.create_mock_event(headers=self.valid_headers + junk_headers)
        result = self.supervisor.evaluate(event)
        self.assertEqual(result, "symbolic_excessive_header_count")

    def test_massive_headers(self):
        # Create a single 10KB header
        massive_header = [{"key": "X-Payload", "value": "A" * 9000}]
        event = self.create_mock_event(headers=self.valid_headers + massive_header)
        result = self.supervisor.evaluate(event)
        self.assertEqual(result, "symbolic_massive_headers")

    def test_missing_host_header(self):
        headers_without_host = [{"key": "User-Agent", "value": "curl/7.68.0"}]
        event = self.create_mock_event(headers=headers_without_host)
        result = self.supervisor.evaluate(event)
        self.assertEqual(result, "symbolic_missing_host_header")

    def test_missing_user_agent(self):
        headers_without_ua = [{"key": "Host", "value": "localhost"}]
        event = self.create_mock_event(headers=headers_without_ua)
        result = self.supervisor.evaluate(event)
        self.assertEqual(result, "symbolic_missing_user_agent")

    def test_get_with_body(self):
        headers_with_body = self.valid_headers + [{"key": "Content-Length", "value": "150"}]
        event = self.create_mock_event(method="GET", headers=headers_with_body)
        result = self.supervisor.evaluate(event)
        self.assertEqual(result, "symbolic_get_with_body")

    def test_duplicate_critical_headers(self):
        duplicate_hosts = self.valid_headers + [{"key": "Host", "value": "evil.com"}]
        event = self.create_mock_event(headers=duplicate_hosts)
        result = self.supervisor.evaluate(event)
        self.assertEqual(result, "symbolic_duplicate_critical_headers")

    def test_http_desync_attempt(self):
        desync_headers = self.valid_headers + [
            {"key": "Content-Length", "value": "50"},
            {"key": "Transfer-Encoding", "value": "chunked"}
        ]
        event = self.create_mock_event(method="POST", headers=desync_headers)
        result = self.supervisor.evaluate(event)
        self.assertEqual(result, "symbolic_http_desync_attempt")
if __name__ == '__main__':
    unittest.main(verbosity=2)