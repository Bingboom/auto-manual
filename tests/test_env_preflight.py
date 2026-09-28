from __future__ import annotations

import tempfile
import unittest
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
        names = [f"pkg{index}" for index in range(12)]
        root = self._repo(lock="".join(f"{name}==1.0\n" for name in names))
        findings = self._findings(root, {})
        missing = next(message for _, _, message in findings if "not installed" in message)
        self.assertIn("+4 more", missing)

    def test_missing_pins_warn_instead_of_crashing(self) -> None:
        root = self._repo(lock="", python_pin=None)
        findings = self._findings(root, {})
        self.assertEqual({"WARN"}, {level for level, _, _ in findings})

    def test_lock_names_are_normalized(self) -> None:
        root = self._repo(lock="Foo_Bar==1.0\n")
        self.assertEqual({"foo-bar": ("Foo_Bar", "1.0")}, env_preflight.load_lock_pins(root))


if __name__ == "__main__":
    unittest.main()
