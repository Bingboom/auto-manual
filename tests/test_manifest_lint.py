from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from tools.manifest_lint import lint_repository, main


class ManifestLintTests(unittest.TestCase):
    def _write_fixture_repo(self, root: Path) -> None:
        (root / "configs").mkdir()
        (root / "docs" / "manifests").mkdir(parents=True)
        (root / "docs" / "templates" / "en").mkdir(parents=True)
        (root / "docs" / "templates" / "en" / "intro.rst").write_text(
            "Intro\n=====\n", encoding="utf-8"
        )
        (root / "configs" / "config.demo.yaml").write_text(
            "\n".join(
                [
                    "build:",
                    "  family_id: demo",
                    "  languages: [fr]",
                    "  default_model: Demo",
                    "  default_region: XX",
                    "paths:",
                    "  docs_dir: docs",
                    "  page_manifest: docs/manifests/used.yaml",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        (root / "docs" / "manifests" / "used.yaml").write_text(
            "\n".join(
                [
                    "manifest_id: used",
                    "pages:",
                    "  - type: rst_include",
                    "    lang: en",
                    "    file: templates/en/intro.rst",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        (root / "docs" / "manifests" / "orphan.yaml").write_text(
            "manifest_id: orphan\npages:\n  - type: rst_include\n    lang: en\n    file: templates/en/intro.rst\n",
            encoding="utf-8",
        )

    def test_report_surfaces_language_and_orphan_drift(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._write_fixture_repo(root)

            report = lint_repository(root)
            codes = {finding.code for finding in report.findings}
            self.assertEqual({"LANGUAGE_SET_DRIFT", "ORPHAN_MANIFEST"}, codes)
            self.assertEqual(2, report.as_dict()["summary"]["WARN"])

    def test_cli_is_report_only_and_can_emit_json(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._write_fixture_repo(root)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = main(["--root", str(root), "--json"])

            self.assertEqual(0, exit_code)
            self.assertIn('"LANGUAGE_SET_DRIFT"', output.getvalue())
            self.assertIn('"ORPHAN_MANIFEST"', output.getvalue())


if __name__ == "__main__":
    unittest.main()
