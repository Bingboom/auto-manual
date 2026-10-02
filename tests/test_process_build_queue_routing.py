from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from typing import Callable
from unittest import mock

from tests.test_helpers import temp_test_root, write_text
from tools import document_link_queue, process_build_queue, queue_bound_records, queue_config_resolution
from tools.process_build_queue_deps import QueueDeps, default_queue_deps


def _queue_deps(**overrides: object) -> QueueDeps:
    """Run-scoped collaborators; built inside the test body so defaults see active patches."""
    return replace(default_queue_deps(process_build_queue), **overrides)  # type: ignore[arg-type]


def _resolve_config_path(*, root: Path, config_loader: Callable[[Path], dict], **kwargs: object) -> Path:
    """The config-path rule with its repo root and loader passed in, not patched on the facade."""
    return queue_config_resolution.resolve_config_path_for_task(
        repo_root=root, config_loader=config_loader, **kwargs,  # type: ignore[arg-type]
    )


class TestProcessBuildQueueRouting(unittest.TestCase):
    def test_facade_resolve_config_path_passes_repo_root_and_loader(self) -> None:
        with mock.patch.object(
            queue_bound_records, "_resolve_config_path_for_task_impl", return_value=Path("c.yaml"),
        ) as rule:
            result = process_build_queue.resolve_config_path_for_task(region="US", lang="en")
        self.assertEqual(Path("c.yaml"), result)
        kwargs = rule.call_args.kwargs
        self.assertEqual(process_build_queue.ROOT, kwargs["repo_root"])
        self.assertIs(process_build_queue.load_config, kwargs["config_loader"])
        self.assertEqual(("US", "en"), (kwargs["region"], kwargs["lang"]))

    def test_parse_document_key_should_split_model_and_region(self) -> None:
        model, region = process_build_queue.parse_document_key("JE-1000F_US")

        self.assertEqual("JE-1000F", model)
        self.assertEqual("US", region)

    def test_parse_document_key_should_preserve_pt_br_region_alias(self) -> None:
        model, region = process_build_queue.parse_document_key("JE-1500D_pt-BR")

        self.assertEqual("JE-1500D", model)
        self.assertEqual("pt-BR", region)

    def test_document_key_from_document_id_should_strip_br_alias(self) -> None:
        document_key = document_link_queue.document_key_from_document_id(
            document_id="JE-1500D_pt-BR_br_0.2",
            lang="br",
            version="0.2",
        )

        self.assertEqual("JE-1500D_pt-BR", document_key)

    def test_document_key_from_document_id_should_keep_pt_br_region_without_lang_segment(self) -> None:
        # pt-BR's region token IS its language and the Document_ID has no separate lang
        # segment, so stripping "pt-BR" as the lang must NOT destroy the region (regression:
        # JE-1000F_pt-BR_0.1 used to collapse to a region-less "JE-1000F").
        document_key = document_link_queue.document_key_from_document_id(
            document_id="JE-1000F_pt-BR_0.1",
            lang="pt-BR",
            version="0.1",
        )

        self.assertEqual("JE-1000F_pt-BR", document_key)

    def test_resolve_target_for_record_should_fallback_to_document_id(self) -> None:
        record = process_build_queue.QueueRecord(
            record_id="rec_1",
            document_id="JE-1000F_US_en_1.0",
            document_key='{"id":"recvfw0zG4PzxS"}',
            version="1.0",
            lang="en",
            doc_phase="",
            git_ref="",
            trigger_value="Y",
            immediate_trigger_value=False,
        )

        model, region = process_build_queue.resolve_target_for_record(record)

        self.assertEqual("JE-1000F", model)
        self.assertEqual("US", region)

    def test_resolve_target_for_record_should_resolve_pt_br_from_link_style_document_key(self) -> None:
        # Reproduces the failed draft build: a link-style Document_Key forces the
        # Document_ID fallback, and pt-BR (region == lang) must still resolve to a target
        # instead of "Unable to resolve build target".
        record = process_build_queue.QueueRecord(
            record_id="rec_ptbr",
            document_id="JE-1000F_pt-BR_0.1",
            document_key='{"id":"recvkenuskc8eF"}',
            version="0.1",
            lang="pt-BR",
            doc_phase="",
            git_ref="",
            trigger_value="Y",
            immediate_trigger_value=False,
        )

        model, region = process_build_queue.resolve_target_for_record(record)

        self.assertEqual("JE-1000F", model)
        self.assertEqual("pt-BR", region)

    def test_queue_record_key_should_ignore_link_style_document_key_for_display(self) -> None:
        record = process_build_queue.QueueRecord(
            record_id="rec_1",
            document_id="JE-1000F_US_en_1.0",
            document_key='{"id":"recvfw0zG4PzxS"}',
            version="1.0",
            lang="en",
            doc_phase="",
            git_ref="",
            trigger_value="Y",
            immediate_trigger_value=False,
        )

        self.assertEqual("JE-1000F_US", process_build_queue.queue_record_key(record))

    def test_resolve_config_path_for_task_should_prefer_lang_specific_config(self) -> None:
        with temp_test_root() as root:
            for name in ("config.yaml", "config.us-en.yaml", "config.us-fr.yaml"):
                write_text(root / "configs" / name, "build: {}\n")

            configs = {
                "config.yaml": {
                    "build": {
                        "default_region": "US",
                        "languages": ["en"],
                        "include_lang_in_output_path": False,
                    }
                },
                "config.us-en.yaml": {
                    "build": {
                        "default_region": "US",
                        "languages": ["en"],
                        "include_lang_in_output_path": True,
                    }
                },
                "config.us-fr.yaml": {
                    "build": {
                        "default_region": "US",
                        "languages": ["fr"],
                        "include_lang_in_output_path": True,
                    }
                },
            }

            config_path = _resolve_config_path(root=root, config_loader=lambda path: configs[path.name], region="US", lang="en")

        self.assertEqual(root / "configs" / "config.us-en.yaml", config_path)

    def test_resolve_config_path_for_task_should_use_document_key_config_as_lang_fallback(self) -> None:
        with temp_test_root() as root:
            for name in ("config.yaml", "config.us-en.yaml"):
                write_text(root / "configs" / name, "build: {}\n")

            configs = {
                "config.yaml": {
                    "build": {
                        "default_region": "US",
                        "languages": ["en", "fr", "es"],
                        "include_lang_in_output_path": True,
                        "queue_by_document_key": True,
                    }
                },
                "config.us-en.yaml": {
                    "build": {
                        "default_region": "US",
                        "languages": ["en"],
                        "include_lang_in_output_path": True,
                    }
                },
            }

            config_path = _resolve_config_path(root=root, config_loader=lambda path: configs[path.name], region="US", lang="fr")

        self.assertEqual(root / "configs" / "config.yaml", config_path)

    def test_resolve_config_path_for_task_should_allow_blank_lang_for_document_key_config(self) -> None:
        with temp_test_root() as root:
            for name in ("config.us.yaml", "config.us-en.yaml", "config.us-fr.yaml"):
                write_text(root / "configs" / name, "build: {}\n")

            configs = {
                "config.us.yaml": {
                    "build": {
                        "default_region": "US",
                        "languages": ["en", "fr", "es"],
                        "include_lang_in_output_path": False,
                        "queue_by_document_key": True,
                    }
                },
                "config.us-en.yaml": {
                    "build": {
                        "default_region": "US",
                        "languages": ["en"],
                        "include_lang_in_output_path": True,
                    }
                },
                "config.us-fr.yaml": {
                    "build": {
                        "default_region": "US",
                        "languages": ["fr"],
                        "include_lang_in_output_path": True,
                    }
                },
            }

            config_path = _resolve_config_path(root=root, config_loader=lambda path: configs[path.name], region="US", lang="")

        self.assertEqual(root / "configs" / "config.us.yaml", config_path)

    def test_resolve_config_path_for_task_should_allow_blank_lang_for_merged_eu_config(self) -> None:
        with temp_test_root() as root:
            for name in ("config.us.yaml", "config.eu.yaml", "config.eu-en.yaml"):
                write_text(root / "configs" / name, "build: {}\n")

            configs = {
                "config.us.yaml": {
                    "build": {
                        "default_region": "US",
                        "languages": ["en", "fr", "es"],
                        "include_lang_in_output_path": False,
                        "queue_by_document_key": True,
                    }
                },
                "config.eu.yaml": {
                    "build": {
                        "family_id": "eu-merged",
                        "default_region": "EU",
                        "languages": ["en", "fr", "es", "de", "it", "uk"],
                        "include_lang_in_output_path": False,
                        "queue_by_document_key": True,
                    }
                },
                "config.eu-en.yaml": {
                    "build": {
                        "family_id": "eu-en",
                        "default_region": "EU",
                        "languages": ["en"],
                        "include_lang_in_output_path": True,
                    }
                },
            }

            config_path = _resolve_config_path(root=root, config_loader=lambda path: configs[path.name], region="EU", lang="")

        self.assertEqual(root / "configs" / "config.eu.yaml", config_path)

    def test_resolve_config_path_for_task_should_reject_blank_lang_without_merged_region_config(self) -> None:
        with temp_test_root() as root:
            for name in ("config.eu-en.yaml", "config.eu-fr.yaml"):
                write_text(root / "configs" / name, "build: {}\n")

            configs = {
                "config.eu-en.yaml": {
                    "build": {
                        "family_id": "eu-en",
                        "default_region": "EU",
                        "languages": ["en"],
                        "include_lang_in_output_path": True,
                    }
                },
                "config.eu-fr.yaml": {
                    "build": {
                        "family_id": "eu-fr",
                        "default_region": "EU",
                        "languages": ["fr"],
                        "include_lang_in_output_path": True,
                    }
                },
            }

            with self.assertRaisesRegex(
                RuntimeError,
                "No config family matches region='EU' and lang=''",
            ):
                _resolve_config_path(
                    root=root, config_loader=lambda path: configs[path.name], region="EU", lang="",
                )

    def test_resolve_config_path_for_task_should_prefer_build_family_when_present(self) -> None:
        with temp_test_root() as root:
            for name in ("config.us.yaml", "config.us-en.yaml", "config.us-fr.yaml"):
                write_text(root / "configs" / name, "build: {}\n")

            configs = {
                "config.us.yaml": {
                    "build": {
                        "family_id": "us-merged",
                        "default_region": "US",
                        "languages": ["en", "fr", "es"],
                        "include_lang_in_output_path": False,
                        "queue_by_document_key": True,
                    }
                },
                "config.us-en.yaml": {
                    "build": {
                        "family_id": "us-en",
                        "default_region": "US",
                        "languages": ["en"],
                        "include_lang_in_output_path": True,
                    }
                },
                "config.us-fr.yaml": {
                    "build": {
                        "family_id": "us-fr",
                        "default_region": "US",
                        "languages": ["fr"],
                        "include_lang_in_output_path": True,
                    }
                },
            }

            config_path = _resolve_config_path(root=root, config_loader=lambda path: configs[path.name], 
                region="US",
                lang="fr",
                build_family="us-merged",
            )

        self.assertEqual(root / "configs" / "config.us.yaml", config_path)

    def test_resolve_config_path_for_task_should_fallback_to_lang_when_build_family_missing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for name in ("config.us.yaml", "config.us-en.yaml"):
                write_text(root / "configs" / name, "build: {}\n")

            configs = {
                "config.us.yaml": {
                    "build": {
                        "family_id": "us-merged",
                        "default_region": "US",
                        "languages": ["en", "fr", "es"],
                        "include_lang_in_output_path": False,
                        "queue_by_document_key": True,
                    }
                },
                "config.us-en.yaml": {
                    "build": {
                        "family_id": "us-en",
                        "default_region": "US",
                        "languages": ["en"],
                        "include_lang_in_output_path": True,
                    }
                },
            }

            config_path = _resolve_config_path(root=root, config_loader=lambda path: configs[path.name], region="US", lang="en")

        self.assertEqual(root / "configs" / "config.us-en.yaml", config_path)

    def test_resolve_config_path_for_task_should_reject_conflicting_build_family_and_lang(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            config_path = root / "configs" / "config.us-en.yaml"
            write_text(config_path, "build: {}\n")
            configs = {
                "config.us-en.yaml": {
                    "build": {
                        "family_id": "us-en",
                        "default_region": "US",
                        "languages": ["en"],
                        "include_lang_in_output_path": True,
                    }
                }
            }

            with self.assertRaisesRegex(RuntimeError, "conflicts with Lang"):
                _resolve_config_path(root=root, config_loader=lambda path: configs[path.name], 
                    region="US",
                    lang="fr",
                    build_family="us-en",
                )

    def test_resolve_config_path_for_task_should_reject_conflicting_build_family_and_region(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            config_path = root / "configs" / "config.us-en.yaml"
            write_text(config_path, "build: {}\n")
            configs = {
                "config.us-en.yaml": {
                    "build": {
                        "family_id": "us-en",
                        "default_region": "US",
                        "languages": ["en"],
                        "include_lang_in_output_path": True,
                    }
                }
            }

            with self.assertRaisesRegex(RuntimeError, "routes to region"):
                _resolve_config_path(root=root, config_loader=lambda path: configs[path.name], 
                    region="JP",
                    lang="en",
                    build_family="us-en",
                )

    def test_resolve_config_path_for_task_should_reject_publish_single_language_family(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            config_path = root / "configs" / "config.us-en.yaml"
            write_text(config_path, "build: {}\n")
            configs = {
                "config.us-en.yaml": {
                    "build": {
                        "family_id": "us-en",
                        "default_region": "US",
                        "languages": ["en"],
                        "include_lang_in_output_path": True,
                    }
                }
            }

            with self.assertRaisesRegex(RuntimeError, "whole-book Build_family"):
                _resolve_config_path(root=root, config_loader=lambda path: configs[path.name], 
                    region="US",
                    lang="",
                    build_family="us-en",
                    workflow_action="publish",
                )

    def test_resolve_config_path_for_task_should_allow_draft_lang_against_document_key_family(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            config_path = root / "configs" / "config.pt-br.yaml"
            write_text(config_path, "build: {}\n")
            configs = {
                "config.pt-br.yaml": {
                    "build": {
                        "family_id": "pt-br",
                        "default_region": "pt-BR",
                        "languages": ["en", "pt-BR"],
                        "include_lang_in_output_path": False,
                        "queue_by_document_key": True,
                    }
                }
            }

            config_path = _resolve_config_path(root=root, config_loader=lambda path: configs[path.name], 
                region="pt-br",
                lang="br",
                build_family="pt-br",
                workflow_action="draft",
            )

        self.assertEqual(root / "configs" / "config.pt-br.yaml", config_path)

    def test_group_pending_queue_records_should_merge_document_key_rows_when_config_requests_it(self) -> None:
        records = [
            process_build_queue.QueueRecord(
                record_id="rec_us_blank",
                document_id="JE-1000F_US_1.0",
                document_key="JE-1000F_US",
                version="1.0",
                lang="",
                workflow_action="Build Draft Package",
                doc_phase="Draft",
                git_ref="codex/review-je-1000f-us",
                trigger_value="Y",
                immediate_trigger_value=True,
                build_family="us-merged",
            ),
            process_build_queue.QueueRecord(
                record_id="rec_us_fr",
                document_id="JE-1000F_US_1.0",
                document_key="JE-1000F_US",
                version="1.0",
                lang="",
                workflow_action="Build Draft Package",
                doc_phase="Draft",
                git_ref="codex/review-je-1000f-us",
                trigger_value="Y",
                immediate_trigger_value=True,
                build_family="us-merged",
            ),
            process_build_queue.QueueRecord(
                record_id="rec_jp",
                document_id="JE-1000F_JP_ja_1.0",
                document_key="JE-1000F_JP",
                version="1.0",
                lang="ja",
                workflow_action="Build Draft Package",
                doc_phase="Draft",
                git_ref="codex/review-je-1000f-jp",
                trigger_value="Y",
                immediate_trigger_value=True,
                build_family="jp-ja",
            ),
        ]

        grouped = process_build_queue.group_pending_queue_records(records)

        self.assertEqual(
            [["rec_us_blank", "rec_us_fr"], ["rec_jp"]],
            [[record.record_id for record in group] for group in grouped],
        )

    def test_group_pending_queue_records_should_keep_single_language_families_separate(self) -> None:
        records = [
            process_build_queue.QueueRecord(
                record_id="rec_us_en",
                document_id="JE-1000F_US_en_1.0",
                document_key="JE-1000F_US",
                version="1.0",
                lang="en",
                workflow_action="Build Draft Package",
                doc_phase="Draft",
                git_ref="codex/review-je-1000f-us-en",
                trigger_value="Y",
                immediate_trigger_value=True,
                build_family="us-en",
            ),
            process_build_queue.QueueRecord(
                record_id="rec_us_fr",
                document_id="JE-1000F_US_fr_1.0",
                document_key="JE-1000F_US",
                version="1.0",
                lang="fr",
                workflow_action="Build Draft Package",
                doc_phase="Draft",
                git_ref="codex/review-je-1000f-us-fr",
                trigger_value="Y",
                immediate_trigger_value=True,
                build_family="us-fr",
            ),
        ]

        grouped = process_build_queue.group_pending_queue_records(records)

        self.assertEqual(
            [["rec_us_en"], ["rec_us_fr"]],
            [[record.record_id for record in group] for group in grouped],
        )

    def test_group_pending_queue_records_should_split_document_key_drafts_by_lang(self) -> None:
        records = [
            process_build_queue.QueueRecord(
                record_id="rec_ptbr_en",
                document_id="JE-1500D_pt-BR_en_0.2",
                document_key="JE-1500D_pt-BR",
                version="0.2",
                lang="en",
                workflow_action="Build Draft Package",
                doc_phase="Draft",
                git_ref="codex/review-je-1500d-pt-br",
                trigger_value="Y",
                immediate_trigger_value=True,
                build_family="pt-br",
            ),
            process_build_queue.QueueRecord(
                record_id="rec_ptbr_br",
                document_id="JE-1500D_pt-BR_br_0.2",
                document_key="JE-1500D_pt-BR",
                version="0.2",
                lang="br",
                workflow_action="Build Draft Package",
                doc_phase="Draft",
                git_ref="codex/review-je-1500d-pt-br",
                trigger_value="Y",
                immediate_trigger_value=True,
                build_family="pt-br",
            ),
            process_build_queue.QueueRecord(
                record_id="rec_ptbr_alias",
                document_id="JE-1500D_pt-BR_pt-BR_0.2",
                document_key="JE-1500D_pt-BR",
                version="0.2",
                lang="pt-BR",
                workflow_action="Build Draft Package",
                doc_phase="Draft",
                git_ref="codex/review-je-1500d-pt-br",
                trigger_value="Y",
                immediate_trigger_value=True,
                build_family="pt-br",
            ),
        ]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write_text(root / "configs" / "config.pt-br.yaml", "build: {}\n")
            configs = {
                "config.pt-br.yaml": {
                    "build": {
                        "family_id": "pt-br",
                        "default_region": "pt-BR",
                        "languages": ["en", "pt-BR"],
                        "include_lang_in_output_path": False,
                        "queue_by_document_key": True,
                    }
                }
            }
            with mock.patch.object(process_build_queue, "ROOT", root), mock.patch.object(
                process_build_queue,
                "load_config",
                side_effect=lambda path: configs[path.name],
            ):
                grouped = process_build_queue.group_pending_queue_records(records)

        self.assertEqual(
            [["rec_ptbr_en"], ["rec_ptbr_br", "rec_ptbr_alias"]],
            [[record.record_id for record in group] for group in grouped],
        )

    def test_group_pending_queue_records_should_not_merge_link_style_document_key_rows(self) -> None:
        records = [
            process_build_queue.QueueRecord(
                record_id="rec_us_1",
                document_id="JE-1000F_US_en_1.0",
                document_key='{"id":"recvfw0zG4PzxS"}',
                version="1.0",
                lang="en",
                workflow_action="Build Draft Package",
                doc_phase="Draft",
                git_ref="codex/review-je-1000f-us-en",
                trigger_value="Y",
                immediate_trigger_value=True,
                build_family="us-en",
            ),
            process_build_queue.QueueRecord(
                record_id="rec_us_2",
                document_id="JE-1000F_US_en_1.0",
                document_key='{"id":"recvfw0zG4PzxS"}',
                version="1.0",
                lang="en",
                workflow_action="Build Draft Package",
                doc_phase="Draft",
                git_ref="codex/review-je-1000f-us-en",
                trigger_value="Y",
                immediate_trigger_value=True,
                build_family="us-en",
            ),
        ]

        grouped = process_build_queue.group_pending_queue_records(records)

        self.assertEqual(
            [["rec_us_1"], ["rec_us_2"]],
            [[record.record_id for record in group] for group in grouped],
        )

    def test_process_build_queue_dry_run_should_use_build_family_for_document_key_groups(self) -> None:
        cfg = {
            "sync": {
                "phase2": {
                    "provider": "lark_cli",
                    "cli_bin": "lark-cli",
                    "base_token_env": "BASE_TOKEN",
                    "document_link": {
                        "table_id_env": "DOCUMENT_LINK_TABLE",
                        "view_id_env": "DOCUMENT_LINK_VIEW",
                    },
                }
            }
        }
        binding = process_build_queue.DocumentLinkBinding(
            base_token_env="BASE_TOKEN",
            table_id_env="DOCUMENT_LINK_TABLE",
            view_id_env="DOCUMENT_LINK_VIEW",
            wiki_parent_token_env=None,
            base_token="app_token",
            table_id="tbl_document_link",
            view_id="vew_document_link",
            wiki_parent_token=None,
        )
        raw_records = [
            {
                "record_id": "rec_group_1",
                "fields": {
                    process_build_queue.DOCUMENT_ID_FIELD: "JE-1000F_US_1.0",
                    process_build_queue.DOCUMENT_KEY_FIELD: "JE-1000F_US",
                    process_build_queue.VERSION_FIELD: ["1.0"],
                    process_build_queue.LANG_FIELD: [""],
                    process_build_queue.BUILD_FAMILY_FIELD: ["us-merged"],
                    process_build_queue.WORKFLOW_ACTION_FIELD: ["Build Draft Package"],
                    process_build_queue.DOC_PHASE_FIELD: ["Draft"],
                    process_build_queue.GIT_REF_FIELD: ["codex/review-je-1000f-us"],
                    process_build_queue.BUILD_STARTED_AT_FIELD: None,
                    process_build_queue.TRIGGER_FIELD: ["Y"],
                    process_build_queue.IMMEDIATE_TRIGGER_FIELD: True,
                },
            },
            {
                "record_id": "rec_group_2",
                "fields": {
                    process_build_queue.DOCUMENT_ID_FIELD: "JE-1000F_US_1.0",
                    process_build_queue.DOCUMENT_KEY_FIELD: "JE-1000F_US",
                    process_build_queue.VERSION_FIELD: ["1.0"],
                    process_build_queue.LANG_FIELD: [""],
                    process_build_queue.BUILD_FAMILY_FIELD: ["us-merged"],
                    process_build_queue.WORKFLOW_ACTION_FIELD: ["Build Draft Package"],
                    process_build_queue.DOC_PHASE_FIELD: ["Draft"],
                    process_build_queue.GIT_REF_FIELD: ["codex/review-je-1000f-us"],
                    process_build_queue.BUILD_STARTED_AT_FIELD: None,
                    process_build_queue.TRIGGER_FIELD: ["Y"],
                    process_build_queue.IMMEDIATE_TRIGGER_FIELD: True,
                },
            },
        ]

        class FakeSource:
            def fetch_records_with_ids(self, **_: object) -> list[dict[str, object]]:
                return raw_records

            def upsert_record(self, **_: object) -> dict[str, object]:
                raise AssertionError("dry-run should not write records")

        sync_mock = mock.MagicMock()
        with (
            mock.patch.object(
                process_build_queue,
                "resolve_config_path_for_task",
                return_value=Path("configs/config.us.yaml"),
            ) as resolve_mock,
        ):
            exit_code = process_build_queue.process_build_queue(
                cfg=cfg,
                config_path=Path("configs/config.us.yaml"),
                data_root="data/phase2",
                dry_run=True,
                deps=_queue_deps(
                    collect_queue_preflight_errors=mock.MagicMock(return_value=[]),
                    resolve_document_link_binding=mock.MagicMock(return_value=binding),
                    source_factory=mock.MagicMock(return_value=FakeSource()),
                    sync_phase2_snapshot_before_queue=sync_mock,
                ),
            )

        self.assertEqual(0, exit_code)
        sync_mock.assert_not_called()
        # Queue loading performs one broad pass to identify claimed sibling
        # rows, then the requested filtered pass, before processing the group.
        self.assertEqual(5, resolve_mock.call_count)
        self.assertTrue(all(call.kwargs.get("model") == "JE-1000F" for call in resolve_mock.call_args_list))
        self.assertTrue(all(call.kwargs.get("build_family") == "us-merged" for call in resolve_mock.call_args_list))
        self.assertTrue(all(call.kwargs.get("workflow_action") == "draft" for call in resolve_mock.call_args_list))
