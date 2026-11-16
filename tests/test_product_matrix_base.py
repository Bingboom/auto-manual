from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tools.product_matrix_base.extract import (
    compare, extract, inside_git_work_tree, load_dictionary, parse_value, quantities, spec_rows, table_rows,
)
from tools.product_matrix_base.stage import (
    BATCH, LoadError, fact_key, plan, preflight, same, stage_rows, write,
)

MANIFEST = Path(__file__).resolve().parents[1] / "bitable_schema" / "product_matrix_base_manifest.json"
EN = """# SAFETY

<table><tr><th>Not</th><td>a spec</td></tr></table>

# SPECIFICATIONS

## GENERAL INFO

<figure><table class="hb-spec-table"><tbody>
<tr><th scope="row">Capacity</th><td>512 Wh (20 Ah / 25.6 V DC)</td></tr>
<tr><th scope="row">Cell Chemistry</th><td>LiFePO<sub>4</sub></td></tr>
<tr><th scope="row">Weight</th><td>About 7.1 kg</td></tr>
<tr><th scope="row">Dimensions</th><td>30 x 20 x 20 cm</td></tr>
<tr><th scope="row">Mystery Row</th><td>42 widgets</td></tr>
</tbody></table></figure>

## OUTPUT PORTS

<table class="hb-spec-table"><tbody>
<tr><th>2 × AC</th><td>230 V~, 800 W Rated, 800 W in Total, 1600 W Surge Peak</td></tr>
<tr><th>1 × USB-C 60 W</th><td>60 W max.</td></tr>
<tr><th>1 × USB-C 100 W</th><td>100 W max.</td></tr>
<tr><th>Discharging Temperature</th><td>-10 °C to 45 °C</td></tr>
</tbody></table>

# WARRANTY

<table><tr><th>Period</th><td>3 years</td></tr></table>
"""
FR = """# SPÉCIFICATIONS

<span id="spec-general"></span>

## INFORMATIONS GÉNÉRALES

<table class="hb-spec-table"><tbody>
<tr><th>Capacité</th><td>512 Wh</td></tr>
<tr><th>Poids</th><td>Environ 7,1 kg</td></tr>
<tr><th>Dimensions</th><td>30 x 20 x 21 cm</td></tr>
</tbody></table>
"""
JA = """## 主な仕様

<div><table class="manual-table native-spec"><tbody>
<tr><td class="native-key">定格容量</td><td>512Wh</td></tr>
<tr><td class="native-key">動作温度</td><td>-10°C~45°C</td></tr>
</tbody></table></div>
"""
PANEL = """# TECHNICAL PARAMETERS

<table class="manual-table"><tbody>
<tr><th>Electrical Data</th><th>STC*</th><th>BNPI*</th></tr>
<tr><td>Maximum Power (Pmax)</td><td>100W±5%</td><td>110W±5%</td></tr>
<tr><td>IP Rating</td><td colspan="2">IP68</td></tr>
</tbody></table>
"""
MANUALS = {("JE-A", "US", "en"): EN, ("JE-A", "US", "fr"): FR, ("JE-B", "JP", "ja"): JA,
           ("JS-S", "US", "en"): PANEL, ("JX-G", "US", "en"): "# GUIDE\n\nNo table here.\n"}
CATALOG = {"JE-A": {"category": "便携储能", "series": "标准", "capacity": "1度以下", "short": "A500"},
           "JS-S": {"category": "太阳能板", "series": "SolarSaga", "short": "100W"}}


def target(model: str, region: str, lang: str) -> dict:
    return {"model": model, "region": region, "lang": lang, "route": f"{model}/{region}/{lang}/md",
            "manual": f"manual_{lang}.md", "version": f"v-{lang}", "built_at": "2026-11-01T00:00:00+00:00"}


class TableParsingTest(unittest.TestCase):
    def test_rows_keep_label_and_text_verbatim_with_sections_and_anchors(self):
        rows = spec_rows(EN)
        self.assertEqual([r["label"] for r in rows][:5],
                         ["Capacity", "Cell Chemistry", "Weight", "Dimensions", "Mystery Row"])
        self.assertNotIn("Not", [r["label"] for r in rows])  # a table outside the specifications
        self.assertNotIn("Period", [r["label"] for r in rows])
        first = rows[0]
        self.assertEqual((first["text"], first["section"], first["anchor"], first["table"], first["row"]),
                         ("512 Wh (20 Ah / 25.6 V DC)", "SPECIFICATIONS > GENERAL INFO", "general-info", 1, 1))
        self.assertEqual(rows[1]["text"], "LiFePO4")
        self.assertEqual(spec_rows(FR)[0]["anchor"], "spec-general")

    def test_column_headers_name_each_value_of_a_multi_column_row(self):
        rows = table_rows(PANEL.split("<table class=\"manual-table\">")[1].split("</table>")[0])
        self.assertEqual([(r["label"], r["column"], r["text"]) for r in rows],
                         [("Maximum Power (Pmax)", "STC*", "100W±5%"), ("Maximum Power (Pmax)", "BNPI*", "110W±5%"),
                          ("IP Rating", "", "IP68")])

    def test_quantities_read_thousands_and_decimal_commas(self):
        self.assertEqual([(q["value"], q["unit"]) for q in quantities("3,000 cycles, Environ 7,1 kg, 1.5 kW")],
                         [(3000, "cycles"), (7.1, "kg"), (1.5, "kW")])

    def test_dictionary_values(self):
        by_key = {a["key"]: a for a in load_dictionary()}
        self.assertEqual(parse_value(by_key["dimensions_mm"], "13 x 9 x 10 in (330 x 229 x 254 mm)"),
                         {"number": None, "text": "330 × 229 × 254", "unit": "mm"})
        self.assertEqual(parse_value(by_key["discharge_temp_range"], "-10 °C to 45 °C")["text"], "-10~45")
        self.assertEqual(parse_value(by_key["usb_c_max_w"], "100 W max.")["number"], 100)
        self.assertIsNone(parse_value(by_key["ac_input_max_w"], "220-240 V~ 50 Hz, 10 A max."))


class DictionaryAndManifestTest(unittest.TestCase):
    def test_dictionary_keeps_the_export_keys_and_matches_the_manifest(self):
        keys = [a["key"] for a in load_dictionary()]
        self.assertEqual(keys[:9], ["capacity_wh", "ac_rated_w", "ac_surge_w", "weight_kg", "cycle_life",
                                    "panel_power_w", "ip_rating", "output_w", "expansion_port"])
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        tables = {t["name"]: t for t in manifest["tables"]}
        self.assertEqual(list(tables), ["产品", "属性", "来源", "事实", "矩阵"])
        matrix_columns = [f["name"] for f in tables["矩阵"]["fields"]]
        self.assertTrue(set(keys) <= set(matrix_columns))
        primaries = {name: t["fields"][0]["name"] for name, t in tables.items()}
        self.assertEqual(primaries, {"产品": "产品键", "属性": "属性键", "来源": "来源键", "事实": "事实键",
                                     "矩阵": "产品键"})
        state = next(f for f in tables["事实"]["fields"] if f["name"] == "核实状态")
        self.assertEqual(state["options"][0], "候选")


def publication(root: Path) -> dict:
    """A synthetic publication under ``root`` and its extraction."""
    publish = root / "docs" / "publish"
    for key, text in MANUALS.items():
        row = target(*key)
        path = publish / "web" / row["route"] / row["manual"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    (publish / "publish_manifest.json").write_text(
        json.dumps({"built_at": "2026-11-12", "targets": [target(*k) for k in MANUALS]}), encoding="utf-8")
    return extract(root, catalog_models=CATALOG)


class ExtractionTest(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.document = publication(Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def edition(self, model: str, market: str, lang: str) -> dict:
        return next(e for e in self.document["editions"]
                    if (e["model"], e["market"], e["language"]) == (model, market, lang))

    def test_every_edition_and_every_row_is_kept(self):
        self.assertEqual(self.document["summary"]["editions"], 5)
        self.assertEqual(len(self.edition("JE-A", "US", "en")["rows"]), 9)
        self.assertIn("JX-G/US/en: no specification table found", self.document["problems"])
        unmapped = {u["label"] for u in self.document["unmapped"]}
        self.assertIn("Mystery Row", unmapped)
        self.assertNotIn("Capacity", unmapped)

    def test_values_by_export_rules_and_by_dictionary(self):
        facts = {f["attribute"]: f for f in self.edition("JE-A", "US", "en")["facts"]}
        self.assertEqual((facts["capacity_wh"]["number"], facts["ac_rated_w"]["number"],
                          facts["ac_surge_w"]["number"]), (512, 800, 1600))
        self.assertEqual((facts["ac_surge_w"]["qualifier"], facts["weight_kg"]["qualifier"]), ("峰值", "约"))
        self.assertEqual(facts["usb_c_max_w"]["number"], 100)
        self.assertEqual(facts["usb_c_max_w"]["label"], "1 × USB-C 100 W")
        self.assertEqual((facts["dimensions_mm"]["text"], facts["dimensions_mm"]["original_unit"]),
                         ("300 × 200 × 200", "cm"))
        self.assertEqual(facts["battery_chemistry"]["text"], "LiFePO4")
        self.assertEqual(facts["discharge_temp_range"]["text"], "-10~45")
        panel = {f["attribute"]: f for f in self.edition("JS-S", "US", "en")["facts"]}
        self.assertEqual((panel["panel_power_w"]["number"], panel["panel_power_w"]["condition"]), (100, "STC*"))
        japanese = {f["attribute"]: f for f in self.edition("JE-B", "JP", "ja")["facts"]}
        self.assertEqual(japanese["capacity_wh"]["number"], 512)  # a td/td table the export's own reader misses

    def test_language_editions_are_compared(self):
        found = {d["attribute"]: d for d in compare(self.document["editions"])}
        self.assertEqual(found["dimensions_mm"]["values"], [{"value": "300 × 200 × 200", "languages": ["en"]},
                                                            {"value": "300 × 200 × 210", "languages": ["fr"]}])
        self.assertIn("_rows", found)


class StagingTest(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.document = publication(Path(self.tmp.name))
        self.moment = datetime(2026, 11, 16, 1, 2, 3, tzinfo=timezone.utc)

    def tearDown(self):
        self.tmp.cleanup()

    def test_rows_per_table_with_keys_and_candidate_state(self):
        staged = stage_rows(self.document, CATALOG, models=["JE-A"], now=self.moment)
        self.assertEqual([p["产品键"] for p in staged["产品"]], ["JE-A/US"])
        self.assertEqual(staged["产品"][0]["容量档"], "1度以下")
        self.assertEqual([s["来源键"] for s in staged["来源"]], ["web/JE-A/US/en/v-en", "web/JE-A/US/fr/v-fr"])
        self.assertEqual(staged["来源"][0]["版本日期依据"], "未知")
        keys = [f["事实键"] for f in staged["事实"]]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertIn("JE-A/US|capacity_wh|-|web/JE-A/US/en/v-en", keys)
        self.assertTrue(all(f["核实状态"] == "候选" for f in staged["事实"]))
        self.assertTrue(all("生效起" not in f and "当前值" not in f for f in staged["事实"]))
        capacity = next(f for f in staged["事实"] if f["事实键"].startswith("JE-A/US|capacity_wh|-|web/JE-A/US/en"))
        self.assertEqual((capacity["原文"], capacity["数值"], capacity["记录时间"]),
                         ("Capacity: 512 Wh (20 Ah / 25.6 V DC)", 512, "2026-11-16 09:02:03"))
        self.assertIn("SPECIFICATIONS > GENERAL INFO · 表1 行1 · #general-info", capacity["来源位置"])
        self.assertEqual(fact_key("P/US", "k", "", "s"), "P/US|k|-|s")


class FakeBase:
    """A base with the five tables that remembers created rows and lists them back."""

    def __init__(self, drop: set[str] | None = None):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.schema = {t["name"]: t["fields"] for t in manifest["tables"]}
        self.rows: dict[str, list[dict]] = {name: [] for name in self.schema}
        self.batches: list[int] = []
        self.drop = drop or set()

    def __call__(self, args: list[str]) -> dict:
        command = args[0]
        table = args[args.index("--table-id") + 1] if "--table-id" in args else None
        if command == "+table-list":
            return {"ok": True, "data": {"tables": [{"name": n, "id": n} for n in self.schema]}}
        if command == "+field-list":
            fields = [{**f, "options": [{"name": o} for o in f.get("options", [])]} for f in self.schema[table]]
            return {"ok": True, "data": {"fields": fields}}
        if command == "+record-list":
            names = [args[i + 1] for i, a in enumerate(args) if a == "--field-id"]
            offset = int(args[args.index("--offset") + 1])
            page = self.rows[table][offset:offset + 200]
            return {"ok": True, "data": {"fields": names, "data": [[r.get(n) for n in names] for r in page],
                                         "record_id_list": [r["_id"] for r in page]}}
        if command == "+record-batch-create":
            payload = json.loads(args[args.index("--json") + 1])
            self.batches.append(len(payload["create_records"]))
            for row in payload["create_records"]:
                if any(str(v) in self.drop for v in row.values()):
                    continue
                self.rows[table].append({**row, "_id": f"rec{len(self.rows[table])}"})
            return {"ok": True, "data": {}}
        return {"ok": False, "error": {"message": command}}


class LoadTest(StagingTest):
    def test_dry_run_write_read_back_and_second_run_creates_nothing(self):
        staged = stage_rows(self.document, CATALOG, now=self.moment)
        base = FakeBase()
        planned = plan(base, staged)
        self.assertEqual(planned["problems"], [])
        self.assertEqual(planned["tables"]["事实"]["existing"], 0)
        report = write(base, planned, use_records_shape=True, sleep=lambda _s: None)
        for table, entry in report.items():
            self.assertEqual((entry["missing"], entry["mismatched"]), ([], []), table)
            self.assertEqual(entry["read_back"], len(staged[table]))
        again = plan(base, staged)
        self.assertEqual({t: len(i["create"]) for t, i in again["tables"].items()},
                         {"产品": 0, "属性": 0, "来源": 0, "事实": 0})

    def test_batches_stay_within_the_limit_and_missing_rows_are_reported(self):
        staged = stage_rows(self.document, CATALOG, now=self.moment)
        staged["事实"] = [dict(staged["事实"][0], 事实键=f"k{i}") for i in range(BATCH * 2 + 5)]
        base = FakeBase(drop={"k3"})
        report = write(base, plan(base, staged), use_records_shape=True, sleep=lambda _s: None)
        self.assertTrue(all(size <= BATCH for size in base.batches))
        self.assertEqual(report["事实"]["missing"], ["k3"])

    def test_preflight_stops_unknown_fields_and_options(self):
        staged = {"来源": [{"来源键": "x", "语言": "xx"}], "事实": [{"事实键": "y", "新字段": "z"}]}
        schema = {"来源": {"来源键": {"type": "text"}, "语言": {"type": "select", "options": [{"name": "en"}]}},
                  "事实": {"事实键": {"type": "text"}}}
        self.assertEqual(preflight(staged, schema), ["事实.新字段: field is missing in the base", "来源.语言: no option 'xx'"])
        base = FakeBase()
        planned = plan(base, {"来源": [{"来源键": "x", "语言": "xx"}]})
        with self.assertRaises(LoadError):
            write(base, planned, use_records_shape=True, sleep=lambda _s: None)

    def test_read_back_comparison(self):
        self.assertTrue(same(["便携储能"], [{"name": "便携储能"}], "select"))
        self.assertTrue(same(512, "512", "number"))
        self.assertTrue(same("a", [{"text": "a"}], "text"))
        self.assertFalse(same("a", "b", "text"))


class OutputGuardTest(unittest.TestCase):
    def test_output_inside_a_git_work_tree_is_refused(self):
        self.assertTrue(inside_git_work_tree(MANIFEST.parent))
        with TemporaryDirectory() as tmp:
            self.assertFalse(inside_git_work_tree(Path(tmp)))


if __name__ == "__main__":
    unittest.main()
