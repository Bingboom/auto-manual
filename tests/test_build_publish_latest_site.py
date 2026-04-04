from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.process_docs import build_publish_latest_site


class TestBuildPublishLatestSite(unittest.TestCase):
    def test_build_site_should_copy_latest_publish_html_and_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            releases_root = root / "reports" / "releases"
            output_dir = root / "site" / "publish-latest" / "dist"
            html_dir = releases_root / "JE-1000F" / "US" / "en" / "latest" / "html"
            meta_path = releases_root / "JE-1000F" / "US" / "en" / "latest" / "publish_meta.json"

            html_dir.mkdir(parents=True, exist_ok=True)
            (html_dir / "index.html").write_text("<html>latest publish</html>\n", encoding="utf-8")
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
            self.assertEqual("<html>latest publish</html>\n", (output_dir / "index.html").read_text(encoding="utf-8"))
            self.assertEqual("body {}\n", (output_dir / "manual.css").read_text(encoding="utf-8"))
            copied_meta = json.loads((output_dir / "generated" / "publish_meta.json").read_text(encoding="utf-8"))
            self.assertEqual("JE-1000F", copied_meta["model"])
            self.assertEqual("0.2", copied_meta["version"])

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


if __name__ == "__main__":
    unittest.main()
