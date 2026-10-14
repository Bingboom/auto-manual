from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup

from tools.rtd import portal as rtd_portal
from tools.rtd.alias_entry import alias_head_markup, forward_markers
from tools.readthedocs_source import assemble_rtd_source
from tools.rtd.design_system_css import live_stylesheet_text


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
        self.assertEqual(list(self.settings["regions"]), ["US", "EU", "UK", "CN", "JP", "KR", "TW"])
        self.assertEqual(self.settings["regions"]["EU"], self.settings["regions"]["UK"])
        self.assertEqual(len(self.settings["languages"]), 16)
        self.assertEqual(self.settings["language_labels"]["ko"], "한국어")
        self.assertEqual(self.settings["language_labels"]["zh-TW"], "繁體中文")

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

    def test_catalog_is_reused_only_within_one_build(self):
        root = self.assemble()
        app = SimpleNamespace(srcdir=root)
        with patch.object(rtd_portal, "catalog", wraps=rtd_portal.catalog) as collect:
            rtd_portal.prepare_catalog(app)
            for _ in range(10):
                self.assertEqual(len(rtd_portal.portal_data(app)[1]), 3)
            self.assertEqual(collect.call_count, 1)
            # Another Sphinx application must not inherit the first one's cache.
            rtd_portal.portal_data(SimpleNamespace(srcdir=root))
            self.assertEqual(collect.call_count, 2)
            # Success and failure both clear state, preserving fail-closed validation
            # if the same application builds changed sources next time.
            for exception in (None, RuntimeError("build interrupted")):
                rtd_portal.clear_catalog_cache(app, exception)
                index = root / "index.md"
                original = index.read_text()
                index.write_text("- [Bad](missing.md)\n")
                with self.assertRaisesRegex(ValueError, "Missing or unsafe"):
                    rtd_portal.portal_data(app)
                index.write_text(original)
                self.assertEqual(len(rtd_portal.portal_data(app)[1]), 3)

    def test_missing_or_remote_image_is_not_replaced_with_another_model(self):
        source = self.root / "manual.md"
        for src in ("https://host/product.png", "../outside.png", "/outside.png", "missing.png"):
            source.write_text(f'<img class="hb-inbox-art" src="{src}"/>')
            self.assertEqual(rtd_portal.product_image(source, self.root), "")

    def test_manuals_role_builds_only_public_pages_with_project_canonical(self):
        root = self.assemble()
        assets = self.root / "portal-assets"
        shutil.copytree(rtd_portal.ASSETS, assets)
        (assets / "settings.json").write_text(json.dumps(dict(self.settings, product_voc_endpoint="")))
        share = self.root / "knowledge" / "ai-share"
        share.mkdir(parents=True)
        (share / "00_打开分享.html").write_text("<!doctype html><p>业务资料</p>")
        with (root / "conf.py").open("a") as conf:
            conf.write(f"\nfrom pathlib import Path\nfrom tools.rtd import portal\nportal.ASSETS = Path({str(assets)!r})\n")
            conf.write(f"rtd_knowledge_dir = {str(self.root / 'knowledge')!r}\n")
        public = "https://manuals.example.com/en/latest/"
        env = dict(os.environ, RTD_SITE_ROLE="manuals", READTHEDOCS_CANONICAL_URL=public)
        out = self.root / "public"
        result = subprocess.run(
            [sys.executable, "-m", "sphinx", "-q", "-b", "html", "-D", "extensions=myst_parser,tools.rtd.portal",
             str(root), str(out)],
            cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, check=False, env=env,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for internal in ("workspace", "products", "market", "ai-share"):
            self.assertFalse((out / internal).exists(), internal)
        self.assertNotIn("业务资料", "".join(p.read_text(errors="ignore") for p in out.rglob("*.html")))
        self.assertIn("说明书资料库", (out / "index.html").read_text())
        shells = [p.relative_to(out).as_posix() for p in out.rglob("*.html")
                  if 'id="app-sidebar"' in p.read_text(errors="ignore")]
        self.assertEqual(shells, ["index.html"])
        root_page = BeautifulSoup((out / "index.html").read_text(), "html.parser")
        self.assertEqual([g.get_text() for g in root_page.select(".app-nav-group")], ["说明书"])
        self.assertIsNone(root_page.select_one(".app-switch"))
        self.assertTrue((out / "JE-TEST/EU/md/manual_EU.html").is_file())
        alias = (out / "manual_EU.html").read_text()
        self.assertIn('href="https://manuals.example.com/en/latest/JE-TEST/EU/md/manual_EU.html"', alias)

    def test_unknown_site_role_fails_the_build(self):
        app = SimpleNamespace(config=SimpleNamespace(rtd_site_role="public"))
        with self.assertRaisesRegex(ValueError, "rtd_site_role"):
            rtd_portal.site_role(app)

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
            conf.write(f"\nfrom pathlib import Path\nfrom tools.rtd import portal\nportal.ASSETS = Path({str(assets)!r})\n")
            conf.write(f"rtd_knowledge_dir = {str(knowledge)!r}\n")
        before = {p.relative_to(root): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in root.rglob("*") if p.is_file()}
        # Compare manual content with the same site branding on both builds.
        for name, flags in (("before", ["-D", "html_title=Manual Center"]),
                            ("after", ["-D", "extensions=myst_parser,tools.rtd.portal"])):
            result = subprocess.run(
                [sys.executable, "-m", "sphinx", "-q", "-b", "html", *flags, str(root), str(self.root / name)],
                cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True,
                check=False,
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
                        for wanted, original in zip(delayed, instant, strict=True):
                            self.assertIn(wanted, after_text, path)
                            after_text = after_text.replace(wanted, original, 1)
                self.assertEqual(without_beacon(before_bytes).decode("utf-8"), after_text, path)
        page = (self.root / "after" / "index.html").read_text()
        self.assertIn('data-default-region="EU"', page)
        self.assertIn('value="EU" data-binding="EU" selected', page)
        self.assertIn('value="UK" data-binding="EU"', page)
        self.assertIn('value="CN" data-binding="CN"', page)
        self.assertIn('value="JP" data-binding="JP"', page)
        self.assertIn('US · EU · UK · CN · JP', page)
        self.assertIn('id="ethical-ad-placement"', page)
        self.assertIn("按目录查看全部说明书", page)
        self.assertIn("说明书资料库", page)
        self.assertNotIn('class="brand" href="#" aria-label="Jackery', page)
        for internal_path in ("workspace/", "products/knowledge.html", "market/policy.html", "ai-share/"):
            self.assertNotIn(f'href="{internal_path}', page)
        self.assertNotIn("workspace/design", page)
        self.assertNotIn("先学最少必要的产品知识", page)
        self.assertNotIn('class="app-switch"', page)
        self.assertIn('JE-TEST/JP/md/manual_JP.html', page)
        self.assertTrue((self.root / "after" / "_static" / "portal.css").is_file())
        self.assertNotIn("LOCAL DESIGN PREVIEW", page)
        self.assertNotIn("AI 分享与说明书", page)

        workspace = (self.root / "after" / "workspace" / "index.html").read_text()
        # The docs link these 知识库首页 sections as workspace/index.html#updates and, with a share package, #shares.
        self.assertIn('id="updates"', workspace)
        self.assertIn('id="shares"', workspace)
        self.assertIn("知识库", workspace)
        self.assertNotIn("我的知识库", workspace)
        self.assertIn("分享资料", workspace)
        self.assertIn('href="../products/knowledge.html"', workspace)
        self.assertIn('href="../market/policy.html"', workspace)
        self.assertIn(">知识库</a>", workspace)
        self.assertIn(">说明书资料库</a>", workspace)
        self.assertEqual(workspace.count("工作资料"), 1)  # the brand only
        self.assertNotIn("内部版", workspace)
        self.assertNotIn("对外版", workspace)
        self.assertNotIn("Jackery", workspace)
        self.assertIn('href="design/index.html"', workspace)
        design_root = self.root / "after" / "workspace" / "design"
        design = (design_root / "index.html").read_text()
        for tab in ("overview", "colors", "type", "components", "assets", "print"):
            self.assertIn(f'data-tab="{tab}"', design)
        self.assertIn('aria-current="page"><i aria-hidden="true">◐</i><span>设计规范</span>', design)
        self.assertIn("<title>设计规范</title>", design)
        self.assertIn('src="previews/title-l1.html"', design)
        self.assertIn('src="assets/symbols/symbol_warning_triangle.svg"', design)
        self.assertIn('src="print/page.html"', design)
        # Versions are a line of small text under the counts, not KPI tiles.
        self.assertIn('class="ds-versions"', design)
        self.assertEqual(design.split('class="ds-versions"', 1)[0].count('class="kpi"'), 4)
        self.assertNotIn("Jackery", design)
        self.assertEqual((design_root / "web_manual.css").read_text(), live_stylesheet_text())
        self.assertIn('href="../web_manual.css"', (design_root / "previews" / "title-l1.html").read_text())
        self.assertIn("--page_paperwidth:", (design_root / "print" / "tokens.css").read_text())
        self.assertTrue((design_root / "assets" / "symbols" / "symbol_warning_triangle.svg").is_file())
        self.assertIn('href="data/index.html"', workspace)
        self.assertIn('href="../data/index.html"', design)
        data_page = (self.root / "after" / "workspace" / "data" / "index.html").read_text()
        self.assertIn('aria-current="page"><i aria-hidden="true">▥</i><span>系统数据</span>', data_page)
        self.assertIn('<script type="application/json" id="system-data-json">', data_page)
        # This tree has no publish manifest: only the publication cards are empty.
        self.assertIn("无数据：本次构建没有可读的发布清单", data_page)
        # 工程规模 moved to the 系统建设 page's 工具与工程规模 tab.
        self.assertNotIn('sd-code', data_page)
        self.assertNotIn("Jackery", data_page)
        self.assertTrue((self.root / "after" / "_static" / "system-data.js").is_file())
        # Without a publish manifest the product matrix and every link to it drop out.
        self.assertFalse((self.root / "after" / "products" / "matrix.html").exists())
        self.assertNotIn("products/matrix", workspace)
        self.assertNotIn("products/matrix", data_page)
        knowledge_page = (self.root / "after" / "products" / "knowledge.html").read_text()
        self.assertIn('href="../index.html"', knowledge_page)
        self.assertIn("返回说明书资料库", knowledge_page)
        # This frozen catalog has no JHP-3600C/US manual, so the HomePower case is left out.
        self.assertNotIn('class="backup-example"', knowledge_page)
        self.assertIn("<title>产品知识</title>", knowledge_page)
        self.assertIn("知识库 <span>/</span> <b>产品知识</b>", knowledge_page)
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
        search_page = (self.root / "after" / "search.html").read_text()
        self.assertIn('id="manual-search-title">Search all manuals</h1>', search_page)
        self.assertIn('id="manual-search-query" name="q" type="search"', search_page)
        self.assertIn('id="search-results"', search_page)
        self.assertIn('manual-search.css', search_page)
        self.assertTrue((self.root / "after" / "_static" / "manual-search.css").is_file())
        self.assertNotIn("manual-search-title", (self.root / "before" / "search.html").read_text())

    def test_real_sphinx_sidebar_links_only_pages_and_marks_the_current_one(self):
        root = self.assemble()
        assets = self.root / "portal-assets"
        shutil.copytree(rtd_portal.ASSETS, assets)
        (assets / "settings.json").write_text(json.dumps(dict(self.settings, product_voc_endpoint="")))
        share = self.root / "knowledge" / "ai-share"
        share.mkdir(parents=True)
        (share / "00_打开分享.html").write_text("<!doctype html><p>业务资料</p>")
        # A publish manifest makes the optional product matrix page build as well.
        target = {"model": "JE-1000F", "region": "US", "lang": "en", "route": "JE-1000F/US/en/md",
                  "manual": "manual_je1000f_us.md", "version": "9.9", "built_at": "2026-09-20T00:00:00+00:00"}
        (self.root / "publish_manifest.json").write_text(json.dumps({"targets": [target]}))
        with (root / "conf.py").open("a") as conf:
            conf.write(f"\nfrom pathlib import Path\nfrom tools.rtd import portal\nportal.ASSETS = Path({str(assets)!r})\n")
            conf.write(f"rtd_knowledge_dir = {str(self.root / 'knowledge')!r}\n")
        out = self.root / "site"
        result = subprocess.run(
            [sys.executable, "-m", "sphinx", "-q", "-b", "html", "-D", "extensions=myst_parser,tools.rtd.portal",
             str(root), str(out)],
            cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        sidebars = {}
        for path in sorted(out.rglob("*.html")):
            sidebar = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser").select_one("#app-sidebar")
            if sidebar:
                sidebars[path.relative_to(out).as_posix()] = sidebar
        def outline(sidebar):
            groups = []
            for node in sidebar.select(".app-nav-group, a.app-nav-link"):
                if "app-nav-group" in node["class"]:
                    groups.append((node.get_text(), []))
                else:
                    groups[-1][1].append(node.span.get_text())
            return groups

        manuals = [("说明书", ["说明书资料库", "搜索说明书正文"])]
        knowledge = [*manuals, ("知识库", ["首页"]), ("产品与市场", ["产品知识", "产品矩阵", "市场与政策"]),
                     ("说明书生产", ["说明书工作台", "系统建设", "设计规范", "系统数据"])]
        pages = ("products/knowledge.html", "products/matrix.html", "market/policy.html", "workspace/index.html",
                 "workspace/system/index.html", "workspace/deliverables/index.html",
                 "workspace/design/index.html", "workspace/data/index.html")
        self.assertEqual({page: outline(sidebar) for page, sidebar in sidebars.items()},
                         {"index.html": manuals, **dict.fromkeys(pages, knowledge)})
        site = "https://site.invalid/"
        for page, sidebar in sidebars.items():
            links = sidebar.select("a.app-nav-link")
            for link in links:
                # Entries are pages; a page's sections (知识库首页's 分享资料, 最近更新) are not sidebar links.
                self.assertEqual(urlsplit(link["href"]).fragment, "", (page, link["href"]))
                self.assertTrue((out / urljoin(site + page, link["href"]).removeprefix(site)).is_file(),
                                (page, link["href"]))
            to_self = [link.get_text() for link in links if urljoin(site + page, link["href"]) == site + page]
            current = [link.get_text() for link in links if link.get("aria-current") == "page"]
            self.assertEqual(len(to_self), 1, (page, to_self))
            self.assertEqual(current, to_self, page)


if __name__ == "__main__":
    unittest.main()
