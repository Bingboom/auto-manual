from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools import pdf_annotate

try:
    import fitz  # noqa: F401

    _HAS_FITZ = True
except ImportError:  # pragma: no cover - environment-dependent
    _HAS_FITZ = False


def _finding(**overrides: object) -> dict:
    finding = {
        "rule": "stale_model_name",
        "severity": "error",
        "message": "foreign model name in copy",
        "source_ref": {"table": "Manual_Copy_Source", "copy_key": "ops_note", "lang": "en"},
        "evidence": {"text": "Charge the JE-2000E battery fully."},
        "suggested_action": "fix the copy row",
    }
    finding.update(overrides)
    return finding


class TestLocatorTexts(unittest.TestCase):
    def test_prefers_longest_evidence_strings(self) -> None:
        finding = _finding(
            evidence={"text": "short one", "value": "a much longer evidence string here"}
        )
        texts = pdf_annotate.locator_texts(finding)
        self.assertEqual(texts[0], "a much longer evidence string here")

    def test_short_strings_are_dropped(self) -> None:
        finding = _finding(evidence={"text": "abc"})
        self.assertEqual(pdf_annotate.locator_texts(finding), [])

    def test_no_evidence_yields_no_locators(self) -> None:
        self.assertEqual(pdf_annotate.locator_texts(_finding(evidence={})), [])


class TestLoadFindings(unittest.TestCase):
    def test_accepts_list_and_dict_shapes(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            as_list = Path(td) / "list.json"
            as_list.write_text(json.dumps([_finding()]), encoding="utf-8")
            self.assertEqual(len(pdf_annotate.load_findings(as_list)), 1)
            as_dict = Path(td) / "dict.json"
            as_dict.write_text(json.dumps({"findings": [_finding()]}), encoding="utf-8")
            self.assertEqual(len(pdf_annotate.load_findings(as_dict)), 1)


@unittest.skipUnless(_HAS_FITZ, "PyMuPDF not installed")
class TestAnnotatePdf(unittest.TestCase):
    def _make_pdf(self, path: Path, text: str) -> None:
        import fitz

        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 100), text)
        doc.save(str(path))
        doc.close()

    @staticmethod
    def _page_one_annot_infos(out: Path) -> list[dict]:
        """Extract annotation info dicts and drop every fitz ref before close.

        Keeping Annot/Page references past ``doc.close()`` makes MuPDF's GC
        teardown segfault nondeterministically — copy the plain dicts out.
        """
        import fitz

        doc = fitz.open(str(out))
        try:
            return [dict(annot.info) for annot in (doc[0].annots() or [])]
        finally:
            doc.close()

    def test_located_finding_gets_highlight_with_source_note(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            pdf = Path(td) / "manual.pdf"
            self._make_pdf(pdf, "Charge the JE-2000E battery fully.")
            out = Path(td) / "manual_annotated.pdf"
            summary = pdf_annotate.annotate_pdf(pdf, [_finding()], out)
            self.assertEqual(summary["unlocated"], 0)
            self.assertEqual(len(summary["located"]), 1)
            self.assertEqual(summary["located"][0]["page"], 1)
            infos = self._page_one_annot_infos(out)
            self.assertEqual(len(infos), 1)
            self.assertIn("Manual_Copy_Source", infos[0].get("content", ""))
            self.assertIn("backport", infos[0].get("content", ""))

    def test_unlocated_finding_lands_in_page_one_note(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            pdf = Path(td) / "manual.pdf"
            self._make_pdf(pdf, "Completely different page content.")
            out = Path(td) / "out.pdf"
            summary = pdf_annotate.annotate_pdf(pdf, [_finding()], out)
            self.assertEqual(summary["unlocated"], 1)
            self.assertEqual(summary["located"], [])
            infos = self._page_one_annot_infos(out)
            self.assertEqual(len(infos), 1)
            self.assertIn("could not be located", infos[0].get("content", ""))

    def test_input_pdf_is_untouched(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            pdf = Path(td) / "manual.pdf"
            self._make_pdf(pdf, "Charge the JE-2000E battery fully.")
            before = pdf.read_bytes()
            out = Path(td) / "out.pdf"
            pdf_annotate.annotate_pdf(pdf, [_finding()], out)
            self.assertEqual(pdf.read_bytes(), before)
            self.assertTrue(out.exists())

    def test_cli_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            pdf = Path(td) / "manual.pdf"
            self._make_pdf(pdf, "Charge the JE-2000E battery fully.")
            findings_path = Path(td) / "findings.json"
            findings_path.write_text(json.dumps([_finding()]), encoding="utf-8")
            rc = pdf_annotate.main(
                ["--pdf", str(pdf), "--findings", str(findings_path)]
            )
            self.assertEqual(rc, 0)
            self.assertTrue((Path(td) / "manual_annotated.pdf").exists())


if __name__ == "__main__":
    unittest.main()
