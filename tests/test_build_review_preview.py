from __future__ import annotations

import argparse
import importlib
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from tools.process_docs import build_review_preview


class TestBuildReviewPreview(unittest.TestCase):
    def test_importing_target_module_should_not_load_config_immediately(self) -> None:
        module_name = "tools.process_docs.build_review_preview_targets"
        sys.modules.pop(module_name, None)

        with mock.patch("tools.build_docs.load_config", side_effect=AssertionError("config load should be lazy")):
            module = importlib.import_module(module_name)

        self.assertEqual(0, module.workspace_target_templates.cache_info().currsize)

    def test_workspace_target_templates_should_derive_family_metadata_from_config(self) -> None:
        templates = {template.config: template for template in build_review_preview.WORKSPACE_TARGET_TEMPLATES}

        self.assertEqual("US", templates["config.us-en.yaml"].family)
        self.assertEqual("en", templates["config.us-en.yaml"].language)
        self.assertTrue(templates["config.us-en.yaml"].include_lang_in_output_path)

        self.assertEqual("JP", templates["config.ja.yaml"].family)
        self.assertEqual("ja", templates["config.ja.yaml"].language)
        self.assertFalse(templates["config.ja.yaml"].include_lang_in_output_path)

    def test_rewrite_manual_switcher_links_should_preserve_manual_mode_and_retarget_preview_paths(self) -> None:
        current = build_review_preview.WorkspaceTarget(
            model="JE-1000F",
            family="US",
            language="en",
            config="config.us-en.yaml",
            include_lang_in_output_path=True,
        )
        es_target = build_review_preview.WorkspaceTarget(
            model="JE-1000F",
            family="US",
            language="es",
            config="config.us-es.yaml",
            include_lang_in_output_path=True,
        )
        jp_target = build_review_preview.WorkspaceTarget(
            model="JE-1000F",
            family="JP",
            language="ja",
            config="config.ja.yaml",
            include_lang_in_output_path=False,
        )
        html = """
<html>
  <head>
    <link rel="stylesheet" href="_static/hb_manual.css">
    <script src="_static/hb_manual.js"></script>
  </head>
  <body class="furo hb-manual-switcher-body">
    <!-- HB_MANUAL_SWITCHER_START -->
    <div class="hb-manual-switcher">
      <a class="hb-manual-switcher__lang" href="../../es/html/index.html">Espanol</a>
      <a class="hb-manual-switcher__lang" href="../../../JP/html/index.html">鏃ユ湰瑾?/a>
    </div>
    <!-- HB_MANUAL_SWITCHER_END -->
    <aside class="sidebar-drawer"><div class="sidebar-tree"></div></aside>
    <main id="furo-main-content"><h1>Demo</h1></main>
  </body>
</html>
"""
        root = Path("C:/preview-test")

        def fake_html_root(_: str, target: build_review_preview.WorkspaceTarget) -> Path:
            mapping = {
                ("US", "en"): root / "docs" / "_build" / "JE-1000F" / "US" / "en" / "html",
                ("US", "es"): root / "docs" / "_build" / "JE-1000F" / "US" / "es" / "html",
                ("JP", "ja"): root / "docs" / "_build" / "JE-1000F" / "JP" / "html",
            }
            return mapping[(target.family, target.language)]

        with mock.patch.object(build_review_preview, "html_root_for_target", side_effect=fake_html_root):
            rewritten = build_review_preview.rewrite_manual_switcher_links(
                html,
                model="JE-1000F",
                current_target=current,
                current_relative_path=Path("index.html"),
                all_targets=[current, es_target, jp_target],
            )

        self.assertIn("hb-manual-switcher-body", rewritten)
        self.assertIn("_static/hb_manual.css", rewritten)
        self.assertIn("HB_MANUAL_SWITCHER_START", rewritten)
        self.assertIn('href="../es/index.html"', rewritten)
        self.assertIn('href="../../../JP/JE-1000F/ja/index.html"', rewritten)

    def test_build_spec_for_target_should_keep_us_en_on_lang_specific_config_in_review_mode(self) -> None:
        args = argparse.Namespace(
            config="config.us-en.yaml",
            model="JE-1000F",
            region="US",
            source="review",
            tracked_root=None,
            from_ref="HEAD~1",
            to_ref="HEAD",
            output_dir="site/review-preview/dist",
            clean_build=False,
            skip_build=False,
            skip_diff=False,
            skip_word=False,
            all_review_models=False,
        )
        target = build_review_preview.WorkspaceTarget(
            model="JE-1000F",
            family="US",
            language="en",
            config="config.us-en.yaml",
            include_lang_in_output_path=True,
        )

        spec = build_review_preview.build_spec_for_target(
            args,
            target,
            requested_target=build_review_preview.requested_workspace_target(args),
        )

        self.assertEqual(build_review_preview.resolve_path("config.us-en.yaml"), spec["config_path"])
        self.assertEqual("review", spec["source_mode"])
        self.assertEqual("review", spec["source_label"])
        self.assertEqual(build_review_preview.output_root_for_target("JE-1000F", target), spec["output_root"])

    def test_build_spec_for_target_should_use_review_for_existing_secondary_language_bundles(self) -> None:
        args = argparse.Namespace(
            config="config.us-en.yaml",
            model="JE-1000F",
            region="US",
            source="review",
            tracked_root=None,
            from_ref="HEAD~1",
            to_ref="HEAD",
            output_dir="site/review-preview/dist",
            clean_build=False,
            skip_build=False,
            skip_diff=False,
            skip_word=False,
            all_review_models=False,
        )
        target = build_review_preview.WorkspaceTarget(
            model="JE-1000F",
            family="US",
            language="es",
            config="config.us-es.yaml",
            include_lang_in_output_path=True,
        )

        spec = build_review_preview.build_spec_for_target(
            args,
            target,
            requested_target=build_review_preview.requested_workspace_target(args),
            review_availability={("JE-1000F", "US", "es")},
        )

        self.assertEqual(build_review_preview.resolve_path("config.us-es.yaml"), spec["config_path"])
        self.assertEqual("review", spec["source_mode"])
        self.assertEqual("review", spec["source_label"])
        self.assertEqual(build_review_preview.output_root_for_target("JE-1000F", target), spec["output_root"])

    def test_build_spec_for_target_should_fallback_to_runtime_for_secondary_language_without_review_baseline(self) -> None:
        args = argparse.Namespace(
            config="config.us-en.yaml",
            model="JE-1000F",
            region="US",
            source="review",
            tracked_root=None,
            from_ref="HEAD~1",
            to_ref="HEAD",
            output_dir="site/review-preview/dist",
            clean_build=False,
            skip_build=False,
            skip_diff=False,
            skip_word=False,
            all_review_models=False,
        )
        target = build_review_preview.WorkspaceTarget(
            model="JE-1000F",
            family="US",
            language="fr",
            config="config.us-fr.yaml",
            include_lang_in_output_path=True,
        )

        spec = build_review_preview.build_spec_for_target(
            args,
            target,
            requested_target=build_review_preview.requested_workspace_target(args),
            review_availability=set(),
        )

        self.assertEqual("runtime", spec["source_mode"])
        self.assertEqual("runtime", spec["source_label"])

    def test_target_has_review_bundle_should_accept_family_shared_review_content_for_secondary_language(self) -> None:
        target = build_review_preview.WorkspaceTarget(
            model="JE-1000F",
            family="US",
            language="fr",
            config="config.us-fr.yaml",
            include_lang_in_output_path=True,
        )

        self.assertTrue(
            build_review_preview.target_has_review_bundle(
                target,
                review_availability={("JE-1000F", "US", None)},
            )
        )

    def test_discover_workspace_targets_should_keep_requested_target_when_review_is_empty(self) -> None:
        args = argparse.Namespace(
            config="config.us-en.yaml",
            model="JE-1000F",
            region="US",
            source="review",
            tracked_root=None,
            from_ref="HEAD~1",
            to_ref="HEAD",
            output_dir="site/review-preview/dist",
            clean_build=False,
            skip_build=False,
            skip_diff=False,
            skip_word=False,
            all_review_models=False,
        )

        targets = build_review_preview.discover_workspace_targets(
            args,
            requested_target=build_review_preview.requested_workspace_target(args),
            review_availability=set(),
        )

        self.assertEqual(1, len(targets))
        self.assertEqual(("JE-1000F", "US", "en"), targets[0].key)

    def test_diff_config_for_family_should_use_us_en_config_for_us_family(self) -> None:
        args = argparse.Namespace(
            config="config.ja.yaml",
            model="JE-1000F",
            region="JP",
            source="review",
            tracked_root=None,
            from_ref="HEAD~1",
            to_ref="HEAD",
            output_dir="site/review-preview/dist",
            clean_build=False,
            skip_build=False,
            skip_diff=False,
            skip_word=False,
        )

        self.assertEqual(
            build_review_preview.resolve_path("config.us.yaml"),
            build_review_preview.diff_config_for_family(args, "US"),
        )

    def test_requested_workspace_target_should_infer_shared_family_config_when_config_missing(self) -> None:
        args = argparse.Namespace(
            config=None,
            model="JE-1000F",
            region="JP",
            source="review",
            tracked_root=None,
            from_ref="HEAD~1",
            to_ref="HEAD",
            output_dir="site/review-preview/dist",
            clean_build=False,
            skip_build=False,
            skip_diff=False,
            skip_word=False,
            all_review_models=False,
        )

        target = build_review_preview.requested_workspace_target(args)

        self.assertEqual("JP", target.family)
        self.assertEqual("ja", target.language)
        self.assertEqual("config.ja.yaml", target.config)
        self.assertFalse(target.include_lang_in_output_path)

    def test_copy_report_assets_should_return_stable_relative_paths(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            report_root = Path(td) / "reports"
            changes_dir = Path(td) / "dist" / "changes" / "US"
            downloads_dir = Path(td) / "dist" / "downloads" / "US"
            prefix = "US_HEAD_1_to_HEAD"
            html_payloads = {
                f"{prefix}_index.html": (
                    f'<a href="{prefix}_files.html">Files</a>'
                    f'<a href="{prefix}_pages.html">Pages</a>'
                    f'<a href="{prefix}_fields.html">Fields</a>'
                ),
                f"{prefix}.html": f'<a href="{prefix}_index.html">Index</a>',
                f"{prefix}_fields.html": "<p>fields</p>",
                f"{prefix}_pages.html": "<p>pages</p>",
                f"{prefix}_files.html": "<p>files</p>",
            }
            csv_names = (
                f"{prefix}.csv",
                f"{prefix}_pages.csv",
                f"{prefix}_fields.csv",
                f"{prefix}_files.csv",
            )
            for file_name, content in html_payloads.items():
                target = report_root / file_name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
            for file_name in csv_names:
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
            packaged_index = (changes_dir / "report-index.html").read_text(encoding="utf-8")
            self.assertIn('href="report-files.html"', packaged_index)
            self.assertIn('href="report-pages.html"', packaged_index)
            self.assertIn('href="report-fields.html"', packaged_index)
            self.assertNotIn(f"{prefix}_files.html", packaged_index)
            self.assertNotIn(f"{prefix}_pages.html", packaged_index)
            self.assertNotIn(f"{prefix}_fields.html", packaged_index)
            packaged_summary = (changes_dir / "report-summary.html").read_text(encoding="utf-8")
            self.assertIn('href="report-index.html"', packaged_summary)

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
                "word_docx": "downloads/US/JE-1000F/en/review-manual.docx",
                "change_workbook": "downloads/US/JE-1000F/change-report.xlsx",
                "csv_reports": {
                    "changes-summary.csv": "downloads/US/JE-1000F/changes-summary.csv",
                    "changes-pages.csv": "downloads/US/JE-1000F/changes-pages.csv",
                    "changes-fields.csv": "downloads/US/JE-1000F/changes-fields.csv",
                    "changes-files.csv": "downloads/US/JE-1000F/changes-files.csv",
                },
            },
            "report_files": {
                "report-index.html": "changes/US/JE-1000F/report-index.html",
                "report-summary.html": "changes/US/JE-1000F/report-summary.html",
                "report-fields.html": "changes/US/JE-1000F/report-fields.html",
                "report-pages.html": "changes/US/JE-1000F/report-pages.html",
                "report-files.html": "changes/US/JE-1000F/report-files.html",
            },
        }

        workspace_html = build_review_preview.render_workspace_html(meta["title"])
        model_entry = {
            "model": "JE-1000F",
            "default_lang": "en",
            "default_manual_url": "manual/US/JE-1000F/en/index.html",
            "shared_language_labels": ["English", "Spanish", "French"],
        }
        change_html = build_review_preview.render_model_changes_html(meta, family_entry, model_entry, family_changes)

        self.assertIn("Review Preview", workspace_html)
        self.assertIn("data-family-tab", workspace_html)
        self.assertIn("data-model-tab", workspace_html)
        self.assertIn("data-lang-tab", workspace_html)
        self.assertIn("Product Name:", workspace_html)
        self.assertNotIn("Current Family", workspace_html)
        self.assertNotIn("renderModelCards", workspace_html)
        self.assertIn('href="../../manual/US/JE-1000F/en/index.html"', change_html)
        self.assertIn('href="../../downloads/US/JE-1000F/change-report.xlsx"', change_html)
        self.assertIn('href="../../changes/US/JE-1000F/report-pages.html"', change_html)
        self.assertIn('href="../../index.html?family=US&model=JE-1000F&lang=en"', change_html)

    def test_render_changes_home_should_list_available_families(self) -> None:
        meta = {
            "title": "JE-1000F Review Preview",
            "model": "JE-1000F",
        }
        families_payload = [
            {
                "family": "US",
                "shared_language_labels": ["English", "Spanish", "French"],
                "default_manual_url": "manual/US/en/index.html",
                "change_index_url": "changes/US/index.html",
                "change_workbook_url": "downloads/US/change-report.xlsx",
                "models": [{"model": "JE-1000F"}],
            },
            {
                "family": "JP",
                "shared_language_labels": ["Japanese"],
                "default_manual_url": "manual/JP/ja/index.html",
                "change_index_url": "changes/JP/index.html",
                "change_workbook_url": "downloads/JP/change-report.xlsx",
                "models": [{"model": "JE-1000F"}],
            },
        ]

        html = build_review_preview.render_changes_home_html(meta, families_payload)

        self.assertIn("US family", html)
        self.assertIn("JP family", html)
        self.assertIn('href="../changes/US/index.html"', html)
        self.assertIn('href="../changes/JP/index.html"', html)

    def test_assert_preview_output_contract_should_require_word_when_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            output_dir = Path(td)
            for relative_path in (
                "index.html",
                "manual/index.html",
                "manual/US/JE-1000F/en/index.html",
                "changes/index.html",
                "changes/US/index.html",
                "changes/US/JE-1000F/index.html",
                "changes/US/JE-1000F/report-index.html",
                "changes/US/JE-1000F/report-summary.html",
                "changes/US/JE-1000F/report-fields.html",
                "changes/US/JE-1000F/report-pages.html",
                "changes/US/JE-1000F/report-files.html",
                "generated/meta.json",
                "generated/changes.json",
                "generated/workspace.json",
                "downloads/US/JE-1000F/change-report.xlsx",
                "downloads/US/JE-1000F/changes-summary.csv",
                "downloads/US/JE-1000F/changes-pages.csv",
                "downloads/US/JE-1000F/changes-fields.csv",
                "downloads/US/JE-1000F/changes-files.csv",
            ):
                target = output_dir / relative_path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("demo", encoding="utf-8")

            workspace = {
                "defaults": {
                    "manual_url": "manual/US/JE-1000F/en/index.html",
                    "change_url": "changes/US/JE-1000F/index.html",
                },
                "families": [
                    {
                        "family": "US",
                        "change_index_url": "changes/US/index.html",
                        "models": [
                            {
                                "model": "JE-1000F",
                                "change_index_url": "changes/US/JE-1000F/index.html",
                                "change_workbook_url": "downloads/US/JE-1000F/change-report.xlsx",
                                "csv_urls": {
                                    "changes-summary.csv": "downloads/US/JE-1000F/changes-summary.csv",
                                    "changes-pages.csv": "downloads/US/JE-1000F/changes-pages.csv",
                                    "changes-fields.csv": "downloads/US/JE-1000F/changes-fields.csv",
                                    "changes-files.csv": "downloads/US/JE-1000F/changes-files.csv",
                                },
                                "report_files": {
                                    "report-index.html": "changes/US/JE-1000F/report-index.html",
                                    "report-summary.html": "changes/US/JE-1000F/report-summary.html",
                                    "report-fields.html": "changes/US/JE-1000F/report-fields.html",
                                    "report-pages.html": "changes/US/JE-1000F/report-pages.html",
                                    "report-files.html": "changes/US/JE-1000F/report-files.html",
                                },
                                "languages": [
                                    {
                                        "lang": "en",
                                        "manual_url": "manual/US/JE-1000F/en/index.html",
                                        "word_url": "downloads/US/JE-1000F/en/review-manual.docx",
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }

            with self.assertRaisesRegex(RuntimeError, "review-manual.docx"):
                build_review_preview.assert_preview_output_contract(output_dir, workspace, require_word=True)

            word_path = output_dir / "downloads" / "US" / "JE-1000F" / "en" / "review-manual.docx"
            word_path.parent.mkdir(parents=True, exist_ok=True)
            word_path.write_text("demo", encoding="utf-8")
            build_review_preview.assert_preview_output_contract(output_dir, workspace, require_word=True)


if __name__ == "__main__":
    unittest.main()
