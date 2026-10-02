"""Source-bound nine-language JE-100C Web acceptance through the normal build lane."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from bs4 import BeautifulSoup

from tools import lang_registry
from tools.content_lint_languages import SUPPORTED_LANGS
from tools.manual_ir import read_manual_ir
from tools.prepared_component_coverage import audit_prepared_component_coverage
from tools.prepared_component_policy import resolve_prepared_component_policy
from tools.web_component_admission import require_fresh_component_admission


ROOT = Path(__file__).resolve().parents[1]
LANGUAGES = ("fr", "es", "de", "it", "uk", "pt", "nl", "pl")


class Je100cEuMultilingualWebTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        staging = Path(cls.temp.name)
        fake_bin = staging / "bin"
        fake_bin.mkdir()
        pandoc = fake_bin / "pandoc"
        pandoc.write_text(
            "#!/usr/bin/env python3\nfrom pathlib import Path\nimport sys\n"
            "if '--list-output-formats' in sys.argv:\n"
            "    print('myst')\n    raise SystemExit(0)\n"
            "Path(sys.argv[sys.argv.index('-o')+1]).write_text(Path(sys.argv[1]).read_text())\n"
        )
        pandoc.chmod(0o755)
        cls.outputs = {}
        cls.packages = {}
        for lang in LANGUAGES:
            result = subprocess.run(
                [sys.executable, "build.py", "md", "--config", f"configs/config.eu-{lang}.yaml",
                 "--model", "JE-100C", "--region", "EU", "--lang", lang,
                 "--data-root", "manual_sources/JE-100C/EU/en/2.0/phase2",
                 "--staging-root", str(staging / lang), "--skip-root-index"],
                cwd=ROOT, capture_output=True, text=True, check=False,
                env={**os.environ, "AUTO_MANUAL_OSS_ARCHIVE_CONFIG": "off",
                     "AUTO_MANUAL_PRESENTATION_PROFILE": "web",
                     "PATH": str(fake_bin) + os.pathsep + os.environ.get("PATH", "")},
            )
            if result.returncode:
                raise AssertionError(f"{lang} Web build failed\n{result.stdout}\n{result.stderr}")
            package = staging / lang / "docs" / "_build" / "JE-100C" / "EU" / lang / "md"
            cls.packages[lang] = package
            cls.outputs[lang] = (
                read_manual_ir(package / "manual.ir.json"),
                BeautifulSoup((package / "manual_bundle.html").read_text(), "html.parser"),
            )

    def test_all_languages_have_localized_source_and_complete_shared_compositions(self):
        for lang, (ir, soup) in self.outputs.items():
            with self.subTest(lang=lang):
                self.assertEqual(lang, ir.language)
                self.assertEqual(11, len(ir.pages))
                self.assertEqual({lang}, {p.language for p in ir.pages})
                self.assertEqual(11, ir.metadata["web_figure_coverage"]["summary"]["total"])
                self.assertEqual(0, ir.metadata["web_figure_coverage"]["summary"]["by_status"]["missing"])
                self.assertEqual(6, len(soup.select("table.manual-callout-table")))
                self.assertEqual(8, len(soup.select(".hb-symbol-pair-composition img")))
                self.assertEqual(2, len(soup.select(".hb-signal-icon")))
                self.assertEqual(4, len(soup.select(".hb-source-purchase")))
                self.assertEqual(18, len(soup.select("img.hb-lcd-icon-art")))
                self.assertEqual(5, len(soup.select(".hb-device-actions tbody > tr")))
                text = soup.get_text(" ", strip=True)
                for token in ("3000", "JE-100C", "Jackery Explorer 100D", "Li-ion LFP"):
                    self.assertIn(token, text)
                for token in ("==MISSING:", "Swipe or scroll", "CHARGING VIA AC", "IMPORTANT SAFETY INFORMATION"):
                    self.assertNotIn(token, text)
                lcd_tables = soup.select("table.hb-lcd-icon-table")
                self.assertEqual([10, 3, 3, 2], [len(t.select("tbody > tr")) for t in lcd_tables])
                self.assertFalse(any(t.select("thead") for t in lcd_tables))
                rows = lcd_tables[0].select("tbody > tr")
                self.assertEqual([2, 2, 2, 3], [len(rows[i].select("td:last-child p")) for i in (2, 3, 4, 6)])

    def test_publication_admission_accepts_source_review_and_rejects_missing_lcd(self):
        for lang, (ir, _) in self.outputs.items():
            with self.subTest(lang=lang):
                report = require_fresh_component_admission(
                    self.packages[lang], model="JE-100C", region="EU", language=lang,
                )
                self.assertEqual([], report["issues"])
                raw = deepcopy(ir.to_dict())
                page = next(p for p in raw["pages"] if p["page_id"] == f"lcd_display_{lang}.rst")
                page["blocks"] = []
                policy = resolve_prepared_component_policy(model="JE-100C", region="EU", language=lang)
                rejected = audit_prepared_component_coverage(raw, policy)
                self.assertTrue(any("HB-TABLE-LCD-ICON" in issue for issue in rejected["issues"]))
                raw = deepcopy(ir.to_dict())
                page = next(p for p in raw["pages"] if p["page_id"] == f"warranty_{lang}.rst")
                page["blocks"] = []
                rejected = audit_prepared_component_coverage(raw, policy)
                self.assertTrue(any("warranty" in issue for issue in rejected["issues"]))

    def test_source_bindings_and_authorized_alignment_are_hash_locked(self):
        for lang in LANGUAGES:
            with self.subTest(lang=lang):
                source = ROOT / "manual_sources" / "JE-100C" / "EU" / lang / "2.0"
                record = json.loads((source / "source_manifest.json").read_text())
                self.assertFalse(record["live_bitable_dependency"])
                for key in ("native_source_intake", "page_manifest", "web_illustration_manifest"):
                    bound = record[key]
                    self.assertEqual(bound["sha256"], hashlib.sha256((ROOT / bound["path"]).read_bytes()).hexdigest())
                for bound in record["templates"]:
                    self.assertEqual(bound["sha256"], hashlib.sha256((ROOT / bound["path"]).read_bytes()).hexdigest())
                if lang in ("uk", "pt", "nl", "pl"):
                    alignment = record["newer_english_alignment"]
                    self.assertEqual(alignment["sha256"], hashlib.sha256((ROOT / alignment["path"]).read_bytes()).hexdigest())
                    edits = json.loads((ROOT / alignment["path"]).read_text())
                    for edit in edits["changes"]:
                        template = ROOT / "docs" / "templates" / f"page_je100c_eu-{lang}" / edit["file"]
                        self.assertIn(edit["after"], template.read_text())

    def test_new_authored_languages_do_not_invent_core_phase2_or_idml_support(self):
        for lang in ("pt", "nl", "pl"):
            spec = lang_registry.language_spec(lang)
            self.assertEqual((), spec.table_columns)
            self.assertIsNone(lang_registry.idml_language_pack(lang))
            self.assertFalse(spec.sync_enabled)
            self.assertIn(lang, SUPPORTED_LANGS)
        self.assertEqual("eu-pt", lang_registry.language_spec("pt").tm_column)

    def test_battery_disposal_uses_the_full_separate_collection_paragraph(self):
        reference = ROOT / "manual_sources/JE-2000F/EU/nine-language/git-20260929-eb899f44-intake/four-language/source/symbols.json"
        locales = json.loads(reference.read_text())["locales"]
        for lang in ("uk", "pt", "nl", "pl"):
            with self.subTest(lang=lang):
                body = next(p["meaning"] for p in locales[lang]["pictograms"]
                            if p["icon_id"] == "battery_separate_collection")
                text = self.outputs[lang][1].get_text(" ", strip=True)
                self.assertEqual(1, text.count(body))


if __name__ == "__main__":
    unittest.main()
