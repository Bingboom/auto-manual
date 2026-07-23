from __future__ import annotations

import re
import tempfile
import unittest
import zipfile
from pathlib import Path

from tools.export_idml import IdmlWriter, load_layout_params


ROOT = Path(__file__).resolve().parents[1]


class IdmlSpecLocalizationTests(unittest.TestCase):
    def test_all_reference_languages_use_native_rounded_spec_panels(self) -> None:
        sections = [
            {
                "title": "GENERAL",
                "rows": [("Product Name", "Jackery Explorer 1000")],
            },
            {
                "title": "INPUT",
                "rows": [("1 x AC Input", "100-120 V~ 60 Hz")],
            },
            {
                "title": "OUTPUT",
                "rows": [("3 x AC", "120 V~ 60 Hz")],
            },
            {
                "title": "TEMPERATURE",
                "rows": [("Charging", "-10 C to 45 C")],
            },
        ]

        for lang in ("en", "fr", "es"):
            with self.subTest(lang=lang):
                writer = IdmlWriter(load_layout_params(ROOT / "data" / "layout_params.csv"))
                sid = writer.add_spec_story(sections, lang=lang)
                story = dict(writer.stories)[sid]
                anchors = {
                    name: xml
                    for name, xml in writer.stories
                    if name.startswith(f"st_anchor_spec_{lang}")
                }

                self.assertEqual(4, len(anchors))
                self.assertEqual(4, story.count("<Group Self=\"grp_st_anchor_spec_"))
                self.assertTrue(all("<Table " in xml for xml in anchors.values()))

    def test_localized_copy_keeps_reference_section_corrections(self) -> None:
        writer = IdmlWriter(load_layout_params(ROOT / "data" / "layout_params.csv"))
        sections = [
            {
                "title": "INFORMATIONS GÉNÉRALES",
                "rows": [("Nom du produit", "Jackery Explorer 1000")],
            },
            {
                "title": "PORTS D’ENTRÉE",
                "rows": [("1 × Entrée CA", "Mode de charge\nMode de dérivation")],
            },
            {
                "title": "PORTS DE SORTIE",
                "rows": [
                    ("3 × Sortie CA", "120 V"),
                    ("Sortie CA en mode dérivation", "120 V"),
                    ("1 × Sortie USB-A", "18 W"),
                ],
            },
            {
                "title": "TEMPÉRATURE DE FONCTIONNEMENT",
                "rows": [("Température de charge", "-10 °C à 45 °C")],
            },
        ]

        writer.add_spec_story(sections, lang="fr")
        anchors = dict(writer.stories)

        # Section-zero shrink and nudge must not depend on the English
        # literal "Product Name".
        general = anchors["st_anchor_spec_fr0"]
        self.assertIn('TopInset="4.175"', general)
        self.assertIn('BaselineShift="1.33"', general)

        # Output-row roles likewise survive translated labels.
        output = anchors["st_anchor_spec_fr2"]
        self.assertIn('BaselineShift="-0.32"', output)
        self.assertIn('BaselineShift="-1.25"', output)
        self.assertIn('BaselineShift="-1.09"', output)

    def test_es_reference_ratio_keeps_final_output_row_in_generated_idml(self) -> None:
        writer = IdmlWriter(load_layout_params(ROOT / "data" / "layout_params.csv"))
        sections = [
            {
                "title": "INFORMACIÓN GENERAL",
                "rows": [("Nombre del producto", "Jackery Explorer 1000")],
            },
            {
                "title": "PUERTOS DE ENTRADA",
                "rows": [("1 × Entrada CA", "100-120 V~ 60 Hz")],
            },
            {
                "title": "PUERTOS DE SALIDA",
                "rows": [
                    ("3 × Salidas CA", "120 V~ 60 Hz"),
                    ("Salida de CA en modo derivación①", "120 V~ 60 Hz"),
                    ("Salida USB-C 30W", "30 W máx."),
                    ("Salida USB-C 100W", "100 W máx."),
                    ("1 × Salida USB-A", "18 W máx."),
                    ("1 × Puerto DC 12V", "12 V⎓10 A máx."),
                ],
            },
            {
                "title": "TEMPERATURA DE FUNCIONAMIENTO",
                "rows": [("Temperatura de carga", "-10 °C a 45 °C")],
            },
        ]
        sid = writer.add_spec_story(sections, lang="es", title="ESPECIFICACIONES")
        writer.add_spread_chain(sid, 1, 0)

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "spec-es.idml"
            writer.write(output)
            with zipfile.ZipFile(output) as package:
                table_story = package.read(
                    "Stories/Story_st_anchor_spec_es2.xml",
                ).decode("utf-8")

        self.assertIn('BodyRowCount="6"', table_story)
        self.assertIn("1 × Puerto DC 12V", table_story)
        width_match = re.search(
            r'Name="0" SingleColumnWidth="([0-9.]+)"', table_story,
        )
        self.assertIsNotNone(width_match)
        body_width = writer.page_w - writer.m_l - writer.m_r - 1.13
        self.assertAlmostEqual(
            body_width * 0.362 + 2.3,
            float(width_match.group(1)),
            places=3,
        )

    def test_localized_spec_rhythm_is_token_driven(self) -> None:
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        sections = [
            {"title": f"SECTION {index}", "rows": [("Label", "Value")]}
            for index in range(1, 5)
        ]
        expected = {
            "fr": ((5.18, 11.05, 9.4, 15.26), (4.56, 3.24, 5.52, 4.07)),
            "es": ((5.18, 7.05, 10.03, 11.99), (4.56, 3.24, 5.52, 4.07)),
        }
        for language, (section_values, table_values) in expected.items():
            with self.subTest(language=language):
                writer = IdmlWriter(params)
                sid = writer.add_spec_story(sections, lang=language)
                story = dict(writer.stories)[sid]
                for value in section_values:
                    self.assertIn(f'SpaceBefore="{value:g}"', story)
                for value in table_values:
                    # The host rhythm lives in the parent spec story.
                    self.assertIn(
                        f'SpaceBefore="{value:g}"',
                        story,
                    )


if __name__ == "__main__":
    unittest.main()
