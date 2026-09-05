from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from tools.idml_rst_extract import ExtractResult, _extract_raw_latex, _parse_text
from tools.manual_ir import build_manual_ir, validate_manual_ir


ROOT = Path(__file__).resolve().parents[1]


def _intro(title: str, *paragraphs: str) -> str:
    return (
        r"\par\noindent \begin{tcolorbox}[colback=BrandDark,width=\textwidth]"
        + r"{\color{white}\bfseries " + title + r"}\end{tcolorbox}"
        + "".join(r"\par\noindent " + paragraph for paragraph in paragraphs)
    )


class BoxedIntroTests(unittest.TestCase):
    def test_multilingual_intro_preserves_order_and_escaped_punctuation(self) -> None:
        for title in ("Symbols", "絵表示について", "기호 설명"):
            with self.subTest(title=title):
                result = ExtractResult()
                _extract_raw_latex(_intro(title, r"First: 50\% \& A\_B.", "Second."), result)
                self.assertEqual(result.skipped_raw, 0)
                self.assertEqual(result.blocks, [
                    ("h2", title), ("body", "First: 50% & A_B."), ("body", "Second."),
                ])

    def test_incomplete_or_content_bearing_constructs_remain_skipped(self) -> None:
        valid = _intro("Symbols", "First.", "Second.")
        cases = (
            valid.replace(r"\end{tcolorbox}", ""),
            valid.replace("colback=BrandDark", "title=Hidden"),
            valid.replace("colback=BrandDark", r"overlay={\section{Hidden}}"),
            valid + r"\section{Extra}",
            valid.replace("First.", r"\unknown{Important}"),
            valid.replace("First.", r"\HBAppBody{Important}"),
            valid.replace("First.", "$x_1$"),
            valid.replace("First.", "A~B"),
            valid.replace("Symbols", " "),
            valid.replace("First.", " "),
            _intro("Symbols"),
            valid.replace("Second.", "Hidden % comment"),
            valid + _intro("Another", "Paragraph."),
        )
        for raw in cases:
            with self.subTest(raw=raw):
                result = ExtractResult()
                _extract_raw_latex(raw, result)
                self.assertEqual(result.blocks, [])
                self.assertEqual(result.skipped_raw, 1)

    def test_actual_jp_page_is_complete_in_strict_public_ir(self) -> None:
        source = ROOT / "docs/templates/page_jp/01_meaning_of_symbols.rst"
        text = source.read_text(encoding="utf-8")
        expected = [
            ("h2", "絵表示について"),
            ("body", "製品を安全に正しくお使いいただき、お客様や他の方々への危害や財産への損害を未然に防止するための表示です。"),
            ("body", "内容をよく理解してから本文をお読みください。"),
        ]
        extracted = _parse_text(text, {"latex", "region_jp"})
        start = extracted.blocks.index(expected[0])
        self.assertEqual(extracted.blocks[start:start + 3], expected)
        self.assertEqual(extracted.blocks[start + 3][0], "table")
        self.assertEqual(extracted.skipped_raw, 0)
        with tempfile.TemporaryDirectory() as td:
            bundle = Path(td)
            (bundle / "page").mkdir()
            (bundle / "page" / source.name).write_text(text, encoding="utf-8")
            (bundle / "index.rst").write_text(f".. include:: page/{source.name}\n", encoding="utf-8")
            ir = build_manual_ir(
                root=ROOT, bundle_root=bundle, model="JE-1000F", region="JP",
                lang="ja", source="runtime", data_root=ROOT / "tests/fixtures/phase2",
            )
        self.assertEqual(validate_manual_ir(
            ir, require_zero_skipped_raw=True, require_known_languages=True,
        ), [])
        blocks = [(block.kind, block.payload) for block in ir.pages[0].blocks]
        self.assertEqual(blocks[start:start + 3], expected)


if __name__ == "__main__":
    unittest.main()
