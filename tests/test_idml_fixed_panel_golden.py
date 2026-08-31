from __future__ import annotations

import hashlib
import inspect
import json
import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from types import SimpleNamespace

from tools.export_idml import IdmlWriter, load_layout_params
from tools.idml import page03, shared_page
from tools.idml.components.inbox_panel import InboxPanel, InboxPanelData
from tools.idml.components.storage_panel import StoragePanel
from tools.idml.data_stories import add_spec_story
from tools.idml.shared_page import add_fcc_inbox_overview_page
from tools.idml.spec_tables import spec_table_row_heights


ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "tests" / "fixtures" / "idml_fixed_panel_golden.json"
ART = "docs/renderers/latex/assets/warning_lockup.png"

COPY = {
    "en": {
        "fcc": (
            "This device complies with part 15 of the FCC Rules. Operation is "
            "subject to conditions (1) and (2). NOTE: Tested to the applicable "
            "limits.",
            "MODIFICATION: Changes could void the user's authority.",
        ),
        "title": "WHAT'S IN THE BOX",
        "labels": ("Explorer", "AC Charging Cable", "Documents"),
        "tip": ("TIP", "The car charging cable is sold separately."),
        "overview": ("PRODUCT OVERVIEW", "FRONT VIEW", "LEFT SIDE VIEW"),
    },
    "fr": {
        "fcc": (
            "Cet appareil est conforme à la partie 15 des règles de la FCC. Son "
            "fonctionnement est soumis aux conditions (1) et (2). REMARQUE : "
            "Cet équipement a été testé.",
            "MODIFICATION : Les changements peuvent annuler l'autorisation.",
        ),
        "title": "CONTENU DE LA BOÎTE",
        "labels": ("Explorer", "Câble de charge CA", "Documents"),
        "tip": ("CONSEILS", "Le câble de charge voiture est vendu séparément."),
        "overview": ("PRÉSENTATION DU PRODUIT", "VUE AVANT", "VUE LATÉRALE"),
    },
    "es": {
        "fcc": (
            "Este dispositivo cumple con la parte 15 de la normativa FCC. Su "
            "operación está sujeta a las condiciones (1) y (2). NOTA: Este "
            "aparato ha sido probado.",
            "MODIFICACIÓN: Los cambios pueden anular la autorización.",
        ),
        "title": "CONTENIDO DE LA CAJA",
        "labels": ("Explorer", "Cable de carga de CA", "Documentos"),
        "tip": ("CONSEJOS", "El cable de carga para automóvil se vende por separado."),
        "overview": ("DESCRIPCIÓN DEL PRODUCTO", "VISTA FRONTAL", "VISTA LATERAL"),
    },
}

STORAGE_COPY = {
    "en": (
        "STORAGE",
        "Store the product in a dry place.",
        "Recharge every three months.",
        "SPECIFICATIONS",
        "GENERAL INFO",
        "Model",
    ),
    "fr": (
        "STOCKAGE",
        "Stockez le produit dans un endroit sec.",
        "Rechargez tous les trois mois.",
        "CARACTÉRISTIQUES",
        "INFORMATIONS GÉNÉRALES",
        "Modèle",
    ),
    "es": (
        "ALMACENAMIENTO",
        "Guarde el producto en un lugar seco.",
        "Recárguelo cada tres meses.",
        "ESPECIFICACIONES",
        "INFORMACIÓN GENERAL",
        "Modelo",
    ),
}

STORAGE_GOLDEN = {
    "en": {
        "spread": "792e51d0f467248d91541006e6bd2ca1c09d0cc25228ccc71f8e4c471127f179",
        "story": "5ad2d5b8e6ab3e83568a555562c6192503a81d8d34bd0de5cbc566e1c0dc8590",
        "title": "cf169f55d11e9204dd1ebd5d8786bf173feca54b91805d4ec377ac930e34382d",
    },
    "fr": {
        "spread": "f316fa0aa5c9033f8b58c04cce80371568fff323b76aa06eb5ddb782f6ce91aa",
        "story": "774e9243fa23fde7c778c9d45b23d25ade02389f75bbcb8e54e0fb2413de6017",
        "title": "e2ef0e428f8ce3948910932acd25cea405ae34c48039f8ec96909a389fd996d6",
    },
    "es": {
        "spread": "8c9973d5afab9ba1ed08e593c031908e7535081466bfa9fe77e5a540936d3bfe",
        "story": "6a37cbbd871eee90b6bb1a0fc28b1d1ef9a577e886ec7126862609827b96d9f5",
        "title": "a8c87b551c5d447ad92df281ff8035c45f71e45047a0124b65e83683bae023c7",
    },
}


def _inbox_blocks(language: str) -> list[tuple[str, str]]:
    copy = COPY[language]
    tip_label, tip_body = copy["tip"]
    return [
        ("h1", copy["title"]),
        (
            "component",
            json.dumps({
                "kind": "inbox",
                "items": [
                    {"img": ART, "label": label}
                    for label in copy["labels"]
                ],
            }, ensure_ascii=False),
        ),
        (
            "component",
            json.dumps({
                "kind": "notice",
                "label": tip_label,
                "variant": "tip",
                "texts": [tip_body],
            }, ensure_ascii=False),
        ),
    ]


def _overview_blocks(language: str) -> list[tuple[str, object]]:
    title, front, side = COPY[language]["overview"]
    return [
        ("h1", title),
        ("h2", front),
        ("image", ART),
        ("table", [["**Power button**", "**LCD display**"]]),
        ("h2", side),
        ("image", ART),
        (
            "table",
            [
                ["**Handle**", "**Expansion port A**"],
                ["", "**Expansion port B**"],
            ],
        ),
    ]


def _digest(value: str) -> str:
    normalized = value.replace(ROOT.resolve().as_uri(), "file://IDML-PANEL-ROOT")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _frame_contract(spread: str, sid: str) -> dict[str, object]:
    root = ET.fromstring(spread)
    frames: dict[str, object] = {}
    prefixes = (
        f"bg_{sid}",
        f"tf_{sid}",
        f"outline_{sid}",
        f"mask_top_left_{sid}",
        f"mask_top_right_{sid}",
        f"mask_bottom_left_{sid}",
        f"mask_bottom_right_{sid}",
    )
    for node in root.iter():
        self_id = node.attrib.get("Self", "")
        if not self_id.startswith(prefixes):
            continue
        anchors = [
            tuple(float(value) for value in point.attrib["Anchor"].split())
            for point in node.iter("PathPointType")
            if "Anchor" in point.attrib
        ]
        if not anchors:
            continue
        xs = [point[0] for point in anchors]
        ys = [point[1] for point in anchors]
        frames[self_id] = {
            "bounds": [min(xs), min(ys), max(xs), max(ys)],
            "object_style": node.attrib.get("AppliedObjectStyle", ""),
            "fill": node.attrib.get("FillColor", ""),
            "stroke": node.attrib.get("StrokeColor", ""),
        }
    return frames


def _snapshot(density: str, language: str) -> dict[str, object]:
    overlays = (
        (ROOT / "data" / "layout_params.idml-compact.csv",)
        if density == "compact"
        else ()
    )
    params = load_layout_params(ROOT / "data" / "layout_params.csv", overlays)
    writer = IdmlWriter(
        params,
        model="JBP-2000B" if density == "compact" else "JE-1000F",
        region="US",
        language=language,
    )
    sid = f"st_fixed_panels_{density}_{language}"
    fcc = [("component", json.dumps({
        "kind": "fcc",
        "texts": list(COPY[language]["fcc"]),
    }, ensure_ascii=False))]
    inbox = _inbox_blocks(language)
    page_index = 4 if density == "compact" else 3
    if density == "compact":
        add_fcc_inbox_overview_page(
            writer,
            sid=sid,
            fcc_blocks=fcc,
            inbox_blocks=inbox,
            overview_blocks=_overview_blocks(language),
            bundle_root=ROOT,
            page_index=page_index,
            language=language,
        )
    else:
        writer.add_fcc_inbox_page(
            sid,
            fcc,
            inbox,
            ROOT,
            page_index,
            lang=language,
        )
    spread = dict(writer.spreads)[f"sp_{page_index}"]
    stories = {
        story_id: xml
        for story_id, xml in writer.stories
        if story_id.startswith(sid)
    }
    return {
        "spread_sha256": _digest(spread),
        "frames": _frame_contract(spread, sid),
        "story_sha256": {
            story_id: _digest(xml)
            for story_id, xml in sorted(stories.items())
        },
    }


def _storage_writer(language: str) -> tuple[IdmlWriter, str]:
    params = load_layout_params(
        ROOT / "data" / "layout_params.csv",
        (ROOT / "data" / "layout_params.idml-compact.csv",),
    )
    writer = IdmlWriter(
        params,
        model="JBP-2000B",
        region="US",
        language=language,
        native_structure_markers=True,
    )
    title, body, item, spec_title, section_title, label = (
        STORAGE_COPY[language]
    )
    sid = f"st_storage_contract_{language}"
    spec_data = SimpleNamespace(
        title=spec_title,
        annotations=(),
        sections=({
            "title": section_title,
            "rows": [(label, "JBP-2000B")] * 3,
        },),
    )
    shared_page.add_storage_specifications_page(
        writer,
        sid=sid,
        storage_blocks=[
            ("h1", title),
            ("body", body),
            ("list", f"• {item}"),
        ],
        spec_data=spec_data,
        bundle_root=ROOT,
        page_index=9,
        language=language,
        composition_data={
            "specifications": {"layout_variant": "compact"},
        },
    )
    return writer, sid


def _storage_snapshot(language: str) -> dict[str, str]:
    writer, sid = _storage_writer(language)
    stories = dict(writer.stories)
    h1_story_id = next(
        story_id for story_id in stories
        if story_id.startswith("st_anchor_h1pill_")
    )
    return {
        "spread": _digest(dict(writer.spreads)["sp_9"]),
        "story": _digest(stories[sid]),
        "title": _digest(stories[h1_story_id]),
    }


class FixedPanelGoldenTests(unittest.TestCase):
    def test_fcc_inbox_tip_visual_contract_is_shared_by_language(self) -> None:
        expected = json.loads(GOLDEN.read_text(encoding="utf-8"))
        actual = {
            density: {
                language: _snapshot(density, language)
                for language in ("en", "fr", "es")
            }
            for density in ("standard", "compact")
        }
        self.assertEqual(expected, actual)

    def test_page_composers_only_assign_fixed_panel_rectangles(self) -> None:
        forbidden = (
            "_fcc_objects",
            "_inbox_objects",
            "_tip_objects",
            "frame_with_background",
            "idml_compact_fcc_inbox_overview_fcc_height",
            "idml_compact_inbox_title_y",
            "idml_inbox_",
            "badge_y_offset",
            "card_height",
            "image_1_width",
        )
        sources = (
            inspect.getsource(page03.add_fcc_inbox_page),
            inspect.getsource(shared_page.add_fcc_inbox_overview_page),
        )
        for source in sources:
            self.assertIn("FccInboxPanel", source)
            self.assertIn("available_height=", source)
            for token in forbidden:
                self.assertNotIn(token, source)

    def test_storage_section_reuses_je_story_contract_by_language(self) -> None:
        actual = {
            language: _storage_snapshot(language)
            for language in ("en", "fr", "es")
        }
        self.assertEqual(STORAGE_GOLDEN, actual)

    def test_storage_page_composer_only_assigns_outer_rectangles(self) -> None:
        source = inspect.getsource(
            shared_page.add_storage_specifications_page
        )
        self.assertIn("StoragePanel", source)
        self.assertIn("add_story_frames", source)
        for token in (
            "idml_compact_storage_spec_body_top",
            "idml_compact_storage_spec_body_bottom",
            "idml_compact_storage_spec_body_inset",
            '"fill": "Color/HB Bg K05"',
            '"rounded": True',
            "frame_with_background",
        ):
            self.assertNotIn(token, source)

        renderer = inspect.getsource(StoragePanel.render)
        self.assertIn('self.layout_variant == "shared_prose"', renderer)
        self.assertIn("add_prose_story", renderer)
        self.assertIn('[("h1", self.data.title)', renderer)
        # The optional rounded variant is still component-owned: the page
        # composer passes only its outer rectangle and target-declared variant.
        for token in (
            "frame_with_background",
            "heading_text",
            "HB Bg K05",
            "rounded",
            "inset",
        ):
            self.assertIn(token, renderer)

    def test_compact_spec_single_line_rows_are_equal_and_own_shell(self) -> None:
        for language in ("en", "fr", "es"):
            with self.subTest(language=language):
                params = load_layout_params(
                    ROOT / "data" / "layout_params.csv",
                    (ROOT / "data" / "layout_params.idml-compact.csv",),
                )
                writer = IdmlWriter(
                    params,
                    model="JBP-2000B",
                    region="US",
                    language=language,
                )
                add_spec_story(
                    writer,
                    [
                        {"title": "Section 1", "rows": [("A", "B")] * 7},
                        {"title": "Section 2", "rows": [("A", "B")] * 2},
                        {"title": "Section 3", "rows": [("A", "B")] * 2},
                    ],
                    lang=language,
                    title=STORAGE_COPY[language][3],
                    layout_variant="compact",
                )
                stories = dict(writer.stories)
                for section_index in range(3):
                    story = stories[
                        f"st_anchor_spec_{language}{section_index}"
                    ]
                    table_match = re.search(
                        rf'<Table Self="tbl_spec_{language}{section_index}".*?</Table>',
                        story,
                        flags=re.DOTALL,
                    )
                    self.assertIsNotNone(table_match)
                    table = table_match.group(0)
                    row_heights = [
                        float(value)
                        for value in re.findall(
                            r'<Row\b[^>]*MinimumHeight="([^"]+)"',
                            table,
                        )
                    ]
                    self.assertEqual(
                        [11.0] * len(row_heights),
                        row_heights,
                    )
                    self.assertEqual(
                        len(row_heights),
                        table.count('AutoGrow="false"'),
                    )
                    spec_host_story = stories[
                        "st_spec" if language == "en"
                        else f"st_spec_{language}"
                    ]

                    background = re.search(
                        rf'<Rectangle Self="bg_group_st_anchor_spec_'
                        rf'{language}{section_index}".*?</Rectangle>',
                        spec_host_story,
                        flags=re.DOTALL,
                    )
                    self.assertIsNotNone(background)
                    y_coordinates = [
                        float(value)
                        for value in re.findall(
                            r'\bAnchor="[^ ]+ ([^"]+)"',
                            background.group(0),
                        )
                    ]
                    self.assertAlmostEqual(
                        sum(row_heights),
                        max(y_coordinates) - min(y_coordinates),
                        places=6,
                    )
                    last_row = len(row_heights) - 1
                    self.assertRegex(
                        table,
                        rf'<Cell\b[^>]*Name="0:{last_row}"[^>]*'
                        r'FillColor="Color/HB Bg K05"',
                    )

    def test_compact_spec_accepts_more_sections_than_legacy_defaults(self) -> None:
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        writer = IdmlWriter(params, language="ko")

        sid = add_spec_story(
            writer,
            [
                {"title": f"Section {index}", "rows": [("A", "B")]}
                for index in range(1, 5)
            ],
            lang="ko",
            title="사양",
            layout_variant="compact",
        )

        self.assertEqual("st_spec_ko", sid)
        stories = dict(writer.stories)
        self.assertIn("st_anchor_spec_ko3", stories)

    def test_compact_spec_row_heights_honor_language_tokens(self) -> None:
        params = {
            "idml_compact_spec_table_row_height": ("10.3", "pt"),
            "idml_compact_spec_table_multiline_min_height": ("13", "pt"),
            "lang_ko_idml_compact_spec_table_row_height": ("12.2", "pt"),
            "lang_ko_idml_compact_spec_table_multiline_min_height": (
                "24.4",
                "pt",
            ),
        }

        heights = spec_table_row_heights(
            [("single", "value"), ("multi", "line one\nline two")],
            params,
            density="compact",
            language="ko-KR",
        )

        self.assertEqual([12.2, 24.4], heights)

    def test_compact_with_tip_keeps_tip_and_owns_internal_geometry(self) -> None:
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        params.update({
            "lang_en_idml_inbox_compact_card_y": ("205.14", "pt"),
            "lang_en_idml_inbox_compact_card_height": ("89.48", "pt"),
            "lang_en_idml_inbox_compact_tip_y": ("300.09", "pt"),
            "lang_en_idml_inbox_compact_tip_height": ("26", "pt"),
            "lang_en_idml_inbox_compact_tip_label_width": ("40", "pt"),
        })
        writer = IdmlWriter(params, language="en")
        data = InboxPanelData.from_blocks(
            _inbox_blocks("en"),
            sid="st_compact_with_tip",
            language="en",
            density="compact",
            reference_profile={"layout_variant": "compact_with_tip"},
        )

        panel = InboxPanel(
            writer,
            sid="st_compact_with_tip",
            data=data,
            bundle_root=ROOT,
            language="en",
            density="compact",
        ).render(x=29.5, y=27.7, width=311.9, available_height=164.0)

        rects = dict(panel.contract.frame_rects)
        self.assertEqual("compact_with_tip", panel.contract.profile)
        self.assertAlmostEqual(58.84, rects["card_1_shell"][1], places=2)
        self.assertAlmostEqual(89.48, rects["card_1_shell"][3], places=2)
        self.assertAlmostEqual(153.79, rects["tip_shell"][1], places=2)
        self.assertAlmostEqual(26.0, rects["tip_shell"][3], places=2)

    def test_compact_korean_tip_typography_is_valid_across_fallback_runs(self) -> None:
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        params.update({
            "lang_ko_idml_inbox_compact_tip_y": ("300.09", "pt"),
            "lang_ko_idml_inbox_compact_tip_height": ("26", "pt"),
            "lang_ko_idml_inbox_compact_tip_label_width": ("40", "pt"),
        })
        writer = IdmlWriter(params, language="ko")
        blocks = _inbox_blocks("en")
        blocks[0] = ("h1", "구성품")
        tip_payload = json.loads(blocks[-1][1])
        tip_payload.update({
            "label": "팁",
            "texts": [
                "차량용 충전 케이블은 포함되어 있지 않으며 당사 웹사이트에서 "
                "별도로 구매할 수 있습니다."
            ],
        })
        blocks[-1] = (
            "component",
            json.dumps(tip_payload, ensure_ascii=False),
        )
        data = InboxPanelData.from_blocks(
            blocks,
            sid="st_compact_ko_tip",
            language="ko",
            density="compact",
            reference_profile={"layout_variant": "compact_with_tip"},
        )

        InboxPanel(
            writer,
            sid="st_compact_ko_tip",
            data=data,
            bundle_root=ROOT,
            language="ko",
            density="compact",
        ).render(x=29.5, y=27.7, width=311.9, available_height=164.0)

        story = dict(writer.stories)["st_compact_ko_tip_tip_body"]
        root = ET.fromstring(story)
        content_ranges = [
            element
            for element in root.iter("CharacterStyleRange")
            if element.find("Content") is not None
        ]
        self.assertGreater(len(content_ranges), 1)
        for element in content_ranges:
            self.assertEqual("6.5", element.attrib.get("PointSize"))
            self.assertEqual("7.83", element.attrib.get("Leading"))
            self.assertEqual("106.9", element.attrib.get("HorizontalScale"))
            self.assertEqual("0.9", element.attrib.get("BaselineShift"))
        fallback_ranges = [
            element
            for element in content_ranges
            if element.find("Properties/AppliedFont") is not None
        ]
        self.assertTrue(fallback_ranges)
        label_story = dict(writer.stories)["st_compact_ko_tip_tip_label"]
        label_root = ET.fromstring(label_story)
        label_range = next(
            element
            for element in label_root.iter("CharacterStyleRange")
            if element.findtext("Content") == "팁"
        )
        self.assertEqual(
            "NanumGothic",
            label_range.findtext("Properties/AppliedFont"),
        )
        self.assertTrue(all(
            element.attrib.get("FontStyle") == "Regular"
            for element in fallback_ranges
        ))


if __name__ == "__main__":
    unittest.main()
