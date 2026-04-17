from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

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
            "paths": {"spec_notes_csv": "data/phase1/Spec_Notes.csv"},
            "pages": [{"type": "rst_include", "lang": "en", "file": "templates/page_us-en/00_preface.rst"}],
        }

        issues = validate(cfg, strict_files=False)
        errors = [issue.msg for issue in issues if issue.level == "ERROR"]
        self.assertEqual([], errors)

    def test_validate_should_accept_phase2_snapshot_config(self) -> None:
        cfg = {
            "build": {"languages": ["en"]},
            "paths": {
                "structured_data_dir": "data/phase1",
                "page_registry_csv": "data/phase1/page_registry.csv",
                "page_blocks_dir": "data/phase1",
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
