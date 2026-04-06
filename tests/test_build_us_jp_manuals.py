from __future__ import annotations

import contextlib
import importlib.util
import io
import sys
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "build_us_jp_manuals.py"
SPEC = importlib.util.spec_from_file_location("build_us_jp_manuals", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Could not load script module from {MODULE_PATH}")
build_us_jp_manuals = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = build_us_jp_manuals
SPEC.loader.exec_module(build_us_jp_manuals)


class TestBuildUsJpManuals(unittest.TestCase):
    def test_targets_should_derive_matrix_metadata_from_configs(self) -> None:
        en_target = build_us_jp_manuals.TARGETS["en"]
        ja_target = build_us_jp_manuals.TARGETS["ja"]

        self.assertEqual("config.us-en.yaml", en_target.config)
        self.assertEqual("US", en_target.region)
        self.assertTrue(en_target.include_lang_in_output_path)
        self.assertEqual("manual_{model_slug}_{region_slug}_{lang_slug}.docx", en_target.word_template)
        self.assertEqual("manual_{model_slug}_{region_slug}_{lang_slug}.pdf", en_target.pdf_template)

        self.assertEqual("config.ja.yaml", ja_target.config)
        self.assertEqual("JP", ja_target.region)
        self.assertFalse(ja_target.include_lang_in_output_path)
        self.assertEqual("manual_{model_slug}_{region_slug}.docx", ja_target.word_template)
        self.assertEqual("manual_{model_slug}_{region_slug}.pdf", ja_target.pdf_template)

    def test_parse_args_should_require_explicit_model(self) -> None:
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                build_us_jp_manuals.parse_args([])

    def test_build_plan_should_default_to_all_languages_and_all_formats(self) -> None:
        args = build_us_jp_manuals.parse_args(["--model", "JE-1000F"])

        plan = build_us_jp_manuals.build_plan(args)

        self.assertEqual(4, len(plan))
        self.assertEqual(
            ["en", "es", "fr", "ja"],
            [item.target.language for item in plan],
        )
        self.assertTrue(all(item.action == "all" for item in plan))
        self.assertTrue(all("--no-clean" not in item.command for item in plan))

    def test_build_plan_should_keep_previous_outputs_when_running_partial_formats(self) -> None:
        args = build_us_jp_manuals.parse_args(
            ["--model", "JE-1000F", "--languages", "en,ja", "--formats", "html,word"]
        )

        plan = build_us_jp_manuals.build_plan(args)

        self.assertEqual(
            [("en", "html"), ("en", "word"), ("ja", "html"), ("ja", "word")],
            [(item.target.language, item.action) for item in plan],
        )
        self.assertNotIn("--no-clean", plan[0].command)
        self.assertIn("--no-clean", plan[1].command)
        self.assertNotIn("--no-clean", plan[2].command)
        self.assertIn("--no-clean", plan[3].command)

    def test_build_plan_should_reuse_clean_output_after_check_first(self) -> None:
        args = build_us_jp_manuals.parse_args(
            ["--model", "JE-1000F", "--languages", "ja", "--formats", "word,pdf", "--check-first"]
        )

        plan = build_us_jp_manuals.build_plan(args)

        self.assertEqual(["check", "word", "pdf"], [item.action for item in plan])
        self.assertNotIn("--no-clean", plan[0].command)
        self.assertIn("--no-clean", plan[1].command)
        self.assertIn("--no-clean", plan[2].command)

    def test_build_plan_should_accept_space_separated_formats_and_languages(self) -> None:
        args = build_us_jp_manuals.parse_args(
            ["--model", "JE-1000F", "--languages", "en", "ja", "--formats", "html", "word"]
        )

        plan = build_us_jp_manuals.build_plan(args)

        self.assertEqual(
            [("en", "html"), ("en", "word"), ("ja", "html"), ("ja", "word")],
            [(item.target.language, item.action) for item in plan],
        )

    def test_validate_open_options_should_require_html_format(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "--open-html requires html"):
            build_us_jp_manuals.validate_open_options(formats=["word", "pdf"], open_html=True)

    def test_open_generated_html_should_target_selected_language_indexes(self) -> None:
        with mock.patch.object(build_us_jp_manuals, "open_path") as open_path_mock:
            build_us_jp_manuals.open_generated_html(
                "JE-1000F",
                targets=[build_us_jp_manuals.TARGETS["en"], build_us_jp_manuals.TARGETS["ja"]],
                dry_run=True,
            )

        self.assertEqual(2, open_path_mock.call_count)
        self.assertEqual(
            [
                mock.call(ROOT / "docs" / "_build" / "JE-1000F" / "US" / "en" / "html" / "index.html", dry_run=True),
                mock.call(ROOT / "docs" / "_build" / "JE-1000F" / "JP" / "html" / "index.html", dry_run=True),
            ],
            open_path_mock.call_args_list,
        )

    def test_expected_artifacts_should_match_us_and_jp_output_layouts(self) -> None:
        en_target = build_us_jp_manuals.TARGETS["en"]
        ja_target = build_us_jp_manuals.TARGETS["ja"]

        en_artifacts = build_us_jp_manuals.expected_artifacts("JE-1000F", en_target, ["html", "word", "pdf"])
        ja_artifacts = build_us_jp_manuals.expected_artifacts("JE-1000F", ja_target, ["word"])

        self.assertEqual(
            ROOT / "docs" / "_build" / "JE-1000F" / "US" / "en" / "html" / "index.html",
            en_artifacts[0],
        )
        self.assertEqual(
            ROOT / "docs" / "_build" / "JE-1000F" / "US" / "en" / "word" / "manual_je1000f_us_en.docx",
            en_artifacts[1],
        )
        self.assertEqual(
            ROOT / "docs" / "_build" / "JE-1000F" / "US" / "en" / "pdf" / "manual_je1000f_us_en.pdf",
            en_artifacts[2],
        )
        self.assertEqual(
            [ROOT / "docs" / "_build" / "JE-1000F" / "JP" / "word" / "manual_je1000f_jp.docx"],
            ja_artifacts,
        )


if __name__ == "__main__":
    unittest.main()
