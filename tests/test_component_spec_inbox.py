from __future__ import annotations

from pathlib import Path
import unittest

from tools.component_specs.inbox import (
    CARD_ASSET_ROLES,
    COMPONENT_ID,
    inbox_component_spec,
    inbox_spec_from_legacy_payload,
)
from tools.component_specs.inbox_adapters import (
    idml_inbox_payload,
    latex_inbox_projection,
    web_inbox_projection,
    word_inbox_projection,
)
from tools.component_specs.model import ComponentSpecError
from tools.component_specs.projection import project_manual_ir_components
from tools.component_specs.registry import load_component_registry, validate_component_spec
from tools.component_specs.theme import load_manual_theme
from tools.manual_ir import ManualBlock, ManualIR, ManualPage
from tools.render_contract import load_render_contract
from tools.utils.path_utils import Paths


ROOT = Path(__file__).resolve().parents[1]
PATHS = Paths(root=ROOT)


class InboxComponentSpecTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = load_component_registry(PATHS.component_registry_contract)
        cls.theme = load_manual_theme(component_registry=cls.registry)

    def _spec(self, language: str = "en"):
        labels = {
            "en": ("AC Charging Cable", "TIP", "Sold separately."),
            "fr": ("Câble de charge CA", "CONSEILS", "Vendu séparément."),
            "es": ("Cable de carga de CA", "CONSEJOS", "Se vende por separado."),
        }
        cable, tip, body = labels[language]
        return inbox_component_spec(
            accessibility_label="What's in the Box",
            cards=(
                {"image_ref": "asset:main", "alt": "Power station", "label": "Jackery Explorer 1000"},
                {"image_ref": "asset:cable", "alt": "Charging cable", "label": cable},
                {"image_ref": "asset:manual", "alt": "Documents", "label": "Documents"},
            ),
            tip_label=tip,
            tip_body=body,
            source_ref=f"page/{language}_inbox.rst#block-2",
            language=language,
            registry=self.registry,
            theme=self.theme,
        )

    def test_registry_theme_and_style_bind_all_four_renderers(self) -> None:
        definition = self.registry["components"][COMPONENT_ID]
        self.assertEqual({"web", "latex", "idml", "word"}, set(definition["adapters"]))
        self.assertEqual(
            [COMPONENT_ID],
            self.theme["component_roles"]["component.special.inbox"]["component_ids"],
        )
        style = load_render_contract(PATHS.manual_style_contract)["styles"][COMPONENT_ID]
        self.assertEqual("aligned", style["conformance"]["state"])
        self.assertEqual([], style["conformance"]["debt"])
        self.assertEqual("rendered", style["word"]["capability"])

    def test_three_ordered_cards_own_asset_roles_alt_and_live_labels(self) -> None:
        spec = self._spec()
        self.assertEqual([], validate_component_spec(spec, self.registry))
        cards = spec.slot("cards").content
        self.assertEqual([1, 2, 3], [card["number"] for card in cards])
        self.assertEqual(list(CARD_ASSET_ROLES), [card["image_asset_role"] for card in cards])
        self.assertEqual(list(CARD_ASSET_ROLES), [asset.role for asset in spec.assets])
        self.assertTrue(all(card["alt"] and card["label"] for card in cards))
        self.assertNotIn("geometry", spec.to_dict())

    def test_four_adapters_share_copy_and_keep_renderer_geometry(self) -> None:
        spec = self._spec()
        web = web_inbox_projection(spec)
        latex = latex_inbox_projection(spec)
        word = word_inbox_projection(spec)
        idml = idml_inbox_payload(spec)
        self.assertEqual("hb-inbox-composition", web["composition_class"])
        self.assertEqual("HBInBoxThree", latex["macro"])
        self.assertEqual(6, len(latex["arguments"]))
        self.assertEqual("hb-inbox-word-table", word["table_class"])
        self.assertEqual("inbox", idml["kind"])
        self.assertEqual(web["tip_body"], word["tip_body"])
        self.assertEqual(
            [card["label"] for card in web["cards"]],
            [item["label"] for item in idml["items"]],
        )

    def test_three_languages_preserve_live_labels_and_tip_copy(self) -> None:
        for language in ("en", "fr", "es"):
            with self.subTest(language=language):
                projection = web_inbox_projection(self._spec(language))
                self.assertEqual(language, self._spec(language).language)
                self.assertEqual(3, len(projection["cards"]))
                self.assertTrue(projection["cards"][1]["label"])
                self.assertTrue(projection["tip_label"])
                self.assertTrue(projection["tip_body"])

    def test_incomplete_or_inaccessible_cards_fail_closed(self) -> None:
        with self.assertRaises(ComponentSpecError):
            inbox_component_spec(
                accessibility_label="Inbox",
                cards=({"image_ref": "one", "alt": "one", "label": "one"},),
                tip_label="TIP",
                tip_body="Body",
                source_ref="page/inbox.rst",
                language="en",
                registry=self.registry,
                theme=self.theme,
            )
        with self.assertRaises(ComponentSpecError):
            inbox_spec_from_legacy_payload(
                {"kind": "inbox", "items": [{"img": "", "label": "Missing image"}] * 3},
                source_ref="page/inbox.rst",
                language="en",
                registry=self.registry,
                theme=self.theme,
            )

    def test_manual_ir_combines_inbox_heading_cards_and_adjacent_tip(self) -> None:
        blocks = (
            ManualBlock("p:b1", "page/inbox.rst#block-1", "h1", "CONTENU DE LA BOÎTE", "a" * 64),
            ManualBlock(
                "p:b2",
                "page/inbox.rst#block-2",
                "component",
                {
                    "kind": "inbox",
                    "items": [
                        {"img": "main.png", "label": "Explorer"},
                        {"img": "cable.png", "label": "Câble"},
                        {"img": "manual.png", "label": "Documents"},
                    ],
                },
                "b" * 64,
            ),
            ManualBlock(
                "p:b3",
                "page/inbox.rst#block-3",
                "component",
                {"kind": "notice", "variant": "tip", "label": "CONSEILS", "texts": ["Vendu séparément."]},
                "c" * 64,
            ),
        )
        page = ManualPage(
            page_id="p",
            source_ref="page/inbox.rst",
            source_path="page/inbox.rst",
            language="fr",
            source_sha256="d" * 64,
            skipped_raw=0,
            blocks=blocks,
        )
        ir = ManualIR(
            model="JE-1000F",
            region="US",
            language="en",
            source="fixture",
            bundle_root="fixture",
            bundle_sha256="e" * 64,
            snapshot_sha256="f" * 64,
            layout_params_sha256="1" * 64,
            style_contract_sha256="2" * 64,
            content_sha256="3" * 64,
            pages=(page,),
        )
        inbox = next(
            spec for spec in project_manual_ir_components(ir) if spec.component_id == COMPONENT_ID
        )
        self.assertEqual("CONTENU DE LA BOÎTE", inbox.slot("accessibility_label").content)
        self.assertEqual("CONSEILS", inbox.slot("tip_label").content)
        self.assertEqual("Vendu séparément.", inbox.slot("tip_body").content)
        self.assertEqual("fr", inbox.language)


if __name__ == "__main__":
    unittest.main()
