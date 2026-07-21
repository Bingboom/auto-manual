from __future__ import annotations

import tempfile
import unittest
import json
from pathlib import Path

from tools.build_docs_export import (
    _copy_attachment_images_for_latex,
    _copy_raw_html_assets_for_html,
)


class TestBuildDocsExport(unittest.TestCase):
    def test_raw_html_assets_are_copied_to_their_browser_path(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bundle_dir = root / "bundle"
            html_out_dir = root / "html"
            reference = bundle_dir / "page" / "fragment.rst"
            asset = bundle_dir / "_assets" / "assets" / "managed.png"
            reference.parent.mkdir(parents=True)
            asset.parent.mkdir(parents=True)
            reference.write_text(
                '.. raw:: html\n\n   <img src="_assets/assets/managed.png">\n',
                encoding="utf-8",
            )
            asset.write_bytes(b"managed image")
            (bundle_dir / "asset_usage_manifest.json").write_text(
                json.dumps(
                    {
                        "rewrites": [
                            {
                                "reference_path": "page/fragment.rst",
                                "rendered_value": "_assets/assets/managed.png",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            messages: list[str] = []

            _copy_raw_html_assets_for_html(bundle_dir, html_out_dir, messages.append)

            self.assertEqual(
                b"managed image",
                (html_out_dir / "_assets" / "assets" / "managed.png").read_bytes(),
            )
            self.assertEqual(1, len(messages))

    def test_dynamic_latex_assets_are_copied_to_output(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bundle_dir = root / "bundle"
            latex_out_dir = root / "latex"
            dynamic = bundle_dir / "renderers" / "latex" / "assets" / "managed-cover.pdf"
            dynamic.parent.mkdir(parents=True)
            latex_out_dir.mkdir()
            dynamic.write_bytes(b"dynamic registry pdf")
            messages: list[str] = []

            _copy_attachment_images_for_latex(bundle_dir, latex_out_dir, messages.append)

            self.assertEqual(
                b"dynamic registry pdf",
                (latex_out_dir / "managed-cover.pdf").read_bytes(),
            )
            self.assertEqual(1, len(messages))

    def test_latex_flat_copy_rejects_same_name_with_different_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bundle_dir = root / "bundle"
            latex_out_dir = root / "latex"
            dynamic = bundle_dir / "renderers" / "latex" / "assets" / "cover.pdf"
            dynamic.parent.mkdir(parents=True)
            latex_out_dir.mkdir()
            dynamic.write_bytes(b"registry bytes")
            (latex_out_dir / "cover.pdf").write_bytes(b"sphinx bytes")

            with self.assertRaisesRegex(RuntimeError, "LaTeX asset basename collision"):
                _copy_attachment_images_for_latex(bundle_dir, latex_out_dir, lambda _message: None)

            self.assertEqual(b"sphinx bytes", (latex_out_dir / "cover.pdf").read_bytes())

    def test_target_scoped_override_wins_over_shared_copy(self) -> None:
        """Registry target overrides (renderers/latex/assets) replace the shared
        common_assets copy of the SAME basename — the 2026-07-20 live case
        (charging/je1000f_us/car_charge over charging/car_charge)."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bundle_dir = root / "bundle"
            latex_out_dir = root / "latex"
            shared = (
                bundle_dir / "_assets" / "templates" / "word_template"
                / "common_assets" / "charging" / "car_charge.png"
            )
            override = bundle_dir / "renderers" / "latex" / "assets" / "car_charge.png"
            shared.parent.mkdir(parents=True)
            override.parent.mkdir(parents=True)
            latex_out_dir.mkdir()
            shared.write_bytes(b"shared burned-text bytes")
            override.write_bytes(b"target-scoped override bytes")
            messages: list[str] = []

            _copy_attachment_images_for_latex(bundle_dir, latex_out_dir, messages.append)

            self.assertEqual(
                b"target-scoped override bytes",
                (latex_out_dir / "car_charge.png").read_bytes(),
            )
            self.assertTrue(
                any("target-scoped override" in message for message in messages),
                messages,
            )

    def test_two_generic_roots_with_different_bytes_still_collide(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bundle_dir = root / "bundle"
            latex_out_dir = root / "latex"
            attachment = bundle_dir / "_repo_assets" / "page" / "_attachments" / "icon.png"
            shared = (
                bundle_dir / "_assets" / "templates" / "word_template"
                / "common_assets" / "symbols" / "icon.png"
            )
            attachment.parent.mkdir(parents=True)
            shared.parent.mkdir(parents=True)
            latex_out_dir.mkdir()
            attachment.write_bytes(b"attachment bytes")
            shared.write_bytes(b"different shared bytes")

            with self.assertRaisesRegex(RuntimeError, "LaTeX asset basename collision"):
                _copy_attachment_images_for_latex(bundle_dir, latex_out_dir, lambda _message: None)

    def test_override_identical_to_shared_copies_once_without_notice(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bundle_dir = root / "bundle"
            latex_out_dir = root / "latex"
            shared = (
                bundle_dir / "_assets" / "templates" / "word_template"
                / "common_assets" / "overview" / "front_controls.png"
            )
            override = bundle_dir / "renderers" / "latex" / "assets" / "front_controls.png"
            shared.parent.mkdir(parents=True)
            override.parent.mkdir(parents=True)
            latex_out_dir.mkdir()
            shared.write_bytes(b"same bytes")
            override.write_bytes(b"same bytes")
            messages: list[str] = []

            _copy_attachment_images_for_latex(bundle_dir, latex_out_dir, messages.append)

            self.assertEqual(b"same bytes", (latex_out_dir / "front_controls.png").read_bytes())
            self.assertFalse(any("override" in message for message in messages), messages)


    def test_override_wins_over_sphinx_precopied_shared_asset(self) -> None:
        """Run-5 live finding: Sphinx pre-copies the shared common_assets image
        into the latex dir whenever a page references it via ``.. image::``.
        When the pre-existing dst's BYTES equal the generic root's
        same-basename file, it is the same shared asset — the target-scoped
        override still wins."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bundle_dir = root / "bundle"
            latex_out_dir = root / "latex"
            shared = (
                bundle_dir / "_assets" / "templates" / "word_template"
                / "common_assets" / "charging" / "car_charge.png"
            )
            override = bundle_dir / "renderers" / "latex" / "assets" / "car_charge.png"
            shared.parent.mkdir(parents=True)
            override.parent.mkdir(parents=True)
            latex_out_dir.mkdir()
            shared.write_bytes(b"shared burned-text bytes")
            override.write_bytes(b"target-scoped override bytes")
            # Sphinx already copied the shared image before the sweep runs
            (latex_out_dir / "car_charge.png").write_bytes(b"shared burned-text bytes")
            messages: list[str] = []

            _copy_attachment_images_for_latex(bundle_dir, latex_out_dir, messages.append)

            self.assertEqual(
                b"target-scoped override bytes",
                (latex_out_dir / "car_charge.png").read_bytes(),
            )
            self.assertTrue(
                any("target-scoped override" in message for message in messages),
                messages,
            )

    def test_sphinx_precopied_unknown_bytes_still_collide_with_override(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bundle_dir = root / "bundle"
            latex_out_dir = root / "latex"
            shared = (
                bundle_dir / "_assets" / "templates" / "word_template"
                / "common_assets" / "charging" / "car_charge.png"
            )
            override = bundle_dir / "renderers" / "latex" / "assets" / "car_charge.png"
            shared.parent.mkdir(parents=True)
            override.parent.mkdir(parents=True)
            latex_out_dir.mkdir()
            shared.write_bytes(b"shared bytes")
            override.write_bytes(b"override bytes")
            # pre-existing dst matches NEITHER the shared source nor the override
            (latex_out_dir / "car_charge.png").write_bytes(b"mystery bytes")

            with self.assertRaisesRegex(RuntimeError, "LaTeX asset basename collision"):
                _copy_attachment_images_for_latex(bundle_dir, latex_out_dir, lambda _m: None)


if __name__ == "__main__":
    unittest.main()
