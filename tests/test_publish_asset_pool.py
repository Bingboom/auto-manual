from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from tools import publish_asset_pool
from tools.publish_asset_pool import POOL_SEGMENT, pool_publish_assets

SHARED = b"\x89PNG shared artwork"
UNIQUE = b"\x89PNG unique artwork"


def _tree(root: Path, *, manuals: dict[str, str], assets: dict[str, bytes]) -> None:
    for relative, payload in assets.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    for relative, text in manuals.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def _two_language_tree(root: Path) -> None:
    """One manual per language, sharing artwork, staged the way assembly leaves it."""
    _tree(
        root,
        assets={
            "_static/manual-assets/JE-1/EU/en/md/assets/panel.png": SHARED,
            "_static/manual-assets/JE-1/EU/fr/md/assets/panel.png": SHARED,
            "_static/manual-assets/JE-1/EU/en/md/assets/cover.png": UNIQUE,
            # The Markdown-adjacent copies assembly also leaves behind.
            "JE-1/EU/en/md/assets/panel.png": SHARED,
            "JE-1/EU/fr/md/assets/panel.png": SHARED,
            "JE-1/EU/en/md/assets/cover.png": UNIQUE,
        },
        manuals={
            "JE-1/EU/en/md/manual.md": (
                "# EN\n\n"
                '<img src="../../../../_static/manual-assets/JE-1/EU/en/md/assets/panel.png"'
                ' alt="panel" data-web-finished-panel-path="assets/panel.png" />\n\n'
                '<img src="../../../../_static/manual-assets/JE-1/EU/en/md/assets/cover.png" alt="cover" />\n'
            ),
            "JE-1/EU/fr/md/manual.md": (
                "# FR\n\n"
                '<img src="../../../../_static/manual-assets/JE-1/EU/fr/md/assets/panel.png"'
                ' alt="panneau" data-web-finished-panel-path="assets/panel.png" />\n'
            ),
        },
    )


def _sources(text: str) -> list[str]:
    return [match.group(3) for match in publish_asset_pool._HTML_IMG_SRC_RE.finditer(text)]


class PublishAssetPoolTests(unittest.TestCase):
    def test_identical_artwork_across_languages_should_keep_one_copy(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            _two_language_tree(root)

            report = pool_publish_assets(output_dir=root)

            self.assertEqual(2, report.unique_assets)
            self.assertEqual(6, report.collapsed_files)
            self.assertEqual(3, report.rewritten_references)
            pooled = sorted(p for p in (root / "_static" / "manual-assets" / POOL_SEGMENT).rglob("*") if p.is_file())
            self.assertEqual(2, len(pooled))
            self.assertEqual({SHARED, UNIQUE}, {p.read_bytes() for p in pooled})

    def test_both_languages_should_point_at_the_same_pooled_file(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            _two_language_tree(root)
            pool_publish_assets(output_dir=root)

            en = root / "JE-1" / "EU" / "en" / "md" / "manual.md"
            fr = root / "JE-1" / "EU" / "fr" / "md" / "manual.md"
            en_panel = (en.parent / _sources(en.read_text(encoding="utf-8"))[0]).resolve()
            fr_panel = (fr.parent / _sources(fr.read_text(encoding="utf-8"))[0]).resolve()

            self.assertEqual(en_panel, fr_panel)
            self.assertEqual(SHARED, en_panel.read_bytes())
            self.assertIn(POOL_SEGMENT, en_panel.parts)

    def test_pooling_should_not_touch_the_finished_panel_data_attribute(self) -> None:
        """The published stylesheet selects on this value, so it is not a path to rewrite."""
        with TemporaryDirectory() as td:
            root = Path(td)
            _two_language_tree(root)
            pool_publish_assets(output_dir=root)

            text = (root / "JE-1" / "EU" / "en" / "md" / "manual.md").read_text(encoding="utf-8")
            self.assertIn('data-web-finished-panel-path="assets/panel.png"', text)

    def test_copies_nothing_references_should_disappear(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            _two_language_tree(root)
            pool_publish_assets(output_dir=root)

            self.assertFalse((root / "JE-1" / "EU" / "en" / "md" / "assets").exists())
            self.assertFalse((root / "_static" / "manual-assets" / "JE-1").exists())
            self.assertTrue((root / "JE-1" / "EU" / "en" / "md" / "manual.md").is_file())

    def test_markdown_image_syntax_should_be_repointed_too(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            _tree(
                root,
                assets={"_static/manual-assets/JE-1/EU/en/md/assets/panel.png": SHARED},
                manuals={
                    "JE-1/EU/en/md/manual.md": (
                        "# EN\n\n![panel](../../../../_static/manual-assets/JE-1/EU/en/md/assets/panel.png)\n"
                    )
                },
            )

            report = pool_publish_assets(output_dir=root)

            self.assertEqual(1, report.rewritten_references)
            text = (root / "JE-1" / "EU" / "en" / "md" / "manual.md").read_text(encoding="utf-8")
            self.assertIn(POOL_SEGMENT, text)
            target = (root / "JE-1" / "EU" / "en" / "md" / text.split("](")[1].split(")")[0]).resolve()
            self.assertEqual(SHARED, target.read_bytes())

    def test_reference_that_was_already_broken_should_stay_broken_without_failing(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            _tree(
                root,
                assets={"_static/manual-assets/JE-1/EU/en/md/assets/panel.png": SHARED},
                manuals={
                    "JE-1/EU/en/md/manual.md": (
                        "# EN\n\n"
                        '<img src="../../../../_static/manual-assets/JE-1/EU/en/md/assets/panel.png" />\n'
                        '<img src="assets/never_existed.png" />\n'
                    )
                },
            )

            pool_publish_assets(output_dir=root)

            text = (root / "JE-1" / "EU" / "en" / "md" / "manual.md").read_text(encoding="utf-8")
            self.assertIn('src="assets/never_existed.png"', text)

    def test_external_and_absolute_sources_should_be_left_alone(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            _tree(
                root,
                assets={"_static/manual-assets/JE-1/EU/en/md/assets/panel.png": SHARED},
                manuals={
                    "JE-1/EU/en/md/manual.md": (
                        "# EN\n\n"
                        '<img src="https://example.invalid/a.png" />\n'
                        '<img src="/absolute/b.png" />\n'
                        '<img src="../../../../_static/manual-assets/JE-1/EU/en/md/assets/panel.png" />\n'
                    )
                },
            )

            report = pool_publish_assets(output_dir=root)

            text = (root / "JE-1" / "EU" / "en" / "md" / "manual.md").read_text(encoding="utf-8")
            self.assertEqual(1, report.rewritten_references)
            self.assertIn('src="https://example.invalid/a.png"', text)
            self.assertIn('src="/absolute/b.png"', text)

    def test_pooling_an_already_pooled_tree_should_refuse(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            _two_language_tree(root)
            pool_publish_assets(output_dir=root)

            with self.assertRaisesRegex(RuntimeError, "already assembled"):
                pool_publish_assets(output_dir=root)

    def test_a_rewrite_that_loses_a_reference_should_fail_the_build(self) -> None:
        """Negative control: without the rewrite the guard has to notice."""
        with TemporaryDirectory() as td:
            root = Path(td)
            _two_language_tree(root)

            with mock.patch.object(publish_asset_pool, "_rewrite_references", return_value=0):
                with self.assertRaisesRegex(RuntimeError, "changed what these manuals point at"):
                    pool_publish_assets(output_dir=root)


if __name__ == "__main__":
    unittest.main()
