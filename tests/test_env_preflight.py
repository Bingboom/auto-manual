from __future__ import annotations

import os
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from tools import env_preflight


class EnvPreflightTest(unittest.TestCase):
    def _repo(self, *, lock: str, python_pin: str | None = "3.12") -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        if python_pin is not None:
            (root / "pyproject.toml").write_text(
                f'[tool.mypy]\npython_version = "{python_pin}"\n', encoding="utf-8"
            )
        (root / "requirements.lock").write_text(lock, encoding="utf-8")
        return root

    def _findings(self, root: Path, installed: dict[str, str], python: tuple[int, int] = (3, 12)):
        return env_preflight.collect_environment_findings(
            root, python_version=python, installed_version=installed.get
        )

    def test_matching_environment_reports_ok_only(self) -> None:
        root = self._repo(lock="# header\nSphinx==8.2.3\npymupdf==1.28.0\n")
        findings = self._findings(root, {"Sphinx": "8.2.3", "pymupdf": "1.28.0"})
        self.assertEqual({"OK"}, {level for level, _, _ in findings})
        self.assertIn(("OK", "env.lock", "all 2 pinned packages match requirements.lock"), findings)

    def test_python_mismatch_is_a_warning(self) -> None:
        root = self._repo(lock="Sphinx==8.2.3\n")
        findings = self._findings(root, {"Sphinx": "8.2.3"}, python=(3, 11))
        python_rows = [row for row in findings if row[1] == "env.python"]
        self.assertEqual("WARN", python_rows[0][0])
        self.assertIn("3.11 differs from the pinned 3.12", python_rows[0][2])

    def test_missing_and_drifted_packages_are_listed_with_remedy(self) -> None:
        root = self._repo(lock="Sphinx==8.2.3\npymupdf==1.28.0\noss2==2.19.1\n")
        findings = self._findings(root, {"Sphinx": "8.2.3", "pymupdf": "1.28.2"})
        messages = [message for level, area, message in findings if area == "env.lock"]
        self.assertTrue(all(level == "WARN" for level, area, _ in findings if area == "env.lock"))
        self.assertIn("1 pinned package(s) not installed: oss2", messages)
        self.assertIn("1 package(s) differ from requirements.lock: pymupdf 1.28.2 (lock 1.28.0)", messages)
        self.assertTrue(any("pip install -r requirements.lock" in message for message in messages))

    def test_long_lists_are_truncated(self) -> None:
        names = [f"pkg{index:02d}" for index in range(env_preflight.MAX_LISTED + 4)]
        root = self._repo(lock="".join(f"{name}==1.0\n" for name in names))
        findings = self._findings(root, {})
        missing = next(message for _, _, message in findings if "not installed" in message)
        self.assertIn("+4 more", missing)

    def test_lists_sort_case_insensitively(self) -> None:
        root = self._repo(lock="PyYAML==6.0.3\ncertifi==1\npymupdf==1.28.0\n")
        findings = self._findings(root, {"PyYAML": "6.0.1", "certifi": "2", "pymupdf": "1.28.2"})
        drifted = next(message for _, _, message in findings if "differ from" in message)
        self.assertIn("certifi 2 (lock 1), pymupdf 1.28.2 (lock 1.28.0), PyYAML 6.0.1", drifted)


    def test_missing_pins_warn_instead_of_crashing(self) -> None:
        root = self._repo(lock="", python_pin=None)
        findings = self._findings(root, {})
        self.assertEqual({"WARN"}, {level for level, _, _ in findings})

    def test_lock_names_are_normalized(self) -> None:
        root = self._repo(lock="Foo_Bar==1.0\n")
        self.assertEqual({"foo-bar": ("Foo_Bar", "1.0")}, env_preflight.load_lock_pins(root))


class TestRunBannerTest(unittest.TestCase):
    """``tests/__init__.py`` names environment drift once per test run."""

    def test_prints_only_warn_rows(self) -> None:
        import io
        import tests

        stream = io.StringIO()
        rows = [("OK", "env.python", "fine"), ("WARN", "env.lock", "pymupdf differs")]
        with mock.patch.dict(os.environ, {tests.ENV_PREFLIGHT_SWITCH: ""}):
            printed = tests._report_environment_drift(collect=lambda: rows, stream=stream)
        self.assertEqual(1, printed)
        self.assertEqual("[env-preflight] WARN env.lock: pymupdf differs\n", stream.getvalue())

    def test_switch_off_and_collector_errors_stay_silent(self) -> None:
        import io
        import tests

        def broken() -> list[tuple[str, str, str]]:
            raise RuntimeError("no metadata")

        stream = io.StringIO()
        with mock.patch.dict(os.environ, {tests.ENV_PREFLIGHT_SWITCH: "0"}):
            self.assertEqual(0, tests._report_environment_drift(collect=lambda: [("WARN", "a", "b")], stream=stream))
        with mock.patch.dict(os.environ, {tests.ENV_PREFLIGHT_SWITCH: ""}):
            self.assertEqual(0, tests._report_environment_drift(collect=broken, stream=stream))
        self.assertEqual("", stream.getvalue())


if __name__ == "__main__":
    unittest.main()
