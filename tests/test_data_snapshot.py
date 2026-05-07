from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.data_snapshot import (
    inspect_phase2_snapshot,
    resolve_data_snapshot_paths,
    resolve_phase2_export_root,
    resolve_phase2_manifest_path,
)


def _complete_manifest() -> dict[str, object]:
    required_tables = [
        "spec_master",
        "spec_footnotes",
        "spec_notes",
        "spec_titles",
        "symbols_blocks",
    ]
    return {
        "export_root": "data/phase2",
        "requested_tables": required_tables,
        "skipped_tables": [],
        "tables": [
            {"logical_name": table_name, "file_name": file_name}
            for table_name, file_name in (
                ("spec_master", "Spec_Master.csv"),
                ("spec_footnotes", "Spec_Footnotes.csv"),
                ("spec_notes", "Spec_Notes.csv"),
                ("spec_titles", "spec_titles.csv"),
                ("symbols_blocks", "symbols_blocks.csv"),
            )
        ],
        "derived_files": [
            {"logical_name": "row_key_mapping", "file_name": "row_key_mapping.csv"},
        ],
    }


class TestDataSnapshotPaths(unittest.TestCase):
    def test_resolve_data_snapshot_paths_should_prefer_data_root_for_structured_files(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cfg = {
                "paths": {
                    "structured_data_dir": "data/phaseX",
                    "spec_master_csv": "custom/Spec_Master.csv",
                    "page_registry_csv": "custom/page_registry.csv",
                }
            }

            paths = resolve_data_snapshot_paths(
                cfg,
                repo_root=root,
                data_root="data/phase2",
            )

            self.assertEqual(root / "data" / "phase2" / "Spec_Master.csv", paths.spec_master_csv)
            self.assertEqual(root / "data" / "phase2" / "Spec_Footnotes.csv", paths.spec_footnotes_csv)
            self.assertEqual(root / "data" / "phase2" / "row_key_mapping.csv", paths.row_key_mapping_csv)
            self.assertEqual(root / "data" / "phase2", paths.page_blocks_dir)
            self.assertEqual(root / "custom" / "page_registry.csv", paths.page_registry_csv)

    def test_resolve_data_snapshot_paths_should_use_configured_dirs_without_data_root(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cfg = {
                "paths": {
                    "structured_data_dir": "data/phase2",
                    "page_blocks_dir": "data/page-blocks",
                }
            }

            paths = resolve_data_snapshot_paths(cfg, repo_root=root)

            self.assertEqual(root / "data" / "phase2" / "Spec_Master.csv", paths.spec_master_csv)
            self.assertEqual(root / "data" / "phase2" / "row_key_mapping.csv", paths.row_key_mapping_csv)
            self.assertEqual(root / "data" / "page-blocks", paths.page_blocks_dir)
            self.assertEqual(root / "data" / "phase1" / "page_registry.csv", paths.page_registry_csv)

    def test_resolve_data_snapshot_paths_should_prefer_valid_phase2_snapshot_without_data_root(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            phase1_dir = root / "data" / "phase1"
            phase2_dir = root / "data" / "phase2"
            phase1_dir.mkdir(parents=True)
            phase2_dir.mkdir(parents=True)
            (phase1_dir / "page_registry.csv").write_text("page_id\nspec\n", encoding="utf-8")
            for file_name in (
                "Spec_Master.csv",
                "Spec_Footnotes.csv",
                "Spec_Notes.csv",
                "spec_titles.csv",
                "row_key_mapping.csv",
                "symbols_blocks.csv",
            ):
                (phase2_dir / file_name).write_text("demo\n", encoding="utf-8")
            (phase2_dir / "snapshot_manifest.json").write_text(
                json.dumps(_complete_manifest(), ensure_ascii=False),
                encoding="utf-8",
            )
            cfg = {
                "paths": {
                    "structured_data_dir": "data/phase1",
                }
            }

            paths = resolve_data_snapshot_paths(cfg, repo_root=root)

            self.assertEqual(root / "data" / "phase2" / "Spec_Master.csv", paths.spec_master_csv)
            self.assertEqual(root / "data" / "phase2", paths.structured_data_dir)
            self.assertEqual(root / "data" / "phase2", paths.page_blocks_dir)
            self.assertEqual(root / "data" / "phase1" / "page_registry.csv", paths.page_registry_csv)

    def test_resolve_data_snapshot_paths_should_fallback_when_phase2_snapshot_is_incomplete(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            phase1_dir = root / "data" / "phase1"
            phase2_dir = root / "data" / "phase2"
            phase1_dir.mkdir(parents=True)
            phase2_dir.mkdir(parents=True)
            (phase1_dir / "Spec_Master.csv").write_text("phase1\n", encoding="utf-8")
            (phase1_dir / "Spec_Footnotes.csv").write_text("phase1\n", encoding="utf-8")
            (phase1_dir / "Spec_Notes.csv").write_text("phase1\n", encoding="utf-8")
            (phase1_dir / "spec_titles.csv").write_text("phase1\n", encoding="utf-8")
            (phase1_dir / "row_key_mapping.csv").write_text("phase1\n", encoding="utf-8")
            (phase1_dir / "page_registry.csv").write_text("page_id\nspec\n", encoding="utf-8")
            (phase2_dir / "snapshot_manifest.json").write_text(
                json.dumps({"export_root": "data/phase2"}, ensure_ascii=False),
                encoding="utf-8",
            )
            cfg = {
                "paths": {
                    "structured_data_dir": "data/phase1",
                }
            }

            paths = resolve_data_snapshot_paths(cfg, repo_root=root)

            self.assertEqual(root / "data" / "phase1" / "Spec_Master.csv", paths.spec_master_csv)
            self.assertEqual(root / "data" / "phase1", paths.structured_data_dir)

    def test_resolve_data_snapshot_paths_should_fallback_when_manifest_skips_required_table(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            phase1_dir = root / "data" / "phase1"
            phase2_dir = root / "data" / "phase2"
            phase1_dir.mkdir(parents=True)
            phase2_dir.mkdir(parents=True)
            (phase1_dir / "Spec_Master.csv").write_text("phase1\n", encoding="utf-8")
            (phase1_dir / "page_registry.csv").write_text("page_id\nspec\n", encoding="utf-8")
            for file_name in (
                "Spec_Master.csv",
                "Spec_Footnotes.csv",
                "Spec_Notes.csv",
                "spec_titles.csv",
                "row_key_mapping.csv",
                "symbols_blocks.csv",
            ):
                (phase2_dir / file_name).write_text("phase2\n", encoding="utf-8")
            manifest = _complete_manifest()
            manifest["requested_tables"] = ["spec_master"]
            manifest["skipped_tables"] = [
                "spec_footnotes",
                "spec_notes",
                "spec_titles",
                "symbols_blocks",
            ]
            manifest["tables"] = [
                {"logical_name": "spec_master", "file_name": "Spec_Master.csv"},
            ]
            (phase2_dir / "snapshot_manifest.json").write_text(
                json.dumps(manifest, ensure_ascii=False),
                encoding="utf-8",
            )
            cfg = {
                "paths": {
                    "structured_data_dir": "data/phase1",
                }
            }

            status = inspect_phase2_snapshot(cfg, repo_root=root)
            paths = resolve_data_snapshot_paths(cfg, repo_root=root)

            self.assertFalse(status.valid)
            self.assertTrue(
                any("skipped required table" in issue for issue in status.issues),
                status.issues,
            )
            self.assertEqual(root / "data" / "phase1" / "Spec_Master.csv", paths.spec_master_csv)

    def test_phase2_export_root_should_default_to_phase2_even_when_structured_data_dir_points_to_phase1(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cfg = {
                "paths": {
                    "structured_data_dir": "data/phase1",
                }
            }

            export_root = resolve_phase2_export_root(cfg, repo_root=root)
            manifest_path = resolve_phase2_manifest_path(cfg, repo_root=root)

            self.assertEqual(root / "data" / "phase2", export_root)
            self.assertEqual(root / "data" / "phase2" / "snapshot_manifest.json", manifest_path)

    def test_phase2_export_root_and_manifest_should_use_sync_config(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cfg = {
                "sync": {
                    "phase2": {
                        "export_root": "exports/phase2",
                        "manifest_path": "exports/phase2/custom-manifest.json",
                    }
                }
            }

            export_root = resolve_phase2_export_root(cfg, repo_root=root)
            manifest_path = resolve_phase2_manifest_path(cfg, repo_root=root)

            self.assertEqual(root / "exports" / "phase2", export_root)
            self.assertEqual(root / "exports" / "phase2" / "custom-manifest.json", manifest_path)


if __name__ == "__main__":
    unittest.main()
