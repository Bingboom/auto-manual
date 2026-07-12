from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.manual_ir import build_manual_ir, read_manual_ir, validate_manual_ir, write_manual_ir
from tools.utils.path_utils import Paths, manual_ir_dir_of


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "tests" / "fixtures" / "idml_bundle"
DATA = ROOT / "tests" / "fixtures" / "phase2"


class ManualIRTests(unittest.TestCase):
    def _build(self, bundle: Path = BUNDLE):
        return build_manual_ir(
            root=ROOT,
            bundle_root=bundle,
            model="JE-1000F",
            region="US",
            lang="en",
            source="review",
            data_root=DATA,
        )

    def test_build_is_deterministic_and_valid(self) -> None:
        first = self._build()
        second = self._build()
        self.assertEqual(first, second)
        self.assertEqual([], validate_manual_ir(first))
        self.assertEqual(10, len(first.pages))
        self.assertGreater(first.metadata["block_count"], 20)
        self.assertRegex(first.content_sha256, r"^[0-9a-f]{64}$")
        self.assertRegex(first.bundle_sha256, r"^[0-9a-f]{64}$")

    def test_ids_and_source_refs_are_unique_and_stable(self) -> None:
        ir = self._build()
        page_ids = [page.page_id for page in ir.pages]
        block_ids = [block.block_id for page in ir.pages for block in page.blocks]
        source_refs = [block.source_ref for page in ir.pages for block in page.blocks]
        self.assertEqual(len(page_ids), len(set(page_ids)))
        self.assertEqual(len(block_ids), len(set(block_ids)))
        self.assertEqual(len(source_refs), len(set(source_refs)))
        self.assertEqual("page-0001-00_preface", page_ids[0])
        self.assertTrue(block_ids[0].startswith(page_ids[0] + ":block-"))

    def test_json_round_trip_preserves_hashes(self) -> None:
        ir = self._build()
        with tempfile.TemporaryDirectory() as td:
            path = write_manual_ir(ir, Path(td) / "manual.ir.json")
            loaded = read_manual_ir(path)
        self.assertEqual(ir, loaded)
        self.assertEqual([], validate_manual_ir(loaded))

    def test_content_mutation_is_detected(self) -> None:
        ir = self._build()
        raw = ir.to_dict()
        raw["pages"][0]["blocks"][0]["payload"] = "mutated without rehash"
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "bad.ir.json"
            path.write_text(json.dumps(raw), encoding="utf-8")
            loaded = read_manual_ir(path)
        issues = validate_manual_ir(loaded)
        self.assertTrue(any("content hash mismatch" in issue for issue in issues))

    def test_bundle_hash_changes_when_source_changes(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            copy = Path(td) / "bundle"
            for source in BUNDLE.rglob("*"):
                if source.is_file():
                    target = copy / source.relative_to(BUNDLE)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(source.read_bytes())
            before = self._build(copy)
            page = copy / "page" / "00_preface.rst"
            page.write_text(page.read_text(encoding="utf-8") + "\nChanged.\n", encoding="utf-8")
            after = self._build(copy)
        self.assertNotEqual(before.bundle_sha256, after.bundle_sha256)
        self.assertNotEqual(before.content_sha256, after.content_sha256)

    def test_path_helper_places_ir_beside_the_prepared_bundle(self) -> None:
        expected = BUNDLE.parent / "ir" / "manual.ir.json"
        self.assertEqual(BUNDLE.parent / "ir", manual_ir_dir_of(BUNDLE))
        self.assertEqual(expected, Paths.manual_ir_json_for(BUNDLE))

    def test_generated_data_page_macros_become_typed_ir(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            bundle = Path(td) / "rst"
            page_dir = bundle / "page"
            page_dir.mkdir(parents=True)
            (bundle / "index.rst").write_text(
                ".. include:: page/spec_en.rst\n"
                ".. include:: page/lcd_icons_en.rst\n"
                ".. include:: page/symbols_en.rst\n",
                encoding="utf-8",
            )
            (page_dir / "spec_en.rst").write_text(
                ".. raw:: latex\n\n"
                "   \\HBSpecPageStart \\section{SPECIFICATIONS}\n\n"
                ".. raw:: latex\n\n"
                "   \\specsectiontitle{INPUT PORTS}\n"
                "   \\begin{spectable}\n"
                "   \\HBTypeSpecLabel{AC Input} & "
                "\\HBTypeSpecValue{120 V\\textasciitilde{} 60 Hz} \\tabularnewline\n"
                "   \\end{spectable}\n\n"
                ".. raw:: latex\n\n"
                "   \\HBTypeSpecNote{\\HBSpecMarkerOne{} Note text}\\par\n\n"
                ".. raw:: latex\n\n"
                "   \\HBSpecPageEnd\n",
                encoding="utf-8",
            )
            (page_dir / "lcd_icons_en.rst").write_text(
                ".. raw:: latex\n\n"
                "   \\begin{HBLcdIconTable}\n"
                "   \\HBLcdIconRow{1}{wifi.png}{Wi-Fi}"
                "{\\textbf{On:} Connected. \\newline \\textbf{Off:} Disconnected.}\n"
                "   \\end{HBLcdIconTable}\n",
                encoding="utf-8",
            )
            (page_dir / "symbols_en.rst").write_text(
                ".. raw:: latex\n\n"
                "   \\HBSymbolTable{Symbol}{Meaning}{%\n"
                "   \\HBSymbolSignalRow{warning.png}{WARNING}{Read this.}\n"
                "   }\n\n"
                ".. raw:: latex\n\n"
                "   \\HBSymbolTwoColumnTables{Symbol}{Meaning}{%\n"
                "   \\HBSymbolIconRow{manual.png}{Read the manual.}\n"
                "   }{%\n"
                "   \\HBSymbolIconRow{fire.png}{Keep away from fire.}\n"
                "   }\n",
                encoding="utf-8",
            )
            ir = self._build(bundle)

        self.assertEqual(0, ir.metadata["skipped_raw"])
        payloads = [
            block.payload for page in ir.pages for block in page.blocks
            if block.kind == "data"
        ]
        self.assertEqual(
            ["spec_start", "spec_section", "spec_annotations", "lcd_icons",
             "symbol_signals", "symbol_icons"],
            [payload["kind"] for payload in payloads],
        )
        self.assertEqual("120 V~ 60 Hz", payloads[1]["rows"][0][1])
        self.assertEqual("On: Connected.\nOff: Disconnected.", payloads[3]["rows"][0]["desc"])
        self.assertEqual(
            ["wifi.png", "warning.png", "manual.png", "fire.png"],
            list(ir.asset_refs),
        )


if __name__ == "__main__":
    unittest.main()
