from __future__ import annotations

from datetime import datetime, timezone
import io
import json
from pathlib import Path
import tempfile
import unittest

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
            "lang": "fr",
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
        notes = delivery_outbox.drop_publish_delivery_outbox(**payload)
        return notes, outbox_root, stderr

    def test_unconfigured_outbox_is_silent_and_writes_nothing(self) -> None:
        notes, outbox_root, stderr = self._drop(environ={})

        self.assertEqual((), notes)
        self.assertFalse(outbox_root.exists())
        self.assertEqual("", stderr.getvalue())

    def test_successful_drop_reports_ok_and_job_name(self) -> None:
        notes, outbox_root, _stderr = self._drop()

        self.assertEqual("delivery_outbox=ok", notes[0])
        self.assertTrue(notes[1].startswith("delivery_outbox_job=JE-1000F_EU_fr_0.8_"))
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

    def test_unmapped_target_degrades_to_a_failed_note_and_never_raises(self) -> None:
        notes, _outbox_root, stderr = self._drop(lang="uk")

        self.assertEqual("delivery_outbox=failed", notes[0])
        self.assertIn("delivery_outbox_error=", notes[1])
        self.assertIn("no entry for", notes[1])
        self.assertIn("WARNING delivery outbox drop failed", stderr.getvalue())

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
        first_outputs = _outputs(directory / "build_a")
        second_outputs = _outputs(directory / "build_b")
        common: dict[str, object] = {
            "model": "JE-1000F",
            "region": "JP",
            "lang": "ja",
            "version": "1.7",
            "git_ref": "main",
            "workflow_action": "publish",
            "built_at": BUILT_AT,
            "queue_record_ids": ("rec_a",),
            "document_link_url": "",
            "stderr": io.StringIO(),
            "environ": environ,
        }

        first = delivery_outbox.drop_publish_delivery_outbox(**common, **first_outputs)
        second = delivery_outbox.drop_publish_delivery_outbox(**common, **second_outputs)

        self.assertEqual("delivery_outbox=ok", first[0])
        self.assertEqual("delivery_outbox=failed", second[0])
        self.assertIn("already exists", second[1])
        delivered = json.loads(
            (outbox_root / first[1].split("=", 1)[1] / delivery_outbox.DELIVERY_MANIFEST_FILENAME)
            .read_text(encoding="utf-8")
        )
        self.assertEqual("build_a", (directory / "build_a").name)
        self.assertEqual(4, len(delivered["files"]))


if __name__ == "__main__":
    unittest.main()
