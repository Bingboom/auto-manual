from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.idml.web_edition import render_web_edition_from_pdf


def _make_pdf(path: Path, *, pages: int, text: str) -> None:
    import fitz

    doc = fitz.open()
    for index in range(pages):
        page = doc.new_page(width=612, height=792)
        page.insert_text((72, 72), f"{text} {index + 1}")
    doc.save(path)
    doc.close()


class WebEditionFromPdfTests(unittest.TestCase):
    def _render(self, *, pages: int = 3, text: str = "Operations page", title: str = "Sample Manual"):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        pdf = root / "manual_sample.pdf"
        _make_pdf(pdf, pages=pages, text=text)
        out_dir = root / "webedition"
        edition = render_web_edition_from_pdf(
            pdf,
            out_dir=out_dir,
            title=title,
            provenance={"version": "1.6", "source": "same-source LaTeX render"},
            log=lambda _m: None,
        )
        body = (out_dir / "body.html").read_text(encoding="utf-8")
        manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
        return edition, body, manifest, out_dir

    def test_rasterizes_one_card_per_page(self) -> None:
        edition, body, manifest, out_dir = self._render(pages=3)
        self.assertEqual(3, edition.page_count)
        self.assertEqual(3, body.count('class="we-sheet"'))
        self.assertEqual(3, len(list((out_dir / "assets").glob("page_*.png"))))
        self.assertIn("1 / 3", body)
        self.assertEqual(3, manifest["page_count"])
        self.assertIn('src="assets/page_001.png"', body)

    def test_toolbar_has_title_provenance_and_pdf_links(self) -> None:
        _, body, _, _ = self._render(title="Jackery Explorer 1000")
        self.assertIn("Jackery Explorer 1000", body)
        self.assertIn("v1.6", body)
        self.assertIn('href="assets/manual_sample.pdf" target="_blank"', body)
        self.assertIn('href="assets/manual_sample.pdf" download', body)

    def test_searchable_text_layer_present_and_escaped(self) -> None:
        _, body, _, _ = self._render(text="Press <b>POWER</b> button")
        self.assertIn('class="we-page-text"', body)
        # extracted text is HTML-escaped
        self.assertIn("&lt;b&gt;POWER&lt;/b&gt;", body)
        self.assertNotIn("<b>POWER</b>", body)

    def test_original_pdf_copied_for_download(self) -> None:
        edition, _, _, out_dir = self._render()
        self.assertEqual("manual_sample.pdf", edition.pdf_name)
        self.assertTrue((out_dir / "assets" / "manual_sample.pdf").is_file())

    def test_manifest_records_pdf_and_zoom(self) -> None:
        _, _, manifest, _ = self._render(pages=2)
        self.assertEqual("manual_sample.pdf", manifest["pdf"])
        self.assertEqual(2, manifest["page_count"])
        self.assertIn("render_zoom", manifest)


if __name__ == "__main__":
    unittest.main()
