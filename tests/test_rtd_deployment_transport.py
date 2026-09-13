from __future__ import annotations

from http.client import IncompleteRead, RemoteDisconnected
from io import BytesIO
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit
from urllib.request import Request

from tools import rtd_deployment_receipt as receipt


class Response(BytesIO):
    def __init__(self, data, url, *, length=None, chunk=None, status=200):
        super().__init__(data)
        self.url = url
        self.status = status
        self.headers = {} if length is None else {"Content-Length": str(length)}
        self.chunk = chunk

    def geturl(self):
        return self.url

    def read(self, size=-1):
        return super().read(min(size, self.chunk) if self.chunk else size)


class DeploymentTransportTests(unittest.TestCase):
    url = "https://example.org/en/latest/assets/original.png"

    def fetch_with(self, open_response):
        opener = SimpleNamespace(open=open_response)
        return patch.object(receipt, "build_opener", return_value=opener)

    def test_each_read_uses_unique_internal_probe_and_original_encoding(self):
        requests = []
        def open_response(request, timeout):
            requests.append(request)
            return Response(b"original", request.full_url, length=8)
        with self.fetch_with(open_response):
            self.assertEqual(receipt._fetch(self.url), b"original")
            self.assertEqual(receipt._fetch(self.url), b"original")
        self.assertNotEqual(requests[0].full_url, requests[1].full_url)
        for request in requests:
            parsed = urlsplit(request.full_url)
            self.assertEqual(parsed.path, urlsplit(self.url).path)
            self.assertEqual(set(parse_qs(parsed.query)), {"receipt_probe"})
            self.assertEqual(request.get_header("Accept-encoding"), "identity")
            self.assertIn("no-transform", request.get_header("Cache-control"))

    def test_reads_all_chunks_and_checks_declared_length(self):
        with self.fetch_with(lambda request, timeout: Response(
                b"original", request.full_url, length=8, chunk=2)):
            self.assertEqual(receipt._fetch(self.url), b"original")

    def test_transient_disconnect_and_truncation_restart_with_new_probe(self):
        requests = []
        def open_response(request, timeout):
            requests.append(request.full_url)
            if len(requests) == 1:
                raise RemoteDisconnected("remote closed before response")
            return Response(b"ori" if len(requests) == 2 else b"original",
                            request.full_url, length=8)
        with self.fetch_with(open_response):
            self.assertEqual(receipt._fetch(self.url), b"original")
        self.assertEqual(len(requests), 3)
        self.assertEqual(len(set(requests)), 3)

    def test_repeated_truncation_fails_after_three_attempts(self):
        calls = []
        def open_response(request, timeout):
            calls.append(request)
            return Response(b"ori", request.full_url, length=8)
        with self.fetch_with(open_response), self.assertRaises(IncompleteRead):
            receipt._fetch(self.url)
        self.assertEqual(len(calls), 3)

    def test_timeout_and_transient_http_retry_but_other_url_errors_fail(self):
        for error in (URLError(TimeoutError("timed out")),
                      HTTPError(self.url, 503, "temporary", {}, None)):
            requests = []
            def open_response(request, timeout):
                requests.append(request)
                if len(requests) == 1:
                    raise error
                return Response(b"original", request.full_url, length=8)
            with self.subTest(error=error), self.fetch_with(open_response):
                self.assertEqual(receipt._fetch(self.url), b"original")
            self.assertEqual(len(requests), 2)
        with patch.object(receipt, "build_opener") as build:
            build.return_value.open.side_effect = URLError("certificate failure")
            with self.assertRaises(URLError):
                receipt._fetch(self.url)
            self.assertEqual(build.return_value.open.call_count, 1)

    def test_elapsed_budget_stops_a_slow_stream_without_extra_attempt(self):
        calls = []
        def open_response(request, timeout):
            calls.append(request)
            return Response(b"original", request.full_url, length=8, chunk=2)
        with self.fetch_with(open_response), patch.object(
                receipt, "monotonic", side_effect=[0, 0, 0, 0, 46, 47]):
            with self.assertRaisesRegex(TimeoutError, "time budget"):
                receipt._fetch(self.url)
        self.assertEqual(len(calls), 1)

    def test_permanent_http_and_invalid_length_do_not_retry(self):
        for error in (HTTPError(self.url, 404, "missing", {}, None),):
            with self.subTest(error=error), patch.object(receipt, "build_opener") as build:
                build.return_value.open.side_effect = error
                with self.assertRaises(HTTPError):
                    receipt._fetch(self.url)
                self.assertEqual(build.return_value.open.call_count, 1)
        for length in ("invalid", -1, receipt.MAX_FILE_BYTES + 1):
            calls = []
            def open_response(request, timeout):
                calls.append(request)
                return Response(b"original", request.full_url, length=length)
            with self.subTest(length=length), self.fetch_with(open_response):
                with self.assertRaises(ValueError):
                    receipt._fetch(self.url)
            self.assertEqual(len(calls), 1)

    def test_no_length_is_read_to_eof_with_size_bound(self):
        with self.fetch_with(lambda request, timeout: Response(
                b"original", request.full_url, chunk=2)):
            self.assertEqual(receipt._fetch(self.url), b"original")
        with patch.object(receipt, "MAX_FILE_BYTES", 3):
            with self.fetch_with(lambda request, timeout: Response(b"1234", request.full_url)):
                with self.assertRaisesRegex(ValueError, "size limit"):
                    receipt._fetch(self.url)

    def test_public_query_and_cross_origin_final_response_still_fail(self):
        with patch.object(receipt, "build_opener") as build:
            for suffix in ("?receipt_probe=caller", "?anything=1", "#fragment"):
                with self.assertRaises(ValueError):
                    receipt._fetch(self.url + suffix)
            build.assert_not_called()
        with self.fetch_with(lambda request, timeout: Response(b"data", "https://other.org/data")):
            with self.assertRaisesRegex(ValueError, "same-origin"):
                receipt._fetch(self.url)

    def test_redirect_retains_internal_probe_only_on_same_origin(self):
        request = Request(self.url + "?receipt_probe=" + "a" * 32)
        handler = receipt._Redirect()
        redirected = handler.redirect_request(request, None, 302, "", {}, self.url)
        self.assertEqual(urlsplit(redirected.full_url).path, urlsplit(self.url).path)
        self.assertEqual(set(parse_qs(urlsplit(redirected.full_url).query)), {"receipt_probe"})
        for target in ("https://other.org/file", self.url + "?unexpected=1", self.url + "#fragment"):
            with self.subTest(target=target), self.assertRaises(ValueError):
                handler.redirect_request(request, None, 302, "", {}, target)


if __name__ == "__main__":
    unittest.main()
