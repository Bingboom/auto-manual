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


class TroubleshootingTableContractTests(unittest.TestCase):
    def _render(
        self,
        rows: list[list[str]],
        *,
        strict: bool = False,
        params: dict[str, tuple[str, str]] | None = None,
        suffix: str = "localized",
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
        )
        xml, estimated_height = render_table_block(
            rows,
            ctx,
            tid=f"trouble_{suffix}",
            terminal=True,
        )
        story = dict(writer.stories)[f"st_anchor_trouble_trouble_{suffix}"]
        return xml, story, estimated_height

    def test_full_french_and_spanish_tables_budget_localized_row_growth(self) -> None:
        cases = (
            ("fr", FR_ROWS, 260.09, 266.79),
            ("es", ES_ROWS, 260.2, 267.95),
        )
        for language, rows, panel_height, estimated_height in cases:
            with self.subTest(language=language):
                self.assertEqual(12, len(rows))
                self.assertEqual("FE", rows[-1][0])

                xml, story, height = self._render(rows, suffix=language)

                self.assertIn("<Content>FE</Content>", story)
                self.assertIn('AutoSizingType="Off"', xml)
                self.assertIn(f'Anchor="0 -{panel_height:g}"', xml)
                self.assertAlmostEqual(estimated_height, height, places=2)

    def test_english_table_keeps_the_approved_measured_row_contract(self) -> None:
        xml, story, height = self._render(EN_ROWS, suffix="en")

        self.assertIn("<Content>FE</Content>", story)
        self.assertIn('Anchor="0 -240"', xml)
        self.assertAlmostEqual(248.74, height, places=2)

    def test_approved_table_fails_closed_for_every_required_style_token(self) -> None:
        required_tokens = (
            "comp_data_table_header_height",
            "comp_data_table_row_height",
            "comp_trouble_left_ratio",
            "idml_trouble_left_optical_width",
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
