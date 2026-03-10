from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from tools import diff_report


def git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(repo),
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return proc.stdout


class TestDiffReport(unittest.TestCase):
    def test_collect_diff_rows_should_parse_model_region_and_stats(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            tracked_root = repo / "docs" / "_build" / "JE-1000F"
            target_file = tracked_root / "US" / "rst" / "page" / "spec_en.rst"
            target_file.parent.mkdir(parents=True)

            git(repo, "init")
            git(repo, "config", "user.name", "Codex")
            git(repo, "config", "user.email", "codex@example.com")

            target_file.write_text("Old line\n", encoding="utf-8")
            git(repo, "add", ".")
            git(repo, "commit", "-m", "first")

            target_file.write_text("Old line\nNew line\n", encoding="utf-8")
            jp_file = tracked_root / "JP" / "rst" / "generated" / "JE-1000F" / "safety_ja.rst"
            jp_file.parent.mkdir(parents=True)
            jp_file.write_text("安全\n", encoding="utf-8")
            git(repo, "add", ".")
            git(repo, "commit", "-m", "second")

            rows = diff_report.collect_diff_rows(
                repo_root=repo,
                tracked_root=tracked_root,
                from_ref="HEAD~1",
                to_ref="HEAD",
            )

            self.assertEqual(2, len(rows))
            us_row = next(row for row in rows if row.region == "US")
            jp_row = next(row for row in rows if row.region == "JP")

            self.assertEqual("JE-1000F", us_row.model)
            self.assertEqual("rst", us_row.artifact)
            self.assertEqual("page", us_row.section)
            self.assertEqual("spec_en", us_row.page_key)
            self.assertEqual("M", us_row.change_type)
            self.assertEqual("1", us_row.insertions)

            self.assertEqual("generated", jp_row.section)
            self.assertEqual("A", jp_row.change_type)
            self.assertEqual("safety_ja", jp_row.page_key)

    def test_generate_diff_report_should_write_csv_and_html(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            tracked_root = repo / "docs" / "_build" / "JE-1000F"
            target_file = tracked_root / "US" / "rst" / "index.rst"
            target_file.parent.mkdir(parents=True)

            git(repo, "init")
            git(repo, "config", "user.name", "Codex")
            git(repo, "config", "user.email", "codex@example.com")

            target_file.write_text("v1\n", encoding="utf-8")
            git(repo, "add", ".")
            git(repo, "commit", "-m", "first")

            target_file.write_text("v1\nv2\n", encoding="utf-8")
            git(repo, "add", ".")
            git(repo, "commit", "-m", "second")

            output_dir = repo / "reports"
            csv_path, html_path = diff_report.generate_diff_report(
                repo_root=repo,
                tracked_root=tracked_root,
                from_ref="HEAD~1",
                to_ref="HEAD",
                output_dir=output_dir,
            )

            self.assertTrue(csv_path.exists())
            self.assertTrue(html_path.exists())
            self.assertIn("JE-1000F", csv_path.read_text(encoding="utf-8-sig"))
            self.assertIn("RST Diff Report", html_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
