from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

from bs4 import BeautifulSoup

from tools.manual_ir import read_manual_ir
from tools.web_document_ir import render_document_fragments


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/config.eu-en.yaml"
FORMAL_SOURCE = ROOT / "manual_sources/JE-1000H/EU/en/2.0"
FORMAL_DATA_ROOT = FORMAL_SOURCE / "phase2"
SOURCE_MANIFEST = FORMAL_SOURCE / "source_manifest.json"
ILLUSTRATIONS = ROOT / "docs/renderers/web/je1000h_eu_en_illustrations.json"
# 同一源 PDF 的六个语言块各出一套成品整图；非英语套系尚未接入 config 目标。
MANUAL_LOCALES = ("en", "fr", "es", "de", "it", "uk")


class Je1000hEuEnWebTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        cls.staging = Path(cls._tmp.name) / "staging"
        fake_bin = Path(cls._tmp.name) / "bin"
        fake_bin.mkdir()
        fake_pandoc = fake_bin / "pandoc"
        fake_pandoc.write_text(
            "#!/usr/bin/env python3\n"
            "from pathlib import Path\n"
            "import sys\n"
            "if '--list-output-formats' in sys.argv:\n"
            "    print('myst')\n"
            "    raise SystemExit(0)\n"
            "source = Path(sys.argv[1])\n"
            "target = Path(sys.argv[sys.argv.index('-o') + 1])\n"
            "target.write_text(source.read_text(encoding='utf-8'), encoding='utf-8')\n",
            encoding="utf-8",
        )
        fake_pandoc.chmod(0o755)
        env = {
            **os.environ,
            "AUTO_MANUAL_OSS_ARCHIVE_CONFIG": "off",
            "AUTO_MANUAL_PRESENTATION_PROFILE": "web",
            "PATH": str(fake_bin) + os.pathsep + os.environ.get("PATH", ""),
        }
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "build.py"),
                "md",
                "--config", str(CONFIG),
                "--model", "JE-1000H",
                "--region", "EU",
                "--lang", "en",
                "--data-root", str(FORMAL_DATA_ROOT),
                "--staging-root", str(cls.staging),
            ],
            cwd=ROOT,
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode:
            raise AssertionError(result.stdout + result.stderr)
        cls.package = cls.staging / "docs/_build/JE-1000H/EU/en/md"
        cls.ir = read_manual_ir(cls.package / "manual.ir.json")
        cls.html = (cls.package / "manual_bundle.html").read_text(encoding="utf-8")

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def test_frozen_source_matches_published_target_facts(self) -> None:
        with (FORMAL_DATA_ROOT / "Spec_Master.csv").open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        values = {
            (row["Row_key"], row["Slot_key"], row["Line_order"]): row["Value_source"]
            for row in rows if row["document_key"] == "JE-1000H_EU"
        }
        expected = {
            ("capacity", "", "1"): "1024 Wh (20Ah/51.2V DC)",
            ("cycle_life", "", "1"): "6000 cycles to 70%+ capacity",
            ("ac_output", "", "1"): "230V~50Hz, 7.83A, 1800W Rated",
            ("ac_output_bypass", "", "1"): "220V-240V~50Hz, 7.83A",
            ("dc_expansion_input", "", "1"): "36.8V-56V⎓59A Max",
            ("dc_expansion_output", "", "1"): "36.8V-56V⎓36A Max",
        }
        for key, value in expected.items():
            self.assertEqual(value, values[key])

        with (FORMAL_DATA_ROOT / "lcd_icons_blocks.csv").open(encoding="utf-8", newline="") as handle:
            lcd = list(csv.DictReader(handle))
        self.assertEqual(27, len(lcd))
        self.assertEqual("Connected Batteries", lcd[20]["icon_en"])
        self.assertEqual(["23", "23"], [lcd[22]["No."], lcd[23]["No."]])

        with (FORMAL_DATA_ROOT / "troubleshooting_blocks.csv").open(encoding="utf-8", newline="") as handle:
            codes = [row["error_code"] for row in csv.DictReader(handle)]
        self.assertEqual(
            ["F0", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "FC", "FE"],
            codes,
        )

    def test_source_manifest_locks_every_frozen_input(self) -> None:
        manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
        self.assertFalse(manifest["live_bitable_dependency"])
        self.assertEqual("V2.0-2026-08-03", manifest["authority"]["published_revision"])
        self.assertEqual(
            "07e9ac4b9faabd0852f61702df06f2837caa952c2fa28151b599ad930b1c0bcc",
            manifest["authority"]["published_pdf_sha256"],
        )
        for binding in ("asset_recipe", "web_illustration_manifest"):
            bound = manifest[binding]
            self.assertEqual(bound["sha256"], hashlib.sha256((ROOT / bound["path"]).read_bytes()).hexdigest())
        for record in manifest["files"]:
            data = (FORMAL_SOURCE / record["path"]).read_bytes()
            self.assertEqual(record["size"], len(data))
            self.assertEqual(record["sha256"], hashlib.sha256(data).hexdigest())
        inventory = json.dumps(manifest["files"], ensure_ascii=False,
                               sort_keys=True, separators=(",", ":")).encode()
        self.assertEqual(manifest["files_inventory_sha256"], hashlib.sha256(inventory).hexdigest())

    def test_ac_total_output_and_footnote_match_released_pdf(self) -> None:
        soup = BeautifulSoup(self.html, "html.parser")
        labels = {cell.get_text("", strip=True): cell.parent
                  for cell in soup.select("th.hb-spec-label")}
        self.assertIn("AC Total Output②", labels)
        total = labels["AC Total Output②"]
        self.assertEqual("1800W Rated, 3600W Surge peak", total.select_one("td").get_text(strip=True))
        self.assertEqual([], labels["3 × AC"].select("sup"))

    def test_usb_parent_and_power_labels_match_released_pdf(self) -> None:
        soup = BeautifulSoup(self.html, "html.parser")
        labels = [cell for cell in soup.select("th.hb-spec-label")
                  if cell.get_text(strip=True) == "2 × USB-C"]
        self.assertEqual(1, len(labels))
        value = labels[0].parent.select_one("td")
        text = value.get_text("\n", strip=True)
        self.assertIn("USB-C 30W: 30W Max", text)
        self.assertIn("USB-C 140W: 140W Max", text)
        self.assertLess(text.index("USB-C 30W:"), text.index("USB-C 140W:"))

    def test_web_output_is_complete_semantic_and_target_local(self) -> None:
        soup = BeautifulSoup(self.html, "html.parser")
        coverage = self.ir.metadata["web_figure_coverage"]
        self.assertEqual(12, coverage["summary"]["total"])
        self.assertEqual(0, coverage["summary"]["by_status"]["missing"])
        self.assertEqual(21, len(soup.select(".manual-finished-illustration")))
        self.assertEqual(18, len(self.ir.pages))
        lcd = soup.select_one("table.lcd-text-only")
        self.assertIsNotNone(lcd)
        self.assertEqual(27, len(lcd.select("tbody > tr")))
        self.assertIsNotNone(soup.select_one('[data-web-finished-panel-path$="/lcd_map.png"]'))
        self.assertEqual([], soup.select("#front-view > table"))
        self.assertEqual([], soup.select("#left-and-right-side-view > table"))
        for ident in ("power-on-off", "ac-output-on-off", "led-light-on-off"):
            self.assertEqual(1, len(soup.select(f"#{ident} > img.manual-finished-illustration")))
        for value in (
            "1024 Wh (20Ah/51.2V DC)",
            "6000 cycles to 70%+ capacity",
            "36.8V-56V⎓59A Max",
            "36.8V-56V⎓36A Max",
            "within 10 ms",
            "USB-C 140W",
            "3 YEARS Standard Warranty",
            "2 YEARS Extended Warranty",
            "https://de.jackery.com/pages/user-guides",
        ):
            self.assertIn(value, self.html)
        for forbidden in (
            "JE-2000F", "JE-2000E", "Jackery Explorer 2000 ",
            "4000 cycles", "4400 W", "USB-C 100W", "2011/65/EU",
        ):
            self.assertNotIn(forbidden, self.html)

    def test_illustration_files_match_recipe_and_manifest(self) -> None:
        manifest = json.loads(ILLUSTRATIONS.read_text(encoding="utf-8"))
        recipe = json.loads((ROOT / manifest["recipe"]).read_text(encoding="utf-8"))
        self.assertEqual(21, len(manifest["illustrations"]))
        self.assertEqual(21 * len(MANUAL_LOCALES), len(recipe["assets"]))
        output_hashes = {
            output["path"]: output["expected_sha256"]
            for asset in recipe["assets"] for output in asset["outputs"]
        }
        app_panels = {"download_panel", "control_panel", "connect_result_panel"}
        for asset in recipe["assets"]:
            if asset["asset_key"].rsplit("/", 1)[-1] in app_panels:
                # App screens and the QR download panel stay quarantined under the
                # App/QR/URL/localized-UI gate; the manifests are their only route.
                self.assertFalse(asset["build_eligible"])
                self.assertTrue(asset["visual_review_required"])
                self.assertEqual("quarantine", asset["gate"]["status"])
                self.assertIn("app-ui", asset["risk_tags"])
                continue
            self.assertTrue(asset["build_eligible"])
            self.assertFalse(asset["visual_review_required"])
            self.assertEqual("approved", asset["gate"]["status"])
        self.assertEqual(
            len(app_panels) * len(MANUAL_LOCALES),
            sum(asset["gate"]["status"] == "quarantine" for asset in recipe["assets"]),
        )
        for illustration in manifest["illustrations"]:
            path = ILLUSTRATIONS.parent / illustration["path"]
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(illustration["sha256"], actual)
            self.assertEqual(actual, output_hashes[path.relative_to(ROOT).as_posix()])

    def test_every_locale_binds_its_own_finished_panels(self) -> None:
        """每种语言都有整套成品整图，且互不共用文件。"""
        recipe_assets = json.loads(
            (ROOT / json.loads(ILLUSTRATIONS.read_text(encoding="utf-8"))["recipe"])
            .read_text(encoding="utf-8")
        )["assets"]
        by_locale: dict[str, dict[str, str]] = {}
        for asset in recipe_assets:
            locale, = asset["scope"]["locales"]
            self.assertEqual(["JE-1000H"], asset["scope"]["models"])
            self.assertEqual(["EU"], asset["scope"]["regions"])
            output, = asset["outputs"]
            by_locale.setdefault(locale, {})[Path(output["path"]).name] = \
                output["expected_sha256"]
        self.assertEqual(set(MANUAL_LOCALES), set(by_locale))
        english = by_locale["en"]
        english_entries = json.loads(
            (ROOT / "docs/renderers/web/je1000h_eu_en_illustrations.json")
            .read_text(encoding="utf-8")
        )["illustrations"]
        for locale in MANUAL_LOCALES:
            self.assertEqual(set(english), set(by_locale[locale]), locale)
            illustrations = ROOT / f"docs/renderers/web/je1000h_eu_{locale}_illustrations.json"
            manifest = json.loads(illustrations.read_text(encoding="utf-8"))
            self.assertEqual(locale, manifest["language"])
            bound = {Path(entry["path"]).stem for entry in manifest["illustrations"]}
            # 每种语言都绑满 21 张：JE-1000H 现在有按语言的 07_extra_battery 模板，
            # battery_pack 不再缺宿主。任何语言掉一张这里就会红。
            self.assertEqual(
                {Path(e["path"]).stem for e in english_entries}, bound, locale
            )
            self.assertEqual(21, len(manifest["illustrations"]), locale)
            for entry in manifest["illustrations"]:
                self.assertEqual(
                    by_locale[locale][Path(entry["path"]).name], entry["sha256"]
                )
                self.assertEqual(
                    entry["sha256"],
                    hashlib.sha256(
                        (illustrations.parent / entry["path"]).read_bytes()
                    ).hexdigest(),
                )
            if locale != "en":
                # 各语块版式不同（英规插座 vs 欧规插座、本地化标注），成品图必须各自独立
                shared = {
                    name for name, digest in by_locale[locale].items()
                    if english[name] == digest
                }
                self.assertEqual(set(), shared, f"{locale} reuses English artwork")

    def test_public_ir_replay_and_tamper_detection(self) -> None:
        self.assertEqual(18, len(render_document_fragments(self.ir, package_root=self.package)))
        with tempfile.TemporaryDirectory() as td:
            copied = Path(td) / "package"
            shutil.copytree(self.package, copied)
            ir = read_manual_ir(copied / "manual.ir.json")
            relative = next(iter(ir.metadata["asset_sha256"]))
            (copied / relative).write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "asset missing or changed"):
                render_document_fragments(ir, package_root=copied)


TRANSLATED_LOCALES = ("fr", "es", "de", "it", "uk")
FIGURES = re.compile(r"\d+(?:[.,]\d+)?")


class Je1000hEuTranslatedSpecCellTests(unittest.TestCase):
    """fr–uk specification and storage cells follow each language block of the released PDF."""

    @classmethod
    def setUpClass(cls) -> None:
        with (FORMAL_DATA_ROOT / "Spec_Master.csv").open(encoding="utf-8", newline="") as handle:
            cls.rows = [row for row in csv.DictReader(handle)
                        if row["Page"] in ("specifications", "storage")]

    def test_every_cell_keeps_the_english_figures(self) -> None:
        # 旧抽取按 y 聚类：⎓ 丢失、值被截断或串入邻格、脚注号粘进标签，只比数字的自检拦不住
        self.assertEqual(25, len(self.rows))
        for row in self.rows:
            source = row["Value_source"]
            for lang in TRANSLATED_LOCALES:
                value = row[f"Value_{lang}"]
                with self.subTest(row=row["spec_row_key"], lang=lang):
                    self.assertEqual(FIGURES.findall(source.replace(",", ".")),
                                     FIGURES.findall(value.replace(",", ".")))
                    self.assertEqual(source.count("⎓"), value.count("⎓"))
                    self.assertEqual(value.count("("), value.count(")"))
                    self.assertNotRegex(value, "[ﬀ-ﬆ]")
                    if row["Page"] == "specifications":
                        label = row[f"Row_label_{lang}"]
                        self.assertTrue(label)
                        self.assertNotRegex(label, r"(?:[^\W\d_]|\s)[12]$")
                    else:
                        self.assertTrue(row[f"Param_{lang}"])

    def test_cells_the_old_extraction_broke_match_the_print(self) -> None:
        cells = {(row["Row_key"], row["Line_order"]): row for row in self.rows}
        self.assertEqual(len(self.rows), len(cells))
        expected = {
            ("ac_total_output", "1", "Value_fr"): "1800 W nominal, 3600 W crête",
            ("ac_output_bypass", "1", "Value_de"): "220 V-240 V~ 50 Hz, 7,83 A",
            ("dc12_port", "1", "Value_uk"): "12 В⎓10 А макс.",
            ("dc8020_ports", "1", "Value_fr"): "Voiture : 11 V-16 V⎓8 A max., double à 8 A max.",
            ("capacity", "1", "Value_es"): "1024 Wh (20 Ah/51,2 V CC)",
            ("ac_total_output", "1", "Row_label_it"): "Uscita totale CA",
            ("charging_temperature", "1", "Row_label_de"): "Ladetemperatur",
            ("ac_output_bypass", "1", "Row_label_uk"): "Вихід змінного струму у байпасному режимі",
            ("ac_input", "2", "Param_fr"): "Mode dérivation",
            ("storage_temperature", "1", "Param_es"): "1 mes",
            ("storage_temperature", "3", "Value_de"): "0 °C bis 25 °C (0–60 % relative Luftfeuchtigkeit)",
        }
        for (key, line, column), value in expected.items():
            with self.subTest(key=key, line=line, column=column):
                self.assertEqual(value, cells[(key, line)][column])

    def test_ukrainian_total_output_footnote_keeps_its_noun(self) -> None:
        # 印刷稿漏印「струму」；操作者 2026-09-25 裁定与 JE-3000C 一并补上
        with (FORMAL_DATA_ROOT / "Spec_Footnotes.csv").open(encoding="utf-8", newline="") as handle:
            notes = {row["Footnote_id"]: row for row in csv.DictReader(handle)}
        self.assertEqual("Вказує, що два або більше вихідних портів змінного струму працюють разом.",
                         notes["ac_total_output"]["Text_uk"])

    def test_trademark_note_has_no_german_conjunction_outside_german(self) -> None:
        # 意/乌语块印刷把商标注记的连词印成德语 und；按跨型号已审定译法改为 e / та
        with (FORMAL_DATA_ROOT / "Spec_Notes.csv").open(encoding="utf-8", newline="") as handle:
            note, = [row for row in csv.DictReader(handle) if row["Note_id"] == "usb_type_c_trademark"]
        self.assertEqual("※ USB Type-C® e USB-C® sono marchi registrati di USB Implementers Forum.",
                         note["Text_it"])
        self.assertEqual("※ USB Type-C® та USB-C® є зареєстрованими торговельними марками USB Implementers Forum.",
                         note["Text_uk"])
        for column, text in note.items():
            if column.startswith("Text_") and column != "Text_de":
                with self.subTest(column=column):
                    self.assertNotRegex(text or "", r"\bund\b")


OVERVIEW_VALUE_SLOTS = ("front.spec", "front.high.spec", "front.low.spec",
                        "side.spec", "side.pv.spec", "side.car.spec")


class Je1000hEuOverviewSlotTests(unittest.TestCase):
    """fr–uk Product-overview callouts follow each block's printed overview.

    The finished overview figures consume these callout tables and keep their
    text as the image alt text (``covered_annotations``), so a damaged cell
    reaches readers only through assistive technology.
    """

    @classmethod
    def setUpClass(cls) -> None:
        with (FORMAL_DATA_ROOT / "Spec_Master.csv").open(encoding="utf-8", newline="") as handle:
            cls.rows = [row for row in csv.DictReader(handle) if row["Page"] == "Product overview"]
        cls.cells = {(row["Row_key"], row["Slot_key"]): row for row in cls.rows}

    def test_value_slots_keep_the_english_figures_and_symbols(self) -> None:
        # 09-15 的抽取丢了 ⎓、截断了值（`1800 W nomi`、`12 В 10`）、吞了 PV/车充前缀并留下 ﬁ 连字
        values = [row for row in self.rows if row["Slot_key"] in OVERVIEW_VALUE_SLOTS
                  and row["Row_key"] != "total_output"]
        self.assertEqual(8, len(values))
        for row in values:
            source = row["Value_source"]
            for lang in TRANSLATED_LOCALES:
                value = row[f"Value_{lang}"]
                with self.subTest(row=row["spec_row_key"], lang=lang):
                    self.assertEqual(FIGURES.findall(source.replace(",", ".")),
                                     FIGURES.findall(value.replace(",", ".")))
                    self.assertEqual(source.count("⎓"), value.count("⎓"))
                    self.assertEqual(value.count("("), value.count(")"))
                    self.assertNotRegex(value, "[ﬀ-ﬆ]")
                    if row["Slot_key"] == "side.pv.spec":
                        self.assertRegex(value, r"^(PV|FV|ФЕ)\s?:")
                    if row["Slot_key"] == "side.car.spec":
                        self.assertRegex(value, r"^(Voiture|Auto|Fahrzeug|Автомобіль)\s?:")

    def test_cells_the_old_extraction_broke_match_the_print(self) -> None:
        expected = {
            ("dc12_port", "front.spec", "Value_uk"): "12 В⎓10 А макс.",
            ("ac_output", "front.spec", "Value_fr"): "230 V~ 50 Hz, 7,83 A, 1800 W nominal",
            ("ac_output", "front.spec", "Value_uk"): "230 В~ 50 Гц, 7,83 A, 1800 Вт ном. потужності",
            ("dc_input", "side.car.spec", "Value_fr"): "Voiture : 11-16 V⎓8 A max., double à 8 A max.",
            ("dc_input", "side.pv.spec", "Value_it"): "FV: 16-60 V⎓12 A, raddoppiabile fino a 21 A max./ 400 W max.",
            ("dc_input", "side.pv.spec", "Value_uk"): "ФЕ: 16 В-60 В⎓12 A, подв. до 21 A макс. / 400 Вт макс.",
            ("usb_c", "front.low.spec", "Value_es"): "30 W máx., 5 V⎓3 A, 9 V⎓3 A, 12 V⎓2,5 A, 15 V⎓2 A, 20 V⎓1,5 A",
            # 德语印刷把 12 V 插座标成输出「按键」（Ausgangstaste）；插图照印，页面文字用跨型号审定译法
            ("dc12_port", "front.label", "Value_de"): "12-V-DC-Anschluss",
        }
        for (key, slot, column), value in expected.items():
            with self.subTest(key=key, slot=slot, column=column):
                self.assertEqual(value, self.cells[(key, slot)][column])

    def test_overview_figures_bind_the_current_callout_cells(self) -> None:
        # 成品概览图吃掉标注表并把原文留作 alt；这里保证绑定文本与冻结源同步
        english = json.loads(ILLUSTRATIONS.read_text(encoding="utf-8"))["illustrations"]
        english_symbols = {
            Path(entry["path"]).name: "".join(b["text"] for b in entry["covered_annotations"]).count("⎓")
            for entry in english if Path(entry["path"]).name.startswith("overview_")
        }
        for lang in TRANSLATED_LOCALES:
            manifest = json.loads(
                (ROOT / f"docs/renderers/web/je1000h_eu_{lang}_illustrations.json").read_text(encoding="utf-8")
            )
            bound = {
                Path(entry["path"]).name: " ".join(b["text"] for b in entry["covered_annotations"])
                for entry in manifest["illustrations"] if Path(entry["path"]).name.startswith("overview_")
            }
            self.assertEqual(set(english_symbols), set(bound), lang)
            for name, text in bound.items():
                with self.subTest(lang=lang, figure=name):
                    self.assertEqual(english_symbols[name], text.count("⎓"))
                    self.assertNotRegex(text, "[ﬀ-ﬆ]")
            for row in self.rows:
                value = " ".join(row[f"Value_{lang}"].split())
                if not value:
                    continue
                figure = "overview_side.png" if row["Slot_key"].startswith("side.") else "overview_front.png"
                with self.subTest(lang=lang, slot=(row["Row_key"], row["Slot_key"])):
                    self.assertIn(value, bound[figure])
        self.assertNotIn("DC-12V-Ausgangstaste",
                         (ROOT / "docs/renderers/web/je1000h_eu_de_illustrations.json").read_text(encoding="utf-8"))


DISPLAYED_SIGNALS = ("warning", "caution", "note", "tips")
# 德/意语块印刷把温度小节标题印成英文（PDF 第 70/87 页），属印刷漏译；操作者 2026-09-27 裁定按审核译文翻译
PRINTED_IN_ENGLISH: set[tuple[str, str]] = set()
REVIEWED_HEADING = {"de": "UMGEBUNGSTEMPERATUR IM BETRIEB", "it": "TEMPERATURA OPERATIVA AMBIENTALE"}


class Je1000hEuResidualCopyTests(unittest.TestCase):
    """fr–uk signal labels and headings are never English or another block's language.

    The uk symbols table prints the Italian ``AVVERTENZA`` (PDF page 91); the same
    page prints the uk WARNING callout as ``ПОПЕРЕДЖЕННЯ``. The de/it blocks print the
    temperature heading in English (PDF pages 70/87); the operator ruled on 2026-09-27
    to use the reviewed translation, as JE-2000F prints it.
    """

    @staticmethod
    def _rows(name: str) -> list[dict[str, str]]:
        with (FORMAL_DATA_ROOT / name).open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def test_signal_labels_and_headings_stay_in_their_block_language(self) -> None:
        # 乌语符号表把 WARNING 印成意大利语 AVVERTENZA：同页安全须知印的是 ПОПЕРЕДЖЕННЯ
        from tools.localized_copy import LocalizedCopyResolver

        with self.subTest(signal="warning", lang="uk"):
            copy = LocalizedCopyResolver.from_csv(FORMAL_DATA_ROOT / "Localized_Copy.csv")
            self.assertEqual("ПОПЕРЕДЖЕННЯ", copy.resolve("symbols.signal.warning.label",
                                                          lang="uk", model="JE-1000H", region="EU"))
            warning, = [row for row in self._rows("symbols_blocks.csv") if row["symbol_key"] == "warning"]
            self.assertEqual(("ПОПЕРЕДЖЕННЯ", "ПОПЕРЕДЖЕННЯ"), (warning["label_uk"], warning["aliases_uk"]))

        titles = {row["title_en"]: row for row in self._rows("spec_titles.csv")}
        section_copy = {row["text_en"]: row for row in self._rows("Localized_Copy.csv")
                        if row["copy_type"] in ("page_title", "section_title")}
        signals = {row["copy_key"]: row for row in self._rows("Localized_Copy.csv")
                   if row["copy_type"] == "signal_label"}
        blocks = {row["symbol_key"]: row for row in self._rows("symbols_blocks.csv")
                  if row["block_type"] == "signal_row"}
        for lang in TRANSLATED_LOCALES:
            for english, row in titles.items():
                with self.subTest(table="spec_titles", title=english, lang=lang):
                    self.assertTrue(row[f"title_{lang}"])
                    if (english, lang) not in PRINTED_IN_ENGLISH:
                        self.assertNotEqual(english, row[f"title_{lang}"])
            for english, row in section_copy.items():
                with self.subTest(table="Localized_Copy", title=english, lang=lang):
                    self.assertTrue(row[f"text_{lang}"])
                    if (english, lang) not in PRINTED_IN_ENGLISH:
                        self.assertNotEqual(english, row[f"text_{lang}"])
            for key in DISPLAYED_SIGNALS:
                label = signals[f"symbols.signal.{key}.label"][f"text_{lang}"]
                with self.subTest(signal=key, lang=lang):
                    self.assertTrue(label)
                    self.assertEqual(label, blocks[key][f"label_{lang}"])
                    self.assertEqual(label, blocks[key][f"aliases_{lang}"])
                    if lang == "uk":
                        self.assertRegex(label, r"^[А-ЯҐЄІЇ’ʼ -]+$")
                    else:
                        self.assertRegex(label, r"^[A-ZÀ-ÖØ-Þ -]+$")
                    # es/it 都写 NOTA 是各自正确的译法；其余语种之间不得互相借用
                    borrowed = {other for other in MANUAL_LOCALES if other != lang and label
                                == signals[f"symbols.signal.{key}.label"][f"text_{other}"]}
                    shared = {"es", "it"} - {lang} if key == "note" and lang in ("es", "it") else set()
                    self.assertEqual(shared, borrowed)


    def test_temperature_heading_uses_the_reviewed_translation(self) -> None:
        titles = {row["title_en"]: row for row in self._rows("spec_titles.csv")}
        copy = {row["copy_key"]: row for row in self._rows("Localized_Copy.csv")}
        for lang, heading in REVIEWED_HEADING.items():
            with self.subTest(lang=lang):
                self.assertEqual(heading, titles["ENVIRONMENTAL OPERATING TEMPERATURE"][f"title_{lang}"])
                self.assertEqual(heading, copy["spec.section.environmental_operating_temperature"][f"text_{lang}"])


class Je1000hEuUsbCCautionTests(unittest.TestCase):
    """JE-1000H's print rates the high-power USB-C port at 140 W (fr/es/de/it/uk PDF pages 29/46/63/80/97).

    The shared EU operation carrier keeps the other models' 100 W text; JE-1000H gets its own
    ``.. only:: model_je_1000h`` branch with the printed wattage and the added 28 V/5 A rating.
    """

    def test_je1000h_branch_carries_the_printed_rating_and_others_keep_100w(self) -> None:

        for lang in ("fr", "es", "de", "it", "uk"):
            text = (ROOT / f"docs/templates/page_eu-{lang}/05_operation_guide_placeholder.rst").read_text(encoding="utf-8")
            je1000h = text.split(".. only:: model_je_1000h", 1)[1].split(".. only:: not model_je_1000h", 1)[0]
            others = text.split(".. only:: not model_je_1000h", 1)[1]
            with self.subTest(lang=lang):
                usb_c = [line for line in je1000h.splitlines() if "PS3" in line]
                self.assertEqual(1, len(usb_c))
                self.assertIn("140", usb_c[0])
                self.assertNotIn("100", usb_c[0])
                self.assertRegex(je1000h, r"\(20\s?(V|В)[^)]*100\s?(W|Вт)\s?; 28\s?(V|В)[^)]*140\s?(W|Вт)\)")
                other_usb_c = [line for line in others.splitlines() if "PS3" in line]
                self.assertEqual(1, len(other_usb_c))
                self.assertIn("100", other_usb_c[0])
                self.assertNotRegex(others.split("PS3", 1)[1].split("\n\n", 1)[0], r"28\s?(V|В)")

if __name__ == "__main__":
    unittest.main()
