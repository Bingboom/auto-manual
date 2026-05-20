from __future__ import annotations

import unittest

from tests.test_helpers import temp_test_root, write_text
from tools.build_paths import load_config
from tools.message_control_contract import (
    ACTION_BUILD_DRAFT_PACKAGE,
    ACTION_PUBLISH,
    ACTION_QUERY_STATUS,
    ACTION_START_REVIEW,
    STATUS_NEEDS_CONFIRMATION,
    STATUS_NEEDS_INPUT,
    STATUS_READY,
)
from tools.message_control_runtime import resolve_message_control


class TestMessageControlDryRun(unittest.TestCase):
    def test_publish_resolution_should_require_confirmation(self) -> None:
        with temp_test_root() as root:
            write_text(root / "config.us.yaml", "build:\n  family_id: us-merged\n  default_region: US\n")

            result = resolve_message_control(
                raw_message="publish JE-1000F us-merged version 0.2 from branch feature/review-123",
                repo_root=root,
                config_loader=load_config,
            )

        self.assertEqual(ACTION_PUBLISH, result.action)
        self.assertEqual(STATUS_NEEDS_CONFIRMATION, result.status)
        self.assertEqual("us-merged", result.selector.build_family)
        self.assertEqual("feature/review-123", result.selector.git_ref)
        self.assertEqual("0.2", result.selector.version)
        self.assertEqual("config.us.yaml", result.resolved_config_path)

    def test_publish_resolution_should_be_ready_when_confirmed(self) -> None:
        with temp_test_root() as root:
            write_text(root / "config.us.yaml", "build:\n  family_id: us-merged\n  default_region: US\n")

            result = resolve_message_control(
                raw_message="publish JE-1000F us-merged from branch feature/review-123",
                repo_root=root,
                config_loader=load_config,
                confirmed=True,
            )

        self.assertEqual(STATUS_READY, result.status)
        self.assertTrue(result.confirmed)

    def test_build_draft_should_require_git_ref(self) -> None:
        with temp_test_root() as root:
            write_text(root / "config.us.yaml", "build:\n  family_id: us-merged\n  default_region: US\n")

            result = resolve_message_control(
                raw_message="build draft package for JE-1000F us-merged",
                repo_root=root,
                config_loader=load_config,
            )

        self.assertEqual(ACTION_BUILD_DRAFT_PACKAGE, result.action)
        self.assertEqual(STATUS_NEEDS_INPUT, result.status)
        self.assertIn("git_ref", result.missing_fields)

    def test_start_review_should_parse_chinese_phrase(self) -> None:
        with temp_test_root() as root:
            write_text(root / "config.us.yaml", "build:\n  family_id: us-merged\n  default_region: US\n")

            result = resolve_message_control(
                raw_message="开始 review JE-1000F us-merged",
                repo_root=root,
                config_loader=load_config,
            )

        self.assertEqual(ACTION_START_REVIEW, result.action)
        self.assertEqual(STATUS_READY, result.status)
        self.assertEqual("JE-1000F", result.selector.model)

    def test_start_review_should_infer_pt_br_family_from_brazil_document_key(self) -> None:
        with temp_test_root() as root:
            write_text(root / "config.pt-br.yaml", "build:\n  family_id: pt-br\n  default_region: pt-BR\n")

            result = resolve_message_control(
                raw_message="开始review JE-1500D_Brazil",
                repo_root=root,
                config_loader=load_config,
            )

        self.assertEqual(ACTION_START_REVIEW, result.action)
        self.assertEqual(STATUS_READY, result.status)
        self.assertEqual("JE-1500D_Brazil", result.selector.document_key)
        self.assertEqual("JE-1500D", result.selector.model)
        self.assertEqual("pt-BR", result.selector.region)
        self.assertEqual("pt-br", result.selector.build_family)
        self.assertEqual("config.pt-br.yaml", result.resolved_config_path)

    def test_query_status_should_parse_document_id(self) -> None:
        with temp_test_root() as root:
            write_text(root / "config.us.yaml", "build:\n  family_id: us-merged\n  default_region: US\n")

            result = resolve_message_control(
                raw_message="what is the latest status for document 12345",
                repo_root=root,
                config_loader=load_config,
            )

        self.assertEqual(ACTION_QUERY_STATUS, result.action)
        self.assertEqual(STATUS_READY, result.status)
        self.assertEqual("12345", result.selector.document_id)

    def test_override_should_replace_message_value_and_warn(self) -> None:
        with temp_test_root() as root:
            write_text(root / "config.us.yaml", "build:\n  family_id: us-merged\n  default_region: US\n")
            write_text(root / "config.ja.yaml", "build:\n  family_id: jp-ja\n  default_region: JP\n")

            result = resolve_message_control(
                raw_message="publish JE-1000F us-merged from branch feature/review-123",
                repo_root=root,
                config_loader=load_config,
                build_family="jp-ja",
                git_ref="release/final",
            )

        self.assertEqual("jp-ja", result.selector.build_family)
        self.assertEqual("release/final", result.selector.git_ref)
        self.assertIn("build_family_overridden", result.warnings)
        self.assertIn("git_ref_overridden", result.warnings)

    def test_unresolved_message_should_stay_unresolved(self) -> None:
        with temp_test_root() as root:
            write_text(root / "config.us.yaml", "build:\n  family_id: us-merged\n  default_region: US\n")

            result = resolve_message_control(
                raw_message="please help with the manual",
                repo_root=root,
                config_loader=load_config,
            )

        self.assertEqual("", result.action)
        self.assertEqual("unresolved", result.status)
