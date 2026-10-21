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
from sphinx.errors import ConfigError

from tools.readthedocs_source import assemble_rtd_source
from tools.rtd.research_build import (
    DIGEST_JSON, DIGEST_TEXT, EVENTS_JSON, KNOWLEDGE_JSON, LENS_JSON, OUTPUTS, demo_enabled, parse_flag, validate_flag,
)

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "external_intel" / "events.json"
PAGE = Path("research") / "product-intelligence.html"
MANIFEST = {"built_at": "2026-10-20T00:00:00Z", "targets": [{
    "model": "JE-TEST", "region": "EU", "lang": "en", "version": "1.0",
    "route": "JE-TEST/EU/md", "manual": "manual.md",
}]}


def fixture_events():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


class FlagTests(unittest.TestCase):
    def test_flag_spellings_and_public_role(self):
        for flag in (False, "", "false", "0", None, "No", "OFF", 0):
            self.assertFalse(parse_flag(flag))
        for flag in (True, "true", "1", "True", "YES", " on ", 1):
            self.assertTrue(parse_flag(flag))
            app = SimpleNamespace(config=SimpleNamespace(rtd_product_intelligence_demo=flag))
            self.assertTrue(demo_enabled(app))
            app.config.rtd_site_role = "manuals"
            self.assertFalse(demo_enabled(app))
        for flag in ("maybe", 2, "enabled"):
            with self.subTest(flag=flag), self.assertRaises(ValueError):
                parse_flag(flag)

    def test_misspelt_flag_is_a_configuration_error_for_every_role(self):
        for role in ("combined", "manuals"):
            with self.subTest(role=role), self.assertRaisesRegex(ConfigError, "rtd_product_intelligence_demo"):
                validate_flag(None, SimpleNamespace(rtd_product_intelligence_demo="maybe", rtd_site_role=role))


class ProductIntelligenceBuildTests(unittest.TestCase):
    def _build(self, root, flag="1", role="combined", *, events=fixture_events, manifest=None, output_name=None,
               expect_success=True, source_dir=("publish", "web"), conf_extra=""):
        build = root / "build"
        manual = build / "JE-TEST" / "EU" / "md"
        manual.mkdir(parents=True, exist_ok=True)
        (manual / "conf.py").write_text("project='test'\n", encoding="utf-8")
        (manual / "index.md").write_text("# Test\n\n```{toctree}\nmanual\n```\n", encoding="utf-8")
        (manual / "manual.md").write_text("# Test manual\n\nFrozen content.\n", encoding="utf-8")
        source = build.joinpath(*source_dir)
        assemble_rtd_source(build_root=build, output_dir=source, title="Test library")
        if conf_extra:
            with (source / "conf.py").open("a", encoding="utf-8") as conf:
                conf.write(conf_extra)
        manifest_path = source.parent / "publish_manifest.json"
        manifest_path.unlink(missing_ok=True)
        if manifest is not None:
            manifest_path.write_text(manifest if isinstance(manifest, str) else json.dumps(manifest), encoding="utf-8")
        knowledge = root / "knowledge"
        intake = knowledge / "external-intel" / "events.json"
        intake.parent.mkdir(parents=True, exist_ok=True)
        intake.unlink(missing_ok=True)
        payload = events() if callable(events) else events
        if payload is not None:
            intake.write_text(payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False),
                              encoding="utf-8")
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
        if expect_success:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(before, (source / "JE-TEST" / "EU" / "md" / "manual.md").read_bytes())
        return output, result

    def exports(self, out):
        return {name for name in OUTPUTS if (out / "_static" / name).is_file()}

    def test_events_are_collected_and_pushed_while_the_product_lens_is_unavailable(self):
        with TemporaryDirectory() as temporary:
            out, result = self._build(Path(temporary), "True")
            soup = BeautifulSoup((out / PAGE).read_text(), "html.parser")
            self.assertEqual(soup.select_one('.app-nav-link[aria-current="page"]').get_text(strip=True),
                             "↗外部情报 · Demo")
            self.assertEqual(len(soup.select(".research-event")), 2)
            self.assertIn("是否按州、负载和停电时长分组", soup.get_text())
            for appendix in soup.select(".product-lens"):
                self.assertIn("产品视角暂不可用", appendix.get_text())
            self.assertIn("product lens unavailable", result.stderr)
            self.assertEqual(self.exports(out), {EVENTS_JSON, DIGEST_JSON, DIGEST_TEXT})
            digest = json.loads((out / "_static" / DIGEST_JSON).read_text())
            events = json.loads((out / "_static" / EVENTS_JSON).read_text())
            self.assertEqual(digest["events_snapshot_id"], events["snapshot_id"])
            self.assertEqual((out / "_static" / DIGEST_TEXT).read_text(), digest["text"])
            for item in digest["items"]:
                page, anchor = item["page"].split("#")
                self.assertIsNotNone(BeautifulSoup((out / page).read_text(), "html.parser").find(id=anchor))
            self.assertIn("research/product-intelligence.html", (out / "workspace" / "index.html").read_text())
            # The manual library itself has no internal research navigation.
            self.assertNotIn("research/product-intelligence", (out / "index.html").read_text())

    def test_events_without_a_lens_never_build_product_knowledge(self):
        def unlensed():
            data = fixture_events()
            for event in data["events"]:
                event.pop("product_lens")
            return data

        with TemporaryDirectory() as temporary:
            out, result = self._build(Path(temporary), events=unlensed, manifest=MANIFEST)
            self.assertEqual(self.exports(out), {EVENTS_JSON, DIGEST_JSON, DIGEST_TEXT})
            soup = BeautifulSoup((out / PAGE).read_text(), "html.parser")
            appendices = soup.select(".product-lens")
            self.assertEqual(len(appendices), 2)
            self.assertTrue(all("未配置产品视角" in appendix.summary.get_text() for appendix in appendices))
            self.assertNotIn("product lens", result.stderr)

    def test_real_extractor_lens_renders_resolvable_manual_links(self):
        with TemporaryDirectory() as temporary:
            out, _result = self._build(Path(temporary), manifest=MANIFEST)
            self.assertEqual(self.exports(out), set(OUTPUTS))
            knowledge = json.loads((out / "_static" / KNOWLEDGE_JSON).read_text())
            lens = json.loads((out / "_static" / LENS_JSON).read_text())
            events = json.loads((out / "_static" / EVENTS_JSON).read_text())
            self.assertEqual(len(knowledge["products"]), 1)
            self.assertEqual((lens["knowledge_snapshot_id"], lens["events_snapshot_id"]),
                             (knowledge["content_sha256"], events["snapshot_id"]))
            page = out / PAGE
            soup = BeautifulSoup(page.read_text(), "html.parser")
            manual_links = [link["href"] for link in soup.select('a[href*="JE-TEST/EU/md/manual.html"]')]
            self.assertTrue(manual_links)
            self.assertTrue(all((page.parent / href).resolve().is_file() for href in manual_links))
            downloads = [link["href"] for link in soup.select(".research-downloads a")]
            self.assertEqual(len(downloads), 5)
            self.assertTrue(all((page.parent / href).resolve().is_file() for href in downloads))

    def test_broken_product_inputs_degrade_only_the_lens(self):
        broken = (json.dumps({"built_at": "2026-10-20"}), "{",
                  json.dumps({"targets": [{**MANIFEST["targets"][0], "route": "../../outside"}]}))
        for manifest in broken:
            with self.subTest(manifest=manifest), TemporaryDirectory() as temporary:
                # The bootstrap layout: the EU query export, which rejects such a manifest itself, skips it.
                out, result = self._build(Path(temporary), manifest=manifest, source_dir=("rtd",))
                self.assertTrue((out / PAGE).is_file())
                self.assertTrue((out / "market" / "policy.html").is_file())
                self.assertEqual(self.exports(out), {EVENTS_JSON, DIGEST_JSON, DIGEST_TEXT})
                self.assertIn("product lens unavailable", result.stderr)
                text = BeautifulSoup((out / PAGE).read_text(), "html.parser").get_text()
                self.assertIn("产品知识快照不可用", text)
                self.assertNotIn(temporary, text)

    def test_malformed_events_skip_only_the_research_page(self):
        with TemporaryDirectory() as temporary:
            out, result = self._build(Path(temporary), events="{", manifest=MANIFEST)
            self.assertIn("External intelligence page skipped", result.stderr)
            self.assertFalse((out / PAGE).exists())
            self.assertEqual(self.exports(out), set())
            self.assertTrue((out / "market" / "policy.html").is_file())
            home = (out / "workspace" / "index.html").read_text()
            self.assertNotIn("research/product-intelligence", home)
            self.assertNotIn("research/product-intelligence", (out / "market" / "policy.html").read_text())

    def test_boolean_flag_from_conf_py_enables_without_a_type_warning(self):
        with TemporaryDirectory() as temporary:
            out, result = self._build(Path(temporary), "0", conf_extra="\nrtd_product_intelligence_demo = True\n")
            self.assertTrue((out / PAGE).is_file())
            self.assertNotIn("has type", result.stderr)

    def test_misspelt_flag_stops_the_build_once_with_a_clear_message(self):
        for role in ("combined", "manuals"):
            with self.subTest(role=role), TemporaryDirectory() as temporary:
                _out, result = self._build(Path(temporary), "maybe", role, expect_success=False)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stderr.count("rtd_product_intelligence_demo must be"), 1, result.stderr)

    def test_default_and_public_builds_do_not_export_research(self):
        for flag, role in (("0", "combined"), ("1", "manuals")):
            with self.subTest(flag=flag, role=role), TemporaryDirectory() as temporary:
                out, _result = self._build(Path(temporary), flag, role)
                self.assertFalse((out / "research").exists())
                self.assertEqual(self.exports(out), set())

    def test_reused_output_does_not_retain_disabled_or_public_research(self):
        for flag, role in (("0", "combined"), ("1", "manuals")):
            with self.subTest(flag=flag, role=role), TemporaryDirectory() as temporary:
                root = Path(temporary)
                out, _result = self._build(root, manifest=MANIFEST, output_name="reused-html")
                self.assertTrue((out / PAGE).is_file())
                self.assertEqual(self.exports(out), set(OUTPUTS))
                unrelated = out / "keep-reviewer-note.txt"
                unrelated.write_text("keep", encoding="utf-8")
                self._build(root, flag, role, manifest=MANIFEST, output_name="reused-html")
                self.assertFalse((out / PAGE).exists())
                self.assertEqual(self.exports(out), set())
                self.assertEqual(unrelated.read_text(), "keep")


if __name__ == "__main__":
    unittest.main()
