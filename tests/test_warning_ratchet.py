from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools import warning_ratchet


class TestSanitize(unittest.TestCase):
    def test_paths_line_numbers_and_ansi_are_stripped(self) -> None:
        raw = (
            "\x1b[91m/private/tmp/x/wt/docs/_build/JE-1000F/US/rst/page/06_ups_mode.rst:42: "
            "WARNING: undefined label: 'foo'\x1b[0m"
        )
        self.assertEqual(
            warning_ratchet.sanitize_line(raw),
            "docs/_build/JE-1000F/US/rst/page/06_ups_mode.rst: WARNING: undefined label: 'foo'",
        )

    def test_non_anchor_paths_fall_back_to_basename(self) -> None:
        raw = "/opt/hostedtoolcache/python/lib/site-packages/sphinx/foo.py:10: DeprecationWarning: x"
        self.assertEqual(
            warning_ratchet.sanitize_line(raw),
            "foo.py: DeprecationWarning: x",
        )

    def test_windows_separators_normalize(self) -> None:
        raw = r"C:\repo\docs\page\a.rst:3: WARNING: y"
        self.assertEqual(
            warning_ratchet.sanitize_line(raw), "docs/page/a.rst: WARNING: y"
        )

    def test_blank_lines_drop_out_of_logs(self) -> None:
        self.assertEqual(
            warning_ratchet.sanitize_log("a: WARNING: x\n\n  \nb: WARNING: y\n"),
            ["a: WARNING: x", "b: WARNING: y"],
        )


class TestCompare(unittest.TestCase):
    def test_new_known_and_stale_are_partitioned(self) -> None:
        result = warning_ratchet.compare(["w1", "w2"], ["w2", "w3"])
        self.assertEqual(result["new"], ["w1"])
        self.assertEqual(result["known"], ["w2"])
        self.assertEqual(result["stale"], ["w3"])


class TestCheckStream(unittest.TestCase):
    def test_missing_baseline_is_its_own_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            rc = warning_ratchet.check_stream(
                stream="sphinx-html", log_text="", baseline_dir=Path(tmp),
                printer=lambda *_: None,
            )
        self.assertEqual(rc, 2)

    def test_new_warning_fails_and_known_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            baseline_dir = Path(tmp)
            warning_ratchet.write_baseline(
                baseline_dir, "sphinx-html", ["docs/a.rst: WARNING: known issue"]
            )
            rc_known = warning_ratchet.check_stream(
                stream="sphinx-html",
                log_text="/x/docs/a.rst:9: WARNING: known issue\n",
                baseline_dir=baseline_dir, printer=lambda *_: None,
            )
            rc_new = warning_ratchet.check_stream(
                stream="sphinx-html",
                log_text="/x/docs/a.rst:9: WARNING: brand new problem\n",
                baseline_dir=baseline_dir, printer=lambda *_: None,
            )
        self.assertEqual(rc_known, 0)
        self.assertEqual(rc_new, 1)

    def test_round_trip_update_then_check_is_clean(self) -> None:
        log = "/x/wt/docs/_build/page/a.rst:5: WARNING: toctree glitch\n"
        with tempfile.TemporaryDirectory() as tmp:
            baseline_dir = Path(tmp)
            warning_ratchet.write_baseline(
                baseline_dir, "sphinx-html", warning_ratchet.sanitize_log(log)
            )
            rc = warning_ratchet.check_stream(
                stream="sphinx-html", log_text=log,
                baseline_dir=baseline_dir, printer=lambda *_: None,
            )
        self.assertEqual(rc, 0)

    def test_stale_baseline_entries_do_not_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            baseline_dir = Path(tmp)
            warning_ratchet.write_baseline(baseline_dir, "s", ["gone: WARNING: fixed"])
            rc = warning_ratchet.check_stream(
                stream="s", log_text="", baseline_dir=baseline_dir,
                printer=lambda *_: None,
            )
        self.assertEqual(rc, 0)


class TestCli(unittest.TestCase):
    def test_update_then_check_via_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "warnings.log"
            log.write_text("docs/a.rst:1: WARNING: x\n", encoding="utf-8")
            baseline_dir = Path(tmp) / "baselines"
            rc = warning_ratchet.main([
                "update", "--stream", "sphinx-html",
                "--log", str(log), "--baseline-dir", str(baseline_dir),
            ])
            self.assertEqual(rc, 0)
            rc = warning_ratchet.main([
                "check", "--stream", "sphinx-html",
                "--log", str(log), "--baseline-dir", str(baseline_dir),
            ])
            self.assertEqual(rc, 0)
            log.write_text("docs/a.rst:1: WARNING: x\ndocs/b.rst:2: WARNING: new\n", encoding="utf-8")
            rc = warning_ratchet.main([
                "check", "--stream", "sphinx-html",
                "--log", str(log), "--baseline-dir", str(baseline_dir),
            ])
            self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()
