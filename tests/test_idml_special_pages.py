from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.export_idml import IdmlWriter, load_layout_params
from tools.idml import ir_projection, page_placed, page_toc
from tools.manual_ir import build_manual_ir


ROOT = Path(__file__).resolve().parents[1]


class IdmlSpecialPageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.writer = IdmlWriter(load_layout_params(ROOT / "data" / "layout_params.csv"))

    def test_back_cover_uses_source_payload_without_template_only_copy(self) -> None:
        copy = {
            "company": "JACKERY INC.",
            "address": "5310 Bunche Dr, Fremont, CA 94538, United States",
            "phone": "1-888-502-2236",
        }
        self.assertTrue(page_placed.add_back_cover_page(self.writer, "US", 0, copy))
        stories = "".join(xml for _, xml in self.writer.stories)
        self.assertIn(copy["address"], stories)
        self.assertIn(copy["phone"], stories)
        self.assertNotIn("hello@jackery.com", stories)
        self.assertNotIn("94538-8301", stories)

    def test_back_cover_stays_editable_when_finished_art_exists(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            docs = Path(td)
            asset = docs / "renderers" / "latex" / "assets" / "back_cover-en.pdf"
            asset.parent.mkdir(parents=True)
            asset.write_bytes(b"finished-art")

            self.assertTrue(page_placed.add_preferred_back_cover_page(
                self.writer, "US", "en", docs, 0, {
                    "company": "SOURCE COMPANY",
                    "address": "Source address",
                    "phone": "Source phone",
                }))

        stories = "".join(xml for _, xml in self.writer.stories)
        self.assertIn("SOURCE COMPANY", stories)
        self.assertIn("Source address", stories)
        self.assertIn("Source phone", stories)
        self.assertNotIn(asset.resolve().as_uri(), self.writer.spreads[0][1])

    def test_cover_prefers_writer_model_art_over_legacy_generic_art(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            docs = Path(td)
            assets = docs / "renderers" / "latex" / "assets"
            assets.mkdir(parents=True)
            generic = assets / "cover-en.pdf"
            jbp = assets / "cover_jbp2000b-en.pdf"
            generic.write_bytes(b"JE-1000F cover")
            jbp.write_bytes(b"JBP-2000B cover")

            selected = page_placed.placed_asset_for(
                "cover-en", "en", docs, model="JBP-2000B",
            )

        self.assertEqual(jbp, selected)

    def test_cover_resolves_historical_jp_language_to_canonical_ja_asset(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            docs = Path(td)
            assets = docs / "renderers" / "latex" / "assets"
            assets.mkdir(parents=True)
            canonical = assets / "cover_jbp2000b-ja.pdf"
            english = assets / "cover_jbp2000b-en.pdf"
            canonical.write_bytes(b"JBP-2000B Japanese cover")
            english.write_bytes(b"JBP-2000B English cover")

            selected = page_placed.placed_asset_for(
                "cover", "jp", docs, model="JBP-2000B",
            )

        self.assertEqual(canonical, selected)

    def test_cover_uses_same_model_english_fallback_not_generic_art(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            docs = Path(td)
            assets = docs / "renderers" / "latex" / "assets"
            assets.mkdir(parents=True)
            generic = assets / "cover-fr.pdf"
            jbp_en = assets / "cover_jbp2000b-en.pdf"
            generic.write_bytes(b"JE-1000F French cover")
            jbp_en.write_bytes(b"JBP-2000B English cover")

            selected = page_placed.placed_asset_for(
                "cover-fr", "fr", docs, model="JBP-2000B",
            )

        self.assertEqual(jbp_en, selected)

    def test_cover_does_not_use_legacy_generic_art_for_another_model(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            docs = Path(td)
            assets = docs / "renderers" / "latex" / "assets"
            assets.mkdir(parents=True)
            (assets / "cover-en.pdf").write_bytes(b"JE-1000F cover")

            selected = page_placed.placed_asset_for(
                "cover-en", "en", docs, model="JBP-2000B",
            )

        self.assertIsNone(selected)

    def test_cover_keeps_legacy_generic_fallback_for_owning_model(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            docs = Path(td)
            assets = docs / "renderers" / "latex" / "assets"
            assets.mkdir(parents=True)
            generic = assets / "cover-fr.pdf"
            generic.write_bytes(b"JE-1000F French cover")

            selected = page_placed.placed_asset_for(
                "cover-fr", "fr", docs, model="JE-1000F",
            )

        self.assertEqual(generic, selected)

    def test_jbp_back_cover_uses_model_qr_profile_without_reference_plan(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            docs = root / "docs"
            qr = docs / "renderers" / "latex" / "assets" / "back_cover_qr_jbp2000b.pdf"
            qr.parent.mkdir(parents=True)
            qr.write_bytes(b"JBP QR")
            self.writer.model = "JBP-2000B"

            added = page_placed.add_preferred_back_cover_page(
                self.writer,
                "US",
                "en",
                docs,
                27,
                {
                    "company": "JACKERY INC.",
                    "address": "5310 Bunche Dr., Fremont, CA 94538-8301",
                    "phone": "1-888-502-2236 (US)",
                    "lines": "hello@jackery.com\nwww.jackery.com",
                },
                reference_plan=None,
            )

        self.assertTrue(added)
        spread = self.writer.spreads[-1][1]
        self.assertIn("rc_st_back_cover_qr", spread)
        self.assertIn(qr.resolve().as_uri(), spread)

    def test_qr_only_back_cover_places_only_target_rect(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            docs = root / "docs"
            qr = docs / "renderers" / "latex" / "assets" / "kr-qr.pdf"
            qr.parent.mkdir(parents=True)
            qr.write_bytes(b"KR QR")
            profile = {
                "variant": "qr_only",
                "qr_asset": "docs/renderers/latex/assets/kr-qr.pdf",
                "qr_rect": [303.99, 457.81, 33.91, 34.02],
            }

            added = page_placed.add_back_cover_page(
                self.writer,
                "KR",
                17,
                {
                    "company": "JACKERY",
                    "address": "대한민국 전용",
                    "phone": "QR 코드를 참조하십시오",
                },
                profile=profile,
                docs_dir=docs,
            )

        self.assertTrue(added)
        self.assertEqual([], self.writer.stories)
        spread = self.writer.spreads[-1][1]
        self.assertIn('Self="rc_st_back_cover_qr"', spread)
        self.assertIn(qr.resolve().as_uri(), spread)
        self.assertNotIn("phone_ring", spread)
        self.assertNotIn("mail_box", spread)
        self.assertNotIn("web_ring", spread)
        x1, y1, x2, y2 = self.writer._page_rect(
            303.99, 457.81, 33.91, 34.02,
        )
        self.assertIn(f'Anchor="{x1:g} {y1:g}"', spread)
        self.assertIn(f'Anchor="{x2:g} {y2:g}"', spread)

    def test_toc_uses_source_titles_ranges_and_folios(self) -> None:
        self.writer.spreads = [(f"sp_{i}", f'<Spread Self="sp_{i}"/>') for i in range(4)]
        source = {
            "title": "SOURCE CONTENTS",
            "languages": [{
                "code": "EN", "label": "English", "page_range": "01-18",
                "entries": [{"title": "OPERATIONS", "folio": "07"}],
            }],
        }
        self.assertTrue(page_toc.finalize(
            self.writer, page_toc.TocCollector(),
            self.writer._add_story_parts, self.writer._psr, source=source))
        stories = "".join(xml for _, xml in self.writer.stories)
        self.assertIn("SOURCE CONTENTS", stories)
        self.assertIn("<Content>EN</Content>", stories)
        self.assertIn('Story Self="st_toc_bar_label_0"', stories)
        self.assertIn(
            'FontStyle="Bold" HorizontalScale="101.194"'
            "><Content>English</Content>",
            stories,
        )
        self.assertIn("01-18", stories)
        self.assertIn("<Content>OPERATIONS</Content>", stories)
        self.assertIn("<Content>07</Content>", stories)

    def test_toc_single_column_variant_keeps_all_entries_in_one_story(self) -> None:
        # A source-authored semantic TOC is virtual until finalize(), so the
        # eleven non-TOC spreads are present before the target's twelfth page
        # is inserted.
        self.writer.spreads = [
            (f"sp_{i}", f'<Spread Self="sp_{i}"/>') for i in range(11)
        ]
        source = {
            "title": "目次",
            "languages": [{
                "code": "JP",
                "label": "日本語",
                "page_range": "01--10",
                "entries": [
                    {"title": f"項目 {index}", "folio": f"{index:02d}"}
                    for index in range(1, 11)
                ],
            }],
        }
        page_plan = {
            "plan_source": "target-assembly",
            "physical_page_count": 12,
            "pages": [{
                "composition_type": "toc",
                "latex_start_page": 2,
                "planned_page_count": 1,
                "composition_data": {
                    "toc": {"layout_variant": "single_column"},
                },
            }],
        }

        self.assertTrue(page_toc.finalize(
            self.writer,
            page_toc.TocCollector(),
            self.writer._add_story_parts,
            self.writer._psr,
            source=source,
            page_plan=page_plan,
        ))

        story_ids = {sid for sid, _xml in self.writer.stories}
        self.assertIn("st_toc_seg0_c0", story_ids)
        self.assertNotIn("st_toc_seg0_c1", story_ids)
        toc_story = dict(self.writer.stories)["st_toc_seg0_c0"]
        self.assertIn(
            "<AppliedFont type=\"string\">HB Manual Sans JP (OTF)</AppliedFont>",
            toc_story,
        )
        self.assertEqual(12, len(self.writer.spreads))
        spread = self.writer.spreads[1][1]
        self.assertEqual(10, spread.count("gl_toc_leader_0_0_"))

    def test_special_page_macros_form_complete_ir_payloads(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            bundle = Path(td)
            page = bundle / "page"
            page.mkdir()
            (bundle / "index.rst").write_text(
                ".. include:: page/00_toc.rst\n.. include:: page/99_back_cover.rst\n",
                encoding="utf-8")
            (page / "00_toc.rst").write_text(
                ".. raw:: latex\n\n"
                "   \\HBTocPageBegin\\HBTocTitle{CONTENTS}"
                "\\HBTocLanguageBlock{EN}{English}{01--02}"
                "{\\HBTocEntry{OPERATIONS}{01}}{\\HBTocEntry{WARRANTY}{02}}"
                "\\HBTocPageEnd\n", encoding="utf-8")
            (page / "99_back_cover.rst").write_text(
                ".. raw:: latex\n\n"
                "   \\HBBackCoverPage{JACKERY INC.}{Fremont, CA}{1-888-502-2236}\n",
                encoding="utf-8")
            ir = build_manual_ir(
                root=ROOT, bundle_root=bundle, model="JE-1000F", region="US",
                lang="en", source="test", data_root=ROOT / "tests/fixtures/phase2")

        self.assertEqual([], ir_projection.same_source_issues(ir))
        self.assertEqual("CONTENTS", ir_projection.toc_page_data(ir)["title"])
        self.assertEqual("Fremont, CA", ir_projection.back_cover_data(ir)["address"])
        self.assertEqual("", ir_projection.back_cover_data(ir)["email"])
        self.assertEqual("", ir_projection.back_cover_data(ir)["web"])

    def test_five_field_back_cover_payload_renders_email_and_web(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            bundle = Path(td)
            page = bundle / "page"
            page.mkdir()
            (bundle / "index.rst").write_text(
                ".. include:: page/99_back_cover.rst\n", encoding="utf-8")
            (page / "99_back_cover.rst").write_text(
                ".. raw:: latex\n\n"
                "   \\HBBackCoverPage{JACKERY INC.}{Fremont, CA}"
                "{1-888-502-2236}{hello@jackery.com}{www.jackery.com}\n",
                encoding="utf-8",
            )
            ir = build_manual_ir(
                root=ROOT, bundle_root=bundle, model="JE-1000F", region="US",
                lang="en", source="test", data_root=ROOT / "tests/fixtures/phase2")

        copy = ir_projection.back_cover_data(ir)
        self.assertIsNotNone(copy)
        assert copy is not None
        self.assertEqual("hello@jackery.com", copy["email"])
        self.assertEqual("www.jackery.com", copy["web"])
        self.assertTrue(page_placed.add_back_cover_page(
            self.writer, "US", 0, copy))
        stories = "".join(xml for _, xml in self.writer.stories)
        self.assertIn("hello@jackery.com", stories)
        self.assertIn("www.jackery.com", stories)


if __name__ == "__main__":
    unittest.main()
