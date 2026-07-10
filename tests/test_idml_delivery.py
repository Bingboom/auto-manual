"""Tests for the publish IDML delivery package (tools/idml/delivery.py)."""
from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

from tools.idml.delivery import build_delivery_package
from tools.idml.params import MIMETYPE

_IDPKG = "http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging"


def _write_production_idml(path: Path, uris: list[str]) -> None:
    """Minimal IDML honoring the zip contract check_idml enforces."""
    rectangles = "".join(
        f'<Rectangle Self="r{i}"><Image Self="r{i}_img">'
        f'<Link Self="r{i}_lnk" LinkResourceURI="{escape(uri, {chr(34): "&quot;"})}"/>'
        "</Image></Rectangle>"
        for i, uri in enumerate(uris)
    )
    story = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        f'<idPkg:Story xmlns:idPkg="{_IDPKG}"><Story Self="s1">{rectangles}</Story></idPkg:Story>\n'
    )
    designmap = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        f'<Document xmlns:idPkg="{_IDPKG}" Self="doc">'
        '<idPkg:Story src="Stories/Story_s1.xml"/></Document>\n'
    )
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr(zipfile.ZipInfo("mimetype"), MIMETYPE, compress_type=zipfile.ZIP_STORED)
        zf.writestr("designmap.xml", designmap, compress_type=zipfile.ZIP_DEFLATED)
        zf.writestr("Stories/Story_s1.xml", story, compress_type=zipfile.ZIP_DEFLATED)


def _write_handoff_tree(root: Path) -> Path:
    handoff = root / "idml"
    (handoff / "flow").mkdir(parents=True)
    (handoff / "production").mkdir()
    (handoff / "flow" / "manual.flow.idml").write_bytes(b"flow-idml")
    (handoff / "flow" / "manual.flow.md").write_text("flow md\n", encoding="utf-8")
    (handoff / "designer_checklist.md").write_text("checklist\n", encoding="utf-8")
    (handoff / "layout_feedback.md").write_text("feedback\n", encoding="utf-8")
    (handoff / "missing_assets_report.md").write_text("missing\n", encoding="utf-8")
    (handoff / "production" / "source_trace.json").write_text(
        json.dumps({"version": "unknown", "model": "JE-1000F"}), encoding="utf-8"
    )
    return handoff


class BuildDeliveryPackageTest(unittest.TestCase):
    def _fixture(self, root: Path) -> tuple[Path, Path, list[str]]:
        (root / "a").mkdir()
        (root / "b").mkdir()
        image_a = root / "a" / "img.png"
        image_b = root / "b" / "img.png"
        image_a.write_bytes(b"png-a")
        image_b.write_bytes(b"png-b")
        uris = [
            image_a.resolve().as_uri(),
            image_b.resolve().as_uri(),
            (root / "gone.png").resolve().as_uri(),
        ]
        idml = root / "manual.idml"
        _write_production_idml(idml, uris)
        return idml, _write_handoff_tree(root), uris

    def test_collects_links_rewrites_uris_and_reports_missing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            idml, handoff, uris = self._fixture(root)
            out = build_delivery_package(
                production_idml=idml,
                handoff_root=handoff,
                out_zip=root / "manual_publish_1.5_handoff.zip",
                idml_arcname="manual_publish_1.5.idml",
                version="1.5",
            )

            with zipfile.ZipFile(out.zip_path) as zf:
                names = set(zf.namelist())
                self.assertIn("manual_publish_1.5.idml", names)
                self.assertIn("Links/img.png", names)
                self.assertIn("Links/img__2.png", names)
                self.assertIn("flow/manual.flow.idml", names)
                self.assertIn("flow/manual.flow.md", names)
                self.assertIn("designer_checklist.md", names)
                self.assertIn("source_trace.json", names)
                self.assertIn("fonts_manifest.md", names)
                self.assertIn("export_notes.md", names)
                self.assertNotIn("reference/manual.pdf", names)

                self.assertEqual(b"png-a", zf.read("Links/img.png"))
                self.assertEqual(b"png-b", zf.read("Links/img__2.png"))
                trace = json.loads(zf.read("source_trace.json"))
                self.assertEqual("1.5", trace["version"])
                notes = zf.read("export_notes.md").decode("utf-8")
                self.assertIn("gone.png", notes)

                inner = root / "inner.idml"
                inner.write_bytes(zf.read("manual_publish_1.5.idml"))
            with zipfile.ZipFile(inner) as zf:
                first = zf.infolist()[0]
                self.assertEqual("mimetype", first.filename)
                self.assertEqual(zipfile.ZIP_STORED, first.compress_type)
                story = zf.read("Stories/Story_s1.xml").decode("utf-8")
                self.assertIn('LinkResourceURI="file:Links/img.png"', story)
                self.assertIn('LinkResourceURI="file:Links/img__2.png"', story)
                self.assertIn(escape(uris[2], {'"': "&quot;"}), story)

            self.assertEqual([uris[2]], out.missing_links)
            self.assertEqual(2, len(out.links))

    def test_fonts_are_opt_in(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            idml, handoff, _ = self._fixture(root)
            fonts_dir = root / "fonts"
            fonts_dir.mkdir()
            (fonts_dir / "Gilroy-Regular.otf").write_bytes(b"font")
            (fonts_dir / "notes.txt").write_text("not a font", encoding="utf-8")

            with_fonts = build_delivery_package(
                production_idml=idml, handoff_root=handoff,
                out_zip=root / "with_fonts.zip", fonts_dir=fonts_dir,
            )
            with zipfile.ZipFile(with_fonts.zip_path) as zf:
                names = set(zf.namelist())
                self.assertIn("Document fonts/Gilroy-Regular.otf", names)
                self.assertNotIn("Document fonts/notes.txt", names)
                manifest = zf.read("fonts_manifest.md").decode("utf-8")
                self.assertIn("included under `Document fonts/`", manifest)

            without_fonts = build_delivery_package(
                production_idml=idml, handoff_root=handoff,
                out_zip=root / "without_fonts.zip",
            )
            with zipfile.ZipFile(without_fonts.zip_path) as zf:
                names = set(zf.namelist())
                self.assertFalse(any(n.startswith("Document fonts/") for n in names))
                manifest = zf.read("fonts_manifest.md").decode("utf-8")
                self.assertIn("No font files are included", manifest)

    def test_reference_pdf_is_included_when_given(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            idml, handoff, _ = self._fixture(root)
            pdf = root / "manual_publish_1.5.pdf"
            pdf.write_bytes(b"%PDF-fake")
            out = build_delivery_package(
                production_idml=idml, handoff_root=handoff,
                out_zip=root / "with_pdf.zip", reference_pdf=pdf,
            )
            with zipfile.ZipFile(out.zip_path) as zf:
                self.assertIn("reference/manual_publish_1.5.pdf", zf.namelist())
                self.assertEqual(b"%PDF-fake", zf.read("reference/manual_publish_1.5.pdf"))


if __name__ == "__main__":
    unittest.main()
