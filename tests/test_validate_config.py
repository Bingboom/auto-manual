from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.validate_config import validate


class TestValidateConfig(unittest.TestCase):
    def test_validate_should_accept_build_targets(self) -> None:
        cfg = {
            "build": {
                "languages": ["en"],
                "default_region": "US",
                "targets": [
                    {"model": "JE-2000F", "region": "US"},
                    {"model": "JE-1000F"},
                ],
            },
            "paths": {},
            "pages": [{"type": "rst_include", "lang": "en", "file": "templates/page_us-en/00_preface.rst"}],
        }

        issues = validate(cfg, strict_files=False)
        errors = [issue.msg for issue in issues if issue.level == "ERROR"]
        self.assertEqual([], errors)

    def test_validate_should_reject_invalid_build_targets(self) -> None:
        cfg = {
            "build": {
                "languages": ["en"],
                "targets": [{"region": "US"}],
            },
            "paths": {},
            "pages": [{"type": "rst_include", "lang": "en", "file": "templates/page_us-en/00_preface.rst"}],
        }

        issues = validate(cfg, strict_files=False)
        errors = [issue.msg for issue in issues if issue.level == "ERROR"]
        self.assertTrue(any("build.targets[1].model" in msg for msg in errors))

    def test_validate_should_require_single_language_when_lang_is_in_output_path(self) -> None:
        cfg = {
            "build": {
                "languages": ["en", "es"],
                "include_lang_in_output_path": True,
            },
            "paths": {},
            "pages": [{"type": "rst_include", "lang": "en", "file": "templates/page_us-en/00_preface.rst"}],
        }

        issues = validate(cfg, strict_files=False)
        errors = [issue.msg for issue in issues if issue.level == "ERROR"]
        self.assertIn("build.include_lang_in_output_path requires exactly one build language", errors)

    def test_validate_should_accept_allowed_foreign_identity_literals(self) -> None:
        cfg = {
            "build": {"languages": ["en"]},
            "checks": {"allowed_foreign_identity_literals": ["Jackery Explorer 2000 Pro"]},
            "paths": {},
            "pages": [{"type": "rst_include", "lang": "en", "file": "templates/page_us-en/00_preface.rst"}],
        }

        issues = validate(cfg, strict_files=False)
        errors = [issue.msg for issue in issues if issue.level == "ERROR"]
        self.assertEqual([], errors)

    def test_validate_should_reject_invalid_allowed_foreign_identity_literals(self) -> None:
        cfg = {
            "build": {"languages": ["en"]},
            "checks": {"allowed_foreign_identity_literals": ["", 123]},
            "paths": {},
            "pages": [{"type": "rst_include", "lang": "en", "file": "templates/page_us-en/00_preface.rst"}],
        }

        issues = validate(cfg, strict_files=False)
        errors = [issue.msg for issue in issues if issue.level == "ERROR"]
        self.assertTrue(any("checks.allowed_foreign_identity_literals" in msg for msg in errors))

    def test_validate_should_accept_page_manifest_without_inline_pages(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            manifest_path = Path(td) / "manual.yaml"
            manifest_path.write_text(
                "\n".join(
                    [
                        "pages:",
                        "  - type: rst_include",
                        "    lang: en",
                        "    file: templates/page_us-en/00_preface.rst",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            cfg = {
                "build": {"languages": ["en"]},
                "paths": {"page_manifest": manifest_path.as_posix()},
            }

            issues = validate(cfg, strict_files=False)

        errors = [issue.msg for issue in issues if issue.level == "ERROR"]
        self.assertEqual([], errors)

    def test_validate_should_accept_spec_notes_csv_path(self) -> None:
        cfg = {
            "build": {"languages": ["en"]},
            "paths": {"spec_notes_csv": "data/phase2/Spec_Notes.csv"},
            "pages": [{"type": "rst_include", "lang": "en", "file": "templates/page_us-en/00_preface.rst"}],
        }

        issues = validate(cfg, strict_files=False)
        errors = [issue.msg for issue in issues if issue.level == "ERROR"]
        self.assertEqual([], errors)

    def test_validate_should_accept_phase2_snapshot_config(self) -> None:
        cfg = {
            "build": {"languages": ["en"]},
            "paths": {
                "structured_data_dir": "data/phase2",
                "page_registry_csv": "data/phase2/page_registry.csv",
                "page_blocks_dir": "data/phase2",
            },
            "sync": {
                "phase2": {
                    "provider": "lark_cli",
                    "cli_bin": "lark-cli",
                    "export_root": "data/phase2",
                    "manifest_path": "data/phase2/snapshot_manifest.json",
                    "base_token_env": "FEISHU_BASE_TOKEN",
                    "tables": {
                        "spec_master": {
                            "table_id_env": "FEISHU_SPEC_MASTER_TABLE_ID",
                            "view_id_env": "FEISHU_SPEC_MASTER_VIEW_ID",
                        },
                    },
                },
            },
            "pages": [{"type": "rst_include", "lang": "en", "file": "templates/page_us-en/00_preface.rst"}],
        }

        issues = validate(cfg, strict_files=False)
        errors = [issue.msg for issue in issues if issue.level == "ERROR"]
        self.assertEqual([], errors)

    def test_validate_should_reject_phase2_table_without_binding(self) -> None:
        cfg = {
            "build": {"languages": ["en"]},
            "sync": {
                "phase2": {
                    "provider": "lark_cli",
                    "tables": {
                        "spec_master": {},
                    },
                },
            },
            "pages": [{"type": "rst_include", "lang": "en", "file": "templates/page_us-en/00_preface.rst"}],
        }

        with mock.patch.dict("os.environ", {}, clear=True):
            issues = validate(cfg, strict_files=False)
        errors = [issue.msg for issue in issues if issue.level == "ERROR"]
        self.assertIn(
            "sync.phase2.tables.spec_master.base_token_env is required, or provide sync.phase2.base_token_env",
            errors,
        )
        self.assertIn(
            "sync.phase2.tables.spec_master.table_id or sync.phase2.tables.spec_master.table_id_env is required",
            errors,
        )

    def test_validate_should_accept_spec_master_source_tables_without_total_binding(self) -> None:
        cfg = {
            "build": {"languages": ["en"]},
            "sync": {
                "phase2": {
                    "provider": "lark_cli",
                    "base_token_env": "FEISHU_BASE_TOKEN",
                    "spec_master_sources": {
                        "spec_rows_source_table_id": "tbl_spec_rows",
                        "page_placeholders_source_table_id": "tbl_placeholders",
                    },
                    "tables": {
                        "spec_master": {},
                    },
                },
            },
            "pages": [{"type": "rst_include", "lang": "en", "file": "templates/page_us-en/00_preface.rst"}],
        }

        issues = validate(cfg, strict_files=False)
        errors = [issue.msg for issue in issues if issue.level == "ERROR"]
        self.assertEqual([], errors)

    def test_validate_should_accept_phase2_snapshot_config_with_literal_table_binding(self) -> None:
        cfg = {
            "build": {"languages": ["ja"]},
            "sync": {
                "phase2": {
                    "provider": "lark_cli",
                    "base_token_env": "FEISHU_BASE_TOKEN",
                    "tables": {
                        "spec_master": {
                            "table_id": "tbl7Kxyq8AaDKwsn",
                            "view_id": "vewbjo4Zfz",
                        },
                    },
                },
            },
            "pages": [{"type": "rst_include", "lang": "ja", "file": "templates/page_jp/cover_jp.rst"}],
        }

        issues = validate(cfg, strict_files=False)
        errors = [issue.msg for issue in issues if issue.level == "ERROR"]
        self.assertEqual([], errors)

    def test_validate_should_accept_lcd_variable_phase2_tables(self) -> None:
        cfg = {
            "build": {"languages": ["en"]},
            "sync": {
                "phase2": {
                    "provider": "lark_cli",
                    "base_token_env": "FEISHU_BASE_TOKEN",
                    "tables": {
                        "lcd_icons": {"table_id": "tblDII3oyqFhQYHn", "view_id": "vewerElnZ3"},
                        "troubleshooting": {"table_id": "tblUSuk3Q5BKTdTh", "view_id": "vewZne4CUk"},
                        "variable_defaults": {"table_id": "tblRyRdqRg2MGVgH", "view_id": "vew5jbxqLj"},
                        "variable_lang_overrides": {"table_id": "tblkcXujDMGXnHMo", "view_id": "vewODokxUs"},
                    },
                },
            },
            "pages": [{"type": "csv_page", "source": "phase2", "page": "lcd_icons", "langs": ["en"]}],
        }

        issues = validate(cfg, strict_files=False)
        errors = [issue.msg for issue in issues if issue.level == "ERROR"]
        self.assertEqual([], errors)

    def test_validate_should_reject_manifest_language_outside_build_languages(self) -> None:
        cfg = {
            "build": {"languages": ["en"]},
            "paths": {},
            "pages": [
                {"type": "rst_include", "lang": "fr", "file": "templates/page_shared/fr/00_preface.rst"},
                {"type": "csv_page", "source": "phase2", "page": "spec", "langs": ["en", "fr"]},
            ],
        }

        issues = validate(cfg, strict_files=False)
        errors = [issue.msg for issue in issues if issue.level == "ERROR"]
        self.assertIn(
            "pages[1] rst_include.lang contains languages not declared in build.languages: fr",
            errors,
        )
        self.assertIn(
            "pages[2] csv_page.langs contains languages not declared in build.languages: fr",
            errors,
        )

    def test_validate_should_reject_pdf_insert_missing_file_map_language(self) -> None:
        cfg = {
            "build": {"languages": ["en", "fr"]},
            "paths": {},
            "pages": [
                {
                    "type": "pdf_insert",
                    "langs": ["en", "fr"],
                    "file_map": {"en": "docs/static/en.pdf"},
                },
            ],
        }

        issues = validate(cfg, strict_files=False)
        errors = [issue.msg for issue in issues if issue.level == "ERROR"]
        self.assertIn("pages[1] pdf_insert.file_map is missing entries for langs: fr", errors)

    def test_validate_should_reject_invalid_phase2_sync_table_key(self) -> None:
        cfg = {
            "build": {"languages": ["en"]},
            "sync": {
                "phase2": {
                    "tables": {
                        "unknown_table": {
                            "table_id_env": "FEISHU_UNKNOWN_TABLE_ID",
                        },
                    },
                },
            },
            "pages": [{"type": "rst_include", "lang": "en", "file": "templates/page_us-en/00_preface.rst"}],
        }

        issues = validate(cfg, strict_files=False)
        errors = [issue.msg for issue in issues if issue.level == "ERROR"]
        self.assertTrue(any("sync.phase2.tables contains unsupported table key" in msg for msg in errors))


if __name__ == "__main__":
    unittest.main()
