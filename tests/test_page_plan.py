from __future__ import annotations

import json
from pathlib import Path
import unittest

from tools.idml import page_folio
from tools.idml.page_roles import classify_page_role
from tools.page_plan import (
    FolioPolicy,
    PagePlan,
    PageTemplateRole,
    build_renderer_page_plan,
    idml_page_binding,
    latex_page_binding,
    page_template_role_for_composition_type,
    web_pagination_binding,
    word_page_binding,
)


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PLAN = (
    ROOT
    / "docs"
    / "renderers"
    / "contracts"
    / "reference_layout"
    / "je1000f_us_v2_20260605.json"
)


def _approved_renderer_plan() -> PagePlan:
    approved = json.loads(REFERENCE_PLAN.read_text(encoding="utf-8"))
    legacy_pages = []
    for entry in approved["pages"]:
        legacy_pages.append(
            {
                "source_ref": entry["source_ref"],
                "source_path": entry["source_ref"],
                "language": entry["language"],
                "page_role": classify_page_role(Path(entry["source_ref"])).value,
                "latex_start_page": entry["start_page"],
                "planned_page_count": entry["page_count"],
                "composition_id": entry["composition_id"],
            }
        )
    return build_renderer_page_plan(
        {
            "physical_page_count": approved["reference_pdf"]["page_count"],
            "pages": legacy_pages,
        }
    )


class PagePlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.plan = _approved_renderer_plan()

    def test_approved_plan_preserves_52_source_and_58_physical_pages(self) -> None:
        self.assertEqual(52, len(self.plan.source_pages))
        self.assertEqual(58, self.plan.physical_page_count)
        self.assertEqual(58, len(self.plan.physical_pages()))
        self.assertEqual(
            ["en", "fr", "es"],
            list(
                dict.fromkeys(
                    page.language
                    for page in self.plan.source_pages
                    if page.language not in {"cover", "toc", ""}
                )
            ),
        )

    def test_preface_safety_composite_is_a_numbered_body_page(self) -> None:
        self.assertEqual(
            PageTemplateRole.STANDARD,
            page_template_role_for_composition_type(
                "preface_safety_maintenance"
            ),
        )
        self.assertEqual(
            PageTemplateRole.NO_FOOTER,
            page_template_role_for_composition_type("preface"),
        )

    def test_source_order_and_composition_map_are_lossless(self) -> None:
        approved = json.loads(REFERENCE_PLAN.read_text(encoding="utf-8"))
        actual = [
            (
                page.source_ref,
                page.language,
                page.physical_start,
                page.physical_span,
                page.composition_id,
            )
            for page in self.plan.source_pages
        ]
        expected = [
            (
                entry["source_ref"],
                entry["language"],
                entry["start_page"],
                entry["page_count"],
                entry["composition_id"],
            )
            for entry in approved["pages"]
        ]
        self.assertEqual(expected, actual)

    def test_page_roles_drive_footer_and_folio_without_localized_text(self) -> None:
        front = self.plan.physical_page(1)
        preface = self.plan.physical_page(2)
        toc = self.plan.physical_page(3)
        first_content = self.plan.physical_page(4)
        last_content = self.plan.physical_page(57)
        back = self.plan.physical_page(58)

        self.assertEqual(PageTemplateRole.FRONT_COVER, front.role)
        self.assertEqual(PageTemplateRole.NO_FOOTER, preface.role)
        self.assertEqual(PageTemplateRole.TOC, toc.role)
        self.assertEqual(PageTemplateRole.STANDARD, first_content.role)
        self.assertEqual(PageTemplateRole.BACK_COVER, back.role)
        self.assertEqual(FolioPolicy.SUPPRESS, front.folio_policy)
        self.assertEqual(FolioPolicy.SUPPRESS, preface.folio_policy)
        self.assertEqual(FolioPolicy.SUPPRESS, toc.folio_policy)
        self.assertEqual(1, first_content.folio_number)
        self.assertEqual(54, last_content.folio_number)
        self.assertIsNone(back.folio_number)

    def test_round_trip_preserves_capabilities_and_roles(self) -> None:
        restored = PagePlan.from_dict(self.plan.to_dict())
        self.assertEqual(self.plan, restored)
        self.assertEqual("rendered", restored.capability("latex").value)
        self.assertEqual("rendered", restored.capability("idml").value)
        self.assertEqual("projection-only", restored.capability("word").value)
        self.assertEqual("not-applicable", restored.capability("web").value)

    def test_four_renderer_adapters_project_semantics_not_geometry(self) -> None:
        front = self.plan.physical_page(1)
        preface = self.plan.physical_page(2)
        content = self.plan.physical_page(4)

        self.assertEqual("HBPageTemplateCover", latex_page_binding(front).page_template)
        self.assertEqual(
            "HBPageTemplateNoFooter",
            latex_page_binding(preface).page_template,
        )
        self.assertEqual(
            "HBPageTemplateStandard",
            latex_page_binding(content).page_template,
        )
        self.assertEqual("HB Cover Page", idml_page_binding(front).page_template)
        self.assertEqual("HB No Footer Page", idml_page_binding(preface).page_template)
        self.assertEqual("HB Standard Page", idml_page_binding(content).page_template)
        self.assertEqual("HB Page Number", idml_page_binding(content).page_number_style)
        self.assertEqual(
            "projection-only",
            word_page_binding(PageTemplateRole.STANDARD).capability.value,
        )
        web = web_pagination_binding(self.plan)
        self.assertEqual("not-applicable", web.capability.value)
        self.assertEqual("not-applicable", web.pagination)
        self.assertIsNone(web.page_template)

    def test_idml_folio_uses_page_plan_and_dedicated_style(self) -> None:
        class Writer:
            page_w = 368.787
            page_h = 524.692
            m_l = 28.35
            m_r = 28.35
            spreads = [
                (
                    f"sp_{index}",
                    '<?xml version="1.0"?><idPkg:Spread><Spread>'
                    "</Spread>\n</idPkg:Spread>",
                )
                for index in range(58)
            ]

            @staticmethod
            def _frame_xml(_frame_id, _story_id, *_bounds, **_kwargs):
                return "<TextFrame/>"

        styles: list[str] = []

        def add_story_parts(story_id, _title, parts):
            styles.extend(parts)
            return story_id

        def psr(style, text, *, terminal):
            return f"{style}:{text}:{terminal}"

        applied = page_folio.apply(
            Writer(),
            add_story_parts,
            psr,
            page_plan={"renderer_page_plan": self.plan.to_dict()},
            has_back_cover=True,
        )

        self.assertEqual(54, applied)
        self.assertEqual("HB Page Number:01:True", styles[0])
        self.assertEqual("HB Page Number:54:True", styles[-1])
        self.assertFalse(any("HB Spec Note" in style for style in styles))


if __name__ == "__main__":
    unittest.main()
