from __future__ import annotations

from datetime import datetime, timezone
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from tools import delivery_outbox


BUILT_AT = datetime(2026, 8, 3, 15, 0, 0, tzinfo=timezone.utc)


def _outputs(directory: Path) -> dict[str, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    paths = {}
    for key, name in (
        ("artifact_output_path", "handoff.zip"),
        ("word_output_path", "manual.docx"),
        ("pdf_output_path", "manual.pdf"),
        ("md_output_path", "manual.md"),
    ):
        path = directory / name
        path.write_text(key, encoding="utf-8")
        paths[key] = path
    return paths


class TestPublishDeliveryFiles(unittest.TestCase):
    def test_pdf_leads_and_directories_are_never_included(self) -> None:
        directory = Path(tempfile.mkdtemp())
        outputs = _outputs(directory / "build")

        files = delivery_outbox.publish_delivery_files(**outputs)

        self.assertEqual(
            ["manual.pdf", "handoff.zip", "manual.docx", "manual.md"],
            [path.name for path in files],
        )

    def test_same_path_in_two_slots_is_deduplicated(self) -> None:
        directory = Path(tempfile.mkdtemp())
        single = directory / "manual.pdf"
        single.write_text("one", encoding="utf-8")

        files = delivery_outbox.publish_delivery_files(
            artifact_output_path=single,
            word_output_path=single,
            pdf_output_path=single,
            md_output_path=None,
        )

        self.assertEqual([single], files)

    def test_absent_and_none_paths_are_skipped(self) -> None:
        directory = Path(tempfile.mkdtemp())
        present = directory / "manual.pdf"
        present.write_text("one", encoding="utf-8")

        files = delivery_outbox.publish_delivery_files(
            artifact_output_path=directory / "never_built.zip",
            word_output_path=None,
            pdf_output_path=present,
            md_output_path=None,
        )

        self.assertEqual([present], files)


class TestDropPublishDeliveryOutbox(unittest.TestCase):
    def _drop(self, **overrides: object) -> tuple[tuple[str, ...], Path, io.StringIO]:
        directory = Path(tempfile.mkdtemp())
        outbox_root = directory / "outbox"
        stderr = io.StringIO()
        payload: dict[str, object] = {
            "model": "JE-1000F",
            "region": "EU",
            "version": "0.8",
            "git_ref": "review/JE-1000F-EU",
            "workflow_action": "publish",
            "built_at": BUILT_AT,
            "queue_record_ids": ("rec_a",),
            "document_link_url": "https://feishu.example.com/wiki/manual",
            "stderr": stderr,
            "environ": {delivery_outbox.DELIVERY_OUTBOX_ROOT_ENV: str(outbox_root)},
            **_outputs(directory / "build"),
        }
        payload.update(overrides)
        return delivery_outbox.drop_publish_delivery_outbox(**payload), outbox_root, stderr

    def test_unconfigured_outbox_is_silent_and_writes_nothing(self) -> None:
        notes, outbox_root, stderr = self._drop(environ={})

        self.assertEqual((), notes)
        self.assertFalse(outbox_root.exists())
        self.assertEqual("", stderr.getvalue())

    def test_successful_drop_reports_ok_and_job_name(self) -> None:
        notes, outbox_root, _stderr = self._drop()

        self.assertEqual("delivery_outbox=ok", notes[0])
        self.assertTrue(notes[1].startswith("delivery_outbox_job=JE-1000F_EU_0.8_"))
        job_dirs = [path for path in outbox_root.iterdir() if path.is_dir()]
        self.assertEqual(1, len(job_dirs))
        manifest = json.loads(
            (job_dirs[0] / delivery_outbox.DELIVERY_MANIFEST_FILENAME).read_text(encoding="utf-8")
        )
        self.assertEqual("欧英规", manifest["dingtalk_target"]["safety_regulation"])
        self.assertEqual(["rec_a"], manifest["source"]["queue_record_ids"])
        self.assertEqual(
            ["manual.pdf", "handoff.zip", "manual.docx", "manual.md"],
            [item["name"] for item in manifest["files"]],
        )

    def test_undelivered_target_is_skipped_not_failed(self) -> None:
        """A good build of a line nobody delivers must not raise an alarm."""

        notes, outbox_root, stderr = self._drop(model="JE-2000E", region="CN")

        self.assertEqual(("delivery_outbox=skipped",), notes)
        self.assertFalse(any(note.startswith("delivery_outbox=failed") for note in notes))
        self.assertFalse(outbox_root.exists())
        self.assertIn("delivery outbox skipped", stderr.getvalue())

    def test_unusable_outbox_root_degrades_instead_of_escaping(self) -> None:
        """`~nosuchuser/...` makes Path.expanduser raise; it must not reach the queue."""

        notes, _outbox_root, stderr = self._drop(
            environ={delivery_outbox.DELIVERY_OUTBOX_ROOT_ENV: "~nosuchuser12345/outbox"}
        )

        self.assertEqual("delivery_outbox=failed", notes[0])
        self.assertIn("delivery_outbox_error=", notes[1])
        self.assertIn("root is unusable", stderr.getvalue())

    def test_no_deliverable_files_degrades_to_a_failed_note(self) -> None:
        notes, _outbox_root, _stderr = self._drop(
            artifact_output_path=None,
            word_output_path=None,
            pdf_output_path=None,
            md_output_path=None,
        )

        self.assertEqual("delivery_outbox=failed", notes[0])
        self.assertIn("at least one artifact", notes[1])

    def test_unwritable_outbox_root_degrades_to_a_failed_note(self) -> None:
        directory = Path(tempfile.mkdtemp())
        blocker = directory / "blocked"
        blocker.write_text("not a directory", encoding="utf-8")

        notes, _outbox_root, _stderr = self._drop(
            environ={delivery_outbox.DELIVERY_OUTBOX_ROOT_ENV: str(blocker / "outbox")}
        )

        self.assertEqual("delivery_outbox=failed", notes[0])

    def test_second_drop_in_the_same_second_degrades_instead_of_overwriting(self) -> None:
        directory = Path(tempfile.mkdtemp())
        outbox_root = directory / "outbox"
        environ = {delivery_outbox.DELIVERY_OUTBOX_ROOT_ENV: str(outbox_root)}
        common: dict[str, object] = {
            "model": "JE-1000F",
            "region": "JP",
            "version": "1.7",
            "git_ref": "main",
            "workflow_action": "publish",
            "built_at": BUILT_AT,
            "queue_record_ids": ("rec_a",),
            "document_link_url": "",
            "stderr": io.StringIO(),
            "environ": environ,
        }

        first = delivery_outbox.drop_publish_delivery_outbox(
            **common, **_outputs(directory / "build_a")
        )
        second = delivery_outbox.drop_publish_delivery_outbox(
            **common, **_outputs(directory / "build_b")
        )

        self.assertEqual("delivery_outbox=ok", first[0])
        self.assertEqual("delivery_outbox=failed", second[0])
        self.assertIn("already exists", second[1])
        self.assertEqual(1, len([p for p in outbox_root.iterdir() if p.is_dir()]))


class TestQueueGroupProcessingDropsDelivery(unittest.TestCase):
    """Drive the real queue path so the call site itself is under test.

    The previous version of this file only exercised the adapter, so deleting the
    call in queue_group_processing.py left the suite green.
    """

    def _run_group(
        self,
        *,
        workflow_action: str,
        environ: dict[str, str],
    ) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
        from tools import queue_group_processing

        directory = Path(tempfile.mkdtemp())
        outputs = _outputs(directory / "build")
        drop_calls: list[dict[str, object]] = []
        success_calls: list[dict[str, object]] = []

        def fake_drop(**kwargs: object) -> tuple[str, ...]:
            drop_calls.append(kwargs)
            return delivery_outbox.drop_publish_delivery_outbox(**kwargs)

        def fake_build_success_fields(**kwargs: object) -> dict[str, object]:
            success_calls.append(kwargs)
            return {"构建结果": "SUCCESS"}

        class FakeSource:
            def __init__(self) -> None:
                self.records: dict[str, dict[str, object]] = {}

            def install(self, record_id: str, fields: dict[str, object]) -> None:
                self.records[record_id] = {"record_id": record_id, "fields": dict(fields)}

            def fetch_records_with_ids(self, **_: object) -> list[dict[str, object]]:
                return list(self.records.values())

            def upsert_record(self, **kwargs: object) -> None:
                record_id = str(kwargs["record_id"])
                raw = self.records.setdefault(record_id, {"record_id": record_id, "fields": {}})
                fields = raw.setdefault("fields", {})
                if isinstance(fields, dict):
                    fields.update(kwargs["record"])  # type: ignore[arg-type]

        source = FakeSource()

        class FakeRecord:
            record_id = "rec_publish"
            document_id = "JE-1000F_EU_0.8"
            document_key = "JE-1000F_EU"
            version = "0.8"
            lang = ""
            workflow_action = "Publish"
            doc_phase = ""
            git_ref = ""
            build_family = "eu-merged"

        class FakeBinding:
            base_token = "base"
            table_id = "table"

        class FakeOutputs:
            word_output_path = outputs["word_output_path"]
            pdf_output_path = outputs["pdf_output_path"]
            md_output_path = outputs["md_output_path"]
            latex_output_dir = None
            html_output_dir = None
            upload_output_path = outputs["artifact_output_path"]

        class FakeClaim:
            acquired = True
            reason = ""

        class FakeArtifactResult:
            latest_link_url = "https://feishu.example.com/drive/file"
            document_link_url = "https://feishu.example.com/wiki/manual"
            document_link_dd_url = ""
            status_notes = ("published_artifact=idml",)

        def fake_acquire(**kwargs: object) -> object:
            for record in kwargs["records"]:  # type: ignore[index]
                source.install(record.record_id, dict(kwargs["claim_fields"]))  # type: ignore[index]
            return FakeClaim()

        def fake_build_started_fields(**kwargs: object) -> dict[str, object]:
            from tools.queue_transitions import format_queue_result

            return {
                "构建结果": format_queue_result(
                    prefix="RUNNING",
                    claim_token=str(kwargs["claim_token"]),
                    claim_expires_at=kwargs["claim_expires_at"],
                )
            }

        with mock.patch.dict("os.environ", environ, clear=False), mock.patch.object(
            queue_group_processing, "drop_publish_delivery_outbox", fake_drop
        ):
            queue_group_processing.process_queue_record_group(
                group=[FakeRecord()],
                cfg={},
                config_path=Path("configs/config.eu.yaml"),
                source=source,
                binding=FakeBinding(),
                data_root=None,
                can_write_started_at=False,
                can_write_force_phase2_refresh=False,
                can_write_data_sync=False,
                can_write_document_link_dd=False,
                can_write_feishu_cloud_doc=False,
                has_upload_dingtalk_field=False,
                cli_bin="lark",
                identity="user",
                artifact_destination=object(),
                acquire_queue_claim=fake_acquire,
                result_field="构建结果",
                queue_claim_ttl_seconds=7200,
                warn_legacy_record_doc_phase=lambda _record: None,
                validate_queue_record_group=lambda _group: None,
                resolve_target_for_record=lambda _record: ("JE-1000F", "EU"),
                queue_group_lang=lambda _group: "",
                queue_group_build_family=lambda _group: "eu-merged",
                queue_group_dingtalk_target_node_url=lambda _group: "",
                queue_group_operator_union_id=lambda _group: "",
                queue_group_force_phase2_refresh=lambda _group: False,
                queue_group_upload_dingtalk=lambda _group: False,
                resolve_config_path_for_task=lambda **_kw: Path("configs/config.eu.yaml"),
                resolve_queue_workflow_action=lambda _record: workflow_action,
                sync_phase2_snapshot_before_queue=lambda **_kw: None,
                resolve_lark_wiki_destination=lambda **_kw: object(),
                resolve_row_artifact_destination=lambda **_kw: object(),
                resolve_artifact_mirror_provider=lambda **_kw: None,
                resolve_dingtalk_mirror_destination=lambda **_kw: None,
                ensure_dingtalk_session_ready=lambda **_kw: None,
                build_started_fields=fake_build_started_fields,
                build_document_for_task=lambda **_kw: FakeOutputs(),
                publish_word_artifact=lambda **_kw: FakeArtifactResult(),
                import_markdown_to_cloud_doc=lambda **_kw: ("", ""),
                finalize_cloud_doc=lambda **_kw: "",
                build_success_fields=fake_build_success_fields,
                queue_record_legacy_doc_phase=lambda _record: None,
                publish_release_latest_dir_for_target=lambda **_kw: Path("."),
                write_publish_release_metadata=lambda **_kw: Path("."),
                write_web_publish_metadata=lambda **_kw: Path("."),
                workflow_action_label=lambda _action: "Published",
                queue_record_key=lambda _record: "JE-1000F_EU",
                build_failure_writeback_fields=lambda **_kw: {},
                best_effort_queue_workflow_action=lambda _record: workflow_action,
                stderr=io.StringIO(),
            )
        return drop_calls, success_calls

    def test_publish_drops_with_blank_lang_and_note_reaches_the_row(self) -> None:
        """The production publish shape carries no Lang; the note must still land."""

        outbox_root = Path(tempfile.mkdtemp()) / "outbox"
        drop_calls, success_calls = self._run_group(
            workflow_action="publish",
            environ={delivery_outbox.DELIVERY_OUTBOX_ROOT_ENV: str(outbox_root)},
        )

        self.assertEqual(1, len(drop_calls))
        self.assertNotIn("lang", drop_calls[0])
        self.assertEqual("JE-1000F", drop_calls[0]["model"])
        self.assertEqual("EU", drop_calls[0]["region"])
        self.assertEqual(("rec_publish",), drop_calls[0]["queue_record_ids"])

        self.assertEqual(1, len(success_calls))
        notes = success_calls[0]["status_notes"]
        self.assertIn("delivery_outbox=ok", notes)
        self.assertTrue(any(str(note).startswith("delivery_outbox_job=") for note in notes))
        job_dirs = [path for path in outbox_root.iterdir() if path.is_dir()]
        self.assertEqual(1, len(job_dirs))

    def test_publish_without_outbox_configured_adds_no_note(self) -> None:
        with mock.patch.dict(
            "os.environ", {delivery_outbox.DELIVERY_OUTBOX_ROOT_ENV: ""}, clear=False
        ):
            drop_calls, success_calls = self._run_group(workflow_action="publish", environ={})

        self.assertEqual(1, len(drop_calls))
        notes = success_calls[0]["status_notes"]
        self.assertFalse([note for note in notes if str(note).startswith("delivery_outbox")])

    def test_draft_never_drops(self) -> None:
        drop_calls, _success_calls = self._run_group(
            workflow_action="draft",
            environ={delivery_outbox.DELIVERY_OUTBOX_ROOT_ENV: "/tmp/should-not-be-used"},
        )

        self.assertEqual([], drop_calls)


if __name__ == "__main__":
    unittest.main()
