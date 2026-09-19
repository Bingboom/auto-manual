"""Rate-limit handling: pace, back off, and keep "undecided" out of "wrong".

Regression cover for the catalog-wide 429 storm (Hello-Docs run 35432328072):
verifying 52 targets fired ~570 requests with no pacing, and every 429 was
retried immediately three times inside _fetch.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from tools import rtd_deployment_receipt as receipt


URL = "https://example.org/en/latest/page.html"


def _http_error(code: int, retry_after: str | None = None) -> HTTPError:
    headers = {} if retry_after is None else {"Retry-After": retry_after}
    return HTTPError(URL, code, "rate limited", headers, None)


class RetryAfterParsingTests(unittest.TestCase):
    def test_parses_delta_seconds_and_caps_absurd_values(self) -> None:
        self.assertEqual(30.0, receipt.retry_after_seconds({"Retry-After": "30"}))
        self.assertEqual(
            receipt.MAX_RETRY_AFTER_SECONDS,
            receipt.retry_after_seconds({"Retry-After": "99999"}),
        )

    def test_parses_http_date_relative_to_now(self) -> None:
        when = datetime.now(timezone.utc) + timedelta(seconds=40)
        parsed = receipt.retry_after_seconds({"Retry-After": format_datetime(when)})
        self.assertIsNotNone(parsed)
        self.assertTrue(30 <= parsed <= 45, parsed)

    def test_past_dates_and_garbage_never_raise(self) -> None:
        past = datetime.now(timezone.utc) - timedelta(seconds=90)
        self.assertEqual(0.0, receipt.retry_after_seconds({"Retry-After": format_datetime(past)}))
        for value in (None, "", "   ", "soon", "-5"):
            with self.subTest(value=value):
                self.assertIsNone(receipt.retry_after_seconds({"Retry-After": value}))
        self.assertIsNone(receipt.retry_after_seconds({}))


class FetchRateLimitTests(unittest.TestCase):
    """_fetch must surrender a rate limit, not hammer through it."""

    def _fetch_raising(self, error):
        opener = SimpleNamespace(open=lambda request, timeout: (_ for _ in ()).throw(error))
        return patch.object(receipt, "build_opener", return_value=opener)

    def test_rate_limit_codes_raise_throttled_on_the_first_attempt(self) -> None:
        for code in sorted(receipt.RATE_LIMIT_STATUS):
            calls = []

            def open_response(request, timeout, code=code):
                calls.append(request)
                raise _http_error(code, "17")

            with self.subTest(code=code):
                opener = SimpleNamespace(open=open_response)
                with patch.object(receipt, "build_opener", return_value=opener):
                    with self.assertRaises(receipt.DeploymentThrottled) as caught:
                        receipt._fetch(URL)
                # The storm was three immediate retries per request; now one.
                self.assertEqual(1, len(calls))
                self.assertEqual(17.0, caught.exception.retry_after)
                self.assertIn(str(code), str(caught.exception))

    def test_missing_retry_after_leaves_the_hint_unset(self) -> None:
        with self._fetch_raising(_http_error(429)):
            with self.assertRaises(receipt.DeploymentThrottled) as caught:
                receipt._fetch(URL)
        self.assertIsNone(caught.exception.retry_after)


class FetchSessionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.slept: list[float] = []
        self.addCleanup(
            patch.object(receipt, "sleep", side_effect=self.slept.append).start().stop
        )

    def session(self, **kwargs) -> receipt.FetchSession:
        kwargs.setdefault("min_interval", 0)
        return receipt.FetchSession(**kwargs)

    def test_backoff_retries_a_429_and_then_succeeds(self) -> None:
        attempts = []

        def fetch(url):
            attempts.append(url)
            if len(attempts) < 3:
                raise receipt.DeploymentThrottled("rate limited", retry_after=None)
            return b"served"

        session = self.session()
        with patch.object(receipt, "_fetch", side_effect=fetch):
            self.assertEqual(b"served", session.fetch(URL))
        self.assertEqual(3, len(attempts))
        # Exponential, not a tight loop.
        self.assertEqual(
            [receipt.THROTTLE_BACKOFF_BASE, receipt.THROTTLE_BACKOFF_BASE * 2], self.slept
        )
        self.assertEqual(2, session.throttle_waits)
        self.assertFalse(session.budget_exhausted)

    def test_retry_after_extends_but_never_shortens_the_backoff(self) -> None:
        for hint, expected in ((90.0, 90.0), (0.5, receipt.THROTTLE_BACKOFF_BASE), (0.0, receipt.THROTTLE_BACKOFF_BASE)):
            self.slept.clear()
            attempts = []

            def fetch(url, hint=hint):
                attempts.append(url)
                if len(attempts) < 2:
                    raise receipt.DeploymentThrottled("rate limited", retry_after=hint)
                return b"served"

            with self.subTest(hint=hint):
                session = self.session()
                with patch.object(receipt, "_fetch", side_effect=fetch):
                    self.assertEqual(b"served", session.fetch(URL))
                self.assertEqual([expected], self.slept)

    def test_exhausted_budget_classifies_as_throttled_and_stops_requesting(self) -> None:
        attempts = []

        def fetch(url):
            attempts.append(url)
            raise receipt.DeploymentThrottled("rate limited", retry_after=None)

        # Enough for the first 2s wait, not the second 4s one.
        session = self.session(retry_budget=3.0)
        with patch.object(receipt, "_fetch", side_effect=fetch):
            with self.assertRaises(receipt.DeploymentThrottled) as caught:
                session.fetch(URL)
        self.assertEqual(2, len(attempts))
        self.assertEqual([receipt.THROTTLE_BACKOFF_BASE], self.slept)
        self.assertTrue(session.budget_exhausted)
        self.assertIn("undecided", str(caught.exception))

    def test_attempt_ceiling_bounds_a_generous_budget(self) -> None:
        attempts = []

        def fetch(url):
            attempts.append(url)
            raise receipt.DeploymentThrottled("rate limited", retry_after=None)

        session = self.session(retry_budget=10_000.0)
        with patch.object(receipt, "_fetch", side_effect=fetch):
            with self.assertRaises(receipt.DeploymentThrottled):
                session.fetch(URL)
        self.assertEqual(receipt.MAX_THROTTLE_ATTEMPTS, len(attempts))

    def test_non_throttle_errors_fail_immediately_without_backoff(self) -> None:
        attempts = []

        def fetch(url):
            attempts.append(url)
            raise ValueError("Live deployment bytes differ: page.html")

        session = self.session()
        with patch.object(receipt, "_fetch", side_effect=fetch):
            with self.assertRaisesRegex(ValueError, "bytes differ"):
                session.fetch(URL)
        self.assertEqual(1, len(attempts))
        self.assertEqual([], self.slept)

    def test_cache_serves_repeat_urls_without_a_second_request(self) -> None:
        attempts = []

        def fetch(url):
            attempts.append(url)
            return b"served"

        session = self.session()
        with patch.object(receipt, "_fetch", side_effect=fetch):
            for _ in range(5):
                self.assertEqual(b"served", session.fetch(URL))
        self.assertEqual(1, len(attempts))
        self.assertEqual(4, session.cache_hits)
        self.assertEqual(1, session.requests)

    def test_cache_can_be_disabled_and_oversized_bodies_are_not_retained(self) -> None:
        attempts = []
        with patch.object(receipt, "_fetch", side_effect=lambda url: attempts.append(url) or b"x"):
            session = self.session(cache=False)
            session.fetch(URL)
            session.fetch(URL)
        self.assertEqual(2, len(attempts))

        attempts.clear()
        big = b"x" * 32
        with patch.object(receipt, "_fetch", side_effect=lambda url: attempts.append(url) or big):
            with patch.object(receipt, "MAX_CACHED_BYTES", 8):
                session = self.session()
                session.fetch(URL)
                session.fetch(URL)
        self.assertEqual(2, len(attempts))

    def test_pacing_waits_between_requests(self) -> None:
        clock = iter([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        with patch.object(receipt, "_fetch", side_effect=lambda url: b"x"):
            with patch.object(receipt, "monotonic", side_effect=lambda: next(clock)):
                session = receipt.FetchSession(min_interval=0.5)
                session.fetch(URL)
                session.fetch(URL + "?other")
        # Second request had to wait out the interval left by the first.
        self.assertEqual([0.5], self.slept)

    def test_source_fingerprint_is_computed_once_per_tree(self) -> None:
        calls = []
        session = self.session()
        with patch.object(receipt, "source_fingerprint", side_effect=lambda root: calls.append(root) or "abc"):
            for _ in range(4):
                self.assertEqual("abc", session.source_fingerprint(__file__))
        self.assertEqual(1, len(calls))


if __name__ == "__main__":
    unittest.main()
