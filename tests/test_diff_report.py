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
    def test_detect_initial_baseline_should_return_true_when_tracked_subtree_first_appears(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            tracked_root = repo / "docs" / "_review" / "JE-1000F"
            target_file = tracked_root / "US" / "index.rst"
            target_file.parent.mkdir(parents=True)

            git(repo, "init")
            git(repo, "config", "user.name", "Codex")
            git(repo, "config", "user.email", "codex@example.com")

            (repo / "README.md").write_text("baseline\n", encoding="utf-8")
            git(repo, "add", ".")
            git(repo, "commit", "-m", "first")

            target_file.write_text("hello\n", encoding="utf-8")
            git(repo, "add", ".")
            git(repo, "commit", "-m", "second")

            file_rows = diff_report.collect_diff_rows(
                repo_root=repo,
                tracked_root=tracked_root,
                from_ref="HEAD~1",
                to_ref="HEAD",
            )

            self.assertTrue(
                diff_report.detect_initial_baseline(
                    repo_root=repo,
                    tracked_root=tracked_root,
                    from_ref="HEAD~1",
                    to_ref="HEAD",
                    file_rows=file_rows,
                )
            )

    def test_collect_field_diff_rows_should_back_map_template_fields_to_tpl_rows(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            tracked_root = repo / "docs" / "_review" / "JE-1000F"
            target_file = tracked_root / "US" / "page" / "05_operation_guide_placeholder.rst"
            target_file.parent.mkdir(parents=True)
            data_dir = repo / "data" / "phase1"
            data_dir.mkdir(parents=True)
            (repo / "config.yaml").write_text(
                "\n".join(
                    [
                        "paths:",
                        "  spec_master_csv: data/phase1/Spec_Master.csv",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (data_dir / "Spec_Master.csv").write_text(
                "\n".join(
                    [
                        "Region,Is_Latest,Page,Section,Section_order,Row_key,Row_label_en,Line_order,Value_en,Model",
                        "US,TRUE,specifications,TEMPLATE VARS,99,tpl_default_standby_duration,Default standby time,1,2 hours,JE-1000F",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            git(repo, "init")
            git(repo, "config", "user.name", "Codex")
            git(repo, "config", "user.email", "codex@example.com")

            target_file.write_text(
                "\n".join(
                    [
                        "OPERATIONS",
                        "==========",
                        "",
                        "**Default standby time:** 2 hours.",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            git(repo, "add", ".")
            git(repo, "commit", "-m", "first")

            target_file.write_text(
                "\n".join(
                    [
                        "OPERATIONS",
                        "==========",
                        "",
                        "**Default standby time:** 12 hours.",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            git(repo, "add", ".")
            git(repo, "commit", "-m", "second")

            file_rows = diff_report.collect_diff_rows(
                repo_root=repo,
                tracked_root=tracked_root,
                from_ref="HEAD~1",
                to_ref="HEAD",
            )
            field_rows = diff_report.collect_field_diff_rows(
                repo_root=repo,
                file_rows=file_rows,
                config_path=repo / "config.yaml",
            )

            self.assertEqual(1, len(field_rows))
            self.assertEqual("Default standby time", field_rows[0].field_key)
            self.assertEqual("tpl_default_standby_duration", field_rows[0].source_row_key)
            self.assertEqual("TEMPLATE VARS", field_rows[0].source_section_key)

    def test_collect_field_diff_rows_should_parse_structured_rst_fields(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            tracked_root = repo / "docs" / "_review" / "JE-1000F"
            target_file = tracked_root / "US" / "generated" / "JE-1000F" / "spec_en.rst"
            target_file.parent.mkdir(parents=True)
            data_dir = repo / "data" / "phase1"
            data_dir.mkdir(parents=True)
            (repo / "config.yaml").write_text(
                "\n".join(
                    [
                        "paths:",
                        "  spec_master_csv: data/phase1/Spec_Master.csv",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (data_dir / "Spec_Master.csv").write_text(
                "\n".join(
                    [
                        "Region,Is_Latest,Page,Section,Section_order,Row_key,Row_label_en,Line_order,Value_en,Model",
                        "US,TRUE,specifications,GENERAL INFO,1,product_name,Product Name,1,Jackery 1000,JE-1000F",
                        "US,TRUE,specifications,GENERAL INFO,1,model_no,Model No.,1,JE-1000F,JE-1000F",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            git(repo, "init")
            git(repo, "config", "user.name", "Codex")
            git(repo, "config", "user.email", "codex@example.com")

            target_file.write_text(
                "\n".join(
                    [
                        "SPECIFICATIONS",
                        "==============",
                        "",
                        "GENERAL INFO",
                        "------------",
                        "",
                        ".. list-table::",
                        "   :header-rows: 0",
                        "",
                        "   * - Product Name",
                        "     - Jackery 1000",
                        "   * - Model No.",
                        "     - JE-1000F",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            git(repo, "add", ".")
            git(repo, "commit", "-m", "first")

            target_file.write_text(
                "\n".join(
                    [
                        "SPECIFICATIONS",
                        "==============",
                        "",
                        "GENERAL INFO",
                        "------------",
                        "",
                        ".. list-table::",
                        "   :header-rows: 0",
                        "",
                        "   * - Product Name",
                        "     - Jackery 1000 New v2",
                        "   * - Model No.",
                        "     - JE-1000F",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            git(repo, "add", ".")
            git(repo, "commit", "-m", "second")

            file_rows = diff_report.collect_diff_rows(
                repo_root=repo,
                tracked_root=tracked_root,
                from_ref="HEAD~1",
                to_ref="HEAD",
            )
            field_rows = diff_report.collect_field_diff_rows(
                repo_root=repo,
                file_rows=file_rows,
                config_path=repo / "config.yaml",
            )

            self.assertEqual(1, len(field_rows))
            self.assertEqual("Product Name", field_rows[0].field_key)
            self.assertEqual("Jackery 1000", field_rows[0].old_value)
            self.assertEqual("Jackery 1000 New v2", field_rows[0].new_value)
            self.assertEqual("M", field_rows[0].change_type)
            self.assertEqual("product_name", field_rows[0].source_row_key)
            self.assertEqual("GENERAL INFO", field_rows[0].source_section_key)

    def test_collect_diff_rows_should_parse_review_bundle_paths(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            tracked_root = repo / "docs" / "_review" / "JE-1000F"
            target_file = tracked_root / "US" / "page" / "spec_en.rst"
            target_file.parent.mkdir(parents=True)

            git(repo, "init")
            git(repo, "config", "user.name", "Codex")
            git(repo, "config", "user.email", "codex@example.com")

            target_file.write_text("Old line\n", encoding="utf-8")
            git(repo, "add", ".")
            git(repo, "commit", "-m", "first")

            target_file.write_text("Old line\nNew line\n", encoding="utf-8")
            jp_file = tracked_root / "JP" / "generated" / "JE-1000F" / "safety_ja.rst"
            jp_file.parent.mkdir(parents=True)
            jp_file.write_text("瀹夊叏\n", encoding="utf-8")
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
            self.assertEqual("review", us_row.artifact)
            self.assertEqual("page", us_row.section)
            self.assertEqual("spec_en", us_row.page_key)
            self.assertEqual("M", us_row.change_type)
            self.assertEqual("1", us_row.insertions)

            self.assertEqual("generated", jp_row.section)
            self.assertEqual("A", jp_row.change_type)
            self.assertEqual("safety_ja", jp_row.page_key)

    def test_collect_diff_rows_should_still_support_runtime_build_paths(self) -> None:
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
            git(repo, "add", ".")
            git(repo, "commit", "-m", "second")

            rows = diff_report.collect_diff_rows(
                repo_root=repo,
                tracked_root=tracked_root,
                from_ref="HEAD~1",
                to_ref="HEAD",
            )

            self.assertEqual(1, len(rows))
            self.assertEqual("rst", rows[0].artifact)
            self.assertEqual("page", rows[0].section)

    def test_generate_diff_report_should_write_csv_and_html(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            tracked_root = repo / "docs" / "_review" / "JE-1000F"
            target_file = tracked_root / "US" / "page" / "03_product_overview_placeholder.rst"
            target_file.parent.mkdir(parents=True)

            git(repo, "init")
            git(repo, "config", "user.name", "Codex")
            git(repo, "config", "user.email", "codex@example.com")

            target_file.write_text(
                "\n".join(
                    [
                        "PRODUCT OVERVIEW",
                        "================",
                        "",
                        "**Default standby time:** 2 hours.",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            git(repo, "add", ".")
            git(repo, "commit", "-m", "first")

            target_file.write_text(
                "\n".join(
                    [
                        "PRODUCT OVERVIEW",
                        "================",
                        "",
                        "**Default standby time:** 12 hours.",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
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
            self.assertIn("RST Diff Report - Files", html_path.read_text(encoding="utf-8"))
            self.assertTrue((output_dir / "JE-1000F_HEAD_1_to_HEAD_pages.csv").exists())
            self.assertTrue((output_dir / "JE-1000F_HEAD_1_to_HEAD_pages.html").exists())
            self.assertTrue((output_dir / "JE-1000F_HEAD_1_to_HEAD_fields.csv").exists())
            self.assertTrue((output_dir / "JE-1000F_HEAD_1_to_HEAD_fields.html").exists())
            self.assertTrue((output_dir / "JE-1000F_HEAD_1_to_HEAD_index.html").exists())
            self.assertIn(
                "Default standby time",
                (output_dir / "JE-1000F_HEAD_1_to_HEAD_fields.csv").read_text(encoding="utf-8-sig"),
            )
            fields_html = (output_dir / "JE-1000F_HEAD_1_to_HEAD_fields.html").read_text(encoding="utf-8")
            self.assertIn('id="filter-search"', fields_html)
            self.assertIn('id="filter-source_row_key"', fields_html)
            self.assertIn('id="filter-model"', fields_html)
            self.assertIn("URLSearchParams(window.location.search)", fields_html)
            self.assertIn("rows visible", fields_html)
            index_html = (output_dir / "JE-1000F_HEAD_1_to_HEAD_index.html").read_text(encoding="utf-8")
            self.assertIn("RST Diff Report - Index", index_html)
            self.assertIn("JE-1000F_HEAD_1_to_HEAD_fields.html", index_html)
            self.assertIn("model=JE-1000F&amp;region=US", index_html)
            self.assertIn(
                "source_row_key",
                (output_dir / "JE-1000F_HEAD_1_to_HEAD_fields.csv").read_text(encoding="utf-8-sig"),
            )
            self.assertIn(
                "fields_changed",
                (output_dir / "JE-1000F_HEAD_1_to_HEAD_pages.csv").read_text(encoding="utf-8-sig"),
            )

    def test_generate_diff_report_should_ignore_initial_adds_when_flag_is_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            tracked_root = repo / "docs" / "_review" / "JE-1000F"
            target_file = tracked_root / "US" / "page" / "03_product_overview_placeholder.rst"
            target_file.parent.mkdir(parents=True)

            git(repo, "init")
            git(repo, "config", "user.name", "Codex")
            git(repo, "config", "user.email", "codex@example.com")

            (repo / "README.md").write_text("baseline\n", encoding="utf-8")
            git(repo, "add", ".")
            git(repo, "commit", "-m", "first")

            target_file.write_text(
                "\n".join(
                    [
                        "PRODUCT OVERVIEW",
                        "================",
                        "",
                        "**Default standby time:** 2 hours.",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            git(repo, "add", ".")
            git(repo, "commit", "-m", "second")

            output_dir = repo / "reports"
            diff_report.generate_diff_report(
                repo_root=repo,
                tracked_root=tracked_root,
                from_ref="HEAD~1",
                to_ref="HEAD",
                output_dir=output_dir,
                ignore_initial_adds=True,
            )

            files_csv = (output_dir / "JE-1000F_HEAD_1_to_HEAD_files.csv").read_text(encoding="utf-8-sig")
            files_html = (output_dir / "JE-1000F_HEAD_1_to_HEAD_files.html").read_text(encoding="utf-8")
            index_html = (output_dir / "JE-1000F_HEAD_1_to_HEAD_index.html").read_text(encoding="utf-8")

            self.assertEqual(
                "tracked_root,model,region,artifact,section,page_key,file_name,relative_path,change_type,insertions,deletions,old_path,new_path,from_ref,to_ref\n",
                files_csv,
            )
            self.assertIn("Initial baseline detected", files_html)
            self.assertIn("--ignore-initial-adds is enabled", files_html)
            self.assertIn("Initial baseline detected", index_html)


if __name__ == "__main__":
    unittest.main()
