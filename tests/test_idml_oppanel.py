"""Tests for the operation-panel detection pass (tools/idml/oppanel.py)."""
from __future__ import annotations

import json
import unittest

from tools.idml.oppanel import parse_rows, transform


class ParseRowsTest(unittest.TestCase):
    def test_colon_form(self) -> None:
        self.assertEqual(
            [("On", "Press once."), ("Off", "Press and hold for 3s.")],
            parse_rows("On: Press once.\nOff: Press and hold for 3s."),
        )

    def test_bold_label_form(self) -> None:
        self.assertEqual(
            [("On", "Press once"), ("Off", "Press once")],
            parse_rows("**On**\nPress once\n**Off**\nPress once"),
        )

    def test_localized_labels(self) -> None:
        self.assertEqual(
            [("Marche", "appuyez une fois"), ("Arrêt", "appuyez une fois")],
            parse_rows("**Marche**\nappuyez une fois\n**Arrêt**\nappuyez une fois"),
        )

    def test_bold_field_after_two_rows_is_not_folded_into_off_instruction(self) -> None:
        self.assertEqual(
            [("Marche", "appuyez une fois."),
             ("Arrêt", "appuyez et maintenez pendant 3 secondes.")],
            parse_rows(
                "Marche : appuyez une fois.\n"
                "Arrêt : appuyez et maintenez pendant 3 secondes.\n"
                "**Temps de veille par défaut :** 2 heures.\n"
                "Le produit s'éteindra automatiquement."
            ),
        )

    def test_non_panel_body_returns_none(self) -> None:
        self.assertIsNone(parse_rows("Just a paragraph of text."))
        self.assertIsNone(parse_rows("On: only one row"))


class TransformTest(unittest.TestCase):
    def test_image_plus_rows_with_prereq_becomes_component(self) -> None:
        blocks = [
            ("h2", "AC OUTPUT ON/OFF"),
            ("body", "**Prerequisite**: The product is powered on."),
            ("image", "_assets/x/ac_output.png"),
            ("body", "**On**\nPress once\n**Off**\nPress once"),
            ("body", "Trailing paragraph."),
        ]
        out = transform(blocks)
        kinds = [k for k, _ in out]
        self.assertEqual(["h2", "component", "body"], kinds)
        spec = json.loads(out[1][1])
        self.assertEqual("oppanel", spec["kind"])
        self.assertEqual("_assets/x/ac_output.png", spec["image"])
        self.assertTrue(spec["prereq"].startswith("Prerequisite"))
        self.assertEqual([["On", "Press once"], ["Off", "Press once"]], spec["rows"])

    def test_consolidated_operation_tail_returns_to_full_width_body(self) -> None:
        tail_lines = [
            "**Temps de veille par défaut :** 2 heures.",
            "Le produit s'éteindra automatiquement après 2 heures d'inactivité.",
            "*Le temps de veille peut être réglé dans l'application Jackery.",
            "Lorsque le mode d'économie d'énergie est activé, le produit s'éteint.",
        ]
        blocks = [
            ("image", "_assets/x/main_power.png"),
            ("body", "\n".join([
                "Marche : appuyez une fois.",
                "Arrêt : appuyez et maintenez pendant 3 secondes.",
                *tail_lines,
            ])),
        ]

        out = transform(blocks)

        self.assertEqual(["component", "body"], [kind for kind, _ in out])
        spec = json.loads(out[0][1])
        self.assertEqual(
            [["Marche", "appuyez une fois."],
             ["Arrêt", "appuyez et maintenez pendant 3 secondes."]],
            spec["rows"],
        )
        self.assertEqual("\n".join(tail_lines), out[1][1])

    def test_flattened_langtag_becomes_component(self) -> None:
        blocks = [
            ("body", "**IMPORTANT**"),
            ("body", "Congratulations."),
            ("body", "**FR IMPORTANT**"),
            ("body", "Félicitations."),
        ]
        out = transform(blocks)
        self.assertEqual(["component", "body", "component", "body"],
                         [k for k, _ in out])
        first = json.loads(out[0][1])
        self.assertEqual({"kind": "langtag", "lang": "EN", "texts": ["IMPORTANT"]}, first)
        second = json.loads(out[2][1])
        self.assertEqual("FR", second["lang"])

    def test_warranty_years_table_becomes_component(self) -> None:
        rows = [[
            "**3 YEARS** **Standard Warranty** The standard warranty period is 36 months.",
            "**2 YEARS** **Extended Warranty** To activate, register your product online.",
        ]]
        out = transform([("table", str(rows))])
        self.assertEqual("component", out[0][0])
        spec = json.loads(out[0][1])
        self.assertEqual("warrantyyears", spec["kind"])
        self.assertEqual(
            [("3", "YEARS", "Standard Warranty"), ("2", "YEARS", "Extended Warranty")],
            [(i["number"], i["unit"], i["label"]) for i in spec["items"]],
        )

    def test_localized_combined_warranty_cells_become_component(self) -> None:
        cases = (
            ("**3 ANS Garantie standard** Texte.", "ANS", "Garantie standard"),
            ("**3 AÑOS Garantía estándar** Texto.", "AÑOS", "Garantía estándar"),
        )
        for cell, unit, label in cases:
            with self.subTest(unit=unit):
                out = transform([("table", str([[cell, cell.replace("3 ", "2 ", 1)]]))])
                self.assertEqual("component", out[0][0])
                spec = json.loads(out[0][1])
                self.assertEqual("warrantyyears", spec["kind"])
                self.assertEqual(unit, spec["items"][0]["unit"])
                self.assertEqual(label, spec["items"][0]["label"])

    def test_charging_emphasis_uses_structure_not_rendered_wording(self) -> None:
        blocks = [
            ("h1", "CHARGING"),
            ("body", "**Green first:** Introductory copy."),
            ("body", "**Localized source sentence.**"),
            ("component", json.dumps({"kind": "notice", "label": "NOTE"})),
        ]
        out = transform(blocks)
        self.assertEqual("component", out[2][0])
        self.assertEqual("emphasispill", json.loads(out[2][1])["kind"])
        self.assertEqual(["Localized source sentence."], json.loads(out[2][1])["texts"])

    def test_warranty_page_groups_source_sections(self) -> None:
        blocks = [
            ("h1", "WARRANTY"),
            ("body", "**Purchase channel.**"),
            ("body", "*Local-law note."),
            ("h2", "Limited Warranty"),
            ("body", "Warranty copy."),
            ("h2", "Warranty Period"),
            ("table", str([[
                "**3 YEARS** **Standard Warranty** Standard copy.",
                "**2 YEARS** **Extended Warranty** Extended copy.",
            ]])),
        ]
        out = transform(blocks)
        self.assertEqual(["h1", "component", "warrantynote", "component", "component"],
                         [kind for kind, _ in out])
        self.assertEqual("warrantylead", json.loads(out[1][1])["kind"])
        section = json.loads(out[3][1])
        self.assertEqual("warrantysection", section["kind"])
        self.assertEqual("Limited Warranty", section["title"])

    def test_localized_warranty_pages_group_by_structure(self) -> None:
        cases = (
            (
                "GARANTIE",
                "Garantie limitée",
                "Période de garantie",
                "**3 ANS Garantie standard** Texte standard.",
            ),
            (
                "GARANTÍA",
                "Garantía limitada",
                "Período de garantía",
                "**3 AÑOS Garantía estándar** Texto estándar.",
            ),
        )
        for h1, first_section, period_section, period_cell in cases:
            with self.subTest(h1=h1):
                blocks = [
                    ("h1", h1),
                    ("body", "**Localized purchase-channel lead.**"),
                    ("body", "*Localized law note.*"),
                    ("h2", first_section),
                    ("body", "Localized warranty copy."),
                    ("h2", period_section),
                    ("table", str([[period_cell, period_cell.replace("3 ", "2 ", 1)]])),
                ]

                out = transform(blocks)

                self.assertNotIn("h2", [kind for kind, _ in out])
                specs = [json.loads(payload) for kind, payload in out if kind == "component"]
                self.assertEqual("warrantylead", specs[0]["kind"])
                self.assertEqual([first_section, period_section],
                                 [spec["title"] for spec in specs[1:]])
                period_blocks = specs[-1]["blocks"]
                self.assertEqual("warrantyyears", period_blocks[0]["spec"]["kind"])

    def test_ordinary_table_is_untouched(self) -> None:
        blocks = [("table", str([["Header", "Value"], ["A", "B"]]))]
        self.assertEqual(blocks, transform(blocks))

    def test_plain_image_is_untouched(self) -> None:
        blocks = [("image", "_assets/x/solar.png"), ("body", "A caption line.")]
        self.assertEqual(blocks, transform(blocks))


if __name__ == "__main__":
    unittest.main()
