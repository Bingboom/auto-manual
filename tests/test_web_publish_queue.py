from __future__ import annotations

from pathlib import Path
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
        commands: list[tuple[list[str], dict[str, str] | None]] = []
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
            main_workspace = root / "main-worktree"
            review_workspace = root / "review-worktree"
            main_workspace.mkdir()
            (review_workspace / "docs" / "_review" / "JE-1000F" / "US").mkdir(parents=True)

            with mock.patch.object(process_build_queue, "ROOT", root), mock.patch.object(
                process_build_queue,
                "_run_command",
                side_effect=lambda cmd, **kwargs: commands.append((cmd, kwargs.get("env"))),
            ), mock.patch(
                "tools.queue_build_execution.git_commit_epoch",
                return_value=1234567890,
            ) as git_epoch, mock.patch.object(
                process_build_queue,
                "_prepare_git_ref_worktree",
                side_effect=[main_workspace, review_workspace],
            ), mock.patch.object(
                process_build_queue,
                "_remove_worktree",
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
                    git_ref="review/JE-1000F-US",
                )

        self.assertEqual(staged_md, outputs.md_output_path)
        self.assertEqual(staged_html, outputs.html_output_dir)
        self.assertIsNone(outputs.word_output_path)
        self.assertIsNone(outputs.pdf_output_path)
        self.assertEqual(["check", "md", "html"], [command[0][4] for command in commands])
        for command, env in commands:
            self.assertEqual("env", command[0])
            self.assertEqual("AUTO_MANUAL_PRESENTATION_PROFILE=web", command[1])
            self.assertIn("--source", command)
            self.assertIn("review", command)
            self.assertEqual({"SOURCE_DATE_EPOCH": "1234567890"}, env)
        word_resolver.assert_not_called()
        stage_web.assert_called_once()
        git_epoch.assert_called_once_with(review_workspace)

    def test_explicit_language_build_should_capture_check_md_html_in_order(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            config_path = root / "configs" / "config.shared.yaml"
            config_path.parent.mkdir(parents=True)
            config_path.write_text("build:\n  languages: [en, fr]\n", encoding="utf-8")
            md_path = root / "docs" / "_build" / "MODEL" / "EU" / "fr" / "md" / "manual.md"
            md_path.parent.mkdir(parents=True)
            md_path.write_text("# Manuel\n", encoding="utf-8")
            html_dir = md_path.parent.parent / "html"
            html_dir.mkdir()
            (html_dir / "index.html").write_text("<html></html>\n", encoding="utf-8")
            (md_path.parent.parent / "rst").mkdir()
            (md_path.parent.parent / "rst" / "bundle_manifest.json").write_text(
                "{}\n", encoding="utf-8"
            )
            main_workspace = root / "main-worktree"
            review_workspace = root / "review-worktree"
            main_workspace.mkdir()
            (review_workspace / "docs" / "_review" / "MODEL" / "EU").mkdir(parents=True)
            captures: list[object] = []

            def captured(_path: Path, *, action: str, **_: object) -> object:
                value = SimpleNamespace(action=action, language="fr")
                captures.append(value)
                return value

            with mock.patch.object(process_build_queue, "ROOT", root), mock.patch.object(
                process_build_queue, "_run_command"
            ), mock.patch(
                "tools.queue_build_execution.git_commit_epoch", return_value=1234567890
            ), mock.patch(
                "tools.queue_build_execution.capture_projection", side_effect=captured
            ), mock.patch.object(
                process_build_queue,
                "_prepare_git_ref_worktree",
                side_effect=[main_workspace, review_workspace],
            ), mock.patch.object(
                process_build_queue, "_remove_worktree"
            ), mock.patch.object(
                process_build_queue, "resolve_md_output_path_for_target", return_value=md_path
            ), mock.patch.object(
                process_build_queue, "resolve_html_output_dir_for_target", return_value=html_dir
            ), mock.patch.object(
                process_build_queue,
                "_stage_web_publish_assets_to_host_repo",
                return_value=(root / "staged.md", root / "staged-html"),
            ) as stage_web:
                outputs = process_build_queue.build_document_for_task(
                    config_path=config_path,
                    model="MODEL",
                    region="EU",
                    data_root="data/phase2",
                    doc_phase="Web Publish",
                    lang="fr",
                    version="2.0",
                    git_ref="review/MODEL-EU",
                )

            self.assertEqual(["check", "md", "html"], [item.action for item in captures])
            self.assertEqual(tuple(captures), stage_web.call_args.kwargs["projection_captures"])
            self.assertEqual("fr", stage_web.call_args.kwargs["target_lang"])
            self.assertEqual("fr", outputs.target_lang)
            self.assertIsNotNone(outputs.language_projection_evidence_path)

    def test_web_publish_staging_should_seal_version_assets_and_refuse_drift(self) -> None:
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
            )
            stage()
            original_files = {
                path.relative_to(version_dir / "web"): path.read_bytes()
                for path in (version_dir / "web").rglob("*")
                if path.is_file()
            }
            (source_assets / "old.png").unlink()
            (source_assets / "new.png").write_bytes(b"new")
            with self.assertRaisesRegex(RuntimeError, "immutable"):
                stage()

            staged_assets = version_dir / "web" / "md" / "assets"
            self.assertEqual(b"old", (staged_assets / "old.png").read_bytes())
            self.assertFalse((staged_assets / "new.png").exists())
            self.assertEqual(
                original_files,
                {
                    path.relative_to(version_dir / "web"): path.read_bytes()
                    for path in (version_dir / "web").rglob("*")
                    if path.is_file()
                },
            )

    def test_web_publish_staging_exact_retry_should_be_a_noop(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source_dir = root / "build" / "md"
            source_dir.mkdir(parents=True)
            built_md = source_dir / "manual.md"
            built_md.write_text("# Manual\n", encoding="utf-8")
            built_html = root / "build" / "html"
            built_html.mkdir(parents=True)
            (built_html / "index.html").write_text("<html></html>\n", encoding="utf-8")
            doctrees = built_html / ".doctrees"
            doctrees.mkdir()
            (doctrees / "environment.pickle").write_bytes(b"cache")
            version_dir = root / "reports" / "releases" / "versions" / "2.0"

            def stage() -> tuple[Path, Path]:
                return stage_web_publish_assets_to_host_repo(
                    built_md_output_path=built_md,
                    built_html_dir=built_html,
                    host_config_path=root / "configs" / "config.us.yaml",
                    model="JE-1000F",
                    region="US",
                    version="2.0",
                    publish_release_version_dir_for_target=lambda **_: version_dir,
                )

            staged_md, staged_html = stage()
            before = {
                path: (path.stat().st_mtime_ns, path.read_bytes())
                for path in (version_dir / "web").rglob("*")
                if path.is_file()
            }
            stage()

            self.assertEqual(
                before,
                {
                    path: (path.stat().st_mtime_ns, path.read_bytes())
                    for path in (version_dir / "web").rglob("*")
                    if path.is_file()
                },
            )
            self.assertEqual(version_dir / "web" / "md" / "manual.md", staged_md)
            self.assertEqual(version_dir / "web" / "html", staged_html)
            self.assertFalse((staged_html / ".doctrees").exists())

    def test_web_publish_staging_should_refuse_markdown_and_html_drift(self) -> None:
        for changed_file in ("markdown", "html"):
            with self.subTest(changed_file=changed_file), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                source_dir = root / "build" / "md"
                source_dir.mkdir(parents=True)
                built_md = source_dir / "manual.md"
                built_md.write_text("# Manual\n", encoding="utf-8")
                (source_dir / "index.md").write_text("# Index\n", encoding="utf-8")
                built_html = root / "build" / "html"
                built_html.mkdir(parents=True)
                html_index = built_html / "index.html"
                html_index.write_text("<html>first</html>\n", encoding="utf-8")
                version_dir = root / "reports" / "releases" / "versions" / "2.0"

                def stage() -> tuple[Path, Path]:
                    return stage_web_publish_assets_to_host_repo(
                        built_md_output_path=built_md,
                        built_html_dir=built_html,
                        host_config_path=root / "configs" / "config.us.yaml",
                        model="JE-1000F",
                        region="US",
                        version="2.0",
                        publish_release_version_dir_for_target=lambda **_: version_dir,
                    )

                stage()
                original_files = {
                    path.relative_to(version_dir / "web"): path.read_bytes()
                    for path in (version_dir / "web").rglob("*")
                    if path.is_file()
                }
                if changed_file == "markdown":
                    built_md.write_text("# Changed\n", encoding="utf-8")
                else:
                    html_index.write_text("<html>changed</html>\n", encoding="utf-8")

                with self.assertRaisesRegex(RuntimeError, "immutable"):
                    stage()
                self.assertEqual(
                    original_files,
                    {
                        path.relative_to(version_dir / "web"): path.read_bytes()
                        for path in (version_dir / "web").rglob("*")
                        if path.is_file()
                    },
                )

    def test_web_publish_staging_should_reject_all_input_symlinks(self) -> None:
        for symlink_case in ("markdown", "sidecar", "asset", "html_file", "html_root"):
            with self.subTest(symlink_case=symlink_case), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                source_dir = root / "build" / "md"
                assets_dir = source_dir / "assets"
                assets_dir.mkdir(parents=True)
                built_md = source_dir / "manual.md"
                built_md.write_text("# Manual\n", encoding="utf-8")
                index_path = source_dir / "index.md"
                index_path.write_text("# Index\n", encoding="utf-8")
                asset_path = assets_dir / "asset.png"
                asset_path.write_bytes(b"asset")
                built_html = root / "build" / "html"
                built_html.mkdir(parents=True)
                html_index = built_html / "index.html"
                html_index.write_text("<html></html>\n", encoding="utf-8")
                link_target = root / "link-target"
                if symlink_case == "markdown":
                    link_target.write_text("# Linked\n", encoding="utf-8")
                    built_md.unlink()
                    built_md.symlink_to(link_target)
                elif symlink_case == "sidecar":
                    link_target.write_text("# Linked\n", encoding="utf-8")
                    index_path.unlink()
                    index_path.symlink_to(link_target)
                elif symlink_case == "asset":
                    link_target.write_bytes(b"linked")
                    asset_path.unlink()
                    asset_path.symlink_to(link_target)
                elif symlink_case == "html_file":
                    link_target.write_text("<html>linked</html>\n", encoding="utf-8")
                    html_index.unlink()
                    html_index.symlink_to(link_target)
                else:
                    linked_html = root / "linked-html"
                    built_html.rename(linked_html)
                    built_html.symlink_to(linked_html, target_is_directory=True)
                version_dir = root / "reports" / "releases" / "versions" / "2.0"

                with self.assertRaisesRegex(RuntimeError, "symlink|real directory"):
                    stage_web_publish_assets_to_host_repo(
                        built_md_output_path=built_md,
                        built_html_dir=built_html,
                        host_config_path=root / "configs" / "config.us.yaml",
                        model="JE-1000F",
                        region="US",
                        version="2.0",
                        publish_release_version_dir_for_target=lambda **_: version_dir,
                    )
                self.assertFalse((version_dir / "web").exists())

    def test_web_publish_staging_should_reject_version_destination_symlinks(self) -> None:
        for symlink_case in ("version_dir", "web_dir"):
            with self.subTest(symlink_case=symlink_case), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                source_dir = root / "build" / "md"
                source_dir.mkdir(parents=True)
                built_md = source_dir / "manual.md"
                built_md.write_text("# Manual\n", encoding="utf-8")
                built_html = root / "build" / "html"
                built_html.mkdir(parents=True)
                (built_html / "index.html").write_text("<html></html>\n", encoding="utf-8")
                version_dir = root / "versions" / "2.0"
                outside = root / "outside"
                outside.mkdir()
                if symlink_case == "version_dir":
                    version_dir.parent.mkdir()
                    version_dir.symlink_to(outside, target_is_directory=True)
                else:
                    version_dir.mkdir(parents=True)
                    (version_dir / "web").symlink_to(outside, target_is_directory=True)

                with self.assertRaisesRegex(RuntimeError, "symlink"):
                    stage_web_publish_assets_to_host_repo(
                        built_md_output_path=built_md,
                        built_html_dir=built_html,
                        host_config_path=root / "config.yaml",
                        model="MODEL",
                        region="US",
                        version="2.0",
                        publish_release_version_dir_for_target=lambda **_: version_dir,
                    )
                self.assertEqual([], list(outside.iterdir()))

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
            terminal_events: list[str] = []

            class Source:
                def fetch_records_with_ids(self, **_: object) -> list[dict[str, object]]:
                    return raw_records

                def upsert_record(self, **kwargs: object) -> None:
                    upserts.append(kwargs)
                    terminal_events.append("queue_write")
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

            common_processing_kwargs = dict(
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
                workflow_action_label=workflow_action_label,
                queue_record_key=lambda _: "JE-1000F_US",
                build_failure_writeback_fields=lambda **kwargs: {"构建结果": f"FAILED {kwargs['message']}"},
                best_effort_queue_workflow_action=lambda _: "web_publish",
                stderr=None,
            )
            result = process_queue_record_group(
                **common_processing_kwargs,
                write_web_publish_metadata=lambda **kwargs: (
                    metadata_calls.append(kwargs),
                    terminal_events.append("metadata"),
                    md_path,
                )[-1],
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
        self.assertEqual(["metadata", "queue_write"], terminal_events)

        raw_records[0]["fields"] = {"构建结果": ""}
        upserts.clear()
        terminal_events.clear()
        failed_result = process_queue_record_group(
            **common_processing_kwargs,
            write_web_publish_metadata=lambda **_: (_ for _ in ()).throw(
                RuntimeError("metadata seal failed")
            ),
        )
        self.assertEqual(0, failed_result.processed_rows)
        self.assertIn("metadata seal failed", failed_result.failure_message or "")
        self.assertEqual(1, len(upserts))
        failed_fields = upserts[0]["record"]
        self.assertIsInstance(failed_fields, dict)
        self.assertIn("FAILED metadata seal failed", failed_fields["构建结果"])


if __name__ == "__main__":
    unittest.main()
