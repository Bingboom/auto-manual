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
            changes_dir = Path(td) / "dist" / "changes" / "US"
            downloads_dir = Path(td) / "dist" / "downloads" / "US"
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

            report_files = build_review_preview.copy_report_set(
                report_root,
                prefix,
                changes_dir,
                relative_dir="changes/US",
            )
            csv_files = build_review_preview.copy_report_csvs(
                report_root,
                prefix,
                downloads_dir,
                relative_dir="downloads/US",
            )

            self.assertEqual(
                {
                    "report-index.html": "changes/US/report-index.html",
                    "report-summary.html": "changes/US/report-summary.html",
                    "report-fields.html": "changes/US/report-fields.html",
                    "report-pages.html": "changes/US/report-pages.html",
                    "report-files.html": "changes/US/report-files.html",
                },
                report_files,
            )
            self.assertEqual(
                {
                    "changes-summary.csv": "downloads/US/changes-summary.csv",
                    "changes-pages.csv": "downloads/US/changes-pages.csv",
                    "changes-fields.csv": "downloads/US/changes-fields.csv",
                    "changes-files.csv": "downloads/US/changes-files.csv",
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
                csv_files[file_name] = f"downloads/US/{file_name}"

            workbook_path = build_review_preview.build_change_workbook(
                downloads_dir,
                csv_files,
                relative_path="downloads/US/change-report.xlsx",
            )

            self.assertEqual("downloads/US/change-report.xlsx", workbook_path)
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

    def test_render_pages_should_use_workspace_shell_and_family_relative_download_links(self) -> None:
        meta = {
            "title": "JE-1000F Review Preview",
            "model": "JE-1000F",
            "source": "review",
            "branch": "codex/test",
            "commit_sha_short": "abc1234",
            "generated_at": "2026-03-24T12:00:00Z",
            "commit_message": "demo",
        }
        family_entry = {
            "family": "US",
            "default_model": "JE-1000F",
            "default_lang": "en",
            "default_manual_url": "manual/US/en/index.html",
            "shared_language_labels": ["English", "Spanish", "French"],
        }
        family_changes = {
            "areas": [],
            "review_pages": ["page/index.rst"],
            "downloads": {
                "word_docx": "downloads/US/en/review-manual.docx",
                "change_workbook": "downloads/US/change-report.xlsx",
                "csv_reports": {
                    "changes-summary.csv": "downloads/US/changes-summary.csv",
                    "changes-pages.csv": "downloads/US/changes-pages.csv",
                    "changes-fields.csv": "downloads/US/changes-fields.csv",
                    "changes-files.csv": "downloads/US/changes-files.csv",
                },
            },
            "report_files": {
                "report-index.html": "changes/US/report-index.html",
                "report-summary.html": "changes/US/report-summary.html",
                "report-fields.html": "changes/US/report-fields.html",
                "report-pages.html": "changes/US/report-pages.html",
                "report-files.html": "changes/US/report-files.html",
            },
        }

        workspace_html = build_review_preview.render_workspace_html(meta["title"])
        change_html = build_review_preview.render_changes_html(meta, family_entry, family_changes)

        self.assertIn("Review Preview", workspace_html)
        self.assertIn("data-family-tab", workspace_html)
        self.assertIn("data-lang-tab", workspace_html)
        self.assertIn("Product Name:", workspace_html)
        self.assertNotIn("Current Family", workspace_html)
        self.assertNotIn("renderModelCards", workspace_html)
        self.assertIn('href="../../manual/US/en/index.html"', change_html)
        self.assertIn('href="../../downloads/US/change-report.xlsx"', change_html)
        self.assertIn('href="../../changes/US/report-pages.html"', change_html)
        self.assertIn('href="../../index.html?family=US&model=JE-1000F&lang=en"', change_html)

    def test_assert_preview_output_contract_should_require_word_when_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            output_dir = Path(td)
            for relative_path in (
                "index.html",
                "manual/index.html",
                "manual/US/en/index.html",
                "changes/index.html",
                "changes/US/index.html",
                "changes/US/report-index.html",
                "changes/US/report-summary.html",
                "changes/US/report-fields.html",
                "changes/US/report-pages.html",
                "changes/US/report-files.html",
                "generated/meta.json",
                "generated/changes.json",
                "generated/workspace.json",
                "downloads/US/change-report.xlsx",
                "downloads/US/changes-summary.csv",
                "downloads/US/changes-pages.csv",
                "downloads/US/changes-fields.csv",
                "downloads/US/changes-files.csv",
            ):
                target = output_dir / relative_path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("demo", encoding="utf-8")

            workspace = {
                "defaults": {
                    "manual_url": "manual/US/en/index.html",
                    "change_url": "changes/US/index.html",
                },
                "families": [
                    {
                        "family": "US",
                        "change_workbook_url": "downloads/US/change-report.xlsx",
                        "csv_urls": {
                            "changes-summary.csv": "downloads/US/changes-summary.csv",
                            "changes-pages.csv": "downloads/US/changes-pages.csv",
                            "changes-fields.csv": "downloads/US/changes-fields.csv",
                            "changes-files.csv": "downloads/US/changes-files.csv",
                        },
                        "models": [
                            {
                                "model": "JE-1000F",
                                "languages": [
                                    {
                                        "lang": "en",
                                        "manual_url": "manual/US/en/index.html",
                                        "word_url": "downloads/US/en/review-manual.docx",
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }

            with self.assertRaisesRegex(RuntimeError, "review-manual.docx"):
                build_review_preview.assert_preview_output_contract(output_dir, workspace, require_word=True)

            word_path = output_dir / "downloads" / "US" / "en" / "review-manual.docx"
            word_path.parent.mkdir(parents=True, exist_ok=True)
            word_path.write_text("demo", encoding="utf-8")
            build_review_preview.assert_preview_output_contract(output_dir, workspace, require_word=True)


if __name__ == "__main__":
    unittest.main()
