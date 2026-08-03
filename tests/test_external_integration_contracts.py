from __future__ import annotations

import argparse
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import Callable
from unittest import mock

from tools import process_build_queue
from tools import process_review_start_queue
from tools import queue_execute
from tools import queue_query
from tools import queue_resolve_action
from tools.queue_artifact_sink import ArtifactDestination, ArtifactPublishResult
from tools.queue_build_execution import BuiltDocumentOutputs
from tools.queue_group_processing import process_queue_record_group
from tools.queue_transitions import format_queue_result

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "external_integrations"


def _fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURE_ROOT / f"{name}.json").read_text(encoding="utf-8"))


def _queue_query_row(name: str) -> queue_query.QueueQueryRow:
    return queue_query.QueueQueryRow(**_fixture(name)["queue_query_row"])


def _queue_record(name: str) -> process_build_queue.QueueRecord:
    return process_build_queue.QueueRecord(**_fixture(name)["queue_record"])


class FakeBinding:
    base_token = "fake_base_token"
    table_id = "fake_table"


class FakeSource:
    def __init__(self, upsert_error: BaseException | None = None) -> None:
        self.upsert_error = upsert_error
        self.upserts: list[dict[str, object]] = []
        self.records: dict[str, dict[str, object]] = {}
        self.fetch_callbacks: list[Callable[[], None] | None] = []

    def install_claim(self, records: list[object], fields: dict[str, object]) -> None:
        for record in records:
            record_id = str(record.record_id)
            self.records[record_id] = {
                "record_id": record_id,
                "fields": dict(fields),
            }

    def fetch_records_with_ids(self, **_: object) -> list[dict[str, object]]:
        callback = self.fetch_callbacks.pop(0) if self.fetch_callbacks else None
        if callback:
            callback()
        return list(self.records.values())

    def upsert_record(self, **kwargs: object) -> None:
        self.upserts.append(kwargs)
        if self.upsert_error is not None:
            raise self.upsert_error
        record_id = str(kwargs["record_id"])
        raw = self.records.setdefault(record_id, {"record_id": record_id, "fields": {}})
        fields = raw.setdefault("fields", {})
        if isinstance(fields, dict):
            fields.update(kwargs["record"])


class TestExternalIntegrationContracts(unittest.TestCase):
    def _args(self, **overrides: object) -> argparse.Namespace:
        payload = {
            "query_text": None,
            "queue_scope": "all",
            "record_id": None,
            "task_id": None,
            "task_id_prefix": None,
            "document_id": None,
            "document_key": None,
            "document_keys": None,
            "build_family": None,
            "lang": None,
            "langs": None,
            "document_version": None,
            "market_group": None,
            "query_workflow_action": None,
            "git_ref_contains": None,
            "result_contains": None,
            "fresh_since": None,
            "limit": 10,
            "json": False,
            "confirm_publish": False,
            "allow_multiple": False,
            "wait_for_completion": True,
            "wait_timeout_seconds": 420,
            "status_poll_seconds": 3.0,
        }
        payload.update(overrides)
        return argparse.Namespace(**payload)

    def _process_group(
        self,
        *,
        record: process_build_queue.QueueRecord,
        source: FakeSource,
        artifact_output_path: Path,
        group: list[process_build_queue.QueueRecord] | None = None,
        stderr: io.StringIO | None = None,
        mirror_provider: str | None = None,
        mirror_error: str = "",
        validate_queue_record_group: Callable[[object], None] | None = None,
    ) -> tuple[object, list[dict[str, object]], dict[str, object]]:
        stderr = stderr or io.StringIO()
        publish_calls: list[dict[str, object]] = []
        captured_success: dict[str, object] = {}
        artifact_destination = ArtifactDestination(
            provider="lark_drive",
            label="Feishu wiki",
            details={"space_id": "spc_fake"},
            runtime_target=None,
        )

        def fake_publish_word_artifact(**kwargs: object) -> ArtifactPublishResult:
            publish_calls.append(kwargs)
            return ArtifactPublishResult(
                provider="lark_drive",
                reference_id="file_fake",
                latest_link_url="https://feishu.example.com/drive/file_fake",
                document_link_url="https://feishu.example.com/wiki/manual",
                status_notes=("published_artifact=docx",),
            )

        def fake_build_success_fields(**kwargs: object) -> dict[str, object]:
            captured_success.update(kwargs)
            return {
                process_build_queue.RESULT_FIELD: "SUCCESS",
                process_build_queue.DOCUMENT_LINK_FIELD: kwargs["document_link_url"],
            }

        def fake_resolve_dingtalk_mirror_destination(**kwargs: object) -> ArtifactDestination:
            if mirror_error:
                raise RuntimeError(mirror_error)
            return ArtifactDestination(
                provider="dingtalk_alidocs_session",
                label="DingTalk mirror",
                details={"target_node_url": kwargs.get("target_node_url", "")},
                runtime_target=kwargs.get("target_node_url", ""),
            )

        def fake_build_started_fields(**kwargs: object) -> dict[str, object]:
            return {
                process_build_queue.RESULT_FIELD: format_queue_result(
                    prefix="RUNNING",
                    claim_token=str(kwargs["claim_token"]),
                    claim_expires_at=kwargs["claim_expires_at"],
                )
            }

        def fake_acquire_queue_claim(**kwargs: object) -> SimpleNamespace:
            source.install_claim(list(kwargs["records"]), dict(kwargs["claim_fields"]))
            return SimpleNamespace(acquired=True, reason="")

        return (
            process_queue_record_group(
                group=group or [record],
                cfg={},
                config_path=Path("config.us.yaml"),
                source=source,
                binding=FakeBinding(),
                data_root=None,
                can_write_started_at=False,
                can_write_force_phase2_refresh=True,
                can_write_data_sync=True,
                can_write_document_link_dd=True,
                can_write_feishu_cloud_doc=False,
                has_upload_dingtalk_field=True,
                cli_bin="lark",
                identity="fake-identity",
                artifact_destination=artifact_destination,
                acquire_queue_claim=fake_acquire_queue_claim,
                result_field=process_build_queue.RESULT_FIELD,
                queue_claim_ttl_seconds=process_build_queue.QUEUE_CLAIM_TTL_SECONDS,
                warn_legacy_record_doc_phase=lambda _: None,
                validate_queue_record_group=validate_queue_record_group or (lambda _: None),
                resolve_target_for_record=lambda item: process_build_queue.parse_document_key(item.document_key),
                queue_group_lang=lambda items: items[0].lang,
                queue_group_build_family=lambda items: items[0].build_family,
                queue_group_dingtalk_target_node_url=lambda items: items[0].dingtalk_target_node_url,
                queue_group_operator_union_id=lambda items: items[0].operator_union_id,
                queue_group_force_phase2_refresh=lambda items: bool(items[0].force_phase2_refresh_value),
                queue_group_upload_dingtalk=lambda items: bool(items[0].upload_dingtalk_value),
                resolve_config_path_for_task=lambda **_: Path("config.us.yaml"),
                resolve_queue_workflow_action=lambda _: "draft",
                sync_phase2_snapshot_before_queue=lambda **_: None,
                resolve_lark_wiki_destination=lambda **_: artifact_destination,
                resolve_row_artifact_destination=lambda **_: artifact_destination,
                resolve_artifact_mirror_provider=lambda **_: mirror_provider,
                resolve_dingtalk_mirror_destination=fake_resolve_dingtalk_mirror_destination,
                ensure_dingtalk_session_ready=lambda **_: None,
                build_started_fields=fake_build_started_fields,
                build_document_for_task=lambda **_: BuiltDocumentOutputs(
                    word_output_path=artifact_output_path,
                    upload_output_path=artifact_output_path,
                ),
                publish_word_artifact=fake_publish_word_artifact,
                import_markdown_to_cloud_doc=lambda **_: ("", ""),
                finalize_cloud_doc=lambda **kw: kw["cloud_doc_url"],
                build_success_fields=fake_build_success_fields,
                queue_record_legacy_doc_phase=lambda _: None,
                publish_release_latest_dir_for_target=lambda **_: Path("reports/releases/latest"),
                write_publish_release_metadata=lambda **_: Path("reports/releases/latest/manifest.json"),
                workflow_action_label=lambda action: "Build Draft Package" if action in {"draft", "Build Draft Package"} else str(action or ""),
                queue_record_key=lambda item: item.document_key.upper(),
                build_failure_writeback_fields=lambda **kwargs: {
                    process_build_queue.RESULT_FIELD: f"FAILED {kwargs['message']}"
                },
                best_effort_queue_workflow_action=lambda _: "draft",
                stderr=stderr,
            ),
            publish_calls,
            captured_success,
        )

    def test_missing_start_review_and_document_link_fields_return_contract_failures(self) -> None:
        review_row = _queue_query_row("review_start_missing_document_key")
        raw_review_record = {
            "record_id": review_row.record_id,
            "fields": {
                process_review_start_queue.DOCUMENT_ID_FIELD: review_row.document_id,
                process_review_start_queue.WORKFLOW_ACTION_FIELD: review_row.workflow_action,
                process_review_start_queue.REVIEW_STATUS_FIELD: review_row.review_status,
                process_review_start_queue.REVIEW_TRIGGER_FIELD: True,
            },
        }

        with self.assertRaisesRegex(RuntimeError, "Document_Key must be non-empty"):
            process_review_start_queue.select_pending_review_start_records(
                [raw_review_record],
                record_id=review_row.record_id,
            )

        draft_row = _queue_query_row("document_link_draft_missing_git_ref")
        resolution = queue_resolve_action.resolve_queue_action(
            self._args(record_id=draft_row.record_id, query_workflow_action="build-draft"),
            [draft_row],
        )

        self.assertEqual("missing_required_field", resolution.resolution_status)
        self.assertEqual("build_draft_package", resolution.action_name)
        self.assertIn("git_ref", resolution.missing_fields)
        self.assertFalse(resolution.ready)

    def test_feishu_writeback_failure_from_fake_source_is_not_swallowed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            artifact_path = Path(td) / "manual.docx"
            artifact_path.write_text("fake docx", encoding="utf-8")
            source = FakeSource(RuntimeError("Feishu upsert denied: no edit permission"))

            result, _publish_calls, _captured = self._process_group(
                record=_queue_record("document_link_writeback_failure"),
                source=source,
                artifact_output_path=artifact_path,
            )

        self.assertEqual(0, result.processed_rows)
        self.assertIn("Feishu upsert denied: no edit permission", result.failure_message)
        self.assertIn("writeback_failed=Feishu upsert denied: no edit permission", result.failure_message)
        self.assertGreaterEqual(len(source.upserts), 2)

    def test_terminal_writeback_abstains_after_claim_is_reclaimed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            artifact_path = Path(td) / "manual.docx"
            artifact_path.write_text("fake docx", encoding="utf-8")
            source = FakeSource()
            record = _queue_record("document_link_writeback_failure")

            def replace_claim() -> None:
                source.records[record.record_id]["fields"] = {
                    process_build_queue.RESULT_FIELD: format_queue_result(
                        prefix="RUNNING",
                        claim_token="claim-b",
                        claim_expires_at=datetime.now(timezone.utc) + timedelta(hours=2),
                    )
                }

            source.fetch_callbacks = [replace_claim]
            result, _publish_calls, _captured = self._process_group(
                record=record,
                source=source,
                artifact_output_path=artifact_path,
            )

        self.assertEqual(0, result.processed_rows)
        self.assertIn("writeback_failed=claim ownership lost before terminal writeback", result.failure_message)
        self.assertEqual([], source.upserts)

    def test_multi_row_terminal_writeback_does_not_overwrite_rows_after_claim_loss(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            artifact_path = Path(td) / "manual.docx"
            artifact_path.write_text("fake docx", encoding="utf-8")
            source = FakeSource()
            first = _queue_record("document_link_writeback_failure")
            second = replace(first, record_id="rec_writeback_denied_2")

            def replace_second_claim() -> None:
                source.records[second.record_id]["fields"] = {
                    process_build_queue.RESULT_FIELD: format_queue_result(
                        prefix="RUNNING",
                        claim_token="claim-b",
                        claim_expires_at=datetime.now(timezone.utc) + timedelta(hours=2),
                    )
                }

            # The first terminal read succeeds and its SUCCESS write removes its claim;
            # the second terminal read observes a competing runner.
            source.fetch_callbacks = [None, replace_second_claim]
            result, _publish_calls, _captured = self._process_group(
                record=first,
                group=[first, second],
                source=source,
                artifact_output_path=artifact_path,
            )

        self.assertEqual(0, result.processed_rows)
        self.assertIn("writeback_failed=claim ownership lost before terminal writeback", result.failure_message)
        self.assertEqual(1, len(source.upserts))
        self.assertEqual(first.record_id, source.upserts[0]["record_id"])
        self.assertIn("SUCCESS", str(source.upserts[0]["record"]))
        self.assertFalse(any("FAILED" in str(upsert["record"]) for upsert in source.upserts))

    def test_failure_before_claim_still_writes_failed_when_row_is_unclaimed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            artifact_path = Path(td) / "manual.docx"
            artifact_path.write_text("fake docx", encoding="utf-8")
            source = FakeSource()
            record = _queue_record("document_link_writeback_failure")
            source.records[record.record_id] = {
                "record_id": record.record_id,
                "fields": {process_build_queue.RESULT_FIELD: ""},
            }

            def reject_group(_: object) -> None:
                raise RuntimeError("queue group mixes versions")

            result, _publish_calls, _captured = self._process_group(
                record=record,
                source=source,
                artifact_output_path=artifact_path,
                validate_queue_record_group=reject_group,
            )

        self.assertEqual(0, result.processed_rows)
        self.assertIn("queue group mixes versions", result.failure_message)
        self.assertNotIn("writeback_failed", result.failure_message)
        self.assertEqual(1, len(source.upserts))
        self.assertIn("FAILED", str(source.upserts[0]["record"]))

    def test_failure_before_claim_abstains_when_another_runner_holds_the_row(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            artifact_path = Path(td) / "manual.docx"
            artifact_path.write_text("fake docx", encoding="utf-8")
            source = FakeSource()
            record = _queue_record("document_link_writeback_failure")
            source.records[record.record_id] = {
                "record_id": record.record_id,
                "fields": {
                    process_build_queue.RESULT_FIELD: format_queue_result(
                        prefix="RUNNING",
                        claim_token="claim-other",
                        claim_expires_at=datetime.now(timezone.utc) + timedelta(hours=2),
                    )
                },
            }

            def reject_group(_: object) -> None:
                raise RuntimeError("queue group mixes versions")

            result, _publish_calls, _captured = self._process_group(
                record=record,
                source=source,
                artifact_output_path=artifact_path,
                validate_queue_record_group=reject_group,
            )

        self.assertEqual(0, result.processed_rows)
        self.assertIn("queue group mixes versions", result.failure_message)
        self.assertIn("writeback_failed=row is claimed by another runner", result.failure_message)
        self.assertEqual([], source.upserts)

    def test_completed_start_review_fixture_is_idempotent_for_openclaw_duplicate_dispatch(self) -> None:
        row = _queue_query_row("completed_start_review_inreview_git_ref")
        stdout = io.StringIO()

        with mock.patch.object(queue_execute, "load_config", return_value={}), mock.patch.object(
            queue_execute,
            "collect_queue_query_rows",
            return_value=[row],
        ), mock.patch.object(queue_execute, "_run_control_layer_cli") as mock_cli, redirect_stdout(stdout):
            queue_execute.run_queue_execute(
                self._args(
                    record_id=row.record_id,
                    queue_scope="review-init",
                    query_workflow_action="start-review",
                    json=True,
                ),
                config_path=Path("config.ja.yaml"),
                repo_root=Path("."),
            )

        mock_cli.assert_not_called()
        payload = json.loads(stdout.getvalue())
        self.assertEqual(row.record_id, payload["record_id"])
        self.assertEqual(row.git_ref, payload["git_ref"])
        self.assertEqual("InReview", payload["review_status"])
        self.assertEqual(row.pr_url, payload["pr_url"])

    def test_publish_fixture_without_confirmation_blocks_before_openclaw_dispatch(self) -> None:
        row = _queue_query_row("document_link_publish_ready")

        with mock.patch.object(queue_execute, "load_config", return_value={}), mock.patch.object(
            queue_execute,
            "collect_queue_query_rows",
            return_value=[row],
        ), mock.patch.object(queue_execute, "_run_control_layer_cli") as mock_cli:
            with self.assertRaisesRegex(RuntimeError, "--confirm-publish"):
                queue_execute.run_queue_execute(
                    self._args(
                        record_id=row.record_id,
                        queue_scope="document-link",
                        query_workflow_action="publish",
                    ),
                    config_path=Path("config.us.yaml"),
                    repo_root=Path("."),
                )

        mock_cli.assert_not_called()

    def test_dingtalk_mirror_unavailable_falls_back_to_feishu_wiki_with_warning(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            artifact_path = Path(td) / "manual.docx"
            artifact_path.write_text("fake docx", encoding="utf-8")
            source = FakeSource()
            stderr = io.StringIO()

            result, publish_calls, captured = self._process_group(
                record=_queue_record("document_link_dingtalk_mirror"),
                source=source,
                artifact_output_path=artifact_path,
                stderr=stderr,
                mirror_provider="dingtalk_alidocs_session",
                mirror_error="DingTalk session expired",
            )

        self.assertEqual(1, result.processed_rows)
        self.assertIsNone(result.failure_message)
        self.assertEqual(1, len(source.upserts))
        # Draft no longer uploads the artifact, so the publish artifact is never invoked;
        # the DingTalk mirror probe still runs before the phase gate and its failure is
        # surfaced as a warning + deferred status note.
        self.assertEqual(0, len(publish_calls))
        self.assertIn("WARNING DingTalk sync unavailable", stderr.getvalue())
        self.assertIn("using Feishu/wiki only", stderr.getvalue())
        status_notes = captured["status_notes"]
        self.assertIn("dingtalk_sync=failed", status_notes)
        self.assertIn("dingtalk_sync_error=DingTalk session expired", status_notes)


if __name__ == "__main__":
    unittest.main()
