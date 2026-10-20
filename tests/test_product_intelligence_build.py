"""Exercise the demo through the same Sphinx entrypoint used by RTD."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from bs4 import BeautifulSoup

from tools.readthedocs_source import assemble_rtd_source
from tools.rtd.research_build import demo_enabled


class ProductIntelligenceBuildTests(unittest.TestCase):
    def test_explicit_opt_in_and_public_role(self):
        for flag in (False, "", "false", "0", None):
            self.assertFalse(demo_enabled(SimpleNamespace(config=SimpleNamespace(rtd_product_intelligence_demo=flag))))
        for flag in (True, "true", "1"):
            app = SimpleNamespace(config=SimpleNamespace(rtd_product_intelligence_demo=flag))
            self.assertTrue(demo_enabled(app))
            app.config.rtd_site_role = "manuals"
            self.assertFalse(demo_enabled(app))
        with self.assertRaises(ValueError):
            demo_enabled(SimpleNamespace(config=SimpleNamespace(rtd_product_intelligence_demo="yes")))

    def _build(self, root, flag, role, *, with_manifest=False, output_name=None):
        build = root / "build"
        manual = build / "JE-TEST" / "EU" / "md"
        manual.mkdir(parents=True, exist_ok=True)
        (manual / "conf.py").write_text("project='test'\n", encoding="utf-8")
        (manual / "index.md").write_text("# Test\n\n```{toctree}\nmanual\n```\n", encoding="utf-8")
        (manual / "manual.md").write_text("# Test manual\n\nFrozen content.\n", encoding="utf-8")
        source = build / "publish" / "web"
        assemble_rtd_source(build_root=build, output_dir=source, title="Test library")
        if with_manifest:
            (source.parent / "publish_manifest.json").write_text(json.dumps({"targets": [{
                "model": "JE-TEST", "region": "EU", "lang": "en", "version": "1.0",
                "route": "JE-TEST/EU/md", "manual": "manual.md",
            }]}), encoding="utf-8")
        knowledge = root / "knowledge"
        knowledge.mkdir(exist_ok=True)
        output = root / (output_name or f"html-{flag}-{role}")
        before = (source / "JE-TEST" / "EU" / "md" / "manual.md").read_bytes()
        result = subprocess.run(
            [sys.executable, "-m", "sphinx", "-q", "-b", "html",
             "-D", "extensions=myst_parser,tools.rtd.portal",
             "-D", f"rtd_knowledge_dir={knowledge}",
             str(source), str(output)],
            env=dict(os.environ, RTD_PRODUCT_INTELLIGENCE_DEMO=flag, RTD_SITE_ROLE=role),
            cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(before, (source / "JE-TEST" / "EU" / "md" / "manual.md").read_bytes())
        return output

    def test_enabled_private_build_links_page_and_exports_without_inventing_products(self):
        with TemporaryDirectory() as temporary:
            out = self._build(Path(temporary), "1", "combined")
            page = out / "research" / "product-intelligence.html"
            self.assertTrue(page.is_file())
            soup = BeautifulSoup(page.read_text(), "html.parser")
            self.assertEqual(soup.select_one('.app-nav-link[aria-current="page"]').get_text(strip=True),
                             "↗产品情报研究 · Demo")
            home = (out / "workspace" / "index.html").read_text()
            self.assertIn("research/product-intelligence.html", home)
            knowledge = json.loads((out / "_static" / "product-knowledge.v1.json").read_text())
            research = json.loads((out / "_static" / "product-intelligence.v1.json").read_text())
            self.assertEqual(knowledge["schema_version"], "product-knowledge/v1")
            self.assertEqual(knowledge["products"], [])
            self.assertEqual(research["knowledge_snapshot_id"], knowledge["content_sha256"])
            # The manual library itself has no internal research navigation.
            self.assertNotIn("research/product-intelligence", (out / "index.html").read_text())

    def test_real_extractor_unknown_facts_render_with_resolvable_manual_links(self):
        with TemporaryDirectory() as temporary:
            out = self._build(Path(temporary), "1", "combined", with_manifest=True)
            knowledge = json.loads((out / "_static" / "product-knowledge.v1.json").read_text())
            self.assertEqual(len(knowledge["products"]), 1)
            self.assertTrue(knowledge["products"][0]["unknowns"])
            page = out / "research" / "product-intelligence.html"
            soup = BeautifulSoup(page.read_text(), "html.parser")
            manual_links = [link["href"] for link in soup.select('a[href*="JE-TEST/EU/md/manual.html"]')]
            self.assertTrue(manual_links)
            self.assertTrue(all((page.parent / href).resolve().is_file() for href in manual_links))

    def test_default_and_public_builds_do_not_export_research(self):
        for flag, role in (("0", "combined"), ("1", "manuals")):
            with self.subTest(flag=flag, role=role), TemporaryDirectory() as temporary:
                out = self._build(Path(temporary), flag, role)
                self.assertFalse((out / "research").exists())
                self.assertFalse((out / "_static" / "product-knowledge.v1.json").exists())
                self.assertFalse((out / "_static" / "product-intelligence.v1.json").exists())

    def test_reused_output_does_not_retain_disabled_or_public_research(self):
        for flag, role in (("0", "combined"), ("1", "manuals")):
            with self.subTest(flag=flag, role=role), TemporaryDirectory() as temporary:
                root = Path(temporary)
                out = self._build(root, "1", "combined", output_name="reused-html")
                self.assertTrue((out / "research" / "product-intelligence.html").is_file())
                unrelated = out / "keep-reviewer-note.txt"
                unrelated.write_text("keep", encoding="utf-8")
                self._build(root, flag, role, output_name="reused-html")
                self.assertFalse((out / "research" / "product-intelligence.html").exists())
                self.assertFalse((out / "_static" / "product-knowledge.v1.json").exists())
                self.assertFalse((out / "_static" / "product-intelligence.v1.json").exists())
                self.assertEqual(unrelated.read_text(), "keep")
