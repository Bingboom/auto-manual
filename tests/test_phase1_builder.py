from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.phase1.builder import BuildPaths, BuildSelector, Phase1Builder


class TestPhase1BuilderNormalization(unittest.TestCase):
    def test_build_paths_from_root_should_use_phase1_spec_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            paths = BuildPaths.from_root(root)
            self.assertEqual(root / "data" / "phase1" / "Spec_Master.csv", paths.spec_master_csv)
            self.assertEqual(root / "data" / "phase1" / "Spec_Footnotes.csv", paths.spec_footnotes_csv)
            self.assertEqual(root / "data" / "phase1" / "Spec_Notes.csv", paths.spec_notes_csv)
            self.assertEqual(root / "data" / "phase1" / "spec_titles.csv", paths.spec_titles_csv)
            self.assertEqual(root / "data" / "phase1", paths.page_blocks_dir)

    def test_spec_master_rows_can_be_detected(self) -> None:
        rows = [
            {
                "Section": "GENERAL INFO",
                "Row_key": "product_name",
                "Line_order": "1",
                "Value_source": "Demo",
            }
        ]
        self.assertTrue(Phase1Builder._looks_like_spec_master_rows(rows))

    def test_load_spec_prefers_configured_spec_master_source(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            spec_master_csv = root / "data" / "phase1" / "Spec_Master.csv"
            spec_master_csv.parent.mkdir(parents=True, exist_ok=True)

            csv_head = "Section,Row_key,Line_order,Value_source\n"
            spec_master_csv.write_text(
                csv_head + "GENERAL INFO,draft_row,1,draft\n",
                encoding="utf-8",
            )

            paths = BuildPaths(
                root=root,
                page_registry=root / "dummy_registry.csv",
                page_blocks_dir=root / "data" / "phase1",
                template_dir=root / "docs" / "templates",
                output_dir=root / "docs" / "generated",
                spec_master_csv=spec_master_csv,
                spec_footnotes_csv=spec_master_csv.parent / "Spec_Footnotes.csv",
            )
            builder = Phase1Builder(paths)
            rows = builder._load_page_blocks("spec")
            self.assertEqual("draft_row", rows[0]["Row_key"])

    def test_load_spec_merges_configured_footnotes_csv(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            spec_master_csv = root / "data" / "phase1" / "Spec_Master.csv"
            spec_footnotes_csv = root / "data" / "phase1" / "Spec_Footnotes.csv"
            spec_notes_csv = root / "data" / "phase1" / "Spec_Notes.csv"
            spec_master_csv.parent.mkdir(parents=True, exist_ok=True)

            spec_master_csv.write_text(
                "Section,Row_key,Line_order,Value_source\n"
                "GENERAL INFO,draft_row,1,draft\n",
                encoding="utf-8",
            )
            spec_footnotes_csv.write_text(
                "Region,Model,Source_lang,Is_Latest,Page,Footnote_id,Footnote_order,Text_en,Enabled\n"
                "US,DEMO-1000,en,TRUE,specifications,demo_ref,1,Demo footnote from dedicated csv,TRUE\n",
                encoding="utf-8",
            )
            spec_notes_csv.write_text(
                "Region,Model,Source_lang,Is_Latest,Page,Note_id,Note_order,Text_en,Enabled\n"
                "US,DEMO-1000,en,TRUE,specifications,demo_note,2,Demo note from dedicated csv,TRUE\n",
                encoding="utf-8",
            )

            paths = BuildPaths(
                root=root,
                page_registry=root / "dummy_registry.csv",
                page_blocks_dir=root / "data" / "phase1",
                template_dir=root / "docs" / "templates",
                output_dir=root / "docs" / "generated",
                spec_master_csv=spec_master_csv,
                spec_footnotes_csv=spec_footnotes_csv,
                spec_notes_csv=spec_notes_csv,
            )
            builder = Phase1Builder(paths)
            rows = builder._load_page_blocks("spec")
            self.assertTrue(any(row.get("footnote_id") == "demo_ref" for row in rows))
            self.assertTrue(any(row.get("note_id") == "demo_note" for row in rows))

    def test_load_spec_keeps_master_rows_when_titles_csv_is_configured(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            spec_master_csv = root / "data" / "phase1" / "Spec_Master.csv"
            spec_titles_csv = root / "data" / "phase1" / "spec_titles.csv"
            spec_master_csv.parent.mkdir(parents=True, exist_ok=True)

            spec_master_csv.write_text(
                "Section,Row_key,Line_order,Value_source\n"
                "GENERAL INFO,draft_row,1,draft\n",
                encoding="utf-8",
            )
            spec_titles_csv.write_text(
                "title_en,title_jp\n"
                "SPECIFICATIONS,涓汇仾浠曟\n",
                encoding="utf-8",
            )

            paths = BuildPaths(
                root=root,
                page_registry=root / "dummy_registry.csv",
                page_blocks_dir=root / "data" / "phase1",
                template_dir=root / "docs" / "templates",
                output_dir=root / "docs" / "generated",
                spec_master_csv=spec_master_csv,
                spec_footnotes_csv=None,
                spec_titles_csv=spec_titles_csv,
            )
            builder = Phase1Builder(paths)
            rows = builder._load_page_blocks("spec")
            self.assertEqual(1, len(rows))
            self.assertEqual("draft_row", rows[0]["Row_key"])

    def test_select_targets_supports_model_and_region_filters(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            paths = BuildPaths(
                root=root,
                page_registry=root / "dummy_registry.csv",
                page_blocks_dir=root / "data" / "phase1",
                template_dir=root / "docs" / "templates",
                output_dir=root / "docs" / "generated",
                spec_master_csv=root / "data" / "phase1" / "Spec_Master.csv",
            )
            builder = Phase1Builder(paths)
            selector = BuildSelector(models={"JHP-2000A"}, regions={"US"})
            targets = builder._select_targets(selector)

            self.assertEqual(1, len(targets))
            target_key, vars_map = targets[0]
            self.assertEqual("JHP-2000A", target_key)
            self.assertEqual("JHP-2000A", vars_map.get("model"))
            self.assertEqual("US", vars_map.get("region"))

    def test_select_targets_uses_default_target_without_model_or_region(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            paths = BuildPaths(
                root=root,
                page_registry=root / "dummy_registry.csv",
                page_blocks_dir=root / "data" / "phase1",
                template_dir=root / "docs" / "templates",
                output_dir=root / "docs" / "generated",
                spec_master_csv=root / "data" / "phase1" / "Spec_Master.csv",
            )
            builder = Phase1Builder(paths)
            self.assertEqual([("default", {})], builder._select_targets(BuildSelector()))


if __name__ == "__main__":
    unittest.main()
