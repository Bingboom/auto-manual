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

    def test_spanish_status_labels(self) -> None:
        self.assertEqual(
            [("Encendido", "Presione una vez"),
             ("Apagado", "Mantenga presionado")],
            parse_rows(
                "**Encendido**\nPresione una vez\n"
                "**Apagado**\nMantenga presionado"
            ),
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
        self.assertEqual("\n".join(tail_lines[:3]), spec["tail"])
        self.assertEqual(tail_lines[3], out[1][1])

    def test_split_power_tail_is_folded_into_panel(self) -> None:
        blocks = [
            ("image", "_assets/x/main_power.png"),
            ("body", "On: Press once.\nOff: Press and hold for 3s."),
            ("body", "**Default standby time:** 2 hours.\nThe product shuts down."),
            ("h2", "AC OUTPUT ON/OFF"),
        ]

        out = transform(blocks)

        self.assertEqual(["component", "h2"], [kind for kind, _ in out])
        spec = json.loads(out[0][1])
        self.assertEqual(
            "**Default standby time:** 2 hours.\nThe product shuts down.",
            spec["tail"],
        )

    def test_localized_energy_saving_sections_become_editable_panels(self) -> None:
        cases = (
            {
                "language": "en",
                "heading": "ENERGY SAVING MODE",
                "intro": "Energy Saving Mode is enabled by default.",
                "guidance": [
                    "To disable the mode, press and hold both power buttons.",
                    "For low-power devices, disable Energy Saving Mode.",
                ],
                "action": "Press and hold both buttons for more than 3 seconds.",
                "notice_label": "NOTE",
            },
            {
                "language": "fr",
                "heading": "MODE D'ÉCONOMIE D'ÉNERGIE",
                "intro": "Le mode d'économie d'énergie est activé par défaut.",
                "guidance": [
                    "Pour désactiver le mode, maintenez les deux boutons enfoncés.",
                    "Pour les appareils à faible puissance, désactivez ce mode.",
                ],
                "action": (
                    "Maintenez les deux boutons enfoncés pendant plus de 3 secondes."
                ),
                "notice_label": "REMARQUE",
            },
            {
                "language": "es",
                "heading": "MODO DE AHORRO DE ENERGÍA",
                "intro": "El modo de ahorro de energía está activado por defecto.",
                "guidance": [
                    "Para desactivar el modo, mantenga pulsados ambos botones.",
                    "Para dispositivos de baja potencia, desactive este modo.",
                ],
                "action": "Mantenga pulsados ambos botones durante 3 segundos.",
                "notice_label": "NOTA",
            },
        )
        for case in cases:
            with self.subTest(language=case["language"]):
                notice = json.dumps(
                    {
                        "kind": "notice",
                        "label": case["notice_label"],
                        "texts": ["Localized note copy."],
                    },
                    ensure_ascii=False,
                )
                # The component contract intentionally requires the governed
                # de-localized artwork; the original template PNG still has
                # baked On/Off/action copy and must not receive overlays.
                image = "renderers/latex/assets/op_energy_saving.png"
                blocks = [
                    ("h2", case["heading"]),
                    ("body", case["intro"]),
                    ("body", case["guidance"][0]),
                    ("body", case["guidance"][1]),
                    ("image", image),
                    ("body", case["action"]),
                    ("component", notice),
                    ("h2", "NEXT SECTION"),
                ]

                out = transform(blocks)

                self.assertEqual(
                    [
                        "h2_operation_energy",
                        "body_operation_energy_intro",
                        "component",
                        "component",
                        "h2",
                    ],
                    [kind for kind, _payload in out],
                )
                self.assertEqual(case["intro"], out[1][1])
                self.assertEqual(json.loads(notice), json.loads(out[3][1]))
                self.assertNotIn("image", [kind for kind, _payload in out])
                self.assertEqual(
                    [case["intro"]],
                    [
                        payload
                        for kind, payload in out
                        if kind in {"body", "body_operation_energy_intro"}
                    ],
                )
                spec = json.loads(out[2][1])
                self.assertEqual("oppanel", spec["kind"])
                self.assertEqual("energy_saving", spec["layout"])
                self.assertEqual(image, spec["image"])
                self.assertEqual(case["guidance"], spec["guidance"])
                self.assertEqual(case["action"], spec["action"])
                self.assertEqual("On/Off", spec["mode_label"])
                self.assertEqual("3s", spec["duration"])

    def test_energy_panel_upgrades_its_governed_page_break_spacing(self) -> None:
        blocks = [
            ("layout", "page_break"),
            ("h2", "MODO DE AHORRO DE ENERGÍA"),
            ("body", "Introductory copy."),
            ("body", "Disable guidance."),
            ("body", "Low-power guidance."),
            ("image", "renderers/latex/assets/op_energy_saving.png"),
            ("body", "Mantenga pulsados ambos botones durante 3 segundos."),
        ]

        out = transform(blocks)

        self.assertEqual(("layout", "page_break:10.5"), out[0])
        self.assertEqual("h2_operation_energy", out[1][0])
        self.assertEqual("energy_saving", json.loads(out[3][1])["layout"])

    def test_localized_led_sections_become_editable_panels(self) -> None:
        cases = (
            (
                "en",
                "LED LIGHT ON/OFF",
                "The LED light has two modes: Light mode and SOS mode.",
                [
                    "Press the LED Light button once to turn on the light.",
                    "Press it again to switch to SOS Mode.",
                    "Press it a third time to turn off the light.",
                ],
            ),
            (
                "fr",
                "LAMPE LED MARCHE/ARRÊT",
                "La lampe LED dispose de deux modes : éclairage et SOS.",
                [
                    "Appuyez une fois sur le bouton pour allumer la lampe.",
                    "Appuyez de nouveau pour passer en mode SOS.",
                    "Appuyez une troisième fois pour éteindre la lampe.",
                ],
            ),
            (
                "es",
                "ENCENDER/APAGAR LUZ LED",
                "La luz LED tiene dos modos: modo de luz y modo SOS.",
                [
                    "Presione una vez el botón para encender la luz.",
                    "Presiónelo nuevamente para cambiar al modo SOS.",
                    "Presiónelo una tercera vez para apagar la luz.",
                ],
            ),
        )
        for language, heading, lead, steps in cases:
            with self.subTest(language=language):
                image = (
                    "_assets/templates/word_template/common_assets/operation/"
                    "led_light.png"
                )
                blocks = [
                    ("h2", heading),
                    ("body", lead),
                    ("image", image),
                    ("body", "\n".join(steps)),
                    ("h2", "NEXT SECTION"),
                ]

                out = transform(blocks)

                self.assertEqual(
                    ["h2_operation_led", "component", "h2"],
                    [kind for kind, _payload in out],
                )
                self.assertFalse(
                    {"body", "image"}.intersection(
                        kind for kind, _payload in out
                    )
                )
                spec = json.loads(out[1][1])
                self.assertEqual("oppanel", spec["kind"])
                self.assertEqual("led_light", spec["layout"])
                self.assertEqual(image, spec["image"])
                self.assertEqual(lead, spec["lead"])
                self.assertEqual(steps, spec["steps"])

    def test_incomplete_special_operation_sections_are_untouched(self) -> None:
        cases = (
            [
                ("h2", "ENERGY SAVING MODE"),
                ("body", "Introductory copy."),
                ("body", "Only one guidance paragraph."),
                ("image", "renderers/latex/assets/op_energy_saving.png"),
                ("body", "Press and hold both buttons for 3 seconds."),
            ],
            [
                ("h2", "LED LIGHT ON/OFF"),
                ("body", "The LED light has two modes."),
                ("image", "_assets/operation/led_light.png"),
                ("body", "First step.\nSecond step."),
            ],
        )
        for blocks in cases:
            with self.subTest(image=blocks[-2][1]):
                self.assertEqual(blocks, transform(blocks))

    def test_baked_energy_saving_art_never_receives_editable_overlays(self) -> None:
        blocks = [
            ("h2", "ENERGY SAVING MODE"),
            ("body", "Introductory copy."),
            ("body", "Disable guidance."),
            ("body", "Low-power guidance."),
            (
                "image",
                "_assets/templates/word_template/common_assets/operation/"
                "energy_saving.png",
            ),
            ("body", "Press and hold both buttons for 3 seconds."),
        ]

        self.assertEqual(blocks, transform(blocks))

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
