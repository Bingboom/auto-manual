from __future__ import annotations

from pathlib import Path
import shutil
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import tempfile
import unittest
from unittest import mock

from tools import process_build_queue, queue_execute, queue_query
from tools.queue_outputs import stage_web_publish_assets_to_host_repo
from tools.document_link_actions import normalize_workflow_action, workflow_action_label
from tools.queue_contract import DocumentLinkBinding, QueueRecord
from tools.queue_group_processing import process_queue_record_group
from tools.queue_transitions import format_queue_result


def _apply_queue_upsert(raw_records: list[dict[str, object]], kwargs: dict[str, object]) -> None:
    record_id = str(kwargs["record_id"])
    update = kwargs["record"]
    for raw_record in raw_records:
        if raw_record.get("record_id") == record_id and isinstance(update, dict):
            fields = raw_record.setdefault("fields", {})
            if isinstance(fields, dict):
                fields.update(update)


class WebPublishQueueTests(unittest.TestCase):
    def test_action_contract_should_keep_web_publish_separate_from_print_publish(self) -> None:
        self.assertEqual("publish", normalize_workflow_action("Publish"))
        self.assertEqual("web_publish", normalize_workflow_action("Web Publish"))
        self.assertEqual("Web Publish", workflow_action_label("web_publish"))

    def test_cli_and_query_should_route_web_publish_to_its_own_worker(self) -> None:
        parsed = process_build_queue.parse_args(
            ["--config", "configs/config.us.yaml", "--workflow-action", "web-publish", "--record-id", "rec_web"]
        )
        self.assertEqual("web-publish", parsed.workflow_action)
        inferred = queue_query.infer_queue_query_from_text(
            "执行 JE-1000F_US_2.0_Web Publish"
        )
        self.assertEqual("web-publish", inferred.query_workflow_action)
        row = queue_query.QueueQueryRow(
            queue_scope="document-link",
            record_id="rec_web",
            document_id="JE-1000F_US_2.0",
            document_key="JE-1000F_US",
            build_family="us",
            lang="",
            version="2.0",
            workflow_action="Web Publish",
            normalized_workflow_action="web_publish",
            git_ref="review/JE-1000F-US",
            document_link="https://example.com/manual.idml",
            document_directory="/tmp/manual.idml",
            result="",
            pr_url="",
            review_status="ReadyForPublish",
            review_trigger_enabled=None,
            build_trigger_requested=True,
            immediate_build=True,
            initial_result="",
            remarks="",
        )
        self.assertEqual("web-publish", queue_execute.dispatch_command_for_row(row))

    def test_web_publish_build_should_only_render_web_profile_outputs(self) -> None:
        commands: list[list[str]] = []
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            config_path = root / "configs" / "config.us.yaml"
            config_path.parent.mkdir(parents=True)
            config_path.write_text("build:\n  languages: [en, fr, es]\n", encoding="utf-8")
            md_path = root / "docs" / "_build" / "JE-1000F" / "US" / "md" / "manual.md"
            html_dir = root / "docs" / "_build" / "JE-1000F" / "US" / "html"
            staged_md = root / "reports" / "releases" / "manual_web_publish_2.0.md"
            staged_html = root / "reports" / "releases" / "web" / "html"
            md_path.parent.mkdir(parents=True)
            md_path.write_text("# Manual\n", encoding="utf-8")
            html_dir.mkdir(parents=True)
            (html_dir / "index.html").write_text("<html></html>\n", encoding="utf-8")

            with mock.patch.object(process_build_queue, "ROOT", root), mock.patch.object(
                process_build_queue,
                "_run_command",
                side_effect=lambda cmd, **_: commands.append(cmd),
            ), mock.patch.object(
                process_build_queue,
                "resolve_md_output_path_for_target",
                return_value=md_path,
            ), mock.patch.object(
                process_build_queue,
                "resolve_html_output_dir_for_target",
                return_value=html_dir,
            ), mock.patch.object(
                process_build_queue,
                "resolve_word_output_path_for_target",
            ) as word_resolver, mock.patch.object(
                process_build_queue,
                "_stage_web_publish_assets_to_host_repo",
                return_value=(staged_md, staged_html),
            ) as stage_web:
                outputs = process_build_queue.build_document_for_task(
                    config_path=config_path,
                    model="JE-1000F",
                    region="US",
                    data_root="data/phase2",
                    doc_phase="Web Publish",
                    version="2.0",
                )

        self.assertEqual(staged_md, outputs.md_output_path)
        self.assertEqual(staged_html, outputs.html_output_dir)
        self.assertIsNone(outputs.word_output_path)
        self.assertIsNone(outputs.pdf_output_path)
        self.assertEqual(["check", "md", "html"], [command[4] for command in commands])
        for command in commands:
            self.assertEqual("env", command[0])
            self.assertEqual("AUTO_MANUAL_PRESENTATION_PROFILE=web", command[1])
            self.assertIn("--source", command)
            self.assertIn("review", command)
        word_resolver.assert_not_called()
        stage_web.assert_called_once()

    def test_web_publish_staging_should_replace_stale_version_assets(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source_dir = root / "build" / "md"
            source_assets = source_dir / "assets"
            source_assets.mkdir(parents=True)
            built_md = source_dir / "manual.md"
            built_md.write_text("# Manual\n", encoding="utf-8")
            (source_dir / "conf.py").write_text("extensions = []\n", encoding="utf-8")
            (source_dir / "index.md").write_text("# Index\n", encoding="utf-8")
            (source_assets / "old.png").write_bytes(b"old")
            built_html = root / "build" / "html"
            built_html.mkdir(parents=True)
            (built_html / "index.html").write_text("<html></html>\n", encoding="utf-8")
            version_dir = root / "reports" / "releases" / "versions" / "2.0"

            stage = lambda: stage_web_publish_assets_to_host_repo(
                built_md_output_path=built_md,
                built_html_dir=built_html,
                host_config_path=root / "configs" / "config.us.yaml",
                model="JE-1000F",
                region="US",
                version="2.0",
                publish_release_version_dir_for_target=lambda **_: version_dir,
                copy_tree=lambda src, dst: shutil.copytree(src, dst),
            )
            stage()
            (source_assets / "old.png").unlink()
            (source_assets / "new.png").write_bytes(b"new")
            stage()

            staged_assets = version_dir / "web" / "md" / "assets"
            self.assertFalse((staged_assets / "old.png").exists())
            self.assertEqual(b"new", (staged_assets / "new.png").read_bytes())

    def test_web_publish_group_should_refresh_assets_and_skip_print_writebacks(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            md_path = root / "reports" / "releases" / "manual_web_publish_2.0.md"
            html_dir = root / "reports" / "releases" / "web" / "html"
            md_path.parent.mkdir(parents=True)
            md_path.write_text("# Manual\n", encoding="utf-8")
            html_dir.mkdir(parents=True)
            (html_dir / "index.html").write_text("<html></html>\n", encoding="utf-8")

            record = QueueRecord(
                record_id="rec_web",
                document_id="JE-1000F_US_2.0",
                document_key="JE-1000F_US",
                version="2.0",
                lang="",
                workflow_action="Web Publish",
                git_ref="review/JE-1000F-US",
                trigger_value="Y",
                build_family="us",
            )
            binding = DocumentLinkBinding(
                base_token_env="BASE",
                table_id_env="TABLE",
                view_id_env=None,
                wiki_parent_token_env=None,
                base_token="base",
                table_id="table",
                view_id=None,
                wiki_parent_token=None,
            )
            upserts: list[dict[str, object]] = []
            raw_records: list[dict[str, object]] = [
                {"record_id": "rec_web", "fields": {"构建结果": ""}},
            ]
            sync_calls: list[dict[str, object]] = []
            success_calls: list[dict[str, object]] = []
            metadata_calls: list[dict[str, object]] = []

            class Source:
                def fetch_records_with_ids(self, **_: object) -> list[dict[str, object]]:
                    return raw_records

                def upsert_record(self, **kwargs: object) -> None:
                    upserts.append(kwargs)
                    _apply_queue_upsert(raw_records, kwargs)

            def fake_build_started_fields(**kwargs: object) -> dict[str, object]:
                return {
                    "构建结果": format_queue_result(
                        prefix="RUNNING",
                        claim_token=str(kwargs["claim_token"]),
                        claim_expires_at=kwargs["claim_expires_at"],
                    )
                }

            def fake_acquire_queue_claim(**kwargs: object) -> SimpleNamespace:
                _apply_queue_upsert(
                    raw_records,
                    {"record_id": "rec_web", "record": kwargs["claim_fields"]},
                )
                return SimpleNamespace(acquired=True, reason="")

            def fake_success_fields(**kwargs: object) -> dict[str, object]:
                success_calls.append(kwargs)
                return {"构建结果": "SUCCESS | workflow_action=Web Publish"}

            result = process_queue_record_group(
                group=[record],
                cfg={},
                config_path=Path("configs/config.us.yaml"),
                source=Source(),
                binding=binding,
                data_root="data/phase2",
                can_write_started_at=True,
                can_write_force_phase2_refresh=True,
                can_write_data_sync=True,
                can_write_document_link_dd=True,
                can_write_feishu_cloud_doc=True,
                has_upload_dingtalk_field=True,
                cli_bin="lark",
                identity="bot",
                artifact_destination=None,
                acquire_queue_claim=fake_acquire_queue_claim,
                result_field="构建结果",
                queue_claim_ttl_seconds=7200,
                warn_legacy_record_doc_phase=lambda _: None,
                validate_queue_record_group=lambda _: None,
                resolve_target_for_record=lambda _: ("JE-1000F", "US"),
                queue_group_lang=lambda _: "",
                queue_group_build_family=lambda _: "us",
                queue_group_dingtalk_target_node_url=lambda _: "",
                queue_group_operator_union_id=lambda _: "",
                queue_group_force_phase2_refresh=lambda _: False,
                queue_group_upload_dingtalk=lambda _: False,
                resolve_config_path_for_task=lambda **_: Path("configs/config.us.yaml"),
                resolve_queue_workflow_action=lambda _: "web_publish",
                sync_phase2_snapshot_before_queue=lambda **kwargs: sync_calls.append(kwargs),
                resolve_lark_wiki_destination=lambda **_: None,
                resolve_row_artifact_destination=lambda **_: None,
                resolve_artifact_mirror_provider=lambda **_: (_ for _ in ()).throw(
                    AssertionError("Web Publish must not resolve an artifact mirror")
                ),
                resolve_dingtalk_mirror_destination=lambda **_: None,
                ensure_dingtalk_session_ready=lambda **_: (_ for _ in ()).throw(
                    AssertionError("Web Publish must not open a DingTalk session")
                ),
                build_started_fields=fake_build_started_fields,
                build_document_for_task=lambda **_: process_build_queue.BuiltDocumentOutputs(
                    md_output_path=md_path,
                    html_output_dir=html_dir,
                ),
                publish_word_artifact=lambda **_: (_ for _ in ()).throw(
                    AssertionError("Web Publish must not upload a print artifact")
                ),
                import_markdown_to_cloud_doc=lambda **_: (_ for _ in ()).throw(
                    AssertionError("Web Publish must not import a review cloud doc")
                ),
                finalize_cloud_doc=lambda **_: "",
                build_success_fields=fake_success_fields,
                queue_record_legacy_doc_phase=lambda _: None,
                publish_release_latest_dir_for_target=lambda **_: Path("reports/releases/latest"),
                write_publish_release_metadata=lambda **_: (_ for _ in ()).throw(
                    AssertionError("Web Publish must not write print metadata")
                ),
                write_web_publish_metadata=lambda **kwargs: metadata_calls.append(kwargs) or md_path,
                workflow_action_label=workflow_action_label,
                queue_record_key=lambda _: "JE-1000F_US",
                build_failure_writeback_fields=lambda **kwargs: {"构建结果": f"FAILED {kwargs['message']}"},
                best_effort_queue_workflow_action=lambda _: "web_publish",
                stderr=None,
            )

        self.assertEqual(1, result.processed_rows)
        self.assertIsNone(result.failure_message)
        self.assertEqual(1, len(sync_calls))
        self.assertEqual(1, len(metadata_calls))
        self.assertEqual(md_path, metadata_calls[0]["md_output_path"])
        self.assertEqual(html_dir, metadata_calls[0]["html_dir"])
        self.assertFalse(success_calls[0]["write_document_directory"])
        self.assertFalse(success_calls[0]["write_document_link"])
        self.assertEqual(1, len(upserts))


if __name__ == "__main__":
    unittest.main()
