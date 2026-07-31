from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from tools.release_snapshot import freeze_release_snapshot, verify_frozen_release_snapshot


class ReleaseSnapshotTests(unittest.TestCase):
    def _copy_fixture(self, root: Path) -> Path:
        source = Path(__file__).parent / "fixtures" / "phase2"
        destination = root / "data" / "phase2"
        shutil.copytree(source, destination)
        return destination

    def test_freeze_should_archive_complete_snapshot_and_be_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = self._copy_fixture(root)
            destination = root / "reports" / "releases" / "M" / "US" / "en" / "versions" / "1.0" / "snapshot"
            first_time = datetime(2026, 7, 31, 1, 2, tzinfo=timezone.utc)

            first = freeze_release_snapshot(
                cfg={},
                repo_root=root,
                data_root=source,
                model="M",
                region="US",
                languages=["en", "es"],
                snapshot_dir=destination,
                frozen_at=first_time,
            )
            second = freeze_release_snapshot(
                cfg={},
                repo_root=root,
                data_root=source,
                model="M",
                region="US",
                languages=["en", "es"],
                snapshot_dir=destination,
                frozen_at=datetime(2026, 8, 1, tzinfo=timezone.utc),
            )

            self.assertEqual(first.identity, second.identity)
            self.assertEqual(first_time.isoformat(), second.identity["frozen_at"])
            self.assertEqual(
                [
                    {"model": "M", "region": "US", "lang": "en"},
                    {"model": "M", "region": "US", "lang": "es"},
                ],
                first.identity["target_matrix"],
            )
            source_manifest = source / "snapshot_manifest.json"
            self.assertEqual(
                hashlib.sha256(source_manifest.read_bytes()).hexdigest(),
                first.identity["source_revision"]["value"],
            )
            self.assertTrue((destination / "Spec_Master.csv").exists())
            self.assertTrue((destination / "_attachments" / "symbols").is_dir())

    def test_freeze_should_refuse_rebinding_or_archive_drift(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = self._copy_fixture(root)
            destination = root / "release" / "snapshot"
            original_spec_master = (source / "Spec_Master.csv").read_bytes()
            freeze_release_snapshot(
                cfg={},
                repo_root=root,
                data_root=source,
                model="M",
                region="US",
                languages=["en"],
                snapshot_dir=destination,
            )

            (source / "Spec_Master.csv").write_text("changed\n", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "immutable"):
                freeze_release_snapshot(
                    cfg={},
                    repo_root=root,
                    data_root=source,
                    model="M",
                    region="US",
                    languages=["en"],
                    snapshot_dir=destination,
                )

            (source / "Spec_Master.csv").write_bytes(original_spec_master)
            (destination / "Spec_Footnotes.csv").write_text("drift\n", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "drifted"):
                freeze_release_snapshot(
                    cfg={},
                    repo_root=root,
                    data_root=source,
                    model="M",
                    region="US",
                    languages=["en"],
                    snapshot_dir=destination,
                )

    def test_identity_should_be_valid_json(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = self._copy_fixture(root)
            frozen = freeze_release_snapshot(
                cfg={},
                repo_root=root,
                data_root=source,
                model="M",
                region="US",
                languages=["en"],
                snapshot_dir=root / "release" / "snapshot",
            )

            self.assertEqual(frozen.identity, json.loads(frozen.identity_path.read_text(encoding="utf-8")))

    def test_verify_should_bind_manifest_identity_and_archived_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = self._copy_fixture(root)
            frozen = freeze_release_snapshot(
                cfg={},
                repo_root=root,
                data_root=source,
                model="M",
                region="US",
                languages=["en"],
                snapshot_dir=root / "release" / "snapshot",
            )
            matrix = [{"model": "M", "region": "US", "lang": "en"}]

            verified = verify_frozen_release_snapshot(
                frozen.snapshot_dir,
                expected_sha256=frozen.identity["snapshot_sha256"],
                expected_target_matrix=matrix,
            )
            self.assertEqual(frozen.identity, verified)

            (frozen.snapshot_dir / "Spec_Notes.csv").write_text("drift\n", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "drifted"):
                verify_frozen_release_snapshot(
                    frozen.snapshot_dir,
                    expected_sha256=frozen.identity["snapshot_sha256"],
                    expected_target_matrix=matrix,
                )


if __name__ == "__main__":
    unittest.main()
