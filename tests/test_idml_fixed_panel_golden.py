from __future__ import annotations

import hashlib
import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from tools.export_idml import IdmlWriter, load_layout_params
from tools.idml.shared_page import add_fcc_inbox_overview_page


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


if __name__ == "__main__":
    unittest.main()
