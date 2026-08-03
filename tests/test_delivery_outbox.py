from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from tools import delivery_outbox
from tools.dingtalk_delivery_map import DeliveryTargetNotMapped, resolve_delivery_target


BUILT_AT = datetime(2026, 8, 3, 14, 30, 5, tzinfo=timezone.utc)


def _artifacts(directory: Path, names: tuple[str, ...] = ("manual.pdf", "manual.docx")) -> list[Path]:
    directory.mkdir(parents=True, exist_ok=True)
    paths = []
    for index, name in enumerate(names):
        path = directory / name
        path.write_text(f"payload-{index}", encoding="utf-8")
        paths.append(path)
    return paths


class TestDeliveryOutboxRoot(unittest.TestCase):
    def test_root_is_none_when_env_is_unset_or_blank(self) -> None:
        self.assertIsNone(delivery_outbox.delivery_outbox_root(environ={}))
        self.assertIsNone(
            delivery_outbox.delivery_outbox_root(
                environ={delivery_outbox.DELIVERY_OUTBOX_ROOT_ENV: "   "}
            )
        )

    def test_root_is_expanded_when_configured(self) -> None:
        root = delivery_outbox.delivery_outbox_root(
            environ={delivery_outbox.DELIVERY_OUTBOX_ROOT_ENV: "/tmp/outbox"}
        )

        self.assertEqual(Path("/tmp/outbox"), root)


class TestDeliveryJobId(unittest.TestCase):
    def test_job_id_is_stable_and_carries_the_target(self) -> None:
        job_id = delivery_outbox.build_job_id(
            model="JE-1000F", region="EU", version="0.8", built_at=BUILT_AT
        )

        self.assertEqual("JE-1000F_EU_0.8_20260803T143005Z", job_id)

    def test_job_id_stays_in_the_safe_character_set_across_time_zones(self) -> None:
        """A numeric UTC offset would put '+' in the id; '+' means space in URLs."""

        shanghai = timezone(timedelta(hours=8))
        job_id = delivery_outbox.build_job_id(
            model="JE-1000F",
            region="EU",
            version="0.8",
            built_at=BUILT_AT.astimezone(shanghai),
        )

        self.assertEqual("JE-1000F_EU_0.8_20260803T143005Z", job_id)
        self.assertNotIn("+", job_id)
        self.assertRegex(job_id, r"^[A-Za-z0-9._-]+$")

    def test_job_id_differs_when_build_time_differs(self) -> None:
        later = delivery_outbox.build_job_id(
            model="JE-1000F",
            region="EU",
            version="0.8",
            built_at=BUILT_AT + timedelta(seconds=1),
        )

        self.assertNotEqual(
            delivery_outbox.build_job_id(
                model="JE-1000F", region="EU", version="0.8", built_at=BUILT_AT
            ),
            later,
        )

    def test_path_traversal_segments_are_rejected(self) -> None:
        for field, payload in (
            ("model", "../escape"),
            ("region", "EU/../.."),
            ("version", ""),
        ):
            kwargs = {
                "model": "JE-1000F",
                "region": "EU",
                "version": "0.8",
                "built_at": BUILT_AT,
            }
            kwargs[field] = payload
            with self.assertRaises(RuntimeError, msg=f"{field}={payload!r}"):
                delivery_outbox.build_job_id(**kwargs)


class TestWriteDeliveryOutbox(unittest.TestCase):
    def _write(self, **overrides: object) -> tuple[delivery_outbox.DeliveryOutboxResult, Path]:
        directory = Path(tempfile.mkdtemp())
        outbox_root = directory / "outbox"
        payload: dict[str, object] = {
            "outbox_root": outbox_root,
            "model": "JE-1000F",
            "region": "EU",
            "version": "0.8",
            "git_ref": "review/JE-1000F-EU",
            "workflow_action": "publish",
            "built_at": BUILT_AT,
            "queue_record_ids": ("rec_a", "rec_b"),
            "document_link_url": "https://feishu.example.com/wiki/manual",
            "files": _artifacts(directory / "build"),
        }
        payload.update(overrides)
        return delivery_outbox.write_delivery_outbox(**payload), outbox_root

    def test_drop_writes_files_and_verified_manifest(self) -> None:
        result, outbox_root = self._write()

        self.assertEqual(2, result.file_count)
        self.assertTrue((result.job_dir / "manual.pdf").is_file())
        self.assertTrue((result.job_dir / "manual.docx").is_file())
        self.assertEqual(outbox_root, result.job_dir.parent)

        manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(
            delivery_outbox.DELIVERY_MANIFEST_SCHEMA_VERSION, manifest["schema_version"]
        )
        self.assertEqual(
            {
                "project_code": "HTE153",
                "safety_regulation": "欧英规",
                "languages": ["英语（美式）", "法语", "西班牙语", "德语", "意大利语"],
            },
            manifest["dingtalk_target"],
        )
        self.assertEqual(["rec_a", "rec_b"], manifest["source"]["queue_record_ids"])
        self.assertEqual("review/JE-1000F-EU", manifest["source"]["git_ref"])
        self.assertEqual("publish", manifest["source"]["workflow_action"])
        self.assertEqual(64, len(manifest["delivery_key"]))
        self.assertEqual({"manual.pdf", "manual.docx"}, {item["name"] for item in manifest["files"]})

    def test_manifest_carries_no_progress_field(self) -> None:
        """Progress belongs to the agent's status.json; a frozen field would lie."""

        result, _root = self._write()

        manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
        self.assertNotIn("status", manifest)

    def test_delivery_key_is_stable_for_the_same_payload(self) -> None:
        first, _root_a = self._write()
        second, _root_b = self._write()

        key_a = json.loads(first.manifest_path.read_text(encoding="utf-8"))["delivery_key"]
        key_b = json.loads(second.manifest_path.read_text(encoding="utf-8"))["delivery_key"]
        self.assertEqual(key_a, key_b)

    def test_delivery_key_changes_when_content_changes(self) -> None:
        first, _root_a = self._write()
        directory = Path(tempfile.mkdtemp())
        changed = _artifacts(directory / "build")
        changed[0].write_text("different bytes", encoding="utf-8")
        second, _root_b = self._write(files=changed)

        self.assertNotEqual(
            json.loads(first.manifest_path.read_text(encoding="utf-8"))["delivery_key"],
            json.loads(second.manifest_path.read_text(encoding="utf-8"))["delivery_key"],
        )

    def test_manifest_target_matches_the_delivery_map(self) -> None:
        result, _root = self._write()

        manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
        expected = resolve_delivery_target(model="JE-1000F", region="EU")
        self.assertEqual(expected.as_manifest_fields(), manifest["dingtalk_target"])

    def test_unmapped_target_raises_not_mapped_before_copying_anything(self) -> None:
        directory = Path(tempfile.mkdtemp())
        outbox_root = directory / "outbox"

        with self.assertRaises(DeliveryTargetNotMapped):
            delivery_outbox.write_delivery_outbox(
                outbox_root=outbox_root,
                model="JE-2000E",
                region="CN",
                version="0.8",
                git_ref="main",
                workflow_action="publish",
                built_at=BUILT_AT,
                files=_artifacts(directory / "build"),
            )

        self.assertFalse(outbox_root.exists())

    def test_missing_artifact_aborts_and_leaves_no_job(self) -> None:
        directory = Path(tempfile.mkdtemp())
        outbox_root = directory / "outbox"
        present = _artifacts(directory / "build", ("manual.pdf",))

        with self.assertRaises(RuntimeError) as ctx:
            delivery_outbox.write_delivery_outbox(
                outbox_root=outbox_root,
                model="JE-1000F",
                region="EU",
                version="0.8",
                git_ref="main",
                workflow_action="publish",
                built_at=BUILT_AT,
                files=[*present, directory / "build" / "never_built.pdf"],
            )

        self.assertIn("artifact is missing", str(ctx.exception))
        self.assertFalse(outbox_root.exists())

    def test_two_artifacts_with_one_basename_are_refused(self) -> None:
        """Copying both would silently leave one file behind two manifest rows."""

        directory = Path(tempfile.mkdtemp())
        first = _artifacts(directory / "build", ("manual.pdf",))[0]
        second = _artifacts(directory / "latex", ("manual.pdf",))[0]
        second.write_text("a different manual.pdf", encoding="utf-8")

        with self.assertRaises(RuntimeError) as ctx:
            delivery_outbox.write_delivery_outbox(
                outbox_root=directory / "outbox",
                model="JE-1000F",
                region="EU",
                version="0.8",
                git_ref="main",
                workflow_action="publish",
                built_at=BUILT_AT,
                files=[first, second],
            )

        self.assertIn("collide on one file name", str(ctx.exception))

    def test_verify_failure_leaves_no_consumable_job(self) -> None:
        """A rejected payload must not remain readable as a finished job."""

        directory = Path(tempfile.mkdtemp())
        outbox_root = directory / "outbox"
        files = _artifacts(directory / "build", ("manual.pdf",))

        with mock.patch.object(
            delivery_outbox,
            "verify_delivery_manifest",
            side_effect=RuntimeError("digest mismatch"),
        ):
            with self.assertRaises(RuntimeError):
                delivery_outbox.write_delivery_outbox(
                    outbox_root=outbox_root,
                    model="JE-1000F",
                    region="EU",
                    version="0.8",
                    git_ref="main",
                    workflow_action="publish",
                    built_at=BUILT_AT,
                    files=files,
                )

        self.assertEqual([], list(outbox_root.iterdir()))

    def test_copy_failure_leaves_no_partial_directory(self) -> None:
        directory = Path(tempfile.mkdtemp())
        outbox_root = directory / "outbox"
        files = _artifacts(directory / "build", ("manual.pdf", "manual.docx"))

        with mock.patch.object(
            delivery_outbox.shutil, "copy2", side_effect=OSError(28, "No space left")
        ):
            with self.assertRaises(OSError):
                delivery_outbox.write_delivery_outbox(
                    outbox_root=outbox_root,
                    model="JE-1000F",
                    region="EU",
                    version="0.8",
                    git_ref="main",
                    workflow_action="publish",
                    built_at=BUILT_AT,
                    files=files,
                )

        self.assertEqual([], list(outbox_root.iterdir()))

    def test_stale_partial_directory_is_reclaimed(self) -> None:
        directory = Path(tempfile.mkdtemp())
        outbox_root = directory / "outbox"
        job_id = delivery_outbox.build_job_id(
            model="JE-1000F", region="EU", version="0.8", built_at=BUILT_AT
        )
        stale = outbox_root / f"{job_id}{delivery_outbox.PARTIAL_JOB_SUFFIX}"
        stale.mkdir(parents=True)
        (stale / "leftover.txt").write_text("stale", encoding="utf-8")

        result, _root = self._write(outbox_root=outbox_root)

        self.assertFalse(stale.exists())
        self.assertFalse((result.job_dir / "leftover.txt").exists())

    def test_empty_file_list_is_rejected(self) -> None:
        with self.assertRaises(RuntimeError) as ctx:
            self._write(files=[])

        self.assertIn("at least one artifact", str(ctx.exception))

    def test_colliding_job_directory_is_refused(self) -> None:
        _first, outbox_root = self._write()
        directory = Path(tempfile.mkdtemp())

        with self.assertRaises(RuntimeError) as ctx:
            delivery_outbox.write_delivery_outbox(
                outbox_root=outbox_root,
                model="JE-1000F",
                region="EU",
                version="0.8",
                git_ref="main",
                workflow_action="publish",
                built_at=BUILT_AT,
                files=_artifacts(directory / "second", ("manual.pdf",)),
            )

        self.assertIn("already exists", str(ctx.exception))


class TestVerifyDeliveryManifest(unittest.TestCase):
    def _drop(self) -> delivery_outbox.DeliveryOutboxResult:
        directory = Path(tempfile.mkdtemp())
        return delivery_outbox.write_delivery_outbox(
            outbox_root=directory / "outbox",
            model="JE-1000F",
            region="JP",
            version="1.7",
            git_ref="main",
            workflow_action="publish",
            built_at=BUILT_AT,
            files=_artifacts(directory / "build", ("manual.pdf",)),
        )

    def _tamper(self, result: delivery_outbox.DeliveryOutboxResult, mutate) -> None:
        payload = json.loads(result.manifest_path.read_text(encoding="utf-8"))
        mutate(payload)
        result.manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    def test_verify_passes_on_a_fresh_drop(self) -> None:
        payload = delivery_outbox.verify_delivery_manifest(self._drop().manifest_path)

        self.assertEqual("日规", payload["dingtalk_target"]["safety_regulation"])
        self.assertEqual(["日语"], payload["dingtalk_target"]["languages"])

    def test_verify_detects_a_tampered_file(self) -> None:
        result = self._drop()
        (result.job_dir / "manual.pdf").write_text("tampered!!", encoding="utf-8")

        with self.assertRaises(RuntimeError) as ctx:
            delivery_outbox.verify_delivery_manifest(result.manifest_path)

        self.assertIn("digest mismatch", str(ctx.exception))

    def test_verify_detects_a_removed_file(self) -> None:
        result = self._drop()
        (result.job_dir / "manual.pdf").unlink()

        with self.assertRaises(RuntimeError) as ctx:
            delivery_outbox.verify_delivery_manifest(result.manifest_path)

        self.assertIn("missing declared file", str(ctx.exception))

    def test_verify_rejects_a_traversing_file_name(self) -> None:
        """A tampered name must not send verify reading arbitrary paths."""

        result = self._drop()
        self._tamper(result, lambda p: p["files"][0].update({"name": "../../etc/passwd"}))

        with self.assertRaises(RuntimeError) as ctx:
            delivery_outbox.verify_delivery_manifest(result.manifest_path)

        self.assertIn("plain file name", str(ctx.exception))

    def test_verify_rejects_a_missing_delivery_key(self) -> None:
        result = self._drop()
        self._tamper(result, lambda p: p.pop("delivery_key"))

        with self.assertRaises(RuntimeError) as ctx:
            delivery_outbox.verify_delivery_manifest(result.manifest_path)

        self.assertIn("no delivery_key", str(ctx.exception))

    def test_verify_rejects_a_stripped_dingtalk_target(self) -> None:
        result = self._drop()
        self._tamper(result, lambda p: p["dingtalk_target"].pop("safety_regulation"))

        with self.assertRaises(RuntimeError) as ctx:
            delivery_outbox.verify_delivery_manifest(result.manifest_path)

        self.assertIn("missing safety_regulation", str(ctx.exception))

    def test_verify_rejects_an_empty_language_list(self) -> None:
        result = self._drop()
        self._tamper(result, lambda p: p["dingtalk_target"].update({"languages": []}))

        with self.assertRaises(RuntimeError) as ctx:
            delivery_outbox.verify_delivery_manifest(result.manifest_path)

        self.assertIn("lists no languages", str(ctx.exception))

    def test_verify_rejects_a_stripped_source_block(self) -> None:
        result = self._drop()
        self._tamper(result, lambda p: p["source"].pop("region"))

        with self.assertRaises(RuntimeError) as ctx:
            delivery_outbox.verify_delivery_manifest(result.manifest_path)

        self.assertIn("source is missing region", str(ctx.exception))

    def test_verify_rejects_a_foreign_schema_version(self) -> None:
        result = self._drop()
        self._tamper(result, lambda p: p.update({"schema_version": 999}))

        with self.assertRaises(RuntimeError) as ctx:
            delivery_outbox.verify_delivery_manifest(result.manifest_path)

        self.assertIn("schema_version mismatch", str(ctx.exception))

    def test_cli_verifies_and_reports(self) -> None:
        result = self._drop()

        self.assertEqual(0, delivery_outbox.main(["--manifest", str(result.manifest_path)]))


if __name__ == "__main__":
    unittest.main()
