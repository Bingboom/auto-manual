#!/usr/bin/env python3
"""Editable troubleshooting-table sizing and approved-style contract."""
from __future__ import annotations

import unittest
from pathlib import Path

from tools.export_idml import IdmlWriter, load_layout_params
from tools.idml.components import RenderContext
from tools.idml.components.prose_table import render_table_block


ROOT = Path(__file__).resolve().parents[1]


EN_ROWS = [
    ["Error Code", "Corrective Measures"],
    *[[f"F{index}", "Restart the product."] for index in range(6)],
    ["F6", "| 1. First step. | 2. Second step. | 3. Third step. | 4. Fourth step. | 5. Fifth step."],
    ["F7", "| 1. First step. | 2. Second step. | 3. Third step."],
    ["F8", "Contact Jackery Customer Support."],
    ["F9", "Remove the load connected to the USB ports."],
    ["FE", "Contact Jackery Customer Support."],
]


FR_ROWS = [
    ["Code d'erreur", "Mesures correctives"],
    ["F0", "Redémarrez le produit."],
    ["F1", "Redémarrez le produit."],
    ["F2", "Redémarrez le produit."],
    ["F3", "Redémarrez le produit."],
    [
        "F4",
        "Connectez le produit à des charges pour décharger sa batterie "
        "jusqu'à ce que l'erreur disparaisse.",
    ],
    [
        "F5",
        "Chargez le produit via des panneaux solaires ou une prise murale CA "
        "jusqu'à ce que l'erreur disparaisse.",
    ],
    [
        "F6",
        "| 1. Attendez que le réseau se normalise avant de charger le produit "
        "via une prise murale CA. | 2. Vérifiez si les entrées et sorties d'air "
        "sont obstruées; assurez un espace de 0,66 pied (20 cm) de chaque côté "
        "du produit. | 3. Placez le produit dans un endroit qui n'est pas "
        "exposé à la lumière directe du soleil ou à des températures ambiantes "
        "élevées. | 4. Déconnectez toutes les charges du produit. Laissez le "
        "produit inactif et attendez que l'erreur disparaisse. | 5. Redémarrez "
        "le produit.",
    ],
    [
        "F7",
        "| 1. Retirez toutes les entrées CC du produit. | 2. Vérifiez la tension "
        "en circuit ouvert (V\\ :sub:`oc`) des panneaux solaires connectés. Le "
        "produit accepte une tension d'entrée CC maximale de 60V. | 3. "
        "Redémarrez le produit et laissez-le inactif. Attendez que l'erreur "
        "disparaisse.",
    ],
    ["F8", "Contacter le service à la clientèle de Jackery."],
    [
        "F9",
        "Retirez la charge connectée aux ports USB du produit. Attendez que "
        "l'erreur disparaisse.",
    ],
    ["FE", "Contacter le service à la clientèle de Jackery."],
]


ES_ROWS = [
    ["Código de fallo", "Medidas correctivas"],
    ["F0", "Reiniciar el producto."],
    ["F1", "Reiniciar el producto."],
    ["F2", "Reiniciar el producto."],
    ["F3", "Reiniciar el producto."],
    [
        "F4",
        "Conecte el producto a cargas para descargar la batería hasta que la "
        "falla desaparezca.",
    ],
    [
        "F5",
        "Cargue el producto mediante paneles solares o una toma de corriente CA "
        "hasta que la falla desaparezca.",
    ],
    [
        "F6",
        "| 1. Espere a que la red eléctrica se normalice antes de cargar el "
        "producto a través de una toma de corriente CA. | 2. Verifique si las "
        "rejillas de entrada y salida de aire están obstruidas; asegure un "
        "espacio libre de 0,66 pies (20 cm) a ambos lados del producto. | 3. "
        "Coloque el producto en un lugar que no esté expuesto a la luz solar "
        "directa ni a altas temperaturas ambientales. | 4. Desconecte todas "
        "las cargas del producto. Mantenga el producto inactivo y espere hasta "
        "que la falla desaparezca. | 5. Reinicie el producto.",
    ],
    [
        "F7",
        "| 1. Retire todas las entradas de CC del producto. | 2. Si carga el "
        "producto mediante un panel solar, verifique el voltaje en circuito "
        "abierto (V\\ :sub:`oc`) del panel solar conectado. El producto admite "
        "un voltaje máximo de entrada de CC de 60 V. | 3. Reinicie el producto "
        "y déjelo inactivo. Espere hasta que la falla desaparezca.",
    ],
    ["F8", "Contacte con atención al cliente de Jackery."],
    [
        "F9",
        "Retire la carga conectada a los puertos USB del producto. Espere hasta "
        "que la falla desaparezca.",
    ],
    ["FE", "Contacte con atención al cliente de Jackery."],
]


JBP_EN_ROWS = [
    ["Error Code", "Corrective Measures"],
    ["F0", "Restart the product."],
    ["F1, F2", "Contact Jackery Customer Support."],
    ["F3", "Restart the product."],
    [
        "F4",
        "Connect the product to loads to discharge its battery until the "
        "fault disappears.",
    ],
    [
        "F5",
        "Charge the product via solar panels or AC wall outlet until the "
        "fault disappears.",
    ],
    ["F6-F9,\nFA, FC", "Contact Jackery Customer Support."],
    [
        "FF",
        "Place the product in an environment with a proper temperature and "
        "wait till the fault disappears.",
    ],
]


class TroubleshootingTableContractTests(unittest.TestCase):
    def _render(
        self,
        rows: list[list[str]],
        *,
        strict: bool = False,
        params: dict[str, tuple[str, str]] | None = None,
        suffix: str = "localized",
        language: str = "en",
    ) -> tuple[str, str, float]:
        writer = IdmlWriter(
            params
            if params is not None
            else load_layout_params(ROOT / "data" / "layout_params.csv")
        )
        ctx = RenderContext(
            params=writer.params,
            page_w=writer.page_w,
            m_l=writer.m_l,
            m_r=writer.m_r,
            root=ROOT,
            bundle_root=ROOT / "docs",
            add_story=writer._add_story_parts,
            strict_component_assets=strict,
            language=language,
        )
        # The caller declares the semantic; it is no longer inferred from the
        # printed header (which only ever recognised EN/FR/ES).
        xml, estimated_height = render_table_block(
            rows,
            ctx,
            tid=f"trouble_{suffix}",
            terminal=True,
            troubleshooting=True,
        )
        story = dict(writer.stories)[f"st_anchor_trouble_trouble_{suffix}"]
        return xml, story, estimated_height

    def test_full_french_and_spanish_tables_budget_localized_row_growth(self) -> None:
        cases = (
            ("fr", FR_ROWS, 256.09, 262.79),
            ("es", ES_ROWS, 256.2, 263.95),
        )
        for language, rows, panel_height, estimated_height in cases:
            with self.subTest(language=language):
                self.assertEqual(12, len(rows))
                self.assertEqual("FE", rows[-1][0])

                xml, story, height = self._render(
                    rows, suffix=language, language=language,
                )

                self.assertIn("<Content>FE</Content>", story)
                self.assertIn('AutoSizingType="Off"', xml)
                self.assertIn(f'Anchor="0 -{panel_height:g}"', xml)
                self.assertAlmostEqual(estimated_height, height, places=2)

    def test_english_table_keeps_the_approved_measured_row_contract(self) -> None:
        xml, story, height = self._render(EN_ROWS, suffix="en")

        self.assertIn("<Content>FE</Content>", story)
        self.assertIn('Anchor="0 -237.79"', xml)
        self.assertAlmostEqual(246.53, height, places=2)

    def test_seven_row_table_reuses_rows_without_full_master_depth(self) -> None:
        short_rows = EN_ROWS[:8]

        xml, story, height = self._render(short_rows, suffix="short_en")

        self.assertEqual(8, len(short_rows))
        self.assertIn("<Content>F6</Content>", story)
        self.assertNotIn("<Content>F7</Content>", story)
        self.assertNotIn('Anchor="0 -237.79"', xml)
        self.assertLess(height, 190.0)

    def test_compact_table_sizes_columns_and_rows_from_live_copy(self) -> None:
        xml, story, height = self._render(JBP_EN_ROWS, suffix="jbp_en")

        self.assertIn('SingleColumnWidth="42.88"', story)
        self.assertIn('MinimumHeight="29.391"', story)
        self.assertIn('MinimumHeight="17.9"', story)
        self.assertIn(
            'SingleRowHeight="29.391" MinimumHeight="29.391" '
            'AutoGrow="false"',
            story,
        )
        self.assertIn('FillColor="Color/HB Header K08"', story)
        right_header = story.split(
            '<Cell Self="trouble_jbp_enc0_1"',
            1,
        )[1].split("</Cell>", 1)[0]
        self.assertNotIn("FillColor=", right_header)
        self.assertIn('Hyphenation="false"', story)
        self.assertIn('Anchor="-0.37 -4.8"', xml)
        main_frame_id = "tf_group_st_anchor_trouble_trouble_jbp_en"
        carrier_id = "tf_terminal_carrier_group_st_anchor_trouble_trouble_jbp_en"
        self.assertIn(
            f'Self="{main_frame_id}" ParentStory="st_anchor_trouble_trouble_jbp_en" '
            f'PreviousTextFrame="n" NextTextFrame="{carrier_id}"',
            xml,
        )
        self.assertIn(
            f'Self="{carrier_id}" ParentStory="st_anchor_trouble_trouble_jbp_en" '
            f'PreviousTextFrame="{main_frame_id}" NextTextFrame="n"',
            xml,
        )
        main_frame = xml.split(f'<TextFrame Self="{main_frame_id}"', 1)[1].split(
            "</TextFrame>", 1,
        )[0]
        carrier = xml.split(f'<TextFrame Self="{carrier_id}"', 1)[1].split(
            "</TextFrame>", 1,
        )[0]
        self.assertIn('Anchor="311.344 0"', main_frame)
        self.assertNotIn('Anchor="311.344 1"', main_frame)
        self.assertIn('Anchor="0 1"', carrier)
        self.assertIn('FillColor="Swatch/None"', carrier)
        self.assertIn('StrokeColor="Swatch/None"', carrier)
        self.assertGreater(height, 130.0)
        self.assertLess(height, 150.0)

    def test_compact_table_consumes_target_overlay_outer_radius(self) -> None:
        params = load_layout_params(
            ROOT / "data" / "layout_params.csv",
            (ROOT / "data" / "layout_params.idml-compact.csv",),
        )
        params["idml_trouble_compact_outer_radius"] = ("5.25", "pt")

        xml, _story, _height = self._render(
            JBP_EN_ROWS,
            strict=True,
            params=params,
            suffix="jbp_overlay_radius",
        )

        self.assertIn('Anchor="-0.37 -5.25"', xml)

    def test_body_cells_are_natively_vertically_centered_in_all_locales(self) -> None:
        for language, rows in (("en", EN_ROWS), ("fr", FR_ROWS), ("es", ES_ROWS)):
            with self.subTest(language=language):
                _xml, story, _height = self._render(
                    rows, suffix=language, language=language,
                )
                for row_index in range(1, len(rows)):
                    for column_index in range(2):
                        cell_id = f'trouble_{language}c{row_index}_{column_index}'
                        cell_xml = story.split(
                            f'<Cell Self="{cell_id}"', 1,
                        )[1].split("</Cell>", 1)[0]
                        self.assertIn(
                            'VerticalJustification="CenterAlign"', cell_xml,
                        )
                        self.assertNotIn("BaselineShift=", cell_xml)

                # F6/F7 are the multi-step rows. Both columns must use a
                # symmetric content area so CenterAlign is not optically
                # displaced by unequal top/bottom padding.
                for row_index in (7, 8):
                    for column_index in range(2):
                        cell_id = f'trouble_{language}c{row_index}_{column_index}'
                        cell_xml = story.split(
                            f'<Cell Self="{cell_id}"', 1,
                        )[1].split("</Cell>", 1)[0]
                        self.assertIn('TopInset="2.83465"', cell_xml)
                        self.assertIn('BottomInset="2.83465"', cell_xml)

    def test_approved_table_fails_closed_for_every_required_style_token(self) -> None:
        required_tokens = (
            "comp_data_table_header_height",
            "comp_data_table_row_height",
            "comp_trouble_left_ratio",
            "idml_trouble_left_optical_width",
            "idml_trouble_header_height_correction",
            "idml_trouble_body_height_correction",
            "idml_trouble_extra_row_min_height",
            "idml_trouble_inner_rule",
            "idml_trouble_outer_rule",
            "idml_trouble_panel_min_height",
            "idml_trouble_import_safety",
            "idml_trouble_glyph_width_ratio",
            "lang_en_idml_trouble_table_space_before",
            "lang_fr_idml_trouble_table_space_before",
            "lang_es_idml_trouble_table_space_before",
            "type_trouble_body_font_size",
            "type_trouble_body_font_leading",
            "type_data_table_header_font_size",
            "type_data_table_header_font_leading",
            "type_trouble_code_font_size",
            "type_trouble_code_font_leading",
            "comp_trouble_steps_pad_tb",
            "comp_table_outer_arc",
        )
        for token in required_tokens:
            with self.subTest(token=token):
                params = load_layout_params(ROOT / "data" / "layout_params.csv")
                params.pop(token)

                with self.assertRaisesRegex(
                    ValueError,
                    "approved TroubleshootingTableStyle style is missing required layout token",
                ):
                    self._render(
                        FR_ROWS,
                        strict=True,
                        params=params,
                        suffix=f"missing_{token}",
                    )

    def test_approved_locales_require_their_row_minima_token(self) -> None:
        for language, rows in (("en", EN_ROWS), ("fr", FR_ROWS), ("es", ES_ROWS)):
            with self.subTest(language=language):
                params = load_layout_params(ROOT / "data" / "layout_params.csv")
                token = f"lang_{language}_idml_trouble_row_minima"
                params.pop(token)

                with self.assertRaisesRegex(ValueError, token):
                    self._render(
                        rows,
                        strict=True,
                        params=params,
                        suffix=f"missing_minima_{language}",
                        language=language,
                    )

    def test_visible_table_calibrations_are_resolved_from_layout_tokens(self) -> None:
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        params["idml_trouble_header_height_correction"] = ("4", "pt")
        params["idml_trouble_body_height_correction"] = ("3", "pt")
        params["lang_en_idml_trouble_row_minima"] = (
            "20;11.80;12.37;11.79;11.99;11.87;23.89;57.61;31.96;17.41;18.43;11.97",
            "none",
        )
        params["idml_trouble_inner_rule"] = ("0.4", "pt")
        params["idml_trouble_outer_rule"] = ("0.8", "pt")
        params["idml_trouble_panel_min_height"] = ("270", "pt")

        xml, story, height = self._render(
            EN_ROWS,
            strict=True,
            params=params,
            suffix="tokenized",
        )

        self.assertIn('SingleRowHeight="18.7402"', story)
        self.assertIn('SingleRowHeight="14.9055"', story)
        self.assertIn('MinimumHeight="20"', story)
        self.assertIn('LeftEdgeStrokeWeight="0.4"', story)
        self.assertIn('StrokeWeight="0.8"', xml)
        self.assertIn('Anchor="0 -270"', xml)
        self.assertAlmostEqual(278.74, height, places=2)

    def test_invalid_geometry_tokens_fail_before_emitting_idml(self) -> None:
        cases = (
            ("comp_trouble_left_ratio", "0", "finite and positive"),
            ("comp_trouble_left_ratio", "1", "must be less than 1"),
            ("type_trouble_body_font_size", "nan", "finite and positive"),
        )
        for token, value, message in cases:
            with self.subTest(token=token, value=value):
                params = load_layout_params(ROOT / "data" / "layout_params.csv")
                params[token] = (value, params[token][1])
                with self.assertRaisesRegex(ValueError, message):
                    self._render(
                        FR_ROWS,
                        strict=True,
                        params=params,
                        suffix=f"invalid_{token}_{value}",
                    )


if __name__ == "__main__":
    unittest.main()
