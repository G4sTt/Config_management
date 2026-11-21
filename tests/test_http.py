"""Check failures and retry policy without network requests."""

import io
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from registry import Registry, download


class HttpTests(unittest.TestCase):
    def test_transient_http_error_is_retried(self):
        transient = HTTPError("https://test", 503, "busy", {}, None)
        with patch("registry.urlopen",
                   side_effect=[transient, io.BytesIO(b"hello")]) as opener:
            with patch("registry.time.sleep"):
                self.assertEqual(download("https://test"), "hello")
        self.assertEqual(opener.call_count, 2)

    def test_not_found_and_connection_failures(self):
        for failure in (
            HTTPError("https://test", 404, "missing", {}, None),
            URLError("connection failed"), TimeoutError("timeout"),
        ):
            with self.subTest(failure=failure):
                with patch("registry.urlopen", side_effect=failure):
                    with self.assertRaises(ValueError):
                        download("https://test")

    def test_malformed_registry_shapes(self):
        for response in (
            "", "[]", '{"vers":"1.0.0","deps":{}}',
            '{"vers":"1.0.0","deps":[{}]}',
        ):
            with self.subTest(response=response):
                with self.assertRaises(ValueError):
                    Registry("https://test", lambda _: response).root("root")


if __name__ == "__main__":
    unittest.main()
