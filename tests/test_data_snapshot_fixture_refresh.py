from __future__ import annotations

import csv
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from tools.data_snapshot_fixture_refresh import (
    refresh_fixture_by_document_key,
    row_matches_document_key,
)


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\r\n")
    writer.writeheader()
    writer.writerows(row for row in rows)
    path.write_text(output.getvalue(), encoding="utf-8")


def _manifest_for(path: Path) -> dict[str, object]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        row_count = sum(1 for _ in csv.DictReader(handle))
    return {
        "export_root": "tests/fixtures/phase2",
        "manifest_path": "tests/fixtures/phase2/snapshot_manifest.json",
        "requested_tables": ["spec_master"],
        "skipped_tables": [],
        "tables": [
            {
                "logical_name": "spec_master",
                "file_name": path.name,
                "row_count": row_count,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "previous_sha256": None,
                "changed": True,
            }
        ],
        "derived_files": [],
    }


class TestFixtureRefresh(unittest.TestCase):
    def test_row_matching_supports_target_lists_and_global_rows(self) -> None:
        fields = ["Model", "Region", "value"]
        self.assertTrue(row_matches_document_key(
            {"Model": "M1, M2", "Region": "US, EU", "value": "target"},
            fields,
            "M1_US",
        ))
        self.assertTrue(row_matches_document_key(
            {"Model": "ALL", "Region": "ALL", "value": "shared"},
            fields,
            "M1_US",
        ))
        self.assertFalse(row_matches_document_key(
            {"Model": "M2", "Region": "JP", "value": "other"},
            fields,
            "M1_US",
        ))
        self.assertTrue(row_matches_document_key(
            {"Model": "M1", "Region": "US", "value": "localized"},
            fields,
            "M1_US_en",
        ))

    def test_refresh_is_dry_run_safe_and_isolates_other_document_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            fixture = root / "fixture"
            source.mkdir()
            fixture.mkdir()
            fields = ["document_key", "value"]
            _write_csv(source / "Spec_Master.csv", fields, [
                {"document_key": "M1_US", "value": "new"},
                {"document_key": "M2_JP", "value": "source-jp"},
            ])
            _write_csv(fixture / "Spec_Master.csv", fields, [
                {"document_key": "M1_US", "value": "old"},
                {"document_key": "M2_JP", "value": "fixture-jp"},
            ])
            manifest = _manifest_for(fixture / "Spec_Master.csv")
            (fixture / "snapshot_manifest.json").write_text(
                json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
            )
            before = (fixture / "Spec_Master.csv").read_bytes()

            dry_run = refresh_fixture_by_document_key(
                source_root=source,
                fixture_root=fixture,
                document_key="M1_US",
                write=False,
            )
            self.assertTrue(dry_run.dry_run)
            self.assertIn("Spec_Master.csv", dry_run.changed_files)
            self.assertTrue(dry_run.manifest_changed)
            self.assertIn("snapshot_manifest.json", dry_run.changed_files)
            self.assertEqual(before, (fixture / "Spec_Master.csv").read_bytes())

            written = refresh_fixture_by_document_key(
                source_root=source,
                fixture_root=fixture,
                document_key="M1_US",
                write=True,
            )
            self.assertFalse(written.dry_run)
            with (fixture / "Spec_Master.csv").open(encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(
                rows,
                [
                    {"document_key": "M1_US", "value": "new"},
                    {"document_key": "M2_JP", "value": "fixture-jp"},
                ],
            )
            refreshed_manifest = json.loads(
                (fixture / "snapshot_manifest.json").read_text(encoding="utf-8")
            )
            entry = refreshed_manifest["tables"][0]
            self.assertEqual(entry["sha256"], hashlib.sha256(
                (fixture / "Spec_Master.csv").read_bytes()
            ).hexdigest())
            self.assertEqual(entry["row_count"], 2)

    def test_refresh_is_idempotent_after_first_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            fixture = root / "fixture"
            source.mkdir()
            fixture.mkdir()
            fields = ["document_key", "value"]
            _write_csv(source / "Spec_Master.csv", fields, [{"document_key": "M1_US", "value": "same"}])
            _write_csv(fixture / "Spec_Master.csv", fields, [{"document_key": "M1_US", "value": "old"}])
            (fixture / "snapshot_manifest.json").write_text(
                json.dumps(_manifest_for(fixture / "Spec_Master.csv"), indent=2) + "\n",
                encoding="utf-8",
            )
            refresh_fixture_by_document_key(
                source_root=source, fixture_root=fixture, document_key="M1_US", write=True
            )
            before = {
                "csv": (fixture / "Spec_Master.csv").read_bytes(),
                "manifest": (fixture / "snapshot_manifest.json").read_bytes(),
            }
            second = refresh_fixture_by_document_key(
                source_root=source, fixture_root=fixture, document_key="M1_US", write=True
            )
            self.assertEqual(second.changed_files, ())
            self.assertEqual(before["csv"], (fixture / "Spec_Master.csv").read_bytes())
            self.assertEqual(before["manifest"], (fixture / "snapshot_manifest.json").read_bytes())


if __name__ == "__main__":
    unittest.main()
