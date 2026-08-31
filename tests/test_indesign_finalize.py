from __future__ import annotations

import argparse
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.test_helpers import temp_test_root

from tools.indesign_finalize import (
    BATCH_JSX,
    DEFAULT_OUTPUT_CONDITION,
    DEFAULT_OUTPUT_INTENT,
    DEFAULT_PDF_PRESET,
    DEFAULT_PDFX,
    JSX,
    VERSION_PIN,
    _collect_finalize_result,
    _job,
    _pdf_missing_glyphs,
    _overset_pages,
    _parse_pdf_export_compliance,
    check_version_pin,
    main,
    run_finalize_jobs,
    write_version_pin,
)


class InDesignFinalizeTests(unittest.TestCase):
    def test_pdf_missing_glyphs_flags_replacement_and_notdef(self) -> None:
        class FakePage:
            def get_texttrace(self):
                return [{
                    "font": "Example Font",
                    "chars": [
                        (0xFFFD, 42, (1.0, 2.0), (1.0, 2.0, 3.0, 4.0)),
                        (ord("경"), 0, (5.0, 6.0), (5.0, 6.0, 7.0, 8.0)),
                        (ord("A"), 12, (9.0, 10.0), (9.0, 10.0, 11.0, 12.0)),
                        (ord(" "), 0, (13.0, 14.0), (13.0, 14.0, 15.0, 16.0)),
                    ],
                }]

        class FakeDocument:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return None

            def __iter__(self):
                return iter([FakePage()])

        with patch("fitz.open", return_value=FakeDocument()):
            findings = _pdf_missing_glyphs(Path("fake.pdf"))

        self.assertEqual([item["codepoint"] for item in findings], [
            "U+FFFD", "U+ACBD",
        ])
        self.assertEqual(findings[0]["reasons"], ["replacement_character"])
        self.assertEqual(findings[1]["reasons"], ["notdef_glyph"])
        self.assertEqual(findings[1]["glyph_id"], 0)
        self.assertEqual(findings[1]["page"], 1)
        self.assertEqual(findings[1]["font"], "Example Font")

    def test_finalize_result_fails_closed_on_missing_pdf_glyphs(self) -> None:
        finding = {
            "page": 3,
            "character": "경",
            "codepoint": "U+ACBD",
            "glyph_id": 0,
            "font": "Gilroy-Bold",
            "reasons": ["notdef_glyph"],
        }
        with temp_test_root() as root:
            report_path = Path(root) / "report.json"
            pdf_path = Path(root) / "output.pdf"
            report_path.write_text(json.dumps({
                "success": True,
                "overset_stories": [],
                "overset_table_cells": [],
                "missing_fonts": [],
                "bad_links": [],
            }), encoding="utf-8")
            pdf_path.write_bytes(b"%PDF-test")
            job = {
                "job_id": "glyph-negative-control",
                "output_pdf": str(pdf_path),
                "report_json": str(report_path),
                "pdfx": DEFAULT_PDFX,
                "output_intent": DEFAULT_OUTPUT_INTENT,
                "output_condition": DEFAULT_OUTPUT_CONDITION,
            }
            with patch(
                "tools.indesign_finalize._pdf_export_compliance",
                return_value={"pass": True},
            ), patch(
                "tools.indesign_finalize._pdf_missing_glyphs",
                return_value=[finding],
            ), patch(
                "tools.indesign_finalize.indesign_version",
                return_value="Adobe InDesign test",
            ):
                result = _collect_finalize_result(job, pin_status="match")

            written = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertFalse(result["success"])
            self.assertEqual(result["missing_glyphs_count"], 1)
            self.assertFalse(written["success"])
            self.assertEqual(written["missing_glyphs"], [finding])
            self.assertFalse(written["pdf_glyph_validation"]["pass"])

    def test_finalize_result_fails_closed_on_post_reopen_font_error(self) -> None:
        with temp_test_root() as root:
            report_path = Path(root) / "report.json"
            pdf_path = Path(root) / "output.pdf"
            report_path.write_text(json.dumps({
                "schema_version": "indesign-preflight/v2",
                "success": True,
                "page_count": 1,
                "story_count": 1,
                "overset_stories": [],
                "overset_table_cells": [],
                "missing_fonts": [],
                "bad_links": [],
                "post_reopen": {
                    "completed": True,
                    "page_count": 1,
                    "story_count": 1,
                    "overset_stories": [],
                    "overset_table_cells": [],
                    "missing_fonts": [{
                        "name": "HB Refmark Symbols",
                        "status": "NOT_AVAILABLE",
                    }],
                    "bad_links": [],
                },
            }), encoding="utf-8")
            pdf_path.write_bytes(b"%PDF-test")
            job = {
                "job_id": "reopen-negative-control",
                "output_pdf": str(pdf_path),
                "report_json": str(report_path),
                "pdfx": DEFAULT_PDFX,
                "output_intent": DEFAULT_OUTPUT_INTENT,
                "output_condition": DEFAULT_OUTPUT_CONDITION,
            }
            with patch(
                "tools.indesign_finalize._pdf_export_compliance",
                return_value={"pass": True},
            ), patch(
                "tools.indesign_finalize._pdf_missing_glyphs",
                return_value=[],
            ), patch(
                "tools.indesign_finalize.indesign_version",
                return_value="Adobe InDesign test",
            ):
                result = _collect_finalize_result(job, pin_status="match")

            written = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertFalse(result["success"])
            self.assertEqual(1, result["missing_fonts_count"])
            self.assertIn("close/reopen", written["error"])

    def test_job_paths_are_absolute_and_script_checks_required_gates(self) -> None:
        job = _job(argparse.Namespace(
            idml="input.idml", indd="output.indd", pdf="output.pdf",
            report="report.json", pdf_preset="[High Quality Print]",
            output_intent=DEFAULT_OUTPUT_INTENT,
            output_condition=DEFAULT_OUTPUT_CONDITION,
            pdfx=DEFAULT_PDFX))
        self.assertTrue(all(Path(job[key]).is_absolute() for key in (
            "input_idml", "output_indd", "output_pdf", "report_json")))
        jsx = JSX.read_text(encoding="utf-8")
        self.assertIn("story.overflows", jsx)
        self.assertIn("cell.overflows", jsx)
        self.assertIn("collectOversetTableCells(doc)", jsx)
        self.assertIn("overset_table_cells", jsx)
        self.assertIn("collectTableCellOversets(", jsx)
        self.assertIn("cell.tables.everyItem().getElements()", jsx)
        self.assertIn("if (identity && seen[identity])", jsx)
        self.assertIn('report.stage = "preflight_overset"', jsx)
        self.assertLess(
            jsx.index('report.stage = "preflight_overset"'),
            jsx.index("doc.exportFile"),
        )
        self.assertIn('story_title: String(story.storyTitle || "")', jsx)
        self.assertGreaterEqual(
            jsx.count('story_title: String(story.storyTitle || "")'),
            3,
        )
        self.assertIn("FontStatus.INSTALLED", jsx)
        self.assertIn("LinkStatus.NORMAL", jsx)
        self.assertIn("hb:page=", jsx)
        self.assertIn("doc.exportFile", jsx)
        self.assertIn("collectPostReopenState(doc)", jsx)
        self.assertIn('report.stage = "reopen_indd"', jsx)
        self.assertIn("doc = app.open(File(job.output_indd), false)", jsx)
        self.assertIn("report.post_reopen.missing_fonts.length === 0", jsx)
        self.assertIn("backgroundTaskPreferences.enableBackgroundTask = false", jsx)
        self.assertIn("fitLcdCarrierFrames(doc)", jsx)
        self.assertIn('indexOf(" table segment ")', jsx)
        self.assertIn("fitted_lcd_table_groups", jsx)
        lcd_fit = jsx.split(
            "function fitLcdCarrierFrames(doc)",
            1,
        )[1].split("function fitTroubleshootingCarrierFrames", 1)[0]
        self.assertNotIn("allPageItems", lcd_fit)
        self.assertNotIn("item.geometricBounds", lcd_fit)
        self.assertNotIn("table.rows", lcd_fit)
        self.assertIn(
            '"hb:self=tf_terminal_carrier_group_"',
            lcd_fit,
        )
        self.assertIn('=== "troubleshooting table"', jsx)
        self.assertIn("fitted_troubleshooting_table_groups", jsx)
        self.assertIn("fitted_troubleshooting_carrier_frames", jsx)
        self.assertIn("fitTroubleshootingCarrierFrames(doc)", jsx)
        self.assertIn(
            "function growTableTerminalCarrier(doc, story, frame, maxGrowth)",
            jsx,
        )
        self.assertIn("doc, story, frame, 24.0", jsx)
        troubleshooting_fit = jsx.split(
            "function fitTroubleshootingCarrierFrames(doc)",
            1,
        )[1].split("function substituteMissingFont", 1)[0]
        self.assertNotIn("allPageItems", troubleshooting_fit)
        self.assertNotIn("item.geometricBounds", troubleshooting_fit)
        self.assertNotIn("table.rows", troubleshooting_fit)
        self.assertIn(
            '"hb:self=tf_terminal_carrier_group_"',
            troubleshooting_fit,
        )
        self.assertIn("fitComposedSymbolTableShells(doc)", jsx)
        self.assertIn('title.indexOf("Symbol icons ")', jsx)
        self.assertIn("fitted_symbol_table_shells", jsx)
        symbol_fit = jsx.split(
            "function resizeComposedTableShell(frame)", 1
        )[1].split("function fitComposedSymbolTableShells(doc)", 1)[0]
        self.assertNotIn("allPageItems", symbol_fit)
        self.assertNotIn("item.geometricBounds", symbol_fit)
        self.assertIn("applyHostFontSubstitutions(doc)", jsx)
        self.assertIn("font_substitutions", jsx)
        self.assertIn("fontHasTextUsage(doc, font)", jsx)
        self.assertIn("matches = doc.findText()", jsx)
        self.assertIn("textHasVisibleContent(matches[mi].contents)", jsx)
        self.assertNotIn("resizeLcdTableShell", jsx)
        self.assertIn("tableHeight + 4.0", jsx)
        self.assertIn("forced_residuals", jsx)
        self.assertIn("appliedFontName(matches[mi])", jsx)
        self.assertIn("font_usage_audit", jsx)
        self.assertIn("fontUsageSamples(doc, font)", jsx)
        self.assertIn(
            "fitTerminalCarrierFrames(doc, report.carrier_frame_errors)",
            jsx,
        )
        self.assertIn("carrier_frame_fits", jsx)
        self.assertIn("carrier_frame_errors", jsx)
        self.assertIn('title.indexOf("product_overview")', jsx)
        terminal_fit = jsx.split(
            "function fitTerminalCarrierFrames(doc, errors)", 1
        )[1].split("function isComposedSymbolTableStory", 1)[0]
        self.assertIn('"hb:self=tf_terminal_carrier_group_"', terminal_fit)
        self.assertIn("!frame.isValid", terminal_fit)
        self.assertNotIn("isMarkerOnlyCarrier", terminal_fit)
        self.assertIn("app.pdfExportPresets.itemByName(job.pdf_preset)", jsx)
        self.assertIn("if (!pdfPreset.isValid)", jsx)
        self.assertIn("app.pdfExportPreferences.pageRange = PageRange.ALL_PAGES", jsx)
        self.assertIn("doc.cmykProfile = job.output_intent", jsx)
        self.assertIn(
            "doc.exportFile(ExportFormat.pdfType, File(job.output_pdf), false, pdfPreset)",
            jsx,
        )

    def test_overset_pages_merge_story_and_nested_cell_findings(self) -> None:
        self.assertEqual(
            [30, 38, 46],
            _overset_pages({
                "overset_stories": [{
                    "text_containers": [{"page": 30}, {"page": 0}],
                }],
                "overset_table_cells": [
                    {"page": 30, "table_depth": 1},
                    {"page": 38, "table_depth": 1},
                ],
                "post_reopen": {
                    "overset_stories": [],
                    "overset_table_cells": [
                        {"page": 38, "table_depth": 1},
                        {"page": 46, "table_depth": 1},
                        {"page": 0, "table_depth": 1},
                    ],
                },
            }),
        )

    def test_font_substitution_table_is_one_row_per_source(self) -> None:
        """A repeated source font re-enters after its text has already moved.

        changeText moves every range on a source font in one pass, so a second
        row for the same source can never act as a glyph-level cascade — it
        only re-enters substituteMissingFont and demands a target face the
        document no longer needs, which throws and aborts finalize before the
        .indd and .pdf are written. Targets belong in one ordered list per
        source, first installed wins.
        """
        import re

        jsx = JSX.read_text(encoding="utf-8")
        block = jsx.split("var mappings = [", 1)[1].split("\n        ];", 1)[0]
        rows = [
            (match.group(1), re.findall(r'"([^"]+)"', match.group(2)))
            for match in re.finditer(
                r'\["([^"]+)",\s*\[([^\]]*)\]\]', block, re.S,
            )
        ]

        self.assertTrue(rows, "mappings must be [source, [target, ...]] rows")
        sources = [source for source, _targets in rows]
        self.assertEqual(
            len(sources),
            len(set(sources)),
            "a second row for the same source font re-enters "
            "substituteMissingFont after the first has cleared its text — "
            "group its targets into one ordered list instead",
        )
        # The JSX source carries a literal backslash-t, not a tab character.
        self.assertEqual(
            {
                r"Segoe UI Symbol\tRegular",
                r"Yu Gothic\tRegular",
                r"Noto Sans KR\tRegular",
            },
            set(sources),
        )
        for source, targets in rows:
            with self.subTest(source=source):
                self.assertTrue(targets, "every source needs a fallback target")

        # The necessity gate must stay above the target lookup, or a mapping
        # for an already-cleared source can still throw.
        body = jsx.split("function substituteMissingFont", 1)[1].split(
            "\n    function ", 1,
        )[0]
        self.assertIn("if (!fontHasTextUsage(doc, sourceFont))", body)
        self.assertLess(
            body.index("fontHasTextUsage"), body.index("app.fonts.itemByName"),
        )
        self.assertIn("no installed host fallback font for", body)

        audit = jsx.split("function fontHasTextUsage", 1)[1].split(
            "\n    function ", 1,
        )[0]
        self.assertIn("return true;", audit.split("} catch (_) {", 1)[1])

    def test_default_pdf_preset_is_pdfx4(self) -> None:
        self.assertEqual("[PDF/X-4:2008 (Japan)]", DEFAULT_PDF_PRESET)

    def test_pdf_export_compliance_requires_pdfx_and_output_intent(self) -> None:
        result = _parse_pdf_export_compliance(
            pdfinfo_text="PDF subtype:    PDF/X-4\n",
            pdf_bytes=(
                b"/Info(Japan Color 2001 Coated) "
                b"/OutputConditionIdentifier(JC200103)"
            ),
            expected_pdfx=DEFAULT_PDFX,
            expected_output_intent=DEFAULT_OUTPUT_INTENT,
            expected_output_condition=DEFAULT_OUTPUT_CONDITION,
        )

        self.assertTrue(result["pass"])

    def test_pdf_export_compliance_rejects_wrong_output_intent(self) -> None:
        result = _parse_pdf_export_compliance(
            pdfinfo_text="PDF subtype:    PDF/X-4\n",
            pdf_bytes=b"/Info(U.S. Web Coated (SWOP) v2)",
            expected_pdfx=DEFAULT_PDFX,
            expected_output_intent=DEFAULT_OUTPUT_INTENT,
            expected_output_condition=DEFAULT_OUTPUT_CONDITION,
        )

        self.assertFalse(result["pass"])

    def test_runner_allows_synchronous_pdf_export_to_finish(self) -> None:
        runner = (JSX.parent.parent / "indesign_finalize.py").read_text(encoding="utf-8")

        self.assertIn("script_timeout = 600 * max(1, job_count)", runner)
        self.assertIn("process_timeout = script_timeout + 60", runner)
        self.assertIn("timeout=process_timeout", runner)

    def test_batch_driver_loops_and_isolates_each_document(self) -> None:
        batch_jsx = BATCH_JSX.read_text(encoding="utf-8")

        self.assertIn("for (var ji = 0; ji < HB_BATCH_JOBS.length", batch_jsx)
        self.assertIn("try {", batch_jsx)
        self.assertIn("catch (error)", batch_jsx)
        self.assertIn("$.evalFile(File(HB_FINALIZE_SCRIPT_PATH))", batch_jsx)
        self.assertIn("writeJson(HB_BATCH_REPORT_PATH, batch)", batch_jsx)

    def test_batch_runner_groups_by_application_and_preserves_manifest_order(self) -> None:
        jobs = [
            {
                "job_id": "first",
                "application": "InDesign A",
                "input_idml": "/tmp/first.idml",
                "output_indd": "/tmp/first.indd",
                "output_pdf": "/tmp/first.pdf",
                "report_json": "/tmp/first.json",
            },
            {
                "job_id": "second",
                "application": "InDesign A",
                "input_idml": "/tmp/second.idml",
                "output_indd": "/tmp/second.indd",
                "output_pdf": "/tmp/second.pdf",
                "report_json": "/tmp/second.json",
            },
            {
                "job_id": "third",
                "application": "InDesign B",
                "input_idml": "/tmp/third.idml",
                "output_indd": "/tmp/third.indd",
                "output_pdf": "/tmp/third.pdf",
                "report_json": "/tmp/third.json",
            },
        ]
        with patch("tools.indesign_finalize.Path.is_file", return_value=True), \
             patch("tools.indesign_finalize._run_jsx_jobs") as run_batch, \
             patch("tools.indesign_finalize._collect_finalize_result") as collect:
            collect.side_effect = lambda job, **_: {
                "job_id": job["job_id"], "success": True,
            }
            results = run_finalize_jobs(
                jobs, pin_status="match", pin_message="pinned",
            )

        self.assertEqual([item["job_id"] for item in results], [
            "first", "second", "third",
        ])
        self.assertEqual(run_batch.call_count, 2)
        self.assertEqual(
            [job["job_id"] for job in run_batch.call_args_list[0].args[0]],
            ["first", "second"],
        )
        self.assertEqual(run_batch.call_args_list[0].kwargs["application"], "InDesign A")
        self.assertEqual(run_batch.call_args_list[1].kwargs["application"], "InDesign B")


class VersionPinTests(unittest.TestCase):
    """Milestone K7: the finalize leg refuses to run on a version-drifted host."""

    PINNED = "Adobe InDesign 2026 21.0.1.6"

    def _pin(self, root, expected=PINNED) -> Path:
        pin = Path(root) / "pin.json"
        pin.write_text(json.dumps({"expected": expected}), encoding="utf-8")
        return pin

    def test_committed_pin_exists_and_matches_the_check_shape(self) -> None:
        self.assertTrue(VERSION_PIN.is_file(), "committed pin file missing")
        pin = json.loads(VERSION_PIN.read_text(encoding="utf-8"))
        self.assertRegex(pin["expected"], r"^Adobe InDesign .+ \d")
        self.assertIn("pinned_at", pin)

    def test_check_statuses(self) -> None:
        with temp_test_root() as root:
            pin = self._pin(root)
            self.assertEqual(check_version_pin(pin, self.PINNED)[0], "match")
            self.assertEqual(check_version_pin(pin, "Adobe InDesign 2026 21.0.2.1")[0], "mismatch")
            self.assertEqual(check_version_pin(pin, None)[0], "no_indesign")
            self.assertEqual(check_version_pin(Path(root) / "absent.json", self.PINNED)[0], "no_pin")

    def test_mismatch_message_names_both_versions_and_the_runbook(self) -> None:
        with temp_test_root() as root:
            _, message = check_version_pin(self._pin(root), "Adobe InDesign 2027 22.0")
            self.assertIn(self.PINNED, message)
            self.assertIn("Adobe InDesign 2027 22.0", message)
            self.assertIn("indesign_second_host_runbook", message)

    def test_write_pin_seeds_from_host_and_refuses_without_indesign(self) -> None:
        with temp_test_root() as root:
            pin = Path(root) / "pin.json"
            written = write_version_pin(pin, actual="Adobe InDesign 2026 21.0.1.6")
            self.assertEqual(written, self.PINNED)
            data = json.loads(pin.read_text(encoding="utf-8"))
            self.assertEqual(data["expected"], self.PINNED)
            with self.assertRaises(RuntimeError):
                write_version_pin(pin, actual=None)

    def test_check_host_cli_exits_zero_on_match_two_otherwise(self) -> None:
        with patch("tools.indesign_finalize.check_version_pin",
                   return_value=("match", "ok")):
            with patch("sys.argv", ["indesign_finalize.py", "--check-host"]):
                self.assertEqual(main(), 0)
        with patch("tools.indesign_finalize.check_version_pin",
                   return_value=("mismatch", "drift")):
            with patch("sys.argv", ["indesign_finalize.py", "--check-host"]):
                self.assertEqual(main(), 2)

    def test_run_refuses_on_mismatch_without_override_and_never_launches(self) -> None:
        with patch("tools.indesign_finalize.check_version_pin",
                   return_value=("mismatch", "drift")), \
             patch("tools.indesign_finalize._run_jsx") as run_jsx, \
             patch("sys.argv", ["indesign_finalize.py", "--idml", "a.idml",
                                "--indd", "a.indd", "--pdf", "a.pdf", "--report", "r.json"]):
            self.assertEqual(main(), 2)
            run_jsx.assert_not_called()


if __name__ == "__main__":
    unittest.main()
