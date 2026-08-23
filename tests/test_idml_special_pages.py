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
