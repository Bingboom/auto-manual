from __future__ import annotations

import tempfile
import unittest
import zipfile
from argparse import Namespace
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from tools.idml_pdf_parity import (
    _approved_contract_report,
    _idml_editability_gate,
    _occupancy_report,
    _parse_page_sizes,
    _parse_pdfinfo,
    _pdf_output_contract,
    _preflight_gate,
    _render_settings,
    _selected_pages,
    _structure_report,
    _visual_report,
    _visual_metrics,
)


class IdmlPdfParityTests(unittest.TestCase):
    def test_pdfinfo_contract(self) -> None:
        info = _parse_pdfinfo("Pages: 60\nPage size: 368.787 x 524.693 pts\n")

        self.assertEqual(60, info["page_count"])
        self.assertEqual(368.787, info["page_width_pt"])
        self.assertEqual(524.693, info["page_height_pt"])

    def test_page_selector_supports_last_and_deduplicates(self) -> None:
        self.assertEqual([1, 3, 60], _selected_pages("1,3,last,3", 60))
        self.assertEqual([1, 2, 3], _selected_pages("all", 3))

    def test_page_sizes_require_a_contiguous_row_for_every_page(self) -> None:
        text = (
            "Page    1 size:  368.787 x 524.692 pts\n"
            "Page    1 rot:   0\n"
            "Page    2 size:  368.918 x 524.823 pts\n"
            "Page    2 rot:   0\n"
        )

        self.assertEqual([1, 2], [
            row["page"] for row in _parse_page_sizes(text, expected_count=2)
        ])
        with self.assertRaisesRegex(ValueError, "reported 2 page sizes; expected 3"):
            _parse_page_sizes(text, expected_count=3)

    def test_visual_metrics_distinguish_identical_and_changed_pages(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            white = root / "white.png"
            changed = root / "changed.png"
            Image.new("L", (10, 10), 255).save(white)
            image = Image.new("L", (10, 10), 255)
            image.putpixel((0, 0), 0)
            image.save(changed)

            identical = _visual_metrics(white, white)
            delta = _visual_metrics(white, changed)

        self.assertEqual(0.0, identical["mean_absolute_difference"])
        self.assertGreater(delta["mean_absolute_difference"], 0.0)
        self.assertEqual(0.01, delta["changed_pixel_ratio"])

    def test_visual_metrics_apply_both_rgb_thresholds(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            white = root / "white.png"
            changed = root / "changed.png"
            Image.new("RGB", (10, 10), "white").save(white)
            image = Image.new("RGB", (10, 10), "white")
            image.putpixel((0, 0), (0, 0, 0))
            image.save(changed)

            passing = _visual_metrics(
                white, changed, max_rgb_mad=0.02,
                max_changed_pixel_ratio=0.02,
            )
            failing = _visual_metrics(
                white, changed, max_rgb_mad=0.005,
                max_changed_pixel_ratio=0.005,
            )

        self.assertTrue(passing["pass"])
        self.assertFalse(failing["rgb_mad_pass"])
        self.assertFalse(failing["changed_pixel_ratio_pass"])

    def test_visual_metrics_detect_same_luminance_different_rgb(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            red = root / "red.png"
            green = root / "green.png"
            Image.new("RGB", (2, 2), (255, 0, 0)).save(red)
            Image.new("RGB", (2, 2), (0, 130, 0)).save(green)

            report = _visual_metrics(red, green)

        self.assertGreater(report["rgb_mad"], 0)

    def test_changed_pixel_threshold_is_inclusive(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            black = root / "black.png"
            changed = root / "changed.png"
            Image.new("RGB", (2, 1), (0, 0, 0)).save(black)
            image = Image.new("RGB", (2, 1), (0, 0, 0))
            image.putpixel((0, 0), (15, 15, 15))
            image.putpixel((1, 0), (16, 16, 16))
            image.save(changed)

            report = _visual_metrics(
                black, changed, changed_channel_threshold=16,
            )

        self.assertEqual(0.5, report["changed_pixel_ratio"])

    def test_visual_metrics_reject_unapproved_raster_size(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            image = Path(td) / "page.png"
            Image.new("RGB", (10, 10), "white").save(image)

            report = _visual_metrics(
                image, image, expected_pixel_size=(11, 10),
                max_rgb_mad=0.008, max_changed_pixel_ratio=0.04,
            )

        self.assertFalse(report["pass"])

    def test_visual_report_requires_every_approved_page(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            def fake_render(_pdf, _page, _dpi, target, **_kwargs):
                Image.new("RGB", (10, 10), "white").save(target)
                return target

            with patch("tools.idml_pdf_parity._render_page", side_effect=fake_render):
                report = _visual_report(
                    root / "reference.pdf",
                    root / "indesign.pdf",
                    [1],
                    expected_page_count=2,
                    settings={
                        "enforced": True,
                        "dpi": 300,
                        "pixel_size": (10, 10),
                        "display_icc": None,
                        "display_icc_sha256": None,
                        "gaussian_blur_px": 1,
                        "changed_channel_threshold": 16,
                        "max_rgb_mad": 0.008,
                        "max_changed_pixel_ratio": 0.04,
                    },
                )

        self.assertFalse(report["all_pages_compared"])
        self.assertFalse(report["pass"])

    def test_approved_render_contract_cannot_be_loosened(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            profile = Path(td) / "sRGB.icc"
            profile.write_bytes(b"approved profile")
            import hashlib

            plan = {
                "render_contract": {
                    "dpi": 300,
                    "raster_width_px": 1537,
                    "raster_height_px": 2187,
                    "display_icc_sha256": hashlib.sha256(
                        profile.read_bytes(),
                    ).hexdigest(),
                    "gaussian_blur_px": 1,
                    "max_rgb_mad": 0.008,
                    "max_changed_pixel_ratio": 0.04,
                    "changed_channel_threshold": 16,
                },
            }
            arguments = Namespace(
                dpi=None,
                raster_width=None,
                raster_height=None,
                display_icc=str(profile),
                gaussian_blur=None,
                max_rgb_mad=None,
                max_changed_pixel_ratio=None,
                changed_channel_threshold=None,
            )

            settings = _render_settings(arguments, plan)
            loosened = deepcopy(arguments)
            loosened.max_rgb_mad = 0.5
            with self.assertRaisesRegex(ValueError, "cannot override approved value"):
                _render_settings(loosened, plan)

        self.assertEqual((1537, 2187), settings["pixel_size"])
        self.assertTrue(settings["enforced"])

    def test_structure_checks_every_candidate_page_against_contract(self) -> None:
        reference = {"page_count": 2, "page_width_pt": 10.0, "page_height_pt": 20.0}
        indesign = {
            "page_count": 2,
            "page_sizes_pt": [
                {"page": 1, "width_pt": 10.0, "height_pt": 20.0, "rotation": 0},
                {"page": 2, "width_pt": 10.1, "height_pt": 20.0, "rotation": 0},
            ],
        }
        plan = {
            "reference_pdf": {
                "page_count": 2,
                "page_size_pt": {"width": 10.0, "height": 20.0},
                "page_size_tolerance_pt": 0.02,
            },
        }

        report = _structure_report(
            reference, indesign, plan=plan, fallback_tolerance=0.5,
        )

        self.assertFalse(report["pass"])
        self.assertEqual([2], report["failing_page_sizes"])

    def test_structure_rejects_a_rotated_candidate_page(self) -> None:
        reference = {"page_count": 1, "page_width_pt": 10.0, "page_height_pt": 20.0}
        indesign = {
            "page_count": 1,
            "page_sizes_pt": [
                {"page": 1, "width_pt": 10.0, "height_pt": 20.0, "rotation": 90},
            ],
        }

        report = _structure_report(
            reference, indesign, plan=None, fallback_tolerance=0.02,
        )

        self.assertFalse(report["pass"])
        self.assertEqual([1], report["rotated_pages"])

    def test_missing_approved_contract_fails_closed(self) -> None:
        report = _approved_contract_report(
            plan_path=None, plan=None, manual_ir={}, reference={},
        )

        self.assertTrue(report["enforced"])
        self.assertFalse(report["pass"])

    def test_preflight_is_bound_to_the_current_candidate(self) -> None:
        candidate = Path("/tmp/current.pdf")
        plan = {
            "reference_pdf": {
                "pdfx": "PDF/X-4",
                "output_intent": "Japan Color 2001 Coated",
                "output_condition": "JC200103",
            },
        }
        preflight = {
            "success": True,
            "output_pdf": str(candidate),
            "page_count": 58,
            "stage": "complete",
            "overset_stories": [],
            "missing_fonts": [],
            "bad_links": [],
            "pdf_export": {
                "requested_preset": "[PDF/X-4:2008 (Japan)]",
                "applied_preset": "[PDF/X-4:2008 (Japan)]",
                "page_range": "ALL_PAGES",
                "requested_output_intent": "Japan Color 2001 Coated",
                "applied_document_cmyk_profile": "Japan Color 2001 Coated",
            },
            "pdf_export_validation": {
                "pass": True,
                "actual_pdfx": "PDF/X-4",
                "expected_pdfx": "PDF/X-4",
                "expected_output_intent": "Japan Color 2001 Coated",
                "output_intent_match": True,
                "expected_output_condition": "JC200103",
                "output_condition_match": True,
            },
        }

        passing = _preflight_gate(
            preflight, indesign_pdf=candidate,
            expected_page_count=58, plan=plan,
        )
        wrong_candidate = _preflight_gate(
            preflight, indesign_pdf=Path("/tmp/other.pdf"),
            expected_page_count=58, plan=plan,
        )

        self.assertTrue(passing["pass"])
        self.assertFalse(wrong_candidate["binding_checks"]["output_pdf_match"])
        self.assertFalse(wrong_candidate["pass"])

    def test_pdf_output_contract_requires_exact_output_intent_tokens(self) -> None:
        plan = {
            "reference_pdf": {
                "pdfx": "PDF/X-4",
                "output_intent": "Japan Color 2001 Coated",
                "output_condition": "JC200103",
            },
        }
        info = {"pdf_subtype": "PDF/X-4"}
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "candidate.pdf"
            path.write_bytes(
                b"/OutputIntents[<</Info(Japan Color 2001 Coated)"
                b"/OutputConditionIdentifier(JC200103)/S/GTS_PDFX>>]",
            )
            passing = _pdf_output_contract(path, info, plan)
            path.write_bytes(
                b"body says Japan Color 2001 Coated and JC200103 but has no dictionary",
            )
            stray_text = _pdf_output_contract(path, info, plan)

        self.assertTrue(passing["pass"])
        self.assertFalse(stray_text["pass"])

    def test_idml_editability_rejects_forbidden_whole_page_links(self) -> None:
        plan = {
            "idml_contract": {
                "forbidden_visible_whole_page_links": ["flattened.pdf"],
            },
        }
        with tempfile.TemporaryDirectory() as td:
            idml = Path(td) / "manual.idml"
            with zipfile.ZipFile(idml, "w") as package:
                package.writestr(
                    "Spreads/Spread_1.xml",
                    '<Link LinkResourceURI="file:///tmp/flattened.pdf"/>',
                )

            report = _idml_editability_gate(idml, plan)

        self.assertFalse(report["pass"])
        self.assertEqual(["flattened.pdf"], report["violations"])

    def test_content_occupancy_rejects_a_blank_indesign_page(self) -> None:
        report = _occupancy_report([100, 2, 120], [2, 2, 90])

        self.assertFalse(report["pass"])
        self.assertEqual([1], [item["page"] for item in report["missing_content_pages"]])


if __name__ == "__main__":
    unittest.main()
