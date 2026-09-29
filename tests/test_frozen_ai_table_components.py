"""Frozen extracted copy survives registered component assembly and replay."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from bs4 import BeautifulSoup

from tools.component_specs.registry import load_component_registry, registry_sha256
from tools.component_specs.model import ComponentSpec
from tools.component_specs.theme import load_manual_theme, theme_sha256
from tools.frozen_ai_table_components import (
    lcd_mode_flow,
    specification_flow,
    symbol_pictogram_flow,
    symbol_signal_flow,
    troubleshooting_flow,
    warranty_flow,
)
from tools.manual_ir import (
    ManualSource, SourcePage, V2_SCHEMA_VERSION, build_manual_ir_from_source,
    read_manual_ir, write_manual_ir,
)
from tools.manual_ir.components import component_specs_in_flow
from tools.manual_ir.hashing import value_sha256
from tools.web_document_ir import render_document_fragments
from tools.web_manual_table_components import render_manual_table_component


ROOT = Path(__file__).resolve().parents[1]
FROZEN = ROOT / "manual_sources/JE-1000F/EU/nine-language/git-20260927-c38415f5/four-language"


def _read(name):
    return json.loads((FROZEN / "source" / f"{name}.json").read_text(encoding="utf-8"))


class FrozenAITableComponentTests(unittest.TestCase):
    def test_troubleshooting_numbered_steps_break_without_splitting_decimals(self):
        for value, breaks in (
            ("1. Wait for AC. 2. Keep 0.66 ft (20 cm). 3. Restart <unit> & check.", 2),
            ("1. Check 60 V. 2. Unplug. 3. Wait. 4. Disconnect. 5. Restart.", 4),
            ("Keep 0.66 ft (20 cm).", 0),
            ("1. Nonsequential reference. 3. Ordinary continuation.", 0),
        ):
            with self.subTest(value=value):
                nodes = troubleshooting_flow({"rows": [{"code": "F6", "action": value}]},
                                             headings=("Code", "Action"), source_ref="test", language="pl")
                spec = ComponentSpec.from_dict(nodes[0]["component_spec"])
                soup = BeautifulSoup(render_manual_table_component(spec), "html.parser")
                self.assertEqual(breaks, len(soup.select("br")))
                self.assertIn(value, soup.get_text(" ", strip=True))

    def _nodes(self, language):
        symbols = _read("symbols")["locales"][language]
        operation = _read("operation_tables")["locales"][language]["lcd_mode"]
        warranty = _read("warranty_columns")["locales"][language]
        source = _read(f"{language}_direct_source")
        icons = [f"assets/{Path(row['icon_path']).name}" for row in symbols["pictograms"]]
        artwork = f"assets/p{operation['physical_page']}_lcd_mode_art.png"
        nodes = symbol_signal_flow(
            symbols, headings=("Symbol", "Meaning"), accessibility_label="Signals",
            source_ref="symbols#signals", language=language,
        )
        nodes += symbol_pictogram_flow(
            symbols, headings=("Symbol", "Meaning"), accessibility_label="Pictograms",
            icon_refs=icons, source_ref="symbols#pictograms", language=language,
        )
        nodes += troubleshooting_flow(
            source["tables"]["troubleshooting"], headings=("Code", "Action"),
            source_ref="troubleshooting", language=language,
        )
        nodes += specification_flow(
            source["tables"]["specifications"],
            group_headings=list(source["tables"]["specifications"]["groups"]),
            source_ref="specifications", language=language,
        )
        nodes += lcd_mode_flow(
            operation, artwork_ref=artwork, accessibility_label="LCD mode",
            source_ref="operations#lcd-mode", language=language,
        )
        nodes += warranty_flow(warranty, source_ref="warranty", language=language)
        return nodes, symbols, operation, warranty, source

    def _roundtrip(self, nodes, language):
        registry = load_component_registry()
        theme = load_manual_theme(component_registry=registry)
        manifest = json.loads((FROZEN / "source_manifest.json").read_text(encoding="utf-8"))
        assets = {asset.asset_ref for spec in component_specs_in_flow(nodes) for asset in spec.assets}
        with tempfile.TemporaryDirectory() as td:
            package = Path(td)
            (package / "assets").mkdir()
            hashes = {}
            for relative in assets:
                path = package / relative
                shutil.copyfile(FROZEN / "figures" / language / path.name, path)
                hashes[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
            source = ManualSource(
                model="JE-1000F", region="EU", language=language,
                source="frozen-ai-json", bundle_root="missing-source",
                bundle_sha256=value_sha256(manifest), snapshot_sha256=None,
                layout_params_sha256="b" * 64, style_contract_sha256="c" * 64,
                pages=(SourcePage(
                    page_id="tables", source_ref="tables", source_path="missing-source/tables.rst",
                    language=language, source_sha256="d" * 64,
                    blocks=tuple(("flow", node) for node in nodes),
                ),),
                schema_version=V2_SCHEMA_VERSION,
                metadata={
                    "projection": "whole-document-components/v1",
                    "frozen_source_manifest": manifest, "declared_languages": [language],
                    "web_source_normalization": "preface-auto-resume/v1",
                    "web_contract": {}, "composites": [], "page_declarations": {},
                    "asset_sha256": hashes, "component_registry": registry,
                    "component_registry_sha256": registry_sha256(registry),
                    "manual_theme": theme, "manual_theme_sha256": theme_sha256(theme),
                },
            )
            ir = build_manual_ir_from_source(source)
            path = package / "manual.ir.json"
            write_manual_ir(ir, path)
            restored = read_manual_ir(path)
            return BeautifulSoup(render_document_fragments(restored, package_root=package)[0], "html.parser")

    def test_four_language_public_roundtrip_preserves_all_table_and_warranty_copy(self):
        for language in ("uk", "pt", "nl", "pl"):
            with self.subTest(language=language):
                nodes, symbols, operation, warranty, source = self._nodes(language)
                self.assertEqual(15, len(component_specs_in_flow(nodes)))
                soup = self._roundtrip(nodes, language)
                text = soup.get_text(" ", strip=True)
                for row in symbols["rows"]:
                    self.assertIn(row["label"], text)
                    self.assertIn(row["meaning"], text)
                for row in symbols["pictograms"]:
                    self.assertIn(row["meaning"], text)
                for row in source["tables"]["troubleshooting"]["rows"]:
                    self.assertIn(row["action"], text)
                spec_tables = soup.select("table.hb-spec-table")
                self.assertEqual(len(spec_tables), 4)
                for table, rows in zip(spec_tables, source["tables"]["specifications"]["groups"].values(), strict=True):
                    self.assertEqual(
                        [(row["label"], row["value"]) for row in rows],
                        [tuple(cell.get_text() for cell in row.find_all(["th", "td"]))
                         for row in table.select("tbody > tr")],
                    )
                for mode in operation["modes"]:
                    self.assertIn(mode["text"].replace("continuame nte", "continuamente"), text)
                for row in operation["rows"]:
                    self.assertIn(row["action"]["text"], text)
                    self.assertIn(row["instruction"]["text"], text)
                for name, block in warranty["blocks"].items():
                    if name in {"title", "standard_heading", "extension_heading"}:
                        continue
                    for part in block["text"].split("•"):
                        self.assertIn(part.strip(), text)
                self.assertEqual(warranty["blocks"]["scope"]["text"],
                                 soup.select_one(".hb-warranty-intro-panel strong").get_text())
                self.assertEqual(["3", "2"], [node.get_text() for node in soup.select(".hb-warranty-year-badge")])
                for prefix, card in zip(("standard", "extension"), soup.select(".hb-warranty-period-item"), strict=True):
                    label, unit, number = [part.strip() for part in warranty["blocks"][f"{prefix}_heading"]["raw_text"].splitlines() if part.strip()]
                    self.assertEqual(label, card.select_one(".hb-warranty-period-label").get_text())
                    self.assertEqual(unit, card.select_one(".hb-warranty-years-unit").get_text())
                    self.assertEqual(number, card.select_one(".hb-warranty-year-badge").get_text())
                self.assertEqual(
                    [warranty["blocks"][f"{name}_heading"]["text"] for name in
                     ("limited", "period", "exchange", "buyer", "exclusions", "interpretation")],
                    [heading.get_text() for heading in soup.select("h3")],
                )

    def test_escaping_and_carrier_semantics_stay_consistent(self):
        record = {"groups": {"one": [{"label": "Voltage <maximum>", "value": '5 & 10 "V"'}]}}
        nodes = specification_flow(record, group_headings=["Input & output"], source_ref="spec", language="nl")
        before = deepcopy(nodes)
        soup = self._roundtrip(nodes, "nl")
        self.assertEqual("Voltage <maximum>", soup.select_one("th").get_text())
        self.assertEqual('5 & 10 "V"', soup.select_one("td").get_text())
        self.assertEqual(nodes, before)
        nodes[0]["carrier_flow"][1]["children"][0]["children"][0]["children"][1]["children"][0]["text"] = "tampered"
        with self.assertRaisesRegex(ValueError, "semantics do not match"):
            self._roundtrip(nodes, "nl")

    def test_invalid_bindings_or_grouping_are_rejected(self):
        symbols = _read("symbols")["locales"]["nl"]
        with self.assertRaisesRegex(ValueError, "one icon per row"):
            symbol_pictogram_flow(symbols, headings=("A", "B"), accessibility_label="Symbols", icon_refs=[], source_ref="symbols", language="nl")
        operation = _read("operation_tables")["locales"]["nl"]["lcd_mode"]
        operation["rows"][0]["mode_index"] = 1
        with self.assertRaisesRegex(ValueError, "two ordered groups"):
            lcd_mode_flow(operation, artwork_ref="assets/mode.png", accessibility_label="LCD", source_ref="mode", language="nl")
        warranty = _read("warranty_columns")["locales"]["nl"]
        warranty["standard_years"] = 4
        with self.assertRaisesRegex(ValueError, "disagrees with extracted years"):
            warranty_flow(warranty, source_ref="warranty", language="nl")


if __name__ == "__main__":
    unittest.main()
