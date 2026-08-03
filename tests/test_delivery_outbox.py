from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
import unittest

from tools import delivery_outbox
from tools.dingtalk_delivery_map import resolve_delivery_target


BUILT_AT = datetime(2026, 8, 3, 14, 30, 5, tzinfo=timezone.utc)


def _artifacts(directory: Path, names: tuple[str, ...] = ("manual.pdf", "manual.docx")) -> list[Path]:
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
            model="JE-1000F", region="EU", lang="fr", version="0.8", built_at=BUILT_AT
        )

        self.assertTrue(job_id.startswith("JE-1000F_EU_fr_0.8_"))
        self.assertEqual(
            job_id,
            delivery_outbox.build_job_id(
                model="JE-1000F", region="EU", lang="fr", version="0.8", built_at=BUILT_AT
            ),
        )

    def test_job_id_differs_when_build_time_differs(self) -> None:
        later = delivery_outbox.build_job_id(
            model="JE-1000F",
            region="EU",
            lang="fr",
            version="0.8",
            built_at=BUILT_AT + timedelta(seconds=1),
        )
        earlier = delivery_outbox.build_job_id(
            model="JE-1000F", region="EU", lang="fr", version="0.8", built_at=BUILT_AT
        )

        self.assertNotEqual(earlier, later)

    def test_path_traversal_segments_are_rejected(self) -> None:
        for field, payload in (
            ("model", "../escape"),
            ("region", "EU/../.."),
            ("lang", "fr fr"),
            ("version", ""),
        ):
            kwargs = {
                "model": "JE-1000F",
                "region": "EU",
                "lang": "fr",
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
        payload = {
            "outbox_root": outbox_root,
            "model": "JE-1000F",
            "region": "EU",
            "lang": "fr",
            "version": "0.8",
            "git_ref": "review/JE-1000F-EU",
            "workflow_action": "publish",
            "built_at": BUILT_AT,
            "queue_record_ids": ("rec_a", "rec_b"),
            "document_link_url": "https://feishu.example.com/wiki/manual",
            "files": _artifacts(directory),
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
        self.assertEqual(delivery_outbox.DELIVERY_MANIFEST_SCHEMA_VERSION, manifest["schema_version"])
        self.assertEqual("pending", manifest["status"])
        self.assertEqual(
            {"project_code": "HTE153", "safety_regulation": "欧英规", "language": "法语"},
            manifest["dingtalk_target"],
        )
        self.assertEqual(["rec_a", "rec_b"], manifest["source"]["queue_record_ids"])
        self.assertEqual("review/JE-1000F-EU", manifest["source"]["git_ref"])
        self.assertEqual("publish", manifest["source"]["workflow_action"])
        self.assertEqual({"manual.pdf", "manual.docx"}, {item["name"] for item in manifest["files"]})
        for item in manifest["files"]:
            self.assertEqual(64, len(item["sha256"]))
            self.assertGreater(item["size"], 0)

    def test_manifest_target_matches_the_delivery_map(self) -> None:
        result, _root = self._write()

        manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
        expected = resolve_delivery_target(model="JE-1000F", region="EU", lang="fr")
        self.assertEqual(expected.as_manifest_fields(), manifest["dingtalk_target"])

    def test_unmapped_target_aborts_before_copying_anything(self) -> None:
        with self.assertRaises(RuntimeError) as ctx:
            self._write(lang="uk")

        self.assertIn("no entry for", str(ctx.exception))

    def test_unmapped_target_leaves_no_partial_job_dir(self) -> None:
        directory = Path(tempfile.mkdtemp())
        outbox_root = directory / "outbox"
        with self.assertRaises(RuntimeError):
            delivery_outbox.write_delivery_outbox(
                outbox_root=outbox_root,
                model="JE-1000F",
                region="EU",
                lang="uk",
                version="0.8",
                git_ref="main",
                workflow_action="publish",
                built_at=BUILT_AT,
                files=_artifacts(directory),
            )

        self.assertFalse(outbox_root.exists())

    def test_missing_artifact_aborts_and_leaves_no_manifest(self) -> None:
        directory = Path(tempfile.mkdtemp())
        outbox_root = directory / "outbox"
        present = _artifacts(directory, ("manual.pdf",))
        absent = directory / "never_built.pdf"

        with self.assertRaises(RuntimeError) as ctx:
            delivery_outbox.write_delivery_outbox(
                outbox_root=outbox_root,
                model="JE-1000F",
                region="EU",
                lang="fr",
                version="0.8",
                git_ref="main",
                workflow_action="publish",
                built_at=BUILT_AT,
                files=[*present, absent],
            )

        self.assertIn("artifact is missing", str(ctx.exception))
        self.assertFalse(any(outbox_root.rglob(delivery_outbox.DELIVERY_MANIFEST_FILENAME)))

    def test_empty_file_list_is_rejected(self) -> None:
        with self.assertRaises(RuntimeError) as ctx:
            self._write(files=[])

        self.assertIn("at least one artifact", str(ctx.exception))

    def test_colliding_job_directory_is_refused(self) -> None:
        _first, outbox_root = self._write()
        second_source = Path(tempfile.mkdtemp()) / "second"
        second_source.mkdir(parents=True)

        with self.assertRaises(RuntimeError) as ctx:
            delivery_outbox.write_delivery_outbox(
                outbox_root=outbox_root,
                model="JE-1000F",
                region="EU",
                lang="fr",
                version="0.8",
                git_ref="main",
                workflow_action="publish",
                built_at=BUILT_AT,
                files=_artifacts(second_source, ("manual.pdf",)),
            )

        self.assertIn("already exists", str(ctx.exception))


class TestVerifyDeliveryManifest(unittest.TestCase):
    def _drop(self) -> delivery_outbox.DeliveryOutboxResult:
        directory = Path(tempfile.mkdtemp())
        return delivery_outbox.write_delivery_outbox(
            outbox_root=directory / "outbox",
            model="JE-1000F",
            region="JP",
            lang="ja",
            version="1.7",
            git_ref="main",
            workflow_action="publish",
            built_at=BUILT_AT,
            files=_artifacts(directory, ("manual.pdf",)),
        )

    def test_verify_passes_on_a_fresh_drop(self) -> None:
        result = self._drop()

        payload = delivery_outbox.verify_delivery_manifest(result.manifest_path)

        self.assertEqual("pending", payload["status"])
        self.assertEqual("日规", payload["dingtalk_target"]["safety_regulation"])

    def test_verify_detects_a_tampered_file(self) -> None:
        result = self._drop()
        (result.job_dir / "manual.pdf").write_text("tampered", encoding="utf-8")

        with self.assertRaises(RuntimeError) as ctx:
            delivery_outbox.verify_delivery_manifest(result.manifest_path)

        self.assertIn("digest mismatch", str(ctx.exception))

    def test_verify_detects_a_removed_file(self) -> None:
        result = self._drop()
        (result.job_dir / "manual.pdf").unlink()

        with self.assertRaises(RuntimeError) as ctx:
            delivery_outbox.verify_delivery_manifest(result.manifest_path)

        self.assertIn("missing declared file", str(ctx.exception))

    def test_verify_rejects_a_foreign_schema_version(self) -> None:
        result = self._drop()
        payload = json.loads(result.manifest_path.read_text(encoding="utf-8"))
        payload["schema_version"] = 999
        result.manifest_path.write_text(json.dumps(payload), encoding="utf-8")

        with self.assertRaises(RuntimeError) as ctx:
            delivery_outbox.verify_delivery_manifest(result.manifest_path)

        self.assertIn("schema_version mismatch", str(ctx.exception))

    def test_cli_verifies_and_reports(self) -> None:
        result = self._drop()

        self.assertEqual(0, delivery_outbox.main(["--manifest", str(result.manifest_path)]))


if __name__ == "__main__":
    unittest.main()
