from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tools.product_matrix_base import matrix, projects
from tools.product_matrix_base.extract import (
    compare, extract, inside_git_work_tree, load_dictionary, parse_value, quantities, spec_rows, table_rows,
)
from tools.product_matrix_base.stage import (
    BATCH, LoadError, PartialWrite, fact_key, plan, preflight, provenance, read_rows, same, stage_rows, write,
)

MANIFEST = Path(__file__).resolve().parents[1] / "bitable_schema" / "product_matrix_base_manifest.json"
EN = """# SAFETY

<table><tr><th>Not</th><td>a spec</td></tr></table>

# SPECIFICATIONS

## GENERAL INFO

<figure><table class="hb-spec-table"><tbody>
<tr><th scope="row">Capacity</th><td>321 Wh (12.5 Ah / 25.7 V DC)</td></tr>
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
<tr><th>Capacité</th><td>321 Wh</td></tr>
<tr><th>Poids</th><td>Environ 7,1 kg</td></tr>
<tr><th>Dimensions</th><td>30 x 20 x 21 cm</td></tr>
</tbody></table>
"""
JA = """## 主な仕様

<div><table class="manual-table native-spec"><tbody>
<tr><td class="native-key">定格容量</td><td>321Wh</td></tr>
<tr><td class="native-key">動作温度</td><td>-10°C~45°C</td></tr>
</tbody></table></div>
"""
PANEL = """# TECHNICAL PARAMETERS

<table class="manual-table"><tbody>
<tr><th>Electrical Data</th><th>STC*</th><th>BNPI*</th></tr>
<tr><td>Maximum Power (Pmax)</td><td>123W±4%</td><td>134W±4%</td></tr>
<tr><td>IP Rating</td><td colspan="2">IP65</td></tr>
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
                         ("321 Wh (12.5 Ah / 25.7 V DC)", "SPECIFICATIONS > GENERAL INFO", "general-info", 1, 1))
        self.assertEqual(rows[1]["text"], "LiFePO4")
        self.assertEqual(spec_rows(FR)[0]["anchor"], "spec-general")

    def test_column_headers_name_each_value_of_a_multi_column_row(self):
        rows = table_rows(PANEL.split("<table class=\"manual-table\">")[1].split("</table>")[0])
        self.assertEqual([(r["label"], r["column"], r["text"]) for r in rows],
                         [("Maximum Power (Pmax)", "STC*", "123W±4%"), ("Maximum Power (Pmax)", "BNPI*", "134W±4%"),
                          ("IP Rating", "", "IP65")])

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
        self.assertEqual((matrix_columns[0], matrix_columns[-1]), ("产品键", "生成时间"))
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
                          facts["ac_surge_w"]["number"]), (321, 800, 1600))
        self.assertEqual((facts["ac_surge_w"]["qualifier"], facts["weight_kg"]["qualifier"]), ("峰值", "约"))
        self.assertEqual(facts["usb_c_max_w"]["number"], 100)
        self.assertEqual(facts["usb_c_max_w"]["label"], "1 × USB-C 100 W")
        self.assertEqual((facts["dimensions_mm"]["text"], facts["dimensions_mm"]["original_unit"]),
                         ("300 × 200 × 200", "cm"))
        self.assertEqual(facts["battery_chemistry"]["text"], "LiFePO4")
        self.assertEqual(facts["discharge_temp_range"]["text"], "-10~45")
        panel = {f["attribute"]: f for f in self.edition("JS-S", "US", "en")["facts"]}
        self.assertEqual((panel["panel_power_w"]["number"], panel["panel_power_w"]["condition"]), (123, "STC*"))
        japanese = {f["attribute"]: f for f in self.edition("JE-B", "JP", "ja")["facts"]}
        self.assertEqual(japanese["capacity_wh"]["number"], 321)  # a td/td table the export's own reader misses

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
                         ("Capacity: 321 Wh (12.5 Ah / 25.7 V DC)", 321, "2026-11-16 09:02:03"))
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
            if len(names) > 50:  # the CLI's projection limit
                return {"ok": False, "error": {"message": "Array must contain at most 50 element(s)."}}
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
        self.assertTrue(same(321, "321", "number"))
        self.assertTrue(same("2026-11-16 23:57:44", "2026-11-16T23:57:44.000+08:00", "datetime"))
        self.assertTrue(same("2026-11-16 23:57:44", 1794844664000, "datetime"))
        self.assertFalse(same("2026-11-16 23:57:44", "2026-11-16T23:57:45.000+08:00", "datetime"))
        self.assertFalse(same("2026-11-16 23:57:44", "", "datetime"))
        self.assertTrue(same("a", [{"text": "a"}], "text"))
        self.assertFalse(same("a", "b", "text"))


class OutputGuardTest(unittest.TestCase):
    def test_output_inside_a_git_work_tree_is_refused(self):
        self.assertTrue(inside_git_work_tree(MANIFEST.parent))
        with TemporaryDirectory() as tmp:
            self.assertFalse(inside_git_work_tree(Path(tmp)))


class RenameMapTest(unittest.TestCase):
    def test_renames_are_one_to_one_and_reach_every_production_key(self):
        path = Path(__file__).resolve().parents[1] / "tools" / "product_matrix_base" / "attribute_key_renames.json"
        renames = json.loads(path.read_text(encoding="utf-8"))["renames"]
        finals = list(renames.values())
        self.assertEqual(len(finals), len(set(finals)))
        self.assertTrue({a["key"] for a in load_dictionary()} <= set(finals))


PRODUCTS = [{"产品键": "JE-A/US", "型号": "JE-A", "市场": "US", "品牌": "自有", "项目号（仅飞书）": "P-FAKE-1"},
            {"产品键": "JE-B/JP", "型号": "JE-B", "市场": "JP", "品牌": "自有"}]
ATTRIBUTES = [
    {"属性键": "capacity_wh", "中文名": "标称容量", "值类型": ["数值"], "规范单位": "Wh", "状态": ["启用"], "排序": 1},
    {"属性键": "ac_input", "中文名": "AC 输入", "值类型": ["文本"], "规范单位": "W", "状态": ["启用"], "排序": 2},
    {"属性键": "discharge_temp_range", "中文名": "放电温度范围", "值类型": ["范围"], "规范单位": "°C", "排序": 3},
    {"属性键": "model_number", "中文名": "型号", "值类型": ["文本"], "规范单位": "", "排序": 4},
    {"属性键": "unused_key", "中文名": "未用", "值类型": ["文本"], "规范单位": "", "排序": 5},
]
SOURCES = [{"来源键": "web/a", "来源类型": ["网页说明书"], "页面或文件": "JE-A/US/en/md/manual_en.html"},
           {"来源键": "spec/a", "来源类型": ["规格书"], "页面或文件": "sheet-a.pdf"}]


def fact(product, key, **fields):
    return {"产品键": product, "属性键": key, "来源键": "web/a", "核实状态": ["候选"],
            "记录时间": "2026-11-16T10:00:00.000+08:00", **fields}


FACTS = [
    fact("JE-A/US", "capacity_wh", 数值=333, 原文="Capacity: 333 Wh"),
    fact("JE-A/US", "capacity_wh", 数值=500, 来源键="spec/a", 核实状态=["已核实"]),
    fact("JE-A/US", "capacity_wh", 数值=999, 核实状态=["已驳回"]),
    fact("JE-A/US", "ac_input", 文本值="100~120", 原文="AC Input: 100-120 V~ 60 Hz, 15 A max."),
    fact("JE-A/US", "discharge_temp_range", 文本值="-10~45"),
    fact("JE-A/US", "model_number", 文本值="JE-A"),
    fact("JE-A/US", "capacity_wh", 文本值="7777Wh", 条件="组件:Pack"),
    fact("JE-B/JP", "capacity_wh", 文本值="50/60", 原文="容量: 50/60"),
]


class MatrixBuildTest(unittest.TestCase):
    def setUp(self):
        self.built = matrix.build(PRODUCTS, ATTRIBUTES, FACTS, SOURCES)

    def test_columns_are_typed_readable_and_only_for_attributes_with_values(self):
        self.assertEqual([(c["name"], c["type"]) for c in self.built["columns"]],
                         [("标称容量（Wh）", "number"), ("AC 输入", "text"), ("放电温度范围", "text"),
                          ("型号（说明书）", "text")])

    def test_best_value_counts_and_components(self):
        row = self.built["rows"]["JE-A/US"]
        self.assertEqual(row["标称容量（Wh）"], 500)  # the verified fact wins over a newer candidate
        self.assertEqual(row["AC 输入"], "100-120 V~ 60 Hz, 15 A max.")  # printed text, not a bare voltage range
        self.assertEqual(row["放电温度范围"], "-10~45 °C")
        self.assertEqual((row["已核实数"], row["候选数"], row["组件事实数"]), (1, 3, 1))
        self.assertEqual((row["项目号"], row["事实数"]), ("P-FAKE-1", 5))
        self.assertEqual(row["来源"], "JE-A/US/en/md/manual_en.html; sheet-a.pdf")
        self.assertNotIn("项目号", self.built["rows"]["JE-B/JP"])
        self.assertFalse(self.built["launch"])  # no launch date anywhere: no column
        names = [f["name"] for f in matrix.manifest_fields(self.built)]
        self.assertEqual(names[:3], ["产品键", "项目号", "型号"])
        self.assertNotIn("上市日期", names)
        dated = matrix.build([dict(PRODUCTS[0], 上市日期="2026-03-01T00:00:00.000+08:00")], ATTRIBUTES, FACTS, SOURCES)
        self.assertEqual(dated["rows"]["JE-A/US"]["上市日期"], "2026-03-01 00:00:00")
        self.assertEqual(self.built["components"], 1)

    def test_a_numeric_fact_without_a_number_stays_empty_and_is_listed(self):
        self.assertNotIn("标称容量（Wh）", self.built["rows"]["JE-B/JP"])
        self.assertEqual(self.built["empty"], [{"产品键": "JE-B/JP", "属性键": "capacity_wh", "事实键": "",
                                                "原因": "无数值", "原文": "容量: 50/60"}])
        self.assertEqual(matrix.skip_reason({"数值": 12, "原单位": "V"}, "W"), "单位与列不符")
        self.assertEqual(matrix.skip_reason({"数值": 7.1, "原单位": "lbs"}, "kg"), "")
        self.assertEqual(matrix.filled_cells(self.built), (4, 8))


class MatrixBase(FakeBase):
    def __init__(self):
        super().__init__()
        self.schema["矩阵"] = [{"name": "产品键", "type": "text"}, {"name": "capacity_wh", "type": "text"}]

    def __call__(self, args: list[str]) -> dict:
        command = args[0]
        table = args[args.index("--table-id") + 1] if "--table-id" in args else None
        if command == "+field-create":
            self.schema[table].append(json.loads(args[args.index("--json") + 1]))
            return {"ok": True, "data": {}}
        if command == "+field-delete":
            name = args[args.index("--field-id") + 1]
            self.schema[table] = [f for f in self.schema[table] if f["name"] != name]
            return {"ok": True, "data": {}}
        if command == "+record-upsert":
            record = args[args.index("--record-id") + 1]
            row = next(r for r in self.rows[table] if r["_id"] == record)
            row.update(json.loads(args[args.index("--json") + 1]))
            return {"ok": True, "data": {}}
        return super().__call__(args)


class MatrixWriteTest(unittest.TestCase):
    def test_write_read_back_rerun_and_update(self):
        base = MatrixBase()
        snapshot = {"ids": {name: name for name in base.schema}}
        built = matrix.build(PRODUCTS, ATTRIBUTES, FACTS, SOURCES)
        planned = matrix.plan(base, snapshot, built)
        self.assertIn("capacity_wh", planned["unused"])  # the manifest's key-named placeholder columns
        report = matrix.write(base, planned, sleep=lambda _s: None)
        self.assertEqual((report["created"], report["missing"], report["mismatched"]), (2, [], []))
        self.assertEqual(matrix.drop_unused(base, planned), planned["unused"])
        again = matrix.plan(base, snapshot, built)
        self.assertEqual((again["add"], again["create"], again["update"], again["unused"]), ([], [], [], []))
        changed = matrix.build(PRODUCTS, ATTRIBUTES, FACTS + [fact("JE-B/JP", "model_number", 文本值="JE-B")], SOURCES)
        update = matrix.plan(base, snapshot, changed)["update"]
        self.assertEqual([(u["key"], u["fields"]) for u in update],
                         [("JE-B/JP", {"型号（说明书）": "JE-B", "事实数": 2, "候选数": 1})])

    def test_wide_tables_are_read_fifty_fields_at_a_time(self):
        base = MatrixBase()
        base.schema["矩阵"] += [{"name": f"c{i}", "type": "text"} for i in range(80)]
        base.rows["矩阵"].append({"产品键": "X", "c79": "v", "_id": "rec0"})
        rows = read_rows(base, "矩阵", ["产品键"] + [f"c{i}" for i in range(80)])
        self.assertEqual((len(rows), rows[0]["产品键"], rows[0]["c79"]), (1, "X", "v"))

    def test_columns_holding_values_are_never_dropped(self):
        base = MatrixBase()
        base.rows["矩阵"].append({"产品键": "X", "capacity_wh": "333", "_id": "rec0"})
        planned = matrix.plan(base, {"ids": {name: name for name in base.schema}},
                              matrix.build(PRODUCTS, ATTRIBUTES, FACTS, SOURCES))
        with self.assertRaises(LoadError):
            matrix.drop_unused(base, planned)


class ProvenanceTest(unittest.TestCase):
    TARGETS = [{"model": "JE-A", "region": "US", "lang": "en", "version": "v-en"}]

    def test_facts_must_trace_to_a_published_web_manual(self):
        good = {"来源": [{"来源键": "web/JE-A/US/en/v-en", "来源类型": "网页说明书"}],
                "事实": [{"事实键": "k", "来源键": "web/JE-A/US/en/v-en"}]}
        self.assertEqual(provenance(good, [], self.TARGETS), [])
        bad = {"来源": [{"来源键": "web/JE-A/US/en/v-old", "来源类型": "网页说明书"},
                       {"来源键": "sheet/JE-A/1", "来源类型": "规格书"}],
               "事实": [{"事实键": "k", "来源键": "nowhere"}, {"事实键": "j", "来源键": "live/x"}]}
        self.assertEqual(provenance(bad, [{"来源键": "live/x", "来源类型": ["网页说明书"]}], self.TARGETS), [
            "来源 live/x: not a publication in the publish manifest",
            "来源 sheet/JE-A/1: kind '规格书' has no provenance check",
            "来源 web/JE-A/US/en/v-old: not a publication in the publish manifest",
            "事实 cites 来源 nowhere, which is neither staged nor in the base"])


class PartialWriteTest(StagingTest):
    def test_a_failed_batch_still_reads_back_what_was_created(self):
        staged = stage_rows(self.document, CATALOG, now=self.moment)
        base = FakeBase()
        original = base.__call__

        def failing(args):
            if args[0] == "+record-batch-create" and args[args.index("--table-id") + 1] == "来源":
                return {"ok": False, "error": {"message": "boom"}}
            return original(args)

        with self.assertRaises(PartialWrite) as caught:
            write(failing, plan(base, staged), use_records_shape=True, sleep=lambda _s: None)
        report = caught.exception.report
        self.assertEqual(report["产品"]["read_back"], len(staged["产品"]))
        self.assertEqual((report["来源"]["sent"], report["来源"]["read_back"]), (0, 0))
        self.assertNotIn("事实", report)


class ProjectsTest(unittest.TestCase):
    def test_only_a_unique_project_fills_an_empty_field_and_codes_stay_out_of_the_summary(self):
        base = MatrixBase()
        base.schema["网页文档"] = [{"name": "型号", "type": "text"}, {"name": "项目号", "type": "text"}]
        base.rows["网页文档"] = [{"型号": "JE-A", "项目号": "P-FAKE-1", "_id": "w1"},
                                {"型号": "JE-A", "项目号": "P-FAKE-1", "_id": "w2"},
                                {"型号": "JE-C", "项目号": "P-FAKE-2", "_id": "w3"},
                                {"型号": "JE-C", "项目号": "P-FAKE-3", "_id": "w4"}]
        base.rows["产品"] = [{"产品键": "JE-A/US", "型号": "JE-A", "_id": "r1"},
                            {"产品键": "JE-B/JP", "型号": "JE-B", "_id": "r2"},
                            {"产品键": "JE-C/EU", "型号": "JE-C", "_id": "r3"},
                            {"产品键": "JE-D/EU", "型号": "JE-D", "项目号（仅飞书）": "P-HAND", "_id": "r4"}]
        planned = projects.plan(base)
        summary = projects.summary(planned)
        self.assertEqual(summary, {"products": 4, "projects": 3, "filled": ["JE-D/EU"], "fill": ["JE-A/US"],
                                   "ambiguous": ["JE-C/EU"], "unknown": ["JE-B/JP"]})
        self.assertNotIn("P-FAKE", json.dumps(summary))
        written = projects.write(base, planned, sleep=lambda _s: None)
        self.assertEqual((written["sent"], written["matched"], written["problems"]), (1, 1, []))
        self.assertEqual(base.rows["产品"][0]["项目号（仅飞书）"], "P-FAKE-1")
        self.assertEqual(base.rows["产品"][3]["项目号（仅飞书）"], "P-HAND")


if __name__ == "__main__":
    unittest.main()
