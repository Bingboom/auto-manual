"""Use real localized RST sources to prevent skipped shared operation tables."""
from copy import deepcopy
from pathlib import Path
import re
import unittest

from bs4 import BeautifulSoup

from tools.component_specs.operation_tables_html import parse_operation_tables_html
from tools.manual_ir.whole_document_components import discover_registered_components
from tools.web.presentation import load_web_manual_contract, normalize_web_source_fragment
from tools.web.key_combinations_component import render_key_combinations_component
from tools.web.lcd_mode_component import render_lcd_mode_component
from tools.word.bundle_html import _publish_rst_fragment_to_html


ROOT = Path(__file__).resolve().parents[1]
CASES = [("JE-3000C", lang, f"05_operation_guide_{lang}.rst")
         for lang in ("de", "es", "fr", "it", "uk")]
CASES.append(("JE-1000H", "en", "05_operation_guide.rst"))
EXPECTED = {"HB-TABLE-AUTO-RESUME", "HB-TABLE-KEY-COMBINATIONS", "HB-TABLE-LCD-MODE"}


def source(model, language, name):
    path = ROOT / "docs/templates/targets" / model.lower().replace("-", "") / name
    text = path.read_text()
    placeholders = set(re.findall(r"\|([A-Z][A-Z0-9_]+)\|", text))
    text += "\n" + "\n".join(f".. |{key}| replace:: fixture-{key}" for key in sorted(placeholders))
    html = _publish_rst_fragment_to_html(text, path, active_tags={"region_eu"})
    contract = load_web_manual_contract(model=model, region="EU")
    normalized = normalize_web_source_fragment(html, source_path=path, contract=contract)
    return path, html, normalized, contract


class OperationTableIntakeTests(unittest.TestCase):
    def test_eighteen_actual_locale_tables_bind_without_figure_grants(self):
        for model, language, name in CASES:
            with self.subTest(model=model, language=language):
                path, original, normalized, contract = source(model, language, name)
                self.assertEqual([], contract["figure_targets"])
                self.assertEqual([], contract["preface"]["targets"])
                soup = BeautifulSoup(normalized, "html.parser")
                claims = discover_registered_components(
                    soup, source_path=path, contract=contract, model=model,
                    region="EU", language=language,
                )
                self.assertEqual(EXPECTED, {c.spec.component_id for c in claims})
                self.assertEqual(3, len(claims))
                before = BeautifulSoup(original, "html.parser")
                self.assertEqual(before.get_text(" ", strip=True), soup.get_text(" ", strip=True))
                self.assertEqual([im.get("src") for im in before.select("img")],
                                 [im.get("src") for im in soup.select("img")])
                for claim in claims:
                    if claim.spec.component_id == "HB-TABLE-KEY-COMBINATIONS":
                        table = claim.owned_nodes[0].select_one("table")
                        rows = [[td.get_text(" ", strip=True) for td in tr.select("td")]
                                for tr in table.select("tbody > tr")]
                        self.assertEqual(rows, claim.spec.slot("rows").content)

    def test_other_skeleton_does_not_gain_auto_resume_from_same_filename(self):
        path, _, _, _ = source(*CASES[-1])
        contract = load_web_manual_contract(model="JE-3600A", region="EU")
        # Same filename is present in this different skeleton, but it has no
        # auto-resume chapter and must not inherit the new target binding.
        import fnmatch
        self.assertFalse(any(fnmatch.fnmatch(path.stem, p)
                             for p in contract["operations"]["source_patterns"]))

    def test_bad_spans_and_duplicates_fail_instead_of_losing_copy(self):
        path, _, html, _ = source(*CASES[-1])
        for defect in ("span", "duplicate", "extra-copy"):
            with self.subTest(defect=defect):
                soup = BeautifulSoup(html, "html.parser")
                if defect == "span":
                    soup.select_one(".hb-auto-resume-table td[rowspan]")["rowspan"] = "3"
                elif defect == "duplicate":
                    soup.append(deepcopy(soup.select_one(".hb-key-combination-composition")))
                else:
                    soup.select_one(".hb-key-combination-composition").append("Keep this extra copy")
                with self.assertRaises(ValueError):
                    parse_operation_tables_html(soup, source_path=path, language="en")

    def test_unclassified_tables_are_not_guessed_from_row_counts(self):
        path, _, html, _ = source(*CASES[-1])
        soup = BeautifulSoup(html, "html.parser")
        for table in soup.select("table"):
            table.attrs.pop("class", None)
        self.assertEqual([], parse_operation_tables_html(soup, source_path=path, language="en"))

    def test_french_source_emphasis_survives_shared_rendering(self):
        path, _, html, _ = source("JE-3000C", "fr", "05_operation_guide_fr.rst")
        soup = BeautifulSoup(html, "html.parser")
        spec, figure = next((spec, figure) for spec, figure in parse_operation_tables_html(
            soup, source_path=path, language="fr",
        ) if spec.component_id == "HB-TABLE-KEY-COMBINATIONS")
        rendered = BeautifulSoup(render_key_combinations_component(spec, str(figure)), "html.parser")
        self.assertEqual(["CC/USB", "CC/USB"], [node.get_text() for node in rendered.select("strong")])
        self.assertEqual(figure.get_text(" ", strip=True), rendered.get_text(" ", strip=True))
        with self.assertRaisesRegex(ValueError, "copy disagrees"):
            render_key_combinations_component(spec, str(figure).replace("CC/USB", "wrong"))

    def test_lcd_finished_artwork_provenance_survives_shared_rendering(self):
        path, _, html, contract = source(*CASES[-1])
        soup = BeautifulSoup(html, "html.parser")
        image = soup.select_one('img[src*="lcd_mode"]')
        image["class"] = ["manual-finished-illustration"]
        image["data-web-finished-panel-path"] = "assets/approved/lcd.png"
        image["data-web-finished-panel-sha256"] = "a" * 64
        claims = discover_registered_components(
            soup, source_path=path, contract=contract, model="JE-1000H", region="EU", language="en",
        )
        claim = next(c for c in claims if c.spec.component_id == "HB-TABLE-LCD-MODE")
        carrier = str(claim.owned_nodes[0])
        rendered = BeautifulSoup(render_lcd_mode_component(claim.spec, carrier), "html.parser")
        art = rendered.select_one("img.manual-finished-illustration")
        self.assertIsNotNone(art)
        for attr in ("src", "data-web-finished-panel-path", "data-web-finished-panel-sha256"):
            self.assertEqual(image[attr], art[attr])
        with self.assertRaisesRegex(ValueError, "artwork disagrees"):
            render_lcd_mode_component(claim.spec, carrier.replace(image["src"], "wrong.png"))


if __name__ == "__main__":
    unittest.main()
