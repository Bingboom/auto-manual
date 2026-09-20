from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools import rtd_portal
from tools.rtd_alias_entry import alias_head_markup, forward_markers
from tools.readthedocs_source import assemble_rtd_source


class RtdPortalTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.settings = json.loads((rtd_portal.ASSETS / "settings.json").read_text())

    def source(self, region="EU", model="JE-TEST"):
        source = self.root / model / region / "md"
        source.mkdir(parents=True, exist_ok=True)
        (source / "conf.py").write_text("project='manual'\n")
        (source / "index.md").write_text(f"# Jackery Test User Manual\n\n```{{toctree}}\n\nmanual_{region}\n```\n")
        (source / "assets").mkdir(exist_ok=True)
        (source / "assets" / "product.png").write_bytes(b"product")
        (source / f"manual_{region}.md").write_text(
            '# Test\n\n<img class="hb-inbox-art" src="assets/product.png" alt="Product"/>\n'
        )

    def assemble(self):
        for region in ("EU", "US", "JP"):
            self.source(region)
        result = self.root / "rtd"
        assemble_rtd_source(build_root=self.root, output_dir=result, title="Library")
        return result

    def test_default_and_shared_binding(self):
        self.assertEqual(self.settings["default_region"], "EU")
        self.assertEqual(list(self.settings["regions"]), ["US", "EU", "UK"])
        self.assertEqual(self.settings["regions"]["EU"], self.settings["regions"]["UK"])
        self.assertEqual(len(self.settings["languages"]), 12)

    def test_catalog_uses_frozen_links_and_local_product_images(self):
        root = self.assemble()
        records = rtd_portal.catalog(root, self.settings)
        self.assertEqual(len(records), 3)
        eu = next(p for p in records if p["region"] == "EU")
        self.assertEqual(eu["edition"], "EUUK")
        self.assertEqual(eu["name"], "Test")
        self.assertEqual(eu["url"], "JE-TEST/EU/md/manual_EU.html")
        # Pooled by content, so the card points into the shared store rather than
        # a per-model path; what matters is that it stays inside the frozen tree.
        self.assertTrue(eu["image"].startswith("_static/manual-assets/"))
        self.assertTrue((root / eu["image"]).is_file())
        self.assertEqual({r["region"] for r in records}, {"US", "EU", "JP"})

    def test_unsafe_or_missing_links_fail(self):
        for link in ("../escape.md", "https://host/manual.md", "missing.md", "/manual.md"):
            (self.root / "index.md").write_text(f"- [Bad]({link})\n")
            with self.assertRaisesRegex(ValueError, "Missing or unsafe"):
                rtd_portal.catalog(self.root, self.settings)

    def test_missing_or_remote_image_is_not_replaced_with_another_model(self):
        source = self.root / "manual.md"
        for src in ("https://host/product.png", "../outside.png", "/outside.png", "missing.png"):
            source.write_text(f'<img class="hb-inbox-art" src="{src}"/>')
            self.assertEqual(rtd_portal.product_image(source, self.root), "")

    def test_real_sphinx_changes_home_only_and_preserves_sources(self):
        root = self.assemble()
        # This test isolates portal/alias transforms; VOC has its own opt-in tests.
        assets = self.root / "portal-assets"
        shutil.copytree(rtd_portal.ASSETS, assets)
        settings = dict(self.settings, product_voc_endpoint="")
        (assets / "settings.json").write_text(json.dumps(settings))
        knowledge = self.root / "knowledge"
        share = knowledge / "ai-share"
        (share / "配图").mkdir(parents=True)
        (share / "00_打开分享.html").write_text("<!doctype html><p>业务资料</p>")
        (share / "配图" / "00-概览.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')
        with (root / "conf.py").open("a") as conf:
            conf.write(f"\nfrom pathlib import Path\nfrom tools import rtd_portal as portal\nportal.ASSETS = Path({str(assets)!r})\n")
            conf.write(f"rtd_knowledge_dir = {str(knowledge)!r}\n")
        before = {p.relative_to(root): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in root.rglob("*") if p.is_file()}
        # Compare manual content with the same site branding on both builds.
        for name, flags in (("before", ["-D", "html_title=Manual Center"]),
                            ("after", ["-D", "extensions=myst_parser,tools.rtd_portal"])):
            result = subprocess.run(
                [sys.executable, "-m", "sphinx", "-q", "-b", "html", *flags, str(root), str(self.root / name)],
                cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        after = {p.relative_to(root): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in root.rglob("*") if p.is_file()}
        self.assertEqual(before, after)
        def without_beacon(data: bytes) -> bytes:
            return b"".join(line for line in data.splitlines(keepends=True)
                            if b"cloudflareinsights" not in line)

        beacon_token = self.settings.get("analytics_beacon_token", "")
        site_base_url = self.settings.get("site_base_url", "")
        for region in ("EU", "US", "JP"):
            for path in (f"JE-TEST/{region}/md/manual_{region}.html", f"manual_{region}.html"):
                before_bytes = (self.root / "before" / path).read_bytes()
                after_bytes = (self.root / "after" / path).read_bytes()
                if beacon_token:
                    self.assertIn(b"cloudflareinsights", after_bytes, path)
                self.assertNotIn(b"cloudflareinsights", before_bytes, path)
                after_text = without_beacon(after_bytes).decode("utf-8")
                self.assertIn("Manual Center", after_text, path)
                if "/" not in path:
                    # Root aliases may additionally differ by exactly the declared
                    # entry transform: noindex/canonical head and, with a beacon
                    # configured, the forward send window. Reverting those exact
                    # strings must restore the pre-extension page.
                    target = f"JE-TEST/{region}/md/manual_{region}.html"
                    head = alias_head_markup(target_url=target, site_base_url=site_base_url)
                    self.assertIn(head, after_text, path)
                    after_text = after_text.replace(head, "", 1)
                    if beacon_token:
                        instant = forward_markers(target, delayed=False)
                        delayed = forward_markers(target, delayed=True)
                        for wanted, original in zip(delayed, instant):
                            self.assertIn(wanted, after_text, path)
                            after_text = after_text.replace(wanted, original, 1)
                self.assertEqual(without_beacon(before_bytes).decode("utf-8"), after_text, path)
        page = (self.root / "after" / "index.html").read_text()
        self.assertIn('data-default-region="EU"', page)
        self.assertIn('value="EU" data-binding="EU" selected', page)
        self.assertIn('value="UK" data-binding="EU"', page)
        self.assertIn('id="ethical-ad-placement"', page)
        self.assertIn("按目录查看全部说明书", page)
        self.assertIn("说明书资料库", page)
        self.assertNotIn('class="brand" href="#" aria-label="Jackery', page)
        self.assertIn('href="workspace/index.html">知识库</a>', page)
        self.assertIn('class="selected" href="#">工作资料</a>', page)
        self.assertIn('JE-TEST/JP/md/manual_JP.html', page)
        self.assertTrue((self.root / "after" / "_static" / "portal.css").is_file())
        self.assertNotIn("LOCAL DESIGN PREVIEW", page)
        self.assertNotIn("AI 分享与说明书", page)

        workspace = (self.root / "after" / "workspace" / "index.html").read_text()
        self.assertIn("知识库", workspace)
        self.assertNotIn("我的知识库", workspace)
        self.assertIn("分享资料", workspace)
        self.assertIn(">知识库</a>", workspace)
        self.assertIn(">工作资料</a>", workspace)
        self.assertNotIn("内部版", workspace)
        self.assertNotIn("对外版", workspace)
        self.assertNotIn("Jackery", workspace)
        self.assertIn('href="../ai-share/00_打开分享.html"', workspace)
        self.assertIn('href="../index.html"', workspace)
        self.assertTrue(
            (self.root / "after" / "ai-share" / "00_打开分享.html").is_file()
        )
        self.assertTrue(
            (self.root / "after" / "ai-share" / "配图" / "00-概览.svg").is_file()
        )
        self.assertEqual(
            (self.root / "after" / "ai-share" / "00_打开分享.html").read_bytes(),
            (share / "00_打开分享.html").read_bytes(),
        )


if __name__ == "__main__":
    unittest.main()
