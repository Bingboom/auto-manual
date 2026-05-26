from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET

from tools.word_bundle_docx import (
    WordComExportError,
    _export_docx_via_word,
    _embed_external_docx_images,
    _enforce_docx_outline_levels,
    _remap_reference_doc_styles,
    _word_com_timeout_seconds,
    export_word_from_bundle,
)
from tools.word_bundle_docx_pandoc import ensure_supported_pandoc_for_reference_doc, resolve_pandoc_binary
from tools.word_bundle_html import WordBundlePageMeta

_W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_W = "{%s}" % _W_NS
_NS = {"w": _W_NS}
_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
_DOC_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_DRAWING_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
_MC_NS = "http://schemas.openxmlformats.org/markup-compatibility/2006"
_W14_NS = "http://schemas.microsoft.com/office/word/2010/wordml"
_W15_NS = "http://schemas.microsoft.com/office/word/2012/wordml"
_WP14_NS = "http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing"


class TestWordBundleDocx(unittest.TestCase):
    def test_word_com_timeout_seconds_should_parse_env_override(self) -> None:
        with patch.dict(os.environ, {"AUTO_MANUAL_WORD_COM_TIMEOUT_SECONDS": "45"}, clear=False):
            self.assertEqual(45, _word_com_timeout_seconds())
        with patch.dict(os.environ, {"AUTO_MANUAL_WORD_COM_TIMEOUT_SECONDS": "off"}, clear=False):
            self.assertIsNone(_word_com_timeout_seconds())

    def test_export_docx_via_word_should_cleanup_and_raise_on_timeout(self) -> None:
        with patch("tools.word_bundle_docx.sys.platform", "win32"), \
            patch.dict(os.environ, {"AUTO_MANUAL_WORD_COM_TIMEOUT_SECONDS": "12"}, clear=False), \
            patch("tools.word_bundle_docx.subprocess.run") as run_mock, \
            patch("tools.word_bundle_docx._cleanup_timed_out_word_processes") as cleanup_mock:
            run_mock.side_effect = subprocess.TimeoutExpired(cmd=["powershell"], timeout=12)

            with self.assertRaisesRegex(WordComExportError, "timed out after 12s"):
                _export_docx_via_word(Path("bundle.html"), Path("out.docx"), None)

            self.assertEqual(12, run_mock.call_args.kwargs["timeout"])
            cleanup_mock.assert_called_once()

    def test_export_word_from_bundle_should_retry_with_pandoc_when_word_com_fails(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bundle_html = root / "manual_bundle.html"
            bundle_html.write_text("<html><body>demo</body></html>", encoding="utf-8")
            out_path = root / "manual.docx"

            with patch("tools.word_bundle_docx.build_word_bundle_html", return_value=(bundle_html, None, ())), \
                patch("tools.word_bundle_docx._export_docx_via_word", side_effect=WordComExportError("boom")) as word_mock, \
                patch("tools.word_bundle_docx._export_docx_via_pandoc") as pandoc_mock, \
                patch("tools.word_bundle_docx._docx_is_valid", return_value=True), \
                patch("tools.word_bundle_docx._embed_external_docx_images") as images_mock, \
                patch("tools.word_bundle_docx._remap_reference_doc_styles") as styles_mock, \
                patch("tools.word_bundle_docx._enforce_docx_outline_levels") as outline_mock:
                result = export_word_from_bundle({}, "JE-1000F", "JP", str(out_path), output_dir=root)

            self.assertEqual(out_path, result)
            word_mock.assert_called_once()
            pandoc_mock.assert_called_once_with(bundle_html, out_path, None)
            images_mock.assert_called_once_with(out_path)
            styles_mock.assert_called_once_with(out_path, ())
            outline_mock.assert_called_once_with(out_path)

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
                styles_xml = ET.fromstring(bundle.read("word/styles.xml"))
                numbering_xml = ET.fromstring(bundle.read("word/numbering.xml"))

            body = root_xml.find("w:body", _NS)
            self.assertIsNotNone(body)
            blocks = [child for child in list(body) if child.tag in {f"{_W}p", f"{_W}tbl"}]

            self.assertEqual("dingding-heading1", self._paragraph_style(blocks[0]))
            self.assertEqual("34", self._paragraph_run_size(blocks[0]))
            self.assertEqual("000000", self._paragraph_run_color(blocks[0]))
            self.assertTrue(self._paragraph_run_bold(blocks[0]))
            self.assertEqual("", self._paragraph_style(blocks[1]))

            self.assertEqual("dingding-heading1", self._paragraph_style(blocks[2]))
            self.assertEqual("34", self._paragraph_run_size(blocks[2]))
            self.assertEqual("000000", self._paragraph_run_color(blocks[2]))
            self.assertTrue(self._paragraph_run_bold(blocks[2]))
            self.assertEqual("Compact", self._paragraph_style(blocks[3]))
            self.assertEqual("Table", self._table_style(blocks[4]))
            self.assertEqual(("pct", "5000"), self._table_width(blocks[4]))
            self.assertEqual("fixed", self._table_layout(blocks[4]))
            self.assertEqual(["1267", "6653"], self._table_grid_widths(blocks[4]))
            self.assertEqual(
                {
                    "top": ("single", "4", "0", "000000"),
                    "left": ("single", "4", "0", "000000"),
                    "bottom": ("single", "4", "0", "000000"),
                    "right": ("single", "4", "0", "000000"),
                    "insideH": ("single", "4", "0", "000000"),
                    "insideV": ("single", "4", "0", "000000"),
                },
                self._table_borders(blocks[4]),
            )
            self.assertEqual([("pct", "800"), ("pct", "4200")], self._first_row_cell_widths(blocks[4]))
            self.assertEqual(
                {"top": "120", "left": "120", "bottom": "120", "right": "120"},
                self._table_cell_margins(blocks[4]),
            )
            self.assertEqual(["top", "top"], self._first_row_cell_vertical_alignments(blocks[4]))
            self.assertEqual("FirstParagraph", self._paragraph_style(blocks[4].find(".//w:p", _NS)))
            self.assertEqual("dingding-heading2", self._paragraph_style(blocks[5]))
            self.assertEqual("28", self._paragraph_run_size(blocks[5]))
            self.assertEqual("343031", self._paragraph_run_color(blocks[5]))
            self.assertTrue(self._paragraph_run_bold(blocks[5]))

            self.assertEqual("dingding-heading1", self._paragraph_style(blocks[6]))
            self.assertEqual("34", self._paragraph_run_size(blocks[6]))
            self.assertEqual("000000", self._paragraph_run_color(blocks[6]))
            self.assertTrue(self._paragraph_run_bold(blocks[6]))
            self.assertEqual("TableGrid", self._table_style(blocks[7]))
            first_box_cell = blocks[7].find(".//w:p", _NS)
            self.assertIsNotNone(first_box_cell)
            self.assertEqual("", self._paragraph_style(first_box_cell))
            table_list_item = next(
                para
                for para in blocks[7].findall(".//w:p", _NS)
                if "".join(para.itertext()) == "Numbered table item."
            )
            self.assertEqual(("", ""), self._paragraph_indent(table_list_item))
            self.assertEqual(
                ("decimal", "%1."),
                self._numbering_format(numbering_xml, self._paragraph_num_id(table_list_item)),
            )
            self.assertEqual("dingding-heading2", self._paragraph_style(blocks[8]))
            self.assertEqual("28", self._paragraph_run_size(blocks[8]))
            self.assertEqual("343031", self._paragraph_run_color(blocks[8]))
            self.assertTrue(self._paragraph_run_bold(blocks[8]))
            self.assertEqual("", self._paragraph_style(blocks[9]))

            self.assertEqual("dingding-heading1", self._paragraph_style(blocks[10]))
            self.assertEqual("34", self._paragraph_run_size(blocks[10]))
            self.assertEqual("000000", self._paragraph_run_color(blocks[10]))
            self.assertTrue(self._paragraph_run_bold(blocks[10]))
            self.assertEqual("Table", self._table_style(blocks[11]))
            self.assertEqual(("pct", "5000"), self._table_width(blocks[11]))
            self.assertEqual("fixed", self._table_layout(blocks[11]))
            self.assertEqual(["2614", "5306"], self._table_grid_widths(blocks[11]))
            self.assertEqual(
                {
                    "top": ("single", "4", "0", "000000"),
                    "left": ("single", "4", "0", "000000"),
                    "bottom": ("single", "4", "0", "000000"),
                    "right": ("single", "4", "0", "000000"),
                    "insideH": ("single", "4", "0", "000000"),
                    "insideV": ("single", "4", "0", "000000"),
                },
                self._table_borders(blocks[11]),
            )
            self.assertEqual([("pct", "1650"), ("pct", "3350")], self._first_row_cell_widths(blocks[11]))

            self.assertEqual("dingding-heading1", self._paragraph_style(blocks[12]))
            self.assertEqual("34", self._paragraph_run_size(blocks[12]))
            self.assertEqual("000000", self._paragraph_run_color(blocks[12]))
            self.assertTrue(self._paragraph_run_bold(blocks[12]))
            self.assertEqual("", self._style_shading(styles_xml, "dingding-heading1"))
            self.assertFalse(self._style_has_paragraph_borders(styles_xml, "dingding-heading1"))
            self.assertEqual("000000", self._style_run_color(styles_xml, "dingding-heading1"))
            self.assertEqual("", self._style_num_id(styles_xml, "dingding-heading1"))
            self.assertEqual("", self._style_num_id(styles_xml, "dingding-heading2"))
            self.assertEqual("", self._style_num_id(styles_xml, "dingding-heading3"))

    def test_remap_reference_doc_styles_should_preserve_markup_compatibility_prefixes(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            docx_path = root / "demo.docx"
            self._write_minimal_docx(docx_path, with_markup_compat=True)

            page_metas = (WordBundlePageMeta(source_path=Path("00_preface.rst"), anchor_text="IMPORTANT"),)

            _remap_reference_doc_styles(docx_path, page_metas)

            self._assert_markup_compatibility_prefixes(docx_path)

    def test_enforce_docx_outline_levels_should_preserve_markup_compatibility_prefixes(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            docx_path = root / "demo.docx"
            self._write_minimal_docx(docx_path, with_markup_compat=True)

            _enforce_docx_outline_levels(docx_path)

            self._assert_markup_compatibility_prefixes(docx_path)

    def test_remap_reference_doc_styles_should_create_missing_heading3_style(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            docx_path = root / "demo.docx"
            self._write_minimal_docx(docx_path, with_reference_h3_style=False)

            page_metas = (WordBundlePageMeta(source_path=Path("00_preface.rst"), anchor_text="IMPORTANT"),)

            _remap_reference_doc_styles(docx_path, page_metas)

            with zipfile.ZipFile(docx_path) as bundle:
                styles_xml = ET.fromstring(bundle.read("word/styles.xml"))

            self.assertEqual("heading 3", self._style_name(styles_xml, "dingding-heading3"))
            self.assertEqual("343031", self._style_run_color(styles_xml, "dingding-heading3"))
            self.assertEqual("22", self._style_run_size(styles_xml, "dingding-heading3"))
            self.assertEqual("", self._style_num_id(styles_xml, "dingding-heading3"))

    def test_remap_reference_doc_styles_should_leave_table_decimal_lists_alone(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            docx_path = root / "demo.docx"
            self._write_minimal_docx(
                docx_path,
                include_high_decimal_numbering=True,
                table_list_num_id="1000",
            )

            page_metas = (WordBundlePageMeta(source_path=Path("00_preface.rst"), anchor_text="IMPORTANT"),)

            _remap_reference_doc_styles(docx_path, page_metas)

            with zipfile.ZipFile(docx_path) as bundle:
                root_xml = ET.fromstring(bundle.read("word/document.xml"))
                numbering_xml = ET.fromstring(bundle.read("word/numbering.xml"))

            table_list_item = next(
                para
                for para in root_xml.findall(".//w:tbl//w:p", _NS)
                if "".join(para.itertext()) == "Numbered table item."
            )
            self.assertEqual("1000", self._paragraph_num_id(table_list_item))
            self.assertEqual(("decimal", "%1."), self._numbering_format(numbering_xml, "1000"))

    def test_enforce_docx_outline_levels_should_support_heading3(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            docx_path = root / "demo.docx"
            self._write_minimal_docx(docx_path, with_heading3=True)

            _enforce_docx_outline_levels(docx_path)

            with zipfile.ZipFile(docx_path) as bundle:
                root_xml = ET.fromstring(bundle.read("word/document.xml"))

            body = root_xml.find("w:body", _NS)
            self.assertIsNotNone(body)
            blocks = [child for child in list(body) if child.tag == f"{_W}p"]
            heading3 = next(block for block in blocks if "".join(block.itertext()) == "Connect to High-PV Input Port")

            self.assertEqual("Heading3", self._paragraph_style(heading3))
            self.assertEqual("2", self._paragraph_outline_level(heading3))
            self.assertEqual("22", self._paragraph_run_size(heading3))
            self.assertTrue(self._paragraph_run_bold(heading3))

    def test_older_pandoc_version_should_be_rejected_for_reference_doc_exports(self) -> None:
        with patch(
            "tools.word_bundle_docx_pandoc.subprocess.run",
            return_value=subprocess.CompletedProcess(
                args=["pandoc", "--version"],
                returncode=0,
                stdout="pandoc 3.8.2\n",
            ),
        ):
            with self.assertRaisesRegex(RuntimeError, "pandoc 3.8.2"):
                ensure_supported_pandoc_for_reference_doc("pandoc", Path("reference_en.docx"))

    def test_newer_pandoc_version_should_be_allowed_for_reference_doc_exports(self) -> None:
        with patch(
            "tools.word_bundle_docx_pandoc.subprocess.run",
            return_value=subprocess.CompletedProcess(
                args=["pandoc", "--version"],
                returncode=0,
                stdout="pandoc 3.9.0.2\n",
            ),
        ):
            ensure_supported_pandoc_for_reference_doc("pandoc", Path("reference_en.docx"))

    def test_resolve_pandoc_binary_should_prefer_supported_reference_doc_candidate(self) -> None:
        def fake_run(args: list[str], check: bool, capture_output: bool, text: bool) -> subprocess.CompletedProcess[str]:
            binary = args[0]
            stdout = {
                "/opt/homebrew/bin/pandoc": "pandoc 3.8.2\n",
                "/usr/local/bin/pandoc": "pandoc 3.9.0.2\n",
            }[binary]
            return subprocess.CompletedProcess(args=args, returncode=0, stdout=stdout)

        with patch("tools.word_bundle_docx_pandoc.subprocess.run", side_effect=fake_run):
            resolved = resolve_pandoc_binary(
                Path("reference_en.docx"),
                candidates=("/opt/homebrew/bin/pandoc", "/usr/local/bin/pandoc"),
            )

        self.assertEqual("/usr/local/bin/pandoc", resolved)

    def _write_minimal_docx(
        self,
        path: Path,
        *,
        with_markup_compat: bool = False,
        with_heading3: bool = False,
        with_reference_h3_style: bool = True,
        include_high_decimal_numbering: bool = False,
        table_list_num_id: str = "1",
    ) -> None:
        reference_h3_style_xml = (
            '  <w:style w:type="paragraph" w:styleId="dingding-heading3"><w:name w:val="heading 3"/><w:pPr><w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr></w:pPr></w:style>\n'
            if with_reference_h3_style
            else ""
        )
        styles_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="{_W_NS}">
  <w:style w:type="paragraph" w:styleId="dingding-heading1"><w:name w:val="heading 1"/><w:pPr><w:shd w:fill="343031"/><w:pBdr><w:bottom w:val="single" w:sz="4"/></w:pBdr></w:pPr></w:style>
  <w:style w:type="paragraph" w:styleId="dingding-heading2"><w:name w:val="heading 2"/><w:pPr><w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr></w:pPr></w:style>
{reference_h3_style_xml}  <w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="Heading 1"/></w:style>
  <w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="Heading 2"/></w:style>
  <w:style w:type="paragraph" w:styleId="Heading3"><w:name w:val="Heading 3"/></w:style>
  <w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/></w:style>
  <w:style w:type="paragraph" w:styleId="BodyText"><w:name w:val="Body Text"/></w:style>
  <w:style w:type="paragraph" w:styleId="FirstParagraph"><w:name w:val="First Paragraph"/></w:style>
  <w:style w:type="paragraph" w:styleId="Compact"><w:name w:val="Compact"/></w:style>
  <w:style w:type="table" w:styleId="Table"><w:name w:val="Table"/></w:style>
  <w:style w:type="table" w:styleId="TableGrid"><w:name w:val="Table Grid"/></w:style>
  <w:style w:type="table" w:styleId="tableHeader"><w:name w:val="tableHeader"/></w:style>
</w:styles>
"""
        high_decimal_numbering_xml = (
            '  <w:abstractNum w:abstractNumId="99201">\n'
            '    <w:lvl w:ilvl="0"><w:numFmt w:val="decimal"/><w:lvlText w:val="%1."/><w:pPr><w:ind w:left="720" w:hanging="360"/></w:pPr></w:lvl>\n'
            "  </w:abstractNum>\n"
            '  <w:num w:numId="1000"><w:abstractNumId w:val="99201"/></w:num>\n'
            if include_high_decimal_numbering
            else ""
        )
        numbering_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:numbering xmlns:w="{_W_NS}">
  <w:abstractNum w:abstractNumId="0">
    <w:lvl w:ilvl="0"><w:numFmt w:val="decimal"/><w:lvlText w:val="%1."/><w:pPr><w:ind w:left="720" w:hanging="360"/></w:pPr></w:lvl>
  </w:abstractNum>
  <w:num w:numId="1"><w:abstractNumId w:val="0"/></w:num>
{high_decimal_numbering_xml}
</w:numbering>
"""
        document_root_attrs = [f'xmlns:w="{_W_NS}"']
        first_para_attrs = ""
        if with_markup_compat:
            document_root_attrs.extend(
                [
                    f'xmlns:mc="{_MC_NS}"',
                    f'xmlns:w14="{_W14_NS}"',
                    f'xmlns:w15="{_W15_NS}"',
                    f'xmlns:wp14="{_WP14_NS}"',
                    'mc:Ignorable="w14 w15 wp14"',
                ]
            )
            first_para_attrs = ' w14:paraId="4047BD08"'

        heading3_xml = ""
        if with_heading3:
            heading3_xml = (
                '<w:p><w:pPr><w:pStyle w:val="Heading3"/></w:pPr>'
                "<w:r><w:t>Connect to High-PV Input Port</w:t></w:r></w:p>"
            )

        document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document {' '.join(document_root_attrs)}>
  <w:body>
    <w:p{first_para_attrs}><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>IMPORTANT</w:t></w:r></w:p>
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
        <w:tc>
          <w:p><w:pPr><w:pStyle w:val="FirstParagraph"/></w:pPr><w:r><w:t>Main Unit</w:t></w:r></w:p>
          <w:p><w:pPr><w:numPr><w:ilvl w:val="0"/><w:numId w:val="{table_list_num_id}"/></w:numPr></w:pPr><w:r><w:t>Numbered table item.</w:t></w:r></w:p>
        </w:tc>
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
    {heading3_xml}
    <w:sectPr />
  </w:body>
</w:document>
"""

        with zipfile.ZipFile(path, "w") as bundle:
            bundle.writestr("word/styles.xml", styles_xml)
            bundle.writestr("word/numbering.xml", numbering_xml)
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

    def _paragraph_outline_level(self, para: ET.Element) -> str:
        outline = para.find("w:pPr/w:outlineLvl", _NS)
        return outline.attrib.get(f"{_W}val", "") if outline is not None else ""

    def _table_style(self, tbl: ET.Element) -> str:
        style = tbl.find("w:tblPr/w:tblStyle", _NS)
        return style.attrib.get(f"{_W}val", "") if style is not None else ""

    def _table_width(self, tbl: ET.Element) -> tuple[str, str]:
        tbl_w = tbl.find("w:tblPr/w:tblW", _NS)
        if tbl_w is None:
            return "", ""
        return tbl_w.attrib.get(f"{_W}type", ""), tbl_w.attrib.get(f"{_W}w", "")

    def _table_layout(self, tbl: ET.Element) -> str:
        tbl_layout = tbl.find("w:tblPr/w:tblLayout", _NS)
        return tbl_layout.attrib.get(f"{_W}type", "") if tbl_layout is not None else ""

    def _table_grid_widths(self, tbl: ET.Element) -> list[str]:
        return [col.attrib.get(f"{_W}w", "") for col in tbl.findall("w:tblGrid/w:gridCol", _NS)]

    def _table_borders(self, tbl: ET.Element) -> dict[str, tuple[str, str, str, str]]:
        borders = {}
        for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
            border = tbl.find(f"w:tblPr/w:tblBorders/w:{edge}", _NS)
            if border is None:
                continue
            borders[edge] = (
                border.attrib.get(f"{_W}val", ""),
                border.attrib.get(f"{_W}sz", ""),
                border.attrib.get(f"{_W}space", ""),
                border.attrib.get(f"{_W}color", ""),
            )
        return borders

    def _table_cell_margins(self, tbl: ET.Element) -> dict[str, str]:
        margins = {}
        for edge in ("top", "left", "bottom", "right"):
            margin = tbl.find(f"w:tblPr/w:tblCellMar/w:{edge}", _NS)
            if margin is not None:
                margins[edge] = margin.attrib.get(f"{_W}w", "")
        return margins

    def _first_row_cell_widths(self, tbl: ET.Element) -> list[tuple[str, str]]:
        first_row = tbl.find("w:tr", _NS)
        self.assertIsNotNone(first_row)
        widths: list[tuple[str, str]] = []
        for cell in first_row.findall("w:tc", _NS):
            tc_w = cell.find("w:tcPr/w:tcW", _NS)
            widths.append(("", "") if tc_w is None else (tc_w.attrib.get(f"{_W}type", ""), tc_w.attrib.get(f"{_W}w", "")))
        return widths

    def _first_row_cell_vertical_alignments(self, tbl: ET.Element) -> list[str]:
        first_row = tbl.find("w:tr", _NS)
        self.assertIsNotNone(first_row)
        alignments: list[str] = []
        for cell in first_row.findall("w:tc", _NS):
            valign = cell.find("w:tcPr/w:vAlign", _NS)
            alignments.append("" if valign is None else valign.attrib.get(f"{_W}val", ""))
        return alignments

    def _paragraph_run_size(self, para: ET.Element) -> str:
        size = para.find("w:r/w:rPr/w:sz", _NS)
        return size.attrib.get(f"{_W}val", "") if size is not None else ""

    def _paragraph_run_bold(self, para: ET.Element) -> bool:
        bold = para.find("w:r/w:rPr/w:b", _NS)
        return bold is not None and bold.attrib.get(f"{_W}val", "1") != "0"

    def _paragraph_indent(self, para: ET.Element) -> tuple[str, str]:
        ind = para.find("w:pPr/w:ind", _NS)
        if ind is None:
            return "", ""
        return ind.attrib.get(f"{_W}left", ""), ind.attrib.get(f"{_W}hanging", "")

    def _paragraph_num_id(self, para: ET.Element) -> str:
        num_id = para.find("w:pPr/w:numPr/w:numId", _NS)
        return num_id.attrib.get(f"{_W}val", "") if num_id is not None else ""

    def _paragraph_run_color(self, para: ET.Element) -> str:
        color = para.find("w:r/w:rPr/w:color", _NS)
        return color.attrib.get(f"{_W}val", "") if color is not None else ""

    def _style_by_id(self, styles: ET.Element, style_id: str) -> ET.Element:
        style = styles.find(f".//w:style[@w:styleId='{style_id}']", _NS)
        self.assertIsNotNone(style)
        return style

    def _style_shading(self, styles: ET.Element, style_id: str) -> str:
        shd = self._style_by_id(styles, style_id).find("w:pPr/w:shd", _NS)
        return shd.attrib.get(f"{_W}fill", "") if shd is not None else ""

    def _style_has_paragraph_borders(self, styles: ET.Element, style_id: str) -> bool:
        return self._style_by_id(styles, style_id).find("w:pPr/w:pBdr", _NS) is not None

    def _style_name(self, styles: ET.Element, style_id: str) -> str:
        name = self._style_by_id(styles, style_id).find("w:name", _NS)
        return name.attrib.get(f"{_W}val", "") if name is not None else ""

    def _style_run_color(self, styles: ET.Element, style_id: str) -> str:
        color = self._style_by_id(styles, style_id).find("w:rPr/w:color", _NS)
        return color.attrib.get(f"{_W}val", "") if color is not None else ""

    def _style_run_size(self, styles: ET.Element, style_id: str) -> str:
        size = self._style_by_id(styles, style_id).find("w:rPr/w:sz", _NS)
        return size.attrib.get(f"{_W}val", "") if size is not None else ""

    def _style_num_id(self, styles: ET.Element, style_id: str) -> str:
        num_id = self._style_by_id(styles, style_id).find("w:pPr/w:numPr/w:numId", _NS)
        return num_id.attrib.get(f"{_W}val", "") if num_id is not None else ""

    def _numbering_format(self, numbering: ET.Element, num_id: str) -> tuple[str, str]:
        abstract_id = numbering.find(f".//w:num[@w:numId='{num_id}']/w:abstractNumId", _NS)
        self.assertIsNotNone(abstract_id)
        abstract = abstract_id.attrib.get(f"{_W}val", "")
        lvl = numbering.find(f".//w:abstractNum[@w:abstractNumId='{abstract}']/w:lvl", _NS)
        self.assertIsNotNone(lvl)
        num_fmt = lvl.find("w:numFmt", _NS)
        lvl_text = lvl.find("w:lvlText", _NS)
        return (
            num_fmt.attrib.get(f"{_W}val", "") if num_fmt is not None else "",
            lvl_text.attrib.get(f"{_W}val", "") if lvl_text is not None else "",
        )

    def _assert_markup_compatibility_prefixes(self, path: Path) -> None:
        with zipfile.ZipFile(path) as bundle:
            document_xml = bundle.read("word/document.xml").decode("utf-8")

        self.assertIn(f'xmlns:mc="{_MC_NS}"', document_xml)
        self.assertIn(f'xmlns:w14="{_W14_NS}"', document_xml)
        self.assertIn(f'xmlns:w15="{_W15_NS}"', document_xml)
        self.assertIn(f'xmlns:wp14="{_WP14_NS}"', document_xml)
        self.assertIn('mc:Ignorable="w14 w15 wp14"', document_xml)


if __name__ == "__main__":
    unittest.main()
