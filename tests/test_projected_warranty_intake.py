"""Projected battery-pack warranties retain their authored paragraph boundaries."""
from pathlib import Path
import unittest

from bs4 import BeautifulSoup

from tools.component_specs.warranty_html import parse_warranty_html
from tools.manual_ir.whole_document_components import discover_registered_components
from tools.web_presentation import load_web_manual_contract
from tools.word_bundle_html import _publish_rst_fragment_to_html, _rewrite_word_friendly_fragment


ROOT = Path(__file__).resolve().parents[1]


def _source(language):
    suffix = "_eu" if language in {"en", "es", "fr"} else ""
    path = ROOT / "docs/templates/page_bp" / language / f"11_warranty{suffix}.rst"
    html = _rewrite_word_friendly_fragment(
        _publish_rst_fragment_to_html(path.read_text(), path, active_tags={"region_eu"}),
        lang=language,
    )
    return BeautifulSoup(html, "html.parser")


class ProjectedWarrantyIntakeTests(unittest.TestCase):
    def test_five_real_projected_warranties_preserve_lead_paragraphs(self):
        contract = load_web_manual_contract(model="JBP-2000B", region="EU")
        for language in ("en", "de", "es", "fr", "it"):
            with self.subTest(language=language):
                soup = _source(language)
                paragraphs = soup.find_all("p", recursive=False)
                claims = discover_registered_components(
                    soup, source_path=Path(f"warranty_{language}.rst"),
                    contract=contract, model="JBP-2000B", region="EU", language=language,
                )
                self.assertEqual(7, len(claims))
                lead = claims[0]
                self.assertEqual("HB-WARRANTY-LEAD", lead.spec.component_id)
                self.assertEqual(tuple(paragraphs), lead.owned_nodes)
                self.assertEqual(
                    [str(p) for p in paragraphs[:-1]],
                    [str(p) for p in BeautifulSoup(lead.spec.slot("lead").content, "html.parser").find_all("p")],
                )
                self.assertEqual(str(paragraphs[-1]), lead.spec.slot("local_note").content)
                self.assertEqual(4 if language == "fr" else 2, len(paragraphs))

    def test_jp_authored_warranty_keeps_all_seven_sections_and_line_breaks(self):
        from tools.web_warranty_component import render_warranty_component
        path = ROOT / "docs/templates/page_jp/11_warranty.rst"
        html = _rewrite_word_friendly_fragment(
            _publish_rst_fragment_to_html(path.read_text(), path, active_tags={"region_jp"}), lang="ja",
        )
        soup = BeautifulSoup(html, "html.parser")
        claims = discover_registered_components(
            soup, source_path=path, model="JE-1000F", region="JP", language="ja",
            contract=load_web_manual_contract(model="JE-1000F", region="JP"),
        )
        self.assertEqual(8, len(claims))
        self.assertEqual(7, sum(c.spec.component_id == "HB-WARRANTY-SECTION" for c in claims))
        self.assertFalse(any(c.spec.component_id == "HB-WARRANTY-YEARS" for c in claims))
        for claim in claims:
            before = BeautifulSoup("".join(str(n) for n in claim.owned_nodes), "html.parser")
            after = BeautifulSoup(render_warranty_component(claim.spec), "html.parser")
            self.assertEqual(before.get_text(" ", strip=True), after.get_text(" ", strip=True))
            self.assertEqual(len(before.select(".line")), len(after.select(".line")))
        for value in ("3年間", "1年間", "2年間", "050-3198-9007"):
            self.assertIn(value, html)
        with self.assertRaisesRegex(ValueError, "warranty years component"):
            parse_warranty_html(soup, source_path=path, expected_sections=7,
                                expected_years=["3", "2"], language="ja")

    def test_rejects_lead_interleaved_with_sections_or_foreign_blocks(self):
        for mutation in ("interleave", "foreign"):
            with self.subTest(mutation=mutation):
                soup = _source("fr")
                if mutation == "interleave":
                    last = soup.find_all("p", recursive=False)[-1].extract()
                    soup.append(last)
                else:
                    soup.h1.insert_after(soup.new_tag("aside"))
                with self.assertRaisesRegex(ValueError, "must precede sections"):
                    parse_warranty_html(
                        soup, source_path=Path("warranty_fr.rst"), expected_sections=6,
                        expected_years=["3", "2"], language="fr",
                    )


if __name__ == "__main__":
    unittest.main()
