from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.process_docs import build_publish_latest_site, vercel_build_publish_latest


class TestBuildPublishLatestSite(unittest.TestCase):
    def test_build_site_should_copy_each_target_under_target_path_and_write_root_index(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            releases_root = root / "reports" / "releases"
            output_dir = root / "site" / "publish-latest" / "dist"
            html_dir = releases_root / "JE-1000F" / "US" / "en" / "latest" / "html"
            meta_path = releases_root / "JE-1000F" / "US" / "en" / "latest" / "publish_meta.json"

            html_dir.mkdir(parents=True, exist_ok=True)
            markup = '<html><link rel="stylesheet" href="manual.css">latest publish</html>\n'
            (html_dir / "index.html").write_text(markup, encoding="utf-8")
            (html_dir / "manual.css").write_text("body {}\n", encoding="utf-8")
            meta_path.write_text(
                json.dumps(
                    {
                        "model": "JE-1000F",
                        "region": "US",
                        "lang": "en",
                        "version": "0.2",
                        "built_at": "2026-04-04T12:00:00",
                        "html_dir": "reports/releases/JE-1000F/US/en/latest/html",
                        "html_index": "reports/releases/JE-1000F/US/en/latest/html/index.html",
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            with mock.patch.object(build_publish_latest_site, "ROOT", root):
                built_dir = build_publish_latest_site.build_site(
                    releases_root=releases_root,
                    output_dir=output_dir,
                )

            self.assertEqual(output_dir, built_dir)
            target_dir = output_dir / "JE-1000F" / "US" / "en"
            self.assertIn("JE-1000F / US / en", (output_dir / "index.html").read_text(encoding="utf-8"))
            self.assertEqual(markup, (target_dir / "index.html").read_text(encoding="utf-8"))
            self.assertEqual("body {}\n", (target_dir / "manual.css").read_text(encoding="utf-8"))
            copied_meta = json.loads((target_dir / "generated" / "publish_meta.json").read_text(encoding="utf-8"))
            self.assertEqual("JE-1000F", copied_meta["model"])
            self.assertEqual("0.2", copied_meta["version"])

    def test_build_site_should_keep_legacy_single_target_layout_when_requested(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            releases_root = root / "reports" / "releases"
            output_dir = root / "site" / "publish-latest" / "dist"
            html_dir = releases_root / "JE-1000F" / "US" / "en" / "latest" / "html"
            meta_path = releases_root / "JE-1000F" / "US" / "en" / "latest" / "publish_meta.json"
            html_dir.mkdir(parents=True, exist_ok=True)
            (html_dir / "index.html").write_text("<html>legacy</html>\n", encoding="utf-8")
            meta_path.write_text(
                json.dumps(
                    {
                        "model": "JE-1000F",
                        "region": "US",
                        "lang": "en",
                        "html_dir": "reports/releases/JE-1000F/US/en/latest/html",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            with mock.patch.object(build_publish_latest_site, "ROOT", root):
                build_publish_latest_site.build_site(
                    releases_root=releases_root,
                    output_dir=output_dir,
                    multi_target=False,
                )
            self.assertEqual("<html>legacy</html>\n", (output_dir / "index.html").read_text(encoding="utf-8"))
            self.assertFalse((output_dir / "JE-1000F").exists())

    def test_build_site_should_isolate_multiple_targets(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            releases_root = root / "reports" / "releases"
            output_dir = root / "site" / "publish-latest" / "dist"
            for model, region, lang, built_at in (
                ("JE-1000F", "US", "en", "2026-04-04T12:00:00"),
                ("JE-2000F", "JP", "ja", "2026-04-04T11:00:00"),
            ):
                html_dir = releases_root / model / region / lang / "latest" / "html"
                meta_path = releases_root / model / region / lang / "latest" / "publish_meta.json"
                html_dir.mkdir(parents=True, exist_ok=True)
                (html_dir / "index.html").write_text(f"<html>{model}</html>\n", encoding="utf-8")
                meta_path.write_text(
                    json.dumps(
                        {
                            "model": model,
                            "region": region,
                            "lang": lang,
                            "built_at": built_at,
                            "html_dir": f"reports/releases/{model}/{region}/{lang}/latest/html",
                        }
                    )
                    + "\n",
                    encoding="utf-8",
                )
            with mock.patch.object(build_publish_latest_site, "ROOT", root):
                build_publish_latest_site.build_site(releases_root=releases_root, output_dir=output_dir)
            root_index = (output_dir / "index.html").read_text(encoding="utf-8")
            self.assertIn("JE-1000F/US/en/index.html", root_index)
            self.assertIn("JE-2000F/JP/ja/index.html", root_index)
            targets = json.loads((output_dir / "generated" / "publish_targets.json").read_text(encoding="utf-8"))
            self.assertEqual({"JE-1000F/US/en", "JE-2000F/JP/ja"}, {item["path"] for item in targets})

    def test_latest_publish_meta_should_pick_newest_built_at(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            releases_root = Path(td) / "reports" / "releases"
            older = releases_root / "JE-1000F" / "US" / "en" / "latest" / "publish_meta.json"
            newer = releases_root / "JE-1000F" / "JP" / "ja" / "latest" / "publish_meta.json"
            older.parent.mkdir(parents=True, exist_ok=True)
            newer.parent.mkdir(parents=True, exist_ok=True)
            older.write_text('{"built_at":"2026-04-04T10:00:00"}\n', encoding="utf-8")
            newer.write_text('{"built_at":"2026-04-04T11:00:00"}\n', encoding="utf-8")

            resolved = build_publish_latest_site.latest_publish_meta(releases_root)

            self.assertEqual(newer, resolved)

    def test_static_copy_preserves_transitive_browser_assets_and_linked_downloads_only(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            source, output = Path(td) / "html", Path(td) / "preview"
            files = {
                "index.html": (
                    '<link rel="stylesheet" href="_static/main.css">'
                    '<script src="_static/app.js"></script>'
                    '<img src="images/panel%20one.svg?rev=1#part">'
                    '<img srcset="data:image/png;base64,AAAA 1x, images/panel@2x.png 2x">'
                    '<a href="downloads/manual.pdf#page=2">Download</a>'
                    '<a href="guide/">Guide</a><a href="https://example.com/online.pdf">Online</a>'
                    '<div style="background:url(images/inline.png)"></div>'
                ),
                "guide/index.html": '<object data="../images/diagram.svg"></object>',
                "_static/main.css": '@import "nested/theme.css"; body {background:url(../images/bg.png)}',
                "_static/nested/theme.css": '@font-face {src:url(../font.woff2)}',
                "_static/app.js": 'fetch("data.json"); import("./chunk.js");',
                "_static/chunk.js": 'const icon = "../images/script.png";',
                "_static/data.json": '{"icon": "../images/from-json.png"}',
                "searchindex.js": "Search.setIndex({});",
                "_static/font.woff2": "font",
                "images/panel one.svg": "panel",
                "images/panel@2x.png": "2x",
                "images/inline.png": "inline",
                "images/diagram.svg": "diagram",
                "images/bg.png": "background",
                "images/script.png": "script image",
                "images/from-json.png": "json image",
                "downloads/manual.pdf": "%PDF-linked download",
            }
            unused = {
                "cover-en.pdf": "%PDF-duplicate large source",
                "product_overview-en.pdf": "%PDF-duplicate large source",
                "product_overview-fr.pdf": "%PDF-duplicate large source",
                "_sources/index.rst.txt": "source text",
                ".buildinfo": "Sphinx state",
                "unused.css": "unused stylesheet",
                "images/unused.png": "unused image",
            }
            for name, data in {**files, **unused}.items():
                path = source / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(data, encoding="utf-8")

            build_publish_latest_site.copy_contents(source, output)

            self.assertEqual(set(files), {p.relative_to(output).as_posix() for p in output.rglob("*") if p.is_file()})
            for name in files:
                self.assertEqual((source / name).read_bytes(), (output / name).read_bytes(), name)
            self.assertTrue(all((source / name).is_file() for name in unused))

    def test_static_copy_rejects_missing_resources_and_paths_outside_the_target(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "html"
            source.mkdir()
            (root / "outside.png").write_bytes(b"outside")
            (source / "escape.png").symlink_to(root / "outside.png")
            for reference in ("missing.png", "../outside.png", "%2e%2e/outside.png", "escape.png"):
                with self.subTest(reference=reference):
                    (source / "index.html").write_text(f'<img src="{reference}">', encoding="utf-8")
                    with self.assertRaises((ValueError, FileNotFoundError)):
                        build_publish_latest_site.copy_contents(source, root / "preview")

    def test_vercel_reuse_trims_old_payloads_but_keeps_provenance_and_search(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            dist = Path(td) / "dist"
            (dist / "generated").mkdir(parents=True)
            (dist / "index.html").write_text("<html>Manual</html>", encoding="utf-8")
            (dist / "searchindex.js").write_text("Search.setIndex({});", encoding="utf-8")
            metadata = '{"pdf_file": "cover-en.pdf"}'
            (dist / "generated/publish_meta.json").write_text(metadata, encoding="utf-8")
            (dist / "cover-en.pdf").write_bytes(b"duplicate print source")
            with mock.patch.object(vercel_build_publish_latest, "DIST_DIR", dist):
                self.assertEqual(0, vercel_build_publish_latest.main())
            self.assertFalse((dist / "cover-en.pdf").exists())
            self.assertEqual(metadata, (dist / "generated/publish_meta.json").read_text(encoding="utf-8"))
            self.assertTrue((dist / "searchindex.js").is_file())

    def test_invalid_prebuilt_site_is_preserved_when_validation_fails(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            dist = Path(td) / "dist"
            dist.mkdir()
            markup = '<img src="missing.png">'
            (dist / "index.html").write_text(markup, encoding="utf-8")
            (dist / "cover-en.pdf").write_bytes(b"original")
            with mock.patch.object(vercel_build_publish_latest, "DIST_DIR", dist):
                with self.assertRaises(FileNotFoundError):
                    vercel_build_publish_latest.main()
            self.assertEqual(markup, (dist / "index.html").read_text(encoding="utf-8"))
            self.assertEqual(b"original", (dist / "cover-en.pdf").read_bytes())


if __name__ == "__main__":
    unittest.main()
