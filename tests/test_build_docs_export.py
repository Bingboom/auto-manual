from __future__ import annotations

import tempfile
import unittest
import json
import os
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from tools.build_docs_export import (
    _copy_attachment_images_for_latex,
    _copy_raw_html_assets_for_html,
    _prepare_artifact_bundle,
)


class TestBuildDocsExport(unittest.TestCase):
    def test_web_lang_prepares_full_source_then_projects_to_canonical_rst(self) -> None:
        plan = SimpleNamespace(build_root=Path("/tmp/build-target"))
        source = SimpleNamespace(bundle_dir=plan.build_root / "web" / "source" / "rst")
        projected = SimpleNamespace(bundle_dir=plan.build_root / "rst")
        prepare_regular = mock.Mock()
        prepare_web_source = mock.Mock(return_value=source)
        project = mock.Mock(return_value=projected)

        with mock.patch.dict(os.environ, {"AUTO_MANUAL_PRESENTATION_PROFILE": "web"}):
            result = _prepare_artifact_bundle(
                cfg={},
                artifact_plan=plan,
                target_model="JE-1000F",
                target_region="US",
                target_lang="en",
                data_root=None,
                source_mode="review-asis",
                page_selector=None,
                write_wrapper_index=True,
                draft_placeholders=False,
                prepare_manual_bundle=prepare_regular,
                prepare_web_language_source_bundle=prepare_web_source,
                materialize_web_language_projection=project,
            )

        self.assertIs(result, projected)
        prepare_regular.assert_not_called()
        self.assertEqual(
            plan.build_root / "web" / "source",
            prepare_web_source.call_args.kwargs["output_root"],
        )
        self.assertFalse(prepare_web_source.call_args.kwargs["write_wrapper_index"])
        project.assert_called_once_with(
            source,
            language="en",
            destination=plan.build_root / "rst",
            write_wrapper_index=True,
        )

    def test_non_web_or_unspecified_lang_preserves_regular_bundle_path(self) -> None:
        plan = SimpleNamespace(build_root=Path("/tmp/build-target"))
        regular = SimpleNamespace(bundle_dir=plan.build_root / "rst")
        prepare_regular = mock.Mock(return_value=regular)
        prepare_web_source = mock.Mock()
        project = mock.Mock()
        common = dict(
            cfg={}, artifact_plan=plan, target_model="JE-1000F", target_region="US",
            data_root=None, source_mode="review-asis", page_selector=None,
            write_wrapper_index=True, draft_placeholders=False,
            prepare_manual_bundle=prepare_regular,
            prepare_web_language_source_bundle=prepare_web_source,
            materialize_web_language_projection=project,
        )

        with mock.patch.dict(os.environ, {"AUTO_MANUAL_PRESENTATION_PROFILE": "document"}):
            self.assertIs(_prepare_artifact_bundle(target_lang="en", **common), regular)
        with mock.patch.dict(os.environ, {"AUTO_MANUAL_PRESENTATION_PROFILE": "web"}):
            self.assertIs(_prepare_artifact_bundle(target_lang=None, **common), regular)

        self.assertEqual(2, prepare_regular.call_count)
        prepare_web_source.assert_not_called()
        project.assert_not_called()

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

    def test_generic_yields_when_dst_already_carries_the_override(self) -> None:
        """Run-8 live finding: pages referencing the asset through its semantic
        key make Sphinx materialize the OVERRIDE bytes into the latex dir
        first; the shared generic copy must then yield, not raise."""
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
            shared.write_bytes(b"shared base image")
            override.write_bytes(b"US three-socket override")
            # Sphinx already materialized the override via the semantic key
            (latex_out_dir / "front_controls.png").write_bytes(b"US three-socket override")
            messages: list[str] = []

            _copy_attachment_images_for_latex(bundle_dir, latex_out_dir, messages.append)

            self.assertEqual(
                b"US three-socket override",
                (latex_out_dir / "front_controls.png").read_bytes(),
            )
            self.assertTrue(
                any("already" in message and "override" in message for message in messages),
                messages,
            )


if __name__ == "__main__":
    unittest.main()
