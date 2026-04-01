from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.data_snapshot import resolve_data_snapshot_paths, resolve_phase2_export_root, resolve_phase2_manifest_path


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
            self.assertEqual(root / "data" / "page-blocks", paths.page_blocks_dir)
            self.assertEqual(root / "data" / "phase1" / "page_registry.csv", paths.page_registry_csv)

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
