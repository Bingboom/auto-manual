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
