from __future__ import annotations

import hashlib
import unittest
from pathlib import Path

from tools.export_idml import IdmlWriter, load_layout_params
from tools.idml.font_family import BULLET_FONT_FAMILY_TOKEN
from tools.idml.shared_page import add_regulatory_compliance_page


ROOT = Path(__file__).resolve().parents[1]
REGULATORY_GOLDEN = {
    "bottom_card": {
        "en": (
            "869b6c01dcacb75f9f91f982c4e727799fc7b3c6135c13e3b2283f78c0f5ebdb",
            "45dbcc82a7171820dd0f468f64689495778a04cb83202b240e6c8e9c0878bcb3",
        ),
    },
}


def _digest(value: str) -> str:
    normalized = value.replace(
        ROOT.resolve().as_uri(),
        "file://IDML-PANEL-ROOT",
    )
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _render_panel():
    params = load_layout_params(
        ROOT / "data" / "layout_params.csv",
        (ROOT / "data" / "layout_params.idml-compact.csv",),
    )
    writer = IdmlWriter(
        params,
        model="JBP-2000B",
        region="EU",
        language="en",
        strict_component_assets=True,
    )
    blocks = [
        ("h1", "EU REGULATIONS"),
        ("h2", "RED DECLARATION OF CONFORMITY"),
        (
            "body",
            "Shenzhen Hello Tech Energy Co., Ltd. hereby declares that the "
            "Jackery Battery Pack 2000 with Bluetooth and Wi-Fi, model "
            "JBP-2000B, complies with the essential requirements and other "
            "relevant provisions of RED Directive 2014/53/EU. The full text "
            "of the EU declaration of conformity is available at: "
            "https://de.jackery.com/pages/user-guides",
        ),
        ("h2", "MANUFACTURER"),
        ("body", "SHENZHEN HELLO TECH ENERGY CO., LTD."),
        (
            "body",
            "F2-3, Bldg. 7, Jiaanda Science and Technology Industrial Park "
            "Factory, east side of Huafan Road, Tongsheng Community, Dalang "
            "Street, Longhua District, Shenzhen, Guangdong, China",
        ),
        (
            "body",
            "+86 400 668 9293\nsales@hello-tech.com\nwww.hello-tech.com",
        ),
    ]
    panel = add_regulatory_compliance_page(
        writer,
        sid="st_regulatory",
        blocks=blocks,
        page_index=53,
        language="en",
        root=ROOT,
        composition_data={
            "regulatory": {
                "layout_variant": "bottom_card",
                "qr_asset": (
                    "docs/renderers/latex/assets/"
                    "jbp2000b_eu_regulatory_qr.png"
                ),
            },
        },
    )
    return writer, panel


class RegulatoryCompliancePanelTests(unittest.TestCase):
    def test_bottom_card_matches_component_golden(self) -> None:
        writer, panel = _render_panel()
        spread = dict(writer.spreads)["sp_53"]
        stories = "\n".join(
            f"{story_id}\0{xml}" for story_id, xml in writer.stories
        )
        self.assertEqual(
            REGULATORY_GOLDEN["bottom_card"]["en"],
            (_digest(spread), _digest(stories)),
        )
        self.assertEqual("bottom_card", panel.contract.layout_variant)
        self.assertEqual(3, panel.contract.contact_count)
        self.assertTrue(panel.contract.has_qr)
        self.assertEqual(8, len(panel.frames))

    def test_contact_icons_use_the_bundled_symbols_face(self) -> None:
        writer, _panel = _render_panel()
        stories = dict(writer.stories)
        for index, icon in enumerate(("☎", "✉", "◉")):
            story = stories[f"st_regulatory_contact_{index}"]
            self.assertIn(f"<Content>{icon}</Content>", story)
            self.assertIn(BULLET_FONT_FAMILY_TOKEN.name, story)


if __name__ == "__main__":
    unittest.main()
