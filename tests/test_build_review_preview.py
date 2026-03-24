from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path

from tools.process_docs import build_review_preview


class TestBuildReviewPreview(unittest.TestCase):
    def test_copy_report_assets_should_return_stable_relative_paths(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            report_root = Path(td) / "reports"
            changes_dir = Path(td) / "dist" / "changes"
            downloads_dir = Path(td) / "dist" / "downloads"
            prefix = "US_HEAD_1_to_HEAD"
            for file_name in (
                f"{prefix}_index.html",
                f"{prefix}.html",
                f"{prefix}_fields.html",
                f"{prefix}_pages.html",
                f"{prefix}_files.html",
                f"{prefix}.csv",
                f"{prefix}_pages.csv",
                f"{prefix}_fields.csv",
                f"{prefix}_files.csv",
            ):
                target = report_root / file_name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("demo", encoding="utf-8")

            report_files = build_review_preview.copy_report_set(report_root, prefix, changes_dir)
            csv_files = build_review_preview.copy_report_csvs(report_root, prefix, downloads_dir)

            self.assertEqual(
                {
                    "report-index.html": "report-index.html",
                    "report-summary.html": "report-summary.html",
                    "report-fields.html": "report-fields.html",
                    "report-pages.html": "report-pages.html",
                    "report-files.html": "report-files.html",
                },
                report_files,
            )
            self.assertEqual(
                {
                    "changes-summary.csv": "downloads/changes-summary.csv",
                    "changes-pages.csv": "downloads/changes-pages.csv",
                    "changes-fields.csv": "downloads/changes-fields.csv",
                    "changes-files.csv": "downloads/changes-files.csv",
                },
                csv_files,
            )

    def test_build_change_workbook_should_create_valid_xlsx_with_expected_sheets(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            downloads_dir = Path(td) / "downloads"
            downloads_dir.mkdir(parents=True)
            csv_rows = {
                "changes-summary.csv": "name,value\nsummary,1\n",
                "changes-pages.csv": "page,status\nindex,modified\n",
                "changes-fields.csv": "field,old,new\nproduct_name,old,new\n",
                "changes-files.csv": "path,status\npage/index.rst,modified\n",
            }
            csv_files: dict[str, str] = {}
            for file_name, content in csv_rows.items():
                (downloads_dir / file_name).write_text(content, encoding="utf-8")
                csv_files[file_name] = f"downloads/{file_name}"

            workbook_path = build_review_preview.build_change_workbook(downloads_dir, csv_files)

            self.assertEqual("downloads/change-report.xlsx", workbook_path)
            actual_path = downloads_dir / "change-report.xlsx"
            self.assertTrue(actual_path.exists())
            self.assertTrue(zipfile.is_zipfile(actual_path))
            with zipfile.ZipFile(actual_path) as bundle:
                workbook_xml = bundle.read("xl/workbook.xml").decode("utf-8")
            self.assertIn('sheet name="Summary"', workbook_xml)
            self.assertIn('sheet name="Pages"', workbook_xml)
            self.assertIn('sheet name="Fields"', workbook_xml)
            self.assertIn('sheet name="Files"', workbook_xml)

    def test_build_downloads_metadata_should_keep_fixed_keys(self) -> None:
        payload = build_review_preview.build_downloads_metadata(
            word_path="downloads/review-manual.docx",
            workbook_path="downloads/change-report.xlsx",
            csv_files={
                "changes-summary.csv": "downloads/changes-summary.csv",
                "changes-pages.csv": "downloads/changes-pages.csv",
                "changes-fields.csv": "downloads/changes-fields.csv",
                "changes-files.csv": "downloads/changes-files.csv",
            },
        )

        self.assertEqual("downloads/review-manual.docx", payload["word_docx"])
        self.assertEqual("downloads/change-report.xlsx", payload["change_workbook"])
        self.assertEqual(
            {
                "changes-summary.csv": "downloads/changes-summary.csv",
                "changes-pages.csv": "downloads/changes-pages.csv",
                "changes-fields.csv": "downloads/changes-fields.csv",
                "changes-files.csv": "downloads/changes-files.csv",
            },
            payload["csv_reports"],
        )

    def test_render_pages_should_use_correct_relative_download_links(self) -> None:
        meta = {
            "title": "JE-1000F / US Review Preview",
            "model": "JE-1000F",
            "region": "US",
            "source": "review",
            "branch": "codex/test",
            "commit_sha_short": "abc1234",
            "generated_at": "2026-03-24T12:00:00Z",
            "commit_message": "demo",
        }
        downloads = build_review_preview.build_downloads_metadata(
            word_path="downloads/review-manual.docx",
            workbook_path="downloads/change-report.xlsx",
            csv_files={
                "changes-summary.csv": "downloads/changes-summary.csv",
                "changes-pages.csv": "downloads/changes-pages.csv",
                "changes-fields.csv": "downloads/changes-fields.csv",
                "changes-files.csv": "downloads/changes-files.csv",
            },
        )
        changes = {
            "areas": [],
            "review_pages": ["page/index.rst"],
            "changed_files": ["README.md"],
            "downloads": downloads,
            "report_files": {
                "report-index.html": "report-index.html",
                "report-summary.html": "report-summary.html",
                "report-fields.html": "report-fields.html",
                "report-pages.html": "report-pages.html",
                "report-files.html": "report-files.html",
            },
        }

        index_html = build_review_preview.render_index_html(meta, changes)
        change_html = build_review_preview.render_changes_html(meta, changes)

        self.assertIn('href="./downloads/review-manual.docx"', index_html)
        self.assertIn('href="./downloads/change-report.xlsx"', index_html)
        self.assertIn("Doc Information", index_html)
        self.assertNotIn("What Changed", index_html)
        self.assertNotIn("Source:</strong>", index_html)
        self.assertNotIn("Branch:</strong>", index_html)
        self.assertNotIn("Commit:</strong>", index_html)
        self.assertNotIn("Generated:</strong>", index_html)
        self.assertNotIn("Review pages:</strong>", index_html)
        self.assertNotIn("Touched pages:</strong>", index_html)
        self.assertNotIn("Changed files:</strong>", index_html)
        self.assertNotIn("Review Pages Touched", index_html)
        self.assertNotIn("Changed Files</h2>", index_html)
        self.assertIn('href="./changes/index.html"', index_html)
        self.assertIn('href="../downloads/review-manual.docx"', change_html)
        self.assertIn('href="../downloads/change-report.xlsx"', change_html)
        self.assertIn('href="./report-pages.html"', change_html)

    def test_assert_preview_output_contract_should_require_word_when_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            output_dir = Path(td)
            for relative_path in (
                "index.html",
                "manual/index.html",
                "changes/index.html",
                "changes/report-index.html",
                "changes/report-summary.html",
                "changes/report-fields.html",
                "changes/report-pages.html",
                "changes/report-files.html",
                "generated/meta.json",
                "generated/changes.json",
                "downloads/change-report.xlsx",
                "downloads/changes-summary.csv",
                "downloads/changes-pages.csv",
                "downloads/changes-fields.csv",
                "downloads/changes-files.csv",
            ):
                target = output_dir / relative_path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("demo", encoding="utf-8")

            downloads = build_review_preview.build_downloads_metadata(
                word_path="downloads/review-manual.docx",
                workbook_path="downloads/change-report.xlsx",
                csv_files={
                    "changes-summary.csv": "downloads/changes-summary.csv",
                    "changes-pages.csv": "downloads/changes-pages.csv",
                    "changes-fields.csv": "downloads/changes-fields.csv",
                    "changes-files.csv": "downloads/changes-files.csv",
                },
            )

            with self.assertRaisesRegex(RuntimeError, "review-manual.docx"):
                build_review_preview.assert_preview_output_contract(output_dir, downloads, require_word=True)

            (output_dir / "downloads" / "review-manual.docx").write_text("demo", encoding="utf-8")
            build_review_preview.assert_preview_output_contract(output_dir, downloads, require_word=True)


if __name__ == "__main__":
    unittest.main()
