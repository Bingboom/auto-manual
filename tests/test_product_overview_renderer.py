from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.draft_engine import render_generated_page
from tools.product_overview_renderer import (
    PRODUCT_OVERVIEW_FIELD_PLACEHOLDERS,
    PRODUCT_OVERVIEW_TOKEN,
    render_product_overview_page,
)


class TestProductOverviewRenderer(unittest.TestCase):
    def _substitutions(self) -> dict[str, str]:
        values = {
            "MAIN_POWER_BUTTON_LABEL": "Main Power Button",
            "FRONT_DC12_PORT_LABEL": "DC 12V Port",
            "FRONT_DC12_PORT_SPEC": "12V/10A Max",
            "DC_USB_POWER_BUTTON_LABEL": "DC/USB Power Button",
            "FRONT_USB_C_LOW_LABEL": "USB-C 30W Output",
            "FRONT_USB_C_LOW_SPEC": "30W Max",
            "FRONT_USB_C_HIGH_LABEL": "USB-C 100W Output",
            "FRONT_USB_C_HIGH_SPEC": "100W Max",
            "AC_POWER_BUTTON_LABEL": "AC Power Button",
            "FRONT_USB_A_LABEL": "USB_A 18% Output",
            "FRONT_USB_A_SPEC": "18W Max",
            "FRONT_AC_OUTPUT_LABEL": "AC Output",
            "FRONT_AC_OUTPUT_SPEC": "120V~60Hz",
            "FRONT_TOTAL_OUTPUT_LABEL": "Total Output",
            "FRONT_TOTAL_OUTPUT_SPEC": "1500W Rated",
            "SIDE_AC_INPUT_LABEL": "AC Input",
            "SIDE_AC_INPUT_SPEC": "100V-120V~60Hz",
            "SIDE_DC_INPUT_LABEL": "DC Input",
            "SIDE_DC_INPUT_PV_SPEC": "PV Input",
            "SIDE_DC_INPUT_CAR_SPEC": "Car Input",
        }
        self.assertEqual(set(PRODUCT_OVERVIEW_FIELD_PLACEHOLDERS), set(values))
        return values

    def _template(self) -> str:
        return (
            PRODUCT_OVERVIEW_TOKEN
            + "\n.. product-overview-fields: "
            + " ".join(f"|{key}|" for key in PRODUCT_OVERVIEW_FIELD_PLACEHOLDERS)
            + "\n"
        )

    def test_render_product_overview_page_should_generate_latex_and_rst_from_one_marker(self) -> None:
        out = render_product_overview_page(self._template(), self._substitutions(), lang="en")

        self.assertNotIn(PRODUCT_OVERVIEW_TOKEN, out)
        self.assertNotIn("product-overview-fields", out)
        self.assertIn(r"\HBOverviewPanel{FRONT VIEW}{front_product.jpg}{%", out)
        self.assertIn(r"\HBOverviewPair{USB\_A 18\% Output}{18W Max}{AC Output}{120V\textasciitilde{}60Hz}", out)
        self.assertIn(".. only:: not latex", out)
        self.assertIn(".. list-table::", out)
        self.assertIn("USB_A 18% Output", out)

    def test_render_product_overview_page_should_keep_language_specific_layout(self) -> None:
        out = render_product_overview_page(self._template(), self._substitutions(), lang="es")

        self.assertIn(r"\section{DESCRIPCIÓN GENERAL DEL PRODUCTO}", out)
        self.assertIn(r"\HBOverviewFull{AC Input}{100V-120V\textasciitilde{}60Hz}", out)
        self.assertIn("   VISTA LATERAL DERECHA", out)
        self.assertIn("      :widths: 100", out)

    def test_draft_engine_should_expand_product_overview_marker(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            docs_dir = root / "docs"
            (docs_dir / "templates" / "recipes").mkdir(parents=True)
            (docs_dir / "templates" / "snippets").mkdir(parents=True)
            (docs_dir / "templates" / "page_us-en").mkdir(parents=True)

            recipe_path = docs_dir / "templates" / "recipes" / "overview.yaml"
            recipe_path.write_text(
                "\n".join(
                    [
                        "page_id: 03_product_overview",
                        "template: templates/page_us-en/03_product_overview_placeholder.rst",
                        "field_map: {}",
                        "required_row_keys: []",
                        "snippet_slots: {}",
                        "contracts: []",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            template_path = docs_dir / "templates" / "page_us-en" / "03_product_overview_placeholder.rst"
            template_path.write_text(self._template(), encoding="utf-8")
            registry_path = docs_dir / "templates" / "snippets" / "registry.yaml"
            registry_path.write_text("snippets: []\n", encoding="utf-8")
            spec_master_csv = root / "Spec_Master.csv"
            spec_master_csv.write_text(
                "Model,Region,Is_Latest,Page,Row_key,Slot_key,Value_source\n",
                encoding="utf-8",
            )

            result = render_generated_page(
                docs_dir=docs_dir,
                recipe_path=recipe_path,
                template_path=template_path,
                spec_master_csv=spec_master_csv,
                registry_path=registry_path,
                vars_map={},
                base_substitutions=self._substitutions(),
                model="JE-1000F",
                region="US",
                lang="en",
            )

        self.assertNotIn(PRODUCT_OVERVIEW_TOKEN, result.text)
        self.assertIn(r"\HBOverviewPanel{FRONT VIEW}{front_product.jpg}{%", result.text)
        self.assertIn("PRODUCT OVERVIEW", result.text)


if __name__ == "__main__":
    unittest.main()
