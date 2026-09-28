from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import tempfile
import unittest

from bs4 import BeautifulSoup

from tools.frozen_ai_media_components import app_nodes, figure_node
from tools.manual_ir.components import component_specs_in_flow
from tools.manual_ir.flow import flow_nodes_to_html, validate_flow_node
from tools.web_embedded_components import render_embedded_web_component


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "manual_sources/JE-1000F/EU/nine-language/git-20260927-c38415f5/four-language/source"


def _render(node: dict, language: str = "nl") -> str:
    return render_embedded_web_component(
        node, source_path=Path("frozen/app.rst"), model="Example", region="EU",
        language=language, composite_manifest=None, contract={},
    )


class FrozenAIMediaComponentsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.art = Path(self.temporary.name) / "approved.png"
        self.art.write_bytes(b"immutable approved source artwork")
        self.digest = hashlib.sha256(self.art.read_bytes()).hexdigest()

    def _figure(self) -> dict:
        return figure_node(
            asset_ref=self.art.as_uri(), content_sha256=self.digest,
            reference_id="source-front", alt="Front — кнопка", language="nl",
            source_ref="source.json#front",
        )

    def test_exact_artwork_uses_public_component_and_hash_contract(self) -> None:
        node = self._figure()
        self.assertEqual([], validate_flow_node(node))
        spec = node["component_spec"]
        self.assertEqual("HB-SPECIAL-REFERENCE-FIGURE", spec["component_id"])
        self.assertEqual("approved-composite", spec["variant"])
        self.assertEqual([self.art.as_uri()] * 2,
                         [asset["asset_ref"] for asset in spec["assets"]])
        rendered = BeautifulSoup(_render(node), "html.parser")
        figure = rendered.select_one(".hb-reference-figure")
        self.assertEqual(self.digest, figure["data-web-composite-sha256"])
        self.assertEqual(spec["metadata"]["source_fragment_sha256"],
                         figure["data-source-fragment-sha256"])
        self.assertEqual(self.art.as_uri(), rendered.select_one(".hb-composite-stage img")["src"])

    def test_public_renderer_rejects_artwork_and_semantic_tampering(self) -> None:
        node = self._figure()
        altered = deepcopy(node)
        altered["carrier_flow"][0]["alt"] = "Changed source copy"
        with self.assertRaisesRegex(ValueError, "source changed"):
            _render(altered)
        self.art.write_bytes(b"changed artwork")
        with self.assertRaisesRegex(ValueError, "SHA-256 changed"):
            _render(node)

    def test_source_hash_survives_asset_rebasing(self) -> None:
        first = self._figure()
        second = figure_node(
            asset_ref="assets/source.png", content_sha256=self.digest,
            reference_id="source-front", alt="Front — кнопка", language="nl",
            source_ref="source.json#front",
        )
        self.assertEqual(first["component_spec"]["metadata"]["source_fragment_sha256"],
                         second["component_spec"]["metadata"]["source_fragment_sha256"])

    def test_all_frozen_app_copy_and_figures_survive_shared_ir_replay(self) -> None:
        locales = json.loads((SOURCE / "app_sections.json").read_text())["locales"]
        for language, record in locales.items():
            with self.subTest(language=language):
                figures = {
                    slug: {"asset_ref": self.art.as_uri(), "sha256": self.digest}
                    for slug in ("app_qr_and_badges", "app_add_device", "app_control", "app_pairing")
                }
                original = deepcopy(record)
                nodes = app_nodes(record, figures, language=language, source_ref="app.json")
                self.assertEqual(original, record)
                for node in nodes:
                    self.assertEqual([], validate_flow_node(node))
                markup = flow_nodes_to_html(
                    nodes, component_renderer=lambda node: _render(node, language),
                )
                soup = BeautifulSoup(markup, "html.parser")
                text = " ".join(soup.get_text(" ", strip=True).split())
                for key, block in record["blocks"].items():
                    if key == "title":  # Owned by the surrounding chapter.
                        continue
                    raw = block["raw_text"]
                    if key == "step_2_1":
                        raw = re.sub(r"\s{5,}", " + ", raw)
                    expected = re.sub(r'\\+"', '"', " ".join(raw.replace("•", " ").split()))
                    self.assertIn(expected, text, key)
                specs = component_specs_in_flow(nodes)
                self.assertEqual(4, sum(s.component_id == "HB-SPECIAL-REFERENCE-FIGURE" for s in specs))
                self.assertEqual(1, sum(s.component_id == "HB-SPECIAL-APP" for s in specs))
                self.assertEqual("+", soup.select_one(".hb-inline-add-device-icon").text)
                self.assertEqual(4, len(soup.select(".hb-reference-figure")))
                self.assertEqual(0, len(soup.select(".hb-app-download-grid")))
                if language == "nl":
                    self.assertIn('Zoek naar "Jackery"', text)
                    self.assertNotIn('\\"', text)

    def test_missing_control_gap_fails_instead_of_guessing(self) -> None:
        record = json.loads((SOURCE / "app_sections.json").read_text())["locales"]["nl"]
        record["blocks"]["step_2_1"]["raw_text"] = "2.1 Missing gap"
        figures = {"app_qr_and_badges": {"asset_ref": self.art.as_uri(), "sha256": self.digest}}
        with self.assertRaisesRegex(ValueError, "control gap is ambiguous"):
            app_nodes(record, figures, language="nl", source_ref="app.json")


if __name__ == "__main__":
    unittest.main()
