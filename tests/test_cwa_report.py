from __future__ import annotations

import unittest
from unittest import mock

from datetime import datetime, timezone

from tools.cwa_report import (
    classify, main, markdown_report, merge_rows, rows_from_payload, window_chunks,
)

_PAYLOAD = {"data": {"viewer": {"accounts": [{"rumPageloadEventsAdaptiveGroups": [
    {"count": 12, "sum": {"visits": 7}, "dimensions": {"requestPath": "/JE-1000F/EU/en/md/manual_je1000f_eu_en.html"}},
    {"count": 5, "sum": {"visits": 4}, "dimensions": {"requestPath": "/manual_je1000f_eu_en.html"}},
    {"count": 3, "sum": {"visits": 2}, "dimensions": {"requestPath": "/"}},
]}]}}}


class CwaReportTests(unittest.TestCase):
    def test_paths_map_to_the_operations_taxonomy(self) -> None:
        self.assertEqual("门户首页", classify("/"))
        self.assertEqual("门户首页", classify("/index.html"))
        self.assertEqual("扫码/印刷入口（根别名）", classify("/manual_je1000f_eu_en.html"))
        self.assertEqual("站内手册页", classify("/JE-1000F/EU/en/md/manual_je1000f_eu_en.html"))
        self.assertEqual("站内功能页", classify("/search.html"))
        self.assertEqual("扫码/印刷入口（根别名）", classify("manual_x.html"))

    def test_rows_flatten_and_errors_or_empty_accounts_raise(self) -> None:
        rows = rows_from_payload(_PAYLOAD)
        self.assertEqual(3, len(rows))
        self.assertEqual({"path": "/manual_je1000f_eu_en.html", "category": "扫码/印刷入口（根别名）",
                          "pageviews": 5, "visits": 4}, rows[1])
        with self.assertRaises(RuntimeError):
            rows_from_payload({"errors": [{"message": "denied"}]})
        with self.assertRaises(RuntimeError):
            rows_from_payload({"data": {"viewer": {"accounts": []}}})

    def test_markdown_report_totals_and_top_table(self) -> None:
        report = markdown_report(rows_from_payload(_PAYLOAD), since="2026-09-09", until="2026-09-16", top=2)
        self.assertIn("| 扫码/印刷入口（根别名） | 5 | 4 |", report)
        self.assertIn("| 合计 | 20 | 13 |", report)
        self.assertIn("`/JE-1000F/EU/en/md/manual_je1000f_eu_en.html`", report)
        self.assertNotIn("`/`", report.split("## Top")[1])
        self.assertIn("（区间内没有任何浏览记录）",
                      markdown_report([], since="a", until="b", top=5))

    def test_main_reports_missing_environment_without_calling_the_api(self) -> None:
        calls = []
        with mock.patch.dict("os.environ", {"CLOUDFLARE_API_TOKEN": "", "CLOUDFLARE_ACCOUNT_ID": ""}):
            code = main(["--days", "1"], fetch=lambda **kw: calls.append(kw))
        self.assertEqual(2, code)
        self.assertEqual([], calls)


    def test_long_windows_split_into_faithful_chunks(self) -> None:
        since = datetime(2026, 8, 17, tzinfo=timezone.utc)
        until = datetime(2026, 9, 16, tzinfo=timezone.utc)
        chunks = window_chunks(since, until)
        self.assertEqual(5, len(chunks))
        self.assertEqual(since, chunks[0][0])
        self.assertEqual(until, chunks[-1][1])
        for lower, upper in chunks:
            self.assertLessEqual((upper - lower).days, 7)
        for (_, upper), (lower, _) in zip(chunks, chunks[1:]):
            self.assertEqual(upper, lower)
        short = window_chunks(since, since.replace(day=20))
        self.assertEqual([(since, since.replace(day=20))], short)

    def test_merge_rows_accumulates_equal_and_unequal_chunks(self) -> None:
        chunk = [{"path": "/a", "category": "站内手册页", "pageviews": 5, "visits": 2}]
        merged = merge_rows([chunk, [dict(chunk[0])], [{"path": "/b", "category": "门户首页", "pageviews": 7, "visits": 7}]])
        self.assertEqual(
            [{"path": "/a", "category": "站内手册页", "pageviews": 10, "visits": 4},
             {"path": "/b", "category": "门户首页", "pageviews": 7, "visits": 7}],
            merged,
        )
        self.assertEqual(5, chunk[0]["pageviews"])

    def test_main_chunks_long_windows_and_merges(self) -> None:
        calls = []

        def fake_fetch(*, token, variables):
            calls.append((variables["since"], variables["until"]))
            return _PAYLOAD

        env = {"CLOUDFLARE_API_TOKEN": "t", "CLOUDFLARE_ACCOUNT_ID": "acc"}
        with mock.patch.dict("os.environ", env):
            with mock.patch("builtins.print") as printed:
                code = main(["--days", "30", "--site-tag", "sitetag"], fetch=fake_fetch)
        self.assertEqual(0, code)
        self.assertEqual(5, len(calls))
        self.assertEqual(calls[0][1], calls[1][0])
        output = "\n".join(str(call.args[0]) for call in printed.call_args_list)
        self.assertIn("| 合计 | 100 | 65 |", output)

    def test_main_renders_markdown_from_fetched_payload(self) -> None:
        seen = {}

        def fake_fetch(*, token, variables):
            seen.update(variables)
            return _PAYLOAD

        env = {"CLOUDFLARE_API_TOKEN": "t", "CLOUDFLARE_ACCOUNT_ID": "acc"}
        with mock.patch.dict("os.environ", env):
            with mock.patch("builtins.print") as printed:
                code = main(["--days", "3", "--site-tag", "sitetag"], fetch=fake_fetch)
        self.assertEqual(0, code)
        self.assertEqual("sitetag", seen["site"])
        self.assertEqual("acc", seen["account"])
        output = "\n".join(str(call.args[0]) for call in printed.call_args_list)
        self.assertIn("按入口分类", output)


if __name__ == "__main__":
    unittest.main()
