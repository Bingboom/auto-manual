from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from tools.word_bundle_docx import _embed_external_docx_images, _remap_reference_doc_styles
from tools.word_bundle_html import WordBundlePageMeta

_W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_W = "{%s}" % _W_NS
_NS = {"w": _W_NS}
_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
_DOC_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_DRAWING_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"


class TestWordBundleDocx(unittest.TestCase):
    def test_embed_external_docx_images_should_promote_internalized_links_to_embeds(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            image_path = root / "sample.png"
            image_path.write_bytes(
                bytes.fromhex(
                    "89504E470D0A1A0A"
                    "0000000D49484452000000010000000108060000001F15C489"
                    "0000000D49444154789C6360000002000154A24F5D00000000"
                    "49454E44AE426082"
                )
            )

            docx_path = root / "linked.docx"
            self._write_linked_image_docx(docx_path, image_path)

            _embed_external_docx_images(docx_path)

            with zipfile.ZipFile(docx_path) as bundle:
                rels_xml = ET.fromstring(bundle.read("word/_rels/document.xml.rels"))
                document_xml = ET.fromstring(bundle.read("word/document.xml"))
                media_names = set(bundle.namelist())

            rel = rels_xml.find(f"{{{_REL_NS}}}Relationship")
            self.assertIsNotNone(rel)
            self.assertEqual("media/image1.png", rel.attrib.get("Target"))
            self.assertNotIn("TargetMode", rel.attrib)

            blip = document_xml.find(f".//{{{_DRAWING_NS}}}blip")
            self.assertIsNotNone(blip)
            self.assertEqual("rId1", blip.attrib.get(f"{{{_DOC_REL_NS}}}embed"))
            self.assertNotIn(f"{{{_DOC_REL_NS}}}link", blip.attrib)
            self.assertIn("word/media/image1.png", media_names)

    def test_remap_reference_doc_styles_should_update_non_preserved_pages_only(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            docx_path = root / "demo.docx"
            self._write_minimal_docx(docx_path)

            page_metas = (
                WordBundlePageMeta(source_path=Path("00_preface.rst"), anchor_text="IMPORTANT"),
                WordBundlePageMeta(source_path=Path("safety_en.rst"), anchor_text="IMPORTANT SAFETY INFORMATION"),
                WordBundlePageMeta(source_path=Path("02_whats_in_the_box.rst"), anchor_text="WHAT'S IN THE BOX"),
                WordBundlePageMeta(source_path=Path("spec_en.rst"), anchor_text="SPECIFICATIONS"),
                WordBundlePageMeta(source_path=Path("11_warranty.rst"), anchor_text="WARRANTY"),
            )

            _remap_reference_doc_styles(docx_path, page_metas)

            with zipfile.ZipFile(docx_path) as bundle:
                root_xml = ET.fromstring(bundle.read("word/document.xml"))

            body = root_xml.find("w:body", _NS)
            self.assertIsNotNone(body)
            blocks = [child for child in list(body) if child.tag in {f"{_W}p", f"{_W}tbl"}]

            self.assertEqual("dingding-heading1", self._paragraph_style(blocks[0]))
            self.assertEqual("", self._paragraph_style(blocks[1]))

            self.assertEqual("dingding-heading1", self._paragraph_style(blocks[2]))
            self.assertEqual("Compact", self._paragraph_style(blocks[3]))
            self.assertEqual("Table", self._table_style(blocks[4]))
            self.assertEqual("FirstParagraph", self._paragraph_style(blocks[4].find(".//w:p", _NS)))
            self.assertEqual("dingding-heading2", self._paragraph_style(blocks[5]))

            self.assertEqual("dingding-heading1", self._paragraph_style(blocks[6]))
            self.assertEqual("TableGrid", self._table_style(blocks[7]))
            first_box_cell = blocks[7].find(".//w:p", _NS)
            self.assertIsNotNone(first_box_cell)
            self.assertEqual("", self._paragraph_style(first_box_cell))
            self.assertEqual("dingding-heading2", self._paragraph_style(blocks[8]))
            self.assertEqual("", self._paragraph_style(blocks[9]))

            self.assertEqual("dingding-heading1", self._paragraph_style(blocks[10]))
            self.assertEqual("Table", self._table_style(blocks[11]))

            self.assertEqual("dingding-heading1", self._paragraph_style(blocks[12]))

    def _write_minimal_docx(self, path: Path) -> None:
        styles_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="{_W_NS}">
  <w:style w:type="paragraph" w:styleId="dingding-heading1"><w:name w:val="heading 1"/></w:style>
  <w:style w:type="paragraph" w:styleId="dingding-heading2"><w:name w:val="heading 2"/></w:style>
  <w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="Heading 1"/></w:style>
  <w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="Heading 2"/></w:style>
  <w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/></w:style>
  <w:style w:type="paragraph" w:styleId="BodyText"><w:name w:val="Body Text"/></w:style>
  <w:style w:type="paragraph" w:styleId="FirstParagraph"><w:name w:val="First Paragraph"/></w:style>
  <w:style w:type="paragraph" w:styleId="Compact"><w:name w:val="Compact"/></w:style>
  <w:style w:type="table" w:styleId="Table"><w:name w:val="Table"/></w:style>
  <w:style w:type="table" w:styleId="TableGrid"><w:name w:val="Table Grid"/></w:style>
  <w:style w:type="table" w:styleId="tableHeader"><w:name w:val="tableHeader"/></w:style>
</w:styles>
"""
        document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="{_W_NS}">
  <w:body>
    <w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>IMPORTANT</w:t></w:r></w:p>
    <w:p><w:pPr><w:pStyle w:val="BodyText"/></w:pPr><w:r><w:t>Intro body.</w:t></w:r></w:p>
    <w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>IMPORTANT SAFETY INFORMATION</w:t></w:r></w:p>
    <w:p><w:pPr><w:pStyle w:val="Compact"/></w:pPr><w:r><w:t>Safety bullet.</w:t></w:r></w:p>
    <w:tbl>
      <w:tblPr><w:tblStyle w:val="Table"/></w:tblPr>
      <w:tr>
        <w:tc><w:p><w:pPr><w:pStyle w:val="FirstParagraph"/></w:pPr><w:r><w:t>WARNING</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:pPr><w:pStyle w:val="BodyText"/></w:pPr><w:r><w:t>Keep dry.</w:t></w:r></w:p></w:tc>
      </w:tr>
    </w:tbl>
    <w:p><w:pPr><w:pStyle w:val="Heading2"/></w:pPr><w:r><w:t>OPERATING INSTRUCTIONS</w:t></w:r></w:p>
    <w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>WHAT'S IN THE BOX</w:t></w:r></w:p>
    <w:tbl>
      <w:tblPr><w:tblStyle w:val="Table"/></w:tblPr>
      <w:tr>
        <w:tc><w:p><w:pPr><w:pStyle w:val="FirstParagraph"/></w:pPr><w:r><w:t>Main Unit</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:pPr><w:pStyle w:val="BodyText"/></w:pPr><w:r><w:t>AC Cable</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:pPr><w:pStyle w:val="Compact"/></w:pPr><w:r><w:t>Manual</w:t></w:r></w:p></w:tc>
      </w:tr>
    </w:tbl>
    <w:p><w:pPr><w:pStyle w:val="Heading2"/></w:pPr><w:r><w:t>DETAILS</w:t></w:r></w:p>
    <w:p><w:pPr><w:pStyle w:val="FirstParagraph"/></w:pPr><w:r><w:t>Box text.</w:t></w:r></w:p>
    <w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>SPECIFICATIONS</w:t></w:r></w:p>
    <w:tbl>
      <w:tblPr><w:tblStyle w:val="Table"/></w:tblPr>
      <w:tr><w:tc><w:p><w:r><w:t>Product Name</w:t></w:r></w:p></w:tc><w:tc><w:p><w:r><w:t>Demo</w:t></w:r></w:p></w:tc></w:tr>
      <w:tr><w:tc><w:p><w:r><w:t>Model</w:t></w:r></w:p></w:tc><w:tc><w:p><w:r><w:t>M1</w:t></w:r></w:p></w:tc></w:tr>
    </w:tbl>
    <w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>WARRANTY</w:t></w:r></w:p>
    <w:sectPr />
  </w:body>
</w:document>
"""

        with zipfile.ZipFile(path, "w") as bundle:
            bundle.writestr("word/styles.xml", styles_xml)
            bundle.writestr("word/document.xml", document_xml)

    def _write_linked_image_docx(self, path: Path, image_path: Path) -> None:
        image_target = image_path.resolve(strict=False).as_uri()
        content_types_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>
"""
        rels_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="{_REL_NS}">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="{image_target}" TargetMode="External"/>
</Relationships>
"""
        document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="{_W_NS}" xmlns:a="{_DRAWING_NS}" xmlns:r="{_DOC_REL_NS}">
  <w:body>
    <w:p>
      <w:r>
        <w:drawing>
          <a:graphic>
            <a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">
              <pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">
                <pic:blipFill>
                  <a:blip r:link="rId1"/>
                </pic:blipFill>
              </pic:pic>
            </a:graphicData>
          </a:graphic>
        </w:drawing>
      </w:r>
    </w:p>
    <w:sectPr />
  </w:body>
</w:document>
"""
        with zipfile.ZipFile(path, "w") as bundle:
            bundle.writestr("[Content_Types].xml", content_types_xml)
            bundle.writestr("word/document.xml", document_xml)
            bundle.writestr("word/_rels/document.xml.rels", rels_xml)

    def _paragraph_style(self, para: ET.Element) -> str:
        style = para.find("w:pPr/w:pStyle", _NS)
        return style.attrib.get(f"{_W}val", "") if style is not None else ""

    def _table_style(self, tbl: ET.Element) -> str:
        style = tbl.find("w:tblPr/w:tblStyle", _NS)
        return style.attrib.get(f"{_W}val", "") if style is not None else ""


if __name__ == "__main__":
    unittest.main()
