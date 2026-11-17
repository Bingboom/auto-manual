from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tools.product_matrix_base import cells, matrix, projects, snapshot
from tools.product_matrix_base.reader import inside_git_work_tree, read_publication
from tools.product_matrix_base.reader.labels import UNMAPPED, map_label
from tools.product_matrix_base.reader.values import parse_value
from tools.product_matrix_base.rows import load_dictionary, stage_rows
from tools.product_matrix_base.stage import (
    BATCH, LoadError, PartialWrite, correct, correction_plan, earliest, fact_key, plan, preflight, provenance,
    read_rows, same, without_excluded, write,
)

MANIFEST = Path(__file__).resolve().parents[1] / "bitable_schema" / "product_matrix_base_manifest.json"
# Synthetic manuals: every figure below is invented.
EN = """# SAFETY

<table><tr><th>Not</th><td>a spec</td></tr></table>

# SPECIFICATIONS

## GENERAL INFO

<figure><table class="hb-spec-table"><tbody>
<tr><th scope="row">Product Name</th><td>Explorer Fake 300</td></tr>
<tr><th scope="row">Model No.</th><td>JE-A</td></tr>
<tr><th scope="row">Capacity</th><td>321 Wh (12.5 Ah / 25.7 V DC)</td></tr>
<tr><th scope="row">Cell Chemistry</th><td>LiFePO<sub>4</sub></td></tr>
<tr><th scope="row">Weight</th><td>About 7.1 kg</td></tr>
<tr><th scope="row">Dimensions</th><td>30 x 20 x 20 cm</td></tr>
<tr><th scope="row">Mystery Row</th><td>42 widgets</td></tr>
</tbody></table></figure>

## INPUT PORTS

<table class="hb-spec-table"><tbody>
<tr><th>AC Input</th><td>100-120 V~ 60 Hz, 12 A max.</td></tr>
<tr><th>USB-C</th><td>5 V⎓3 A, 60 W max.</td></tr>
</tbody></table>

## OUTPUT PORTS

<table class="hb-spec-table"><tbody>
<tr><th>2 × AC</th><td>230 V~, 800 W Rated, 800 W in Total, 1600 W Surge Peak</td></tr>
<tr><th>1 × USB-C 60 W</th><td>60 W max.</td></tr>
<tr><th>1 × USB-C 100 W</th><td>100 W max.</td></tr>
<tr><th>Discharging Temperature</th><td>-10 °C to 45 °C</td></tr>
</tbody></table>

## BATTERY PACK (SOLD SEPARATELY)

<table class="hb-spec-table"><tbody>
<tr><th>Product Name</th><td>Fake Battery Pack 777</td></tr>
<tr><th>Capacity</th><td>777 Wh</td></tr>
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
<tr><td class="native-key">サイズ＆重量</td><td>約 300 x 200 x 200 mm（約 7.1kg）</td></tr>
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
MOMENT = datetime(2026, 11, 16, 1, 2, 3, tzinfo=timezone.utc)


def target(model: str, region: str, lang: str) -> dict:
    return {"model": model, "region": region, "lang": lang, "route": f"{model}/{region}/{lang}/md",
            "manual": f"manual_{lang}.md", "version": f"v-{lang}", "built_at": "2026-11-01T00:00:00+00:00"}


def publication(root: Path) -> dict:
    """A synthetic publication under ``root`` and its reading."""
    publish = root / "docs" / "publish"
    for key, text in MANUALS.items():
        row = target(*key)
        path = publish / "web" / row["route"] / row["manual"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    (publish / "publish_manifest.json").write_text(
        json.dumps({"built_at": "2026-11-12", "targets": [target(*k) for k in MANUALS]}), encoding="utf-8")
    return read_publication(root)


class ReadingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = TemporaryDirectory()
        cls.reading = publication(Path(cls.tmp.name))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def facts(self, model: str, market: str) -> dict:
        return {f["attribute_key"]: f for f in self.reading["facts"] if (f["model"], f["region"]) == (model, market)}

    def test_every_row_is_kept_with_its_section_and_unmapped_labels_are_listed(self):
        rows = [r for r in self.reading["rows"] if r["source_file"].startswith("JE-A/US/en")]
        labels = [r["row_label_clean"] for r in rows]
        self.assertNotIn("Not", labels)  # a table outside the specifications
        period = next(r for r in rows if r["row_label_clean"] == "Period")  # a warranty card: kept, not an attribute
        self.assertEqual((period["table_kind"], period["attribute_key"]), ("spec_like_elsewhere", UNMAPPED))
        capacity = next(r for r in rows if r["row_label_clean"] == "Capacity")
        self.assertEqual((capacity["value_text"], capacity["section_path"]),
                         ("321 Wh (12.5 Ah / 25.7 V DC)", "SPECIFICATIONS > GENERAL INFO"))
        self.assertIn(("en", "Mystery Row"), {(u["language"], u["label"]) for u in self.reading["unmapped"]})
        self.assertIn("JX-G/US/en: no specification table", self.reading["problems"])
        self.assertEqual(self.reading["summary"]["editions"], 5)

    def test_one_fact_per_attribute_from_the_primary_edition(self):
        facts = self.facts("JE-A", "US")
        self.assertEqual((facts["capacity_wh"]["value_metric"], facts["capacity_wh"]["source_language"]), ("321", "en"))
        self.assertEqual((facts["ac_rated_w"]["value_metric"], facts["ac_surge_w"]["value_metric"]), ("800", "1600"))
        self.assertEqual(facts["usb_c_max_w"]["value_metric"], "100")
        self.assertEqual(facts["usb_c_input"]["value_text"], "5 V⎓3 A, 60 W max.")  # bare port, input heading
        self.assertEqual(facts["dimensions_mm"]["value_metric"], "300×200×200")
        self.assertTrue(facts["dimensions_mm"]["language_check"].startswith("extent differs") or
                        facts["dimensions_mm"]["language_check"].startswith("differ"))
        self.assertEqual(self.facts("JS-S", "US")["panel_power_w"]["value_text"],
                         "Maximum Power (Pmax) [STC*]: 123W±4% ‖ Maximum Power (Pmax) [BNPI*]: 134W±4%")
        japanese = self.facts("JE-B", "JP")
        self.assertEqual(japanese["dimensions_and_weight"]["value_metric"], "300×200×200")

    def test_a_component_block_never_becomes_the_main_product(self):
        self.assertEqual(self.facts("JE-A", "US")["capacity_wh"]["value_metric"], "321")
        self.assertEqual([(c["component_product"], c["attribute_key"], c["value_text"])
                          for c in self.reading["components"]],
                         [("Fake Battery Pack 777", "capacity_wh", "777 Wh"),
                          ("Fake Battery Pack 777", "product_name", "Fake Battery Pack 777")])

    def test_labels_and_values(self):
        self.assertEqual(map_label("USB-C", "INPUT PORTS", "spec_section")[0], "usb_c_input")
        self.assertEqual(map_label("USB-C", "OUTPUT PORTS", "spec_section")[0], "usb_c_output")
        self.assertEqual(map_label("USB-C", "GENERAL", "spec_section")[0], UNMAPPED)
        self.assertEqual(map_label("Poids", "", "spec_section")[0], "weight_kg")
        weight = parse_value("weight_kg", "Environ 7,1 kg")
        self.assertEqual((weight["value_metric"], weight["qualifier"]), ("7.1", "Environ"))
        self.assertEqual(parse_value("discharge_temp_range", "-10 °C to 45 °C")["range_min"], "-10")


class DictionaryAndManifestTest(unittest.TestCase):
    def test_dictionary_keeps_the_export_keys_and_matches_the_manifest(self):
        keys = {a["属性键"] for a in load_dictionary()}
        self.assertEqual(len(keys), 140)
        self.assertTrue({"capacity_wh", "ac_rated_w", "ac_surge_w", "weight_kg", "cycle_life", "panel_power_w",
                         "ip_rating", "output_w", "expansion_port"} <= keys)
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


class StagingTest(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.document = publication(Path(self.tmp.name))
        self.moment = MOMENT

    def tearDown(self):
        self.tmp.cleanup()

    def stage(self, **kwargs) -> dict:
        return stage_rows(self.document, CATALOG, batch="test-batch", now=self.moment, dictionary=[], **kwargs)

    def test_rows_per_table_with_keys_and_candidate_state(self):
        staged = self.stage(models=["JE-A"])
        self.assertEqual([p["产品键"] for p in staged["产品"]], ["JE-A/US"])
        self.assertEqual(staged["产品"][0]["容量档"], "1度以下")
        self.assertEqual([s["来源键"] for s in staged["来源"]], ["web/JE-A/US/en/v-en", "web/JE-A/US/fr/v-fr"])
        self.assertEqual((staged["来源"][0]["版本日期依据"], staged["来源"][0]["写入批次"]), ("未知", "test-batch"))
        keys = [f["事实键"] for f in staged["事实"]]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertTrue(all(f["核实状态"] == "候选" and f["写入批次"] == "test-batch" for f in staged["事实"]))
        self.assertTrue(all("生效起" not in f and "当前值" not in f for f in staged["事实"]))
        capacity = next(f for f in staged["事实"] if f["事实键"] == "JE-A/US|capacity_wh|-|web/JE-A/US/en/v-en")
        self.assertEqual((capacity["原文"], capacity["数值"], capacity["记录时间"], capacity["来源位置"]),
                         ("Capacity: 321 Wh (12.5 Ah / 25.7 V DC)", 321, "2026-11-16 09:02:03",
                          "SPECIFICATIONS > GENERAL INFO"))
        weight = next(f for f in staged["事实"] if f["属性键"] == "weight_kg")
        self.assertEqual((weight["数值"], weight["限定"]), (7.1, "约"))
        component = next(f for f in staged["事实"] if f.get("条件", "").startswith("组件:"))
        self.assertEqual(component["事实键"], "JE-A/US|capacity_wh|组件:Fake Battery Pack 777|web/JE-A/US/en/v-en")
        self.assertEqual(fact_key("P/US", "k", "", "s"), "P/US|k|-|s")

    def test_a_power_row_without_watts_keeps_its_printed_text(self):
        ac_input = next(f for f in self.stage()["事实"] if f["属性键"] == "ac_input")
        self.assertEqual((ac_input.get("数值"), ac_input["文本值"], ac_input.get("原单位")),
                         (None, "100-120 V~ 60 Hz, 12 A max.", None))
        temperature = next(f for f in self.stage()["事实"] if f["属性键"] == "discharge_temp_range")
        self.assertEqual((temperature["文本值"], temperature["原单位"]), ("-10~45", "°C"))


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
        staged = self.stage()
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
        staged = self.stage()
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
        self.assertEqual(set(finals), {a["属性键"] for a in load_dictionary()})


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
        self.assertFalse(self.built["sku_time"])
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


class CellsTest(unittest.TestCase):
    ATTRIBUTES = [{"属性键": "capacity_wh", "值类型": ["数值"], "规范单位": "Wh"},
                  {"属性键": "pv_power_w", "值类型": ["数值"], "规范单位": "W"},
                  {"属性键": "ac_input", "值类型": ["文本"]},
                  {"属性键": "old_key", "状态": ["停用"]}]
    SOURCES = [{"来源键": "web/a", "来源类型": ["网页说明书"]}, {"来源键": "sheet/a", "来源类型": ["规格书"]}]

    def build(self, facts):
        return cells.build_cells(facts, self.ATTRIBUTES, self.SOURCES, snapshot.source_id)

    def test_verified_wins_then_source_rank_and_rejected_never_takes_part(self):
        facts = [{"事实键": "w", "产品键": "P/US", "属性键": "capacity_wh", "来源键": "web/a", "数值": 321},
                 {"事实键": "s", "产品键": "P/US", "属性键": "capacity_wh", "来源键": "sheet/a", "数值": 333,
                  "核实状态": ["已核实"]},
                 {"事实键": "r", "产品键": "P/US", "属性键": "capacity_wh", "来源键": "web/a", "数值": 7777,
                  "核实状态": ["已驳回"]},
                 {"事实键": "x", "产品键": "P/US", "属性键": "old_key", "来源键": "web/a", "文本值": "x"}]
        [cell] = self.build(facts)
        self.assertEqual((cell["number"], cell["verified"], cell["candidates"]),
                         (333, True, [cells.value_id("s"), cells.value_id("w")]))

    def test_condition_names_match_without_word_boundaries(self):
        self.assertEqual([cells.cell_condition(c) for c in ("STC条件", "NOCT: 800W/m²", "BNPI", "BNPIX", "to 70% capacity",
                                                            "stc")],
                         ["STC", "NOCT", "BNPI", None, None, "STC"])
        self.assertEqual([cells.display_text(v, True, "Wh") for v in (1e-07, 2.50, 300.0, 0.0)],
                         ["0.0000001 Wh", "2.5 Wh", "300 Wh", "0 Wh"])

    def test_a_bare_range_shows_its_printed_text_and_equal_numbers_agree(self):
        facts = [{"事实键": "a", "产品键": "P/US", "属性键": "ac_input", "来源键": "web/a", "文本值": "100~120",
                  "原文": "AC Input: 100~120V"},
                 {"事实键": "b", "产品键": "P/JP", "属性键": "capacity_wh", "来源键": "web/a", "数值": 100},
                 {"事实键": "c", "产品键": "P/JP", "属性键": "capacity_wh", "来源键": "sheet/a", "数值": 100.0}]
        by_product = {c["product"]: c for c in self.build(facts)}
        self.assertEqual((by_product["P/US"]["display"], by_product["P/US"]["number"]), ("100~120V", None))
        self.assertEqual((by_product["P/JP"]["display"], by_product["P/JP"]["sources_disagree"]), ("100 Wh", False))

    def test_test_conditions_get_their_own_cell_and_others_share_the_main_one(self):
        facts = [{"事实键": "a", "产品键": "P/US", "属性键": "pv_power_w", "来源键": "web/a", "数值": 123},
                 {"事实键": "b", "产品键": "P/US", "属性键": "pv_power_w", "来源键": "web/a", "数值": 99,
                  "条件": "STC (as printed)"},
                 {"事实键": "c", "产品键": "P/US", "属性键": "pv_power_w", "来源键": "web/a", "数值": 123,
                  "条件": "to 70% capacity"}]
        built = self.build(facts)
        self.assertEqual([(c["condition"], len(c["candidates"])) for c in built], [(None, 2), ("STC", 1)])

    def test_a_number_in_another_unit_leaves_the_cell_empty_with_its_reason(self):
        facts = [{"事实键": "a", "产品键": "P/US", "属性键": "capacity_wh", "来源键": "web/a", "数值": 9, "原单位": "Ah"}]
        [cell] = self.build(facts)
        self.assertEqual((cell["display"], cell["number"], cell["empty_reason"]), (None, None, "单位与列不符"))


class EarliestTest(unittest.TestCase):
    def test_lookup_cells_yield_their_earliest_moment(self):
        joined = "2025/02/03 10:00 (GMT+8),2024/07/30 09:15 (GMT+8)"
        self.assertEqual(earliest(joined), int(datetime(2024, 7, 30, 1, 15, tzinfo=timezone.utc).timestamp()))
        self.assertEqual(earliest(["2025-01-01T00:00:00.000+08:00", 1704067200000]), 1704067200)
        self.assertEqual(earliest({"type": 5, "value": [1704067200000]}), 1704067200)
        self.assertEqual(earliest("2024-01-01 08:00"), 1704067200)  # no offset: Beijing time
        self.assertEqual(earliest("45292.3333333333"), 1704067200)  # a formula's day serial, Beijing time
        self.assertEqual(earliest(45292.5), 1704067200 + 4 * 3600)
        self.assertIsNone(earliest("2024"))  # a bare year is not a day serial of 1905
        self.assertIsNone(earliest("2014/12/31 23:00"))  # before any product of ours
        self.assertIsNone(earliest(4102444800000))  # 2100: in the future
        self.assertEqual(earliest(["2024", "2024-01-01 08:00"]), 1704067200)  # the implausible one is skipped
        self.assertIsNone(earliest(""))
        self.assertIsNone(earliest("no date here"))

    def test_the_upper_bound_ends_with_2023(self):
        self.assertTrue(snapshot._first_sku("2023-12-31 23:00")["first_sku_created_upper_bound"])
        self.assertFalse(snapshot._first_sku("2024-01-01 00:00")["first_sku_created_upper_bound"])
        self.assertEqual(snapshot._first_sku("2024")["first_sku_created"], None)

    def test_matrix_and_snapshot_carry_it_apart_from_the_launch_date(self):
        product = dict(PRODUCTS[0], **{"SKU 最早创建时间（本市场）": "2025/02/03 10:00 (GMT+8),2024/07/30 09:15 (GMT+8)"})
        built = matrix.build([product], ATTRIBUTES, FACTS, SOURCES)
        self.assertEqual(built["rows"]["JE-A/US"]["SKU 最早创建时间"], "2024-07-30 09:15:00")
        self.assertNotIn("上市日期", built["rows"]["JE-A/US"])
        self.assertIn({"name": "SKU 最早创建时间", "type": "datetime"}, matrix.manifest_fields(built))
        base = SnapshotTest().base()
        base.rows["产品"][1]["SKU 最早创建时间（本市场）"] = "2025/02/03 10:00 (GMT+8),2024/07/30 09:15 (GMT+8)"
        base.rows["产品"][0]["SKU 最早创建时间（本市场）"] = "45215.5"  # a formula's day serial: 2023-10-16 12:00
        document = snapshot.build_snapshot(base, now=datetime(2026, 11, 17, tzinfo=timezone.utc))
        first = document["products"][0]
        self.assertEqual((first["first_sku_created"], first["launch_date"]), ("2024-07-30", "2026-03-01"))
        self.assertIn("不是上市日期", first["first_sku_created_basis"])
        self.assertFalse(first["first_sku_created_upper_bound"])
        loaded = document["products"][1]  # within PLM's late-2023 data load (to 2023-12-31): only an upper bound
        self.assertEqual((loaded["first_sku_created"], loaded["first_sku_created_upper_bound"]), ("2023-10-16", True))
        bare = snapshot.build_snapshot(SnapshotTest().base(), now=datetime(2026, 11, 17, tzinfo=timezone.utc))
        self.assertEqual({(p["first_sku_created"], p["first_sku_created_basis"]) for p in bare["products"]},
                         {(None, None)})


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
        if command == "+record-delete":
            gone = set(json.loads(args[args.index("--json") + 1])["record_id_list"])
            self.rows[table] = [r for r in self.rows[table] if r["_id"] not in gone]
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
        self.assertEqual(matrix.drop_columns(base, planned, planned["unused"]), planned["unused"])
        again = matrix.plan(base, snapshot, built)
        self.assertEqual((again["add"], again["create"], again["update"], again["unused"]), ([], [], [], []))
        changed = matrix.build(PRODUCTS, ATTRIBUTES, FACTS + [fact("JE-B/JP", "model_number", 文本值="JE-B")], SOURCES)
        update = matrix.plan(base, snapshot, changed)["update"]
        self.assertEqual([(u["key"], u["fields"]) for u in update],
                         [("JE-B/JP", {"型号（说明书）": "JE-B", "事实数": 2, "候选数": 1})])

    def test_excluded_and_deleted_products_leave_the_matrix(self):
        base = MatrixBase()
        snapshot = {"ids": {name: name for name in base.schema}}
        matrix.write(base, matrix.plan(base, snapshot, matrix.build(PRODUCTS, ATTRIBUTES, FACTS, SOURCES)),
                     sleep=lambda _s: None)
        kept = [dict(PRODUCTS[0], 不收录=True)] + PRODUCTS[1:]
        planned = matrix.plan(base, snapshot, matrix.build(kept, ATTRIBUTES, FACTS, SOURCES))
        self.assertEqual(([item["key"] for item in planned["removable"]], planned["remove"]),
                         ([PRODUCTS[0]["产品键"]], []))  # a candidate, never deleted by default
        with self.assertRaises(LoadError):  # a kept product's row can never be named for removal
            matrix.select_removal(planned, [PRODUCTS[1]["产品键"]])
        untouched = matrix.write(base, planned, sleep=lambda _s: None)  # a caller writing a plan deletes nothing
        self.assertEqual((untouched["removed"], untouched["rows_after"], untouched["row_count_ok"]), (0, 2, True))
        planned["remove"] = matrix.select_removal(planned, [PRODUCTS[0]["产品键"]])
        report = matrix.write(base, planned, sleep=lambda _s: None)
        self.assertEqual((report["removed"], report["removed_keys"], report["lingering"]),
                         (1, [PRODUCTS[0]["产品键"]], []))
        self.assertEqual((report["rows_after"], report["rows_expected"], report["row_count_ok"]), (1, 1, True))
        again = matrix.plan(base, snapshot, matrix.build(PRODUCTS[1:], ATTRIBUTES, FACTS, SOURCES))
        self.assertEqual((again["create"], again["update"], again["removable"]), ([], [], []))

    def test_without_the_exclude_field_nothing_runs(self):
        base = MatrixBase()
        base.schema["产品"] = [f for f in base.schema["产品"] if f["name"] != "不收录"]
        with self.assertRaises(LoadError) as caught:
            matrix.read_base(base)
        self.assertIn("不收录", str(caught.exception))
        snap = SnapshotTest().base()
        snap.schema["产品"] = [f for f in snap.schema["产品"] if f["name"] != "不收录"]
        with self.assertRaises(LoadError):
            snapshot.build_snapshot(snap)

    def test_a_row_count_that_does_not_add_up_fails_the_read_back(self):
        base = MatrixBase()
        snapshot = {"ids": {name: name for name in base.schema}}
        planned = matrix.plan(base, snapshot, matrix.build(PRODUCTS, ATTRIBUTES, FACTS, SOURCES))
        planned["rows_before"] = 5  # as if rows vanished between the plan and the read-back
        self.assertFalse(matrix.write(base, planned, sleep=lambda _s: None)["row_count_ok"])

    def test_two_rows_with_one_key_leave_one_behind_without_deleting_more(self):
        base = MatrixBase()
        base.rows["矩阵"] += [{"产品键": "GONE/US", "_id": "d1"}, {"产品键": "GONE/US", "_id": "d2"}]
        snapshot = {"ids": {name: name for name in base.schema}}
        planned = matrix.plan(base, snapshot, matrix.build(PRODUCTS, ATTRIBUTES, FACTS, SOURCES))
        planned["remove"] = matrix.select_removal(planned, ["GONE/US"])
        report = matrix.write(base, planned, sleep=lambda _s: None)
        self.assertEqual((report["lingering"], len(base.rows["矩阵"])), (["GONE/US"], 3))  # 2 created + 1 left

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
            matrix.drop_columns(base, planned, ["capacity_wh"])
        with self.assertRaises(LoadError):  # a column the generator produces is never dropped
            matrix.drop_columns(base, planned, ["产品键"])
        self.assertEqual(matrix.drop_columns(base, planned, []), [])  # nothing is dropped by sweep


class ExcludedProductTest(unittest.TestCase):
    def test_products_marked_not_included_are_never_staged_again(self):
        staged = {"产品": [{"产品键": "JE-A/US"}, {"产品键": "JE-B/JP"}],
                  "来源": [{"来源键": "web/JE-A/US/en/v", "型号": "JE-A", "市场": "US"},
                          {"来源键": "web/JE-B/JP/ja/v", "型号": "JE-B", "市场": "JP"}],
                  "事实": [{"事实键": "a", "产品键": "JE-A/US"}, {"事实键": "b", "产品键": "JE-B/JP"}]}
        kept, skipped = without_excluded(staged, {"JE-A/US"})
        self.assertEqual({t: [r.get("产品键") or r["来源键"] for r in rows] for t, rows in kept.items()},
                         {"产品": ["JE-B/JP"], "来源": ["web/JE-B/JP/ja/v"], "事实": ["JE-B/JP"]})
        self.assertEqual(skipped, {"产品": 1, "来源": 1, "事实": 1})
        self.assertEqual(without_excluded(staged, set()), (staged, {}))

    STAGED = {"产品": [{"产品键": "JE-A/US", "型号": "JE-A"}, {"产品键": "JE-B/JP", "型号": "JE-B"}],
              "来源": [{"来源键": "web/JE-A/US/en/v", "型号": "JE-A", "市场": "US"},
                      {"来源键": "web/JE-B/JP/ja/v", "型号": "JE-B", "市场": "JP"}],
              "事实": [{"事实键": "a", "产品键": "JE-A/US"}, {"事实键": "b", "产品键": "JE-B/JP"}]}

    def test_plan_skips_an_excluded_product_end_to_end(self):
        base = FakeBase()
        base.rows["产品"].append({"产品键": "JE-A/US", "型号": "JE-A", "不收录": True, "_id": "p1"})
        planned = plan(base, self.STAGED)
        self.assertEqual((planned["excluded"], planned["skipped"]), (["JE-A/US"], {"产品": 1, "来源": 1, "事实": 1}))
        self.assertEqual({t: [r.get("产品键") or r["来源键"] for r in info["create"]] for t, info in planned["tables"].items()},
                         {"产品": ["JE-B/JP"], "来源": ["web/JE-B/JP/ja/v"], "事实": ["JE-B/JP"]})
        self.assertEqual([r["事实键"] for r in planned["staged"]["事实"]], ["b"])  # provenance runs on these rows

    def test_plan_stops_without_the_exclude_field(self):
        base = FakeBase()
        base.schema["产品"] = [f for f in base.schema["产品"] if f["name"] != "不收录"]
        with self.assertRaises(LoadError) as caught:
            plan(base, self.STAGED)
        self.assertIn("不收录", str(caught.exception))


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
        staged = self.stage()
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
        self.assertEqual(summary, {"products": 4, "projects": 3, "filled": ["JE-D/EU"], "differs": [], "fill": ["JE-A/US"],
                                   "ambiguous": ["JE-C/EU"], "unknown": ["JE-B/JP"]})
        self.assertNotIn("P-FAKE", json.dumps(summary))
        written = projects.write(base, planned, sleep=lambda _s: None)
        self.assertEqual((written["sent"], written["matched"], written["problems"]), (1, 1, []))
        self.assertEqual(base.rows["产品"][0]["项目号（仅飞书）"], "P-FAKE-1")
        self.assertEqual(base.rows["产品"][3]["项目号（仅飞书）"], "P-HAND")


class CorrectionTest(StagingTest):
    KEY = "JE-A/US|{}|-|web/JE-A/US/en/v-en"

    def loaded(self) -> tuple[MatrixBase, dict, dict]:
        staged = self.stage()
        base = MatrixBase()
        write(base, plan(base, staged), use_records_shape=True, sleep=lambda _s: None)
        return base, staged, {r["事实键"]: r for r in base.rows["事实"]}

    def test_only_text_and_unit_differences_of_candidates_are_corrected_in_place(self):
        base, staged, rows = self.loaded()
        ac_input = rows[self.KEY.format("ac_input")]
        ac_input.update({"文本值": "100~120", "原单位": "V", "备注": "old note"})  # what the seed batch held
        rows[self.KEY.format("capacity_wh")].update({"数值": 999, "核实状态": "已核实"})  # verified: left alone
        rows[self.KEY.format("weight_kg")]["数值"] = 9.9  # a number differs: outside the whitelist
        rows[self.KEY.format("discharge_temp_range")].update({"文本值": "0~1", "来源位置": "elsewhere"})  # mixed
        product_name = rows[self.KEY.format("product_name")]
        product_name["文本值"] = "Old Name"
        planned = plan(base, staged)
        product_name_key = self.KEY.format("product_name")
        for item in planned["tables"]["事实"]["differ"]:  # make one correction empty the printed text value
            if item["key"] == product_name_key:
                item["fields"]["文本值"]["staged"] = None
        chosen = correction_plan(planned)
        self.assertEqual([item["key"] for item in chosen["correct"]], [self.KEY.format("ac_input")])
        reasons = {entry["key"]: entry["reason"] for entry in chosen["decide"]}
        self.assertEqual(reasons, {self.KEY.format("capacity_wh"): "核实状态为 已核实，不是候选",
                                   self.KEY.format("weight_kg"): "差异含白名单以外的字段：数值",
                                   self.KEY.format("discharge_temp_range"): "差异含白名单以外的字段：来源位置",
                                   product_name_key: "修正会清空：文本值"})
        report = correct(base, planned, "fix-batch", sleep=lambda _s: None)
        self.assertEqual((report["corrected"], report["fields"], report["mismatched"]),
                         (1, {"文本值": 1, "原单位": 1}, []))
        self.assertEqual((ac_input["文本值"], ac_input["原单位"], ac_input["写入批次"], ac_input["核实状态"]),
                         ("100-120 V~ 60 Hz, 12 A max.", None, "fix-batch", "候选"))
        self.assertEqual(ac_input["备注"], "old note；fix-batch 修正：文本值 原为「100~120」；原单位 原为「V」")
        self.assertEqual((rows[self.KEY.format("weight_kg")]["数值"],
                          rows[self.KEY.format("discharge_temp_range")]["文本值"]), (9.9, "0~1"))  # not half-corrected
        self.assertNotIn(self.KEY.format("ac_input"), [i["key"] for i in plan(base, staged)["tables"]["事实"]["differ"]])

    def test_a_row_verified_after_the_dry_run_is_not_corrected(self):
        base, staged, rows = self.loaded()
        row = rows[self.KEY.format("ac_input")]
        row.update({"文本值": "100~120", "原单位": "V"})
        planned = plan(base, staged)
        row["核实状态"] = "已核实"  # someone verified it between the dry run and the write
        report = correct(base, planned, "fix-batch", sleep=lambda _s: None)
        self.assertEqual((report["corrected"], report["needs_decision"][0]["reason"]), (0, "写入前复查：已不是候选"))
        self.assertEqual(row["文本值"], "100~120")

    def test_a_failed_correction_still_reads_back_what_it_changed(self):
        base, staged, rows = self.loaded()
        for key in ("ac_input", "product_name"):
            rows[self.KEY.format(key)]["文本值"] = "0~0"
        planned = plan(base, staged)
        calls = []

        def failing(args):
            if args[0] == "+record-upsert":
                calls.append(args)
                if len(calls) == 2:
                    return {"ok": False, "error": {"message": "boom"}}
            return base(args)

        with self.assertRaises(PartialWrite) as caught:
            correct(failing, planned, "fix-batch", sleep=lambda _s: None)
        self.assertEqual(caught.exception.report["事实"]["corrected"], 1)


class ProjectSafetyTest(unittest.TestCase):
    def base(self) -> MatrixBase:
        base = MatrixBase()
        base.schema["网页文档"] = [{"name": "型号", "type": "text"}, {"name": "项目号", "type": "text"}]
        base.rows["网页文档"] = [{"型号": "JE-A", "项目号": "P-FAKE-1", "_id": "w1"},
                                {"型号": "JE-B", "项目号": "P-FAKE-2", "_id": "w2"},
                                {"型号": "JE-D", "项目号": "P-FAKE-4", "_id": "w3"}]
        base.rows["产品"] = [{"产品键": "JE-A/US", "型号": "JE-A", "_id": "r1"},
                            {"产品键": "JE-B/JP", "型号": "JE-B", "_id": "r2"},
                            {"产品键": "JE-D/EU", "型号": "JE-D", "项目号（仅飞书）": "P-HAND", "_id": "r3"}]
        return base

    def test_a_failed_write_never_shows_the_project_number_and_reads_back_what_it_wrote(self):
        base = self.base()
        planned = projects.plan(base)
        self.assertEqual(projects.summary(planned)["differs"], ["JE-D/EU"])  # kept, reported by product key only

        def failing(args):
            if args[0] == "+record-upsert" and "r2" in args:
                return {"ok": False, "error": {"code": 1254000, "message": "bad value P-FAKE-2 in payload"}}
            return base(args)

        with self.assertRaises(PartialWrite) as caught:
            projects.write(failing, planned, sleep=lambda _s: None)
        self.assertNotIn("P-FAKE", str(caught.exception))
        self.assertIn("1254000", str(caught.exception))
        self.assertEqual((caught.exception.report["written"], caught.exception.report["not_written"],
                          caught.exception.report["matched"]), (["JE-A/US"], ["JE-B/JP"], 1))
        self.assertNotIn("P-FAKE", json.dumps(caught.exception.report))

    def test_matrix_write_errors_withhold_the_cli_text(self):
        base = MatrixBase()
        built = matrix.build(PRODUCTS, ATTRIBUTES, FACTS, SOURCES)
        planned = matrix.plan(base, {"ids": {name: name for name in base.schema}}, built)

        def failing(args):
            if args[0] == "+record-batch-create":
                return {"ok": False, "error": {"type": "api_error", "message": "rejected row P-FAKE-1"}}
            return base(args)

        with self.assertRaises(PartialWrite) as caught:
            matrix.write(failing, planned, sleep=lambda _s: None)
        self.assertNotIn("P-FAKE", str(caught.exception))


class SnapshotTest(unittest.TestCase):
    def base(self) -> MatrixBase:
        base = MatrixBase()
        base.rows["产品"] = [
            {"产品键": "JE-B/JP", "型号": "JE-B", "市场": ["JP"], "品牌": ["自有"], "_id": "r2"},
            {"产品键": "JE-A/US", "型号": "JE-A", "市场": ["US"], "品牌": ["自有"], "产品类别": ["便携储能"],
             "项目号（仅飞书）": "P-FAKE-1", "上市日期": "2026-03-01T00:00:00.000+08:00", "_id": "r1"}]
        base.rows["属性"] = [{"属性键": "capacity_wh", "中文名": "标称容量", "值类型": ["数值"], "规范单位": "Wh",
                             "适用类别": ["便携储能", "加电包"], "排序": 2, "_id": "a1"},
                            {"属性键": "product_name", "中文名": "产品名称", "排序": 1, "_id": "a2"}]
        base.rows["来源"] = [{"来源键": "web/JE-A/US/en/git-20260101-abc-internal", "来源类型": ["网页说明书"],
                             "型号": "JE-A", "市场": ["US"], "语言": ["en"], "页面或文件": "JE-A/US/en/md/m.html",
                             "_id": "s1"},
                            {"来源键": "sheet/JE-A/1", "来源类型": ["规格书"], "型号": "JE-A", "_id": "s2"}]
        base.rows["事实"] = [
            {"事实键": "k1", "产品键": "JE-A/US", "属性键": "capacity_wh", "来源键": "web/JE-A/US/en/git-20260101-abc-internal",
             "原文": "Capacity: 333 Wh", "数值": 333, "核实状态": ["候选"], "_id": "f1"},
            {"事实键": "k2", "产品键": "JE-A/US", "属性键": "capacity_wh", "来源键": "sheet/JE-A/1", "数值": 334,
             "核实状态": ["候选"], "_id": "f2"},
            {"事实键": "k3", "产品键": "JE-A/US", "属性键": "capacity_wh", "来源键": "sheet/JE-A/1",
             "文本值": "7777Wh", "条件": "组件:Fake Pack#2", "核实状态": ["候选"], "_id": "f3"}]
        return base

    def test_snapshot_is_sorted_opaque_and_keeps_components_apart(self):
        document = snapshot.build_snapshot(self.base(), now=datetime(2026, 11, 17, tzinfo=timezone.utc))
        self.assertEqual(document["counts"], {"products": 2, "parameters": 2, "sources": 2, "values": 2,
                                              "component_values": 1, "cells": 1, "products_with_project": 1,
                                              "products_with_first_sku": 0, "first_sku_upper_bound": 0})
        self.assertEqual([p["key"] for p in document["products"]], ["JE-A/US", "JE-B/JP"])
        self.assertEqual([p["key"] for p in document["parameters"]], ["product_name", "capacity_wh"])
        product = document["products"][0]
        self.assertEqual((product["project"], product["launch_date"], product["market"], product["category"]),
                         ("P-FAKE-1", "2026-03-01", "US", "便携储能"))
        self.assertEqual(document["parameters"][1]["applies_to"], ["便携储能", "加电包"])
        encoded = snapshot.encode(document).decode()
        for withheld in ("git-20260101", "web/JE-A", "_id", "\"k1\"", "\"f1\"", "\"s1\""):
            self.assertNotIn(withheld, encoded)
        self.assertEqual({v["source"] for v in document["values"]},
                         {snapshot.source_id("web/JE-A/US/en/git-20260101-abc-internal"), snapshot.source_id("sheet/JE-A/1")})
        self.assertTrue(all(v["sources_disagree"] for v in document["values"]))  # 333 vs 334
        self.assertEqual(document["component_values"][0]["component"], "Fake Pack")
        self.assertEqual(snapshot.encode(snapshot.build_snapshot(self.base(), now=datetime(2026, 11, 17, tzinfo=timezone.utc))), snapshot.encode(document))
        self.assertNotIn("P-FAKE", snapshot.summary(document))
        # v1.1: every value has an opaque id; one cell per product × parameter, chosen as the matrix chooses.
        self.assertEqual(document["schema"], "hello-docs-product-matrix-snapshot/v1.1")
        self.assertTrue(all(len(v["id"]) == 12 and v["id"] not in ("k1", "k2") for v in document["values"]))
        cell = document["cells"][0]
        self.assertEqual((cell["product"], cell["parameter"], cell["condition"]), ("JE-A/US", "capacity_wh", None))
        self.assertEqual((cell["number"], cell["display"], cell["unit"]), (333, "333 Wh", "Wh"))  # web manual beats the sheet
        self.assertEqual(cell["candidates"], [cells.value_id("k1"), cells.value_id("k2")])
        self.assertEqual(cell["value"], cell["candidates"][0])
        self.assertTrue(cell["sources_disagree"])
        self.assertFalse(cell["verified"])
        ids = {v["id"] for v in document["values"]}
        self.assertTrue(set(cell["candidates"]) <= ids)
        self.assertNotIn(cells.value_id("k3"), cell["candidates"])  # component facts never enter a cell
        # The cell agrees with the matrix's cell for the same product and parameter (plus the unit after a number).
        base = self.base()
        built = matrix.build(base.rows["产品"], base.rows["属性"], base.rows["事实"], base.rows["来源"])
        column = next(c for c in built["columns"] if c["key"] == "capacity_wh")
        self.assertEqual(cell["display"], f'{built["rows"]["JE-A/US"][column["name"]]} {column["unit"]}')

    def test_excluded_products_have_no_cells(self):
        base = self.base()
        base.rows["产品"][1]["不收录"] = True  # JE-A/US
        self.assertEqual(snapshot.build_snapshot(base, now=datetime(2026, 11, 17, tzinfo=timezone.utc))["cells"], [])

    def test_unresolvable_references_stop_the_snapshot(self):
        base = self.base()
        base.rows["来源"] = [r for r in base.rows["来源"] if not r["来源键"].startswith("web/")]
        for fact in base.rows["事实"][:2]:
            fact["来源键"] = "web/gone"  # the cell's source has no row
        with self.assertRaises(LoadError) as caught:
            snapshot.build_snapshot(base, now=datetime(2026, 11, 17, tzinfo=timezone.utc))
        self.assertIn("1 cells whose source has no row", str(caught.exception))
        self.assertEqual(caught.exception.rows, [("来源行缺失", "k1", "web/gone")])  # only the chosen fact causes it
        twin = self.base()
        twin.rows["事实"][1]["事实键"] = "k1"  # two facts with one key: one id twice
        with self.assertRaises(LoadError) as caught:
            snapshot.build_snapshot(twin, now=datetime(2026, 11, 17, tzinfo=timezone.utc))
        self.assertIn("1 duplicate value ids", str(caught.exception))
        self.assertNotIn("k1", str(caught.exception))
        self.assertEqual(caught.exception.rows, [("同键事实", "k1", "")])  # for --explain-references, never in the message

    def test_excluded_products_take_their_values_and_sources_out(self):
        base = self.base()
        base.rows["产品"][1]["不收录"] = True  # JE-A/US
        document = snapshot.build_snapshot(base, now=datetime(2026, 11, 17, tzinfo=timezone.utc))
        self.assertEqual([p["key"] for p in document["products"]], ["JE-B/JP"])
        self.assertEqual((document["counts"]["values"], document["counts"]["component_values"],
                          document["counts"]["sources"], document["counts"]["products_with_project"]), (0, 0, 0, 0))
        self.assertNotIn("P-FAKE", snapshot.encode(document).decode())
        base.rows["来源"].append({"来源键": "web/JE-B/JP/ja/v", "型号": "JE-B", "市场": ["JP"], "_id": "s3"})
        uncited = snapshot.build_snapshot(base, now=datetime(2026, 11, 17, tzinfo=timezone.utc))
        self.assertEqual(uncited["counts"]["sources"], 1)  # a kept product's source stays without a value

    @staticmethod
    def checkout(root: Path, name: str, landing: str, remote: str | None) -> Path:
        checkout = root / name
        checkout.mkdir()
        subprocess.run(["git", "init", "-q", str(checkout)], check=True)
        if remote:
            subprocess.run(["git", "-C", str(checkout), "remote", "add", "origin", f"https://example.test/Org/{remote}"],
                           check=True)
        for mirror, text in (("Hello-Docs", "hello docs"), ("Hello-Docs-Review", "review")):
            (checkout / "mirrors" / mirror).mkdir(parents=True)
            (checkout / "mirrors" / mirror / "README.md").write_text(text, encoding="utf-8")
        (checkout / "README.md").write_text(landing, encoding="utf-8")
        (checkout / "docs" / "knowledge").mkdir(parents=True)
        return checkout

    def test_it_is_written_only_under_the_knowledge_directory_of_the_private_mirror(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            private = self.checkout(root, "private", "hello docs", "Hello-Docs.git")
            target = snapshot.safe_destination(private / "docs" / "knowledge" / "product-matrix")
            self.assertEqual(target.name, "snapshot.json")
            refused = [
                self.checkout(root, "public", "auto-manual", "auto-manual") / "docs" / "knowledge" / "pm",
                # a copied mirror README does not turn a public checkout into the mirror
                self.checkout(root, "copied", "hello docs", "auto-manual") / "docs" / "knowledge" / "pm",
                self.checkout(root, "no-remote", "hello docs", None) / "docs" / "knowledge" / "pm",
                self.checkout(root, "review", "review", "Hello-Docs-Review") / "docs" / "knowledge" / "pm",
                self.checkout(root, "other", "hello docs", "something-else") / "docs" / "knowledge" / "pm",
                private / "docs" / "publish", root / "elsewhere"]
            for path in refused:
                with self.assertRaises(snapshot.SnapshotError, msg=str(path)):
                    snapshot.safe_destination(path)
            from tools.check_maintainability_guardrails import mirror_name
            self.assertIsNone(mirror_name(root / "copied"))  # the guardrail sees the public checkout too
            self.assertEqual(mirror_name(private), "Hello-Docs")

    def test_a_planted_link_is_never_written_through(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            private = self.checkout(root, "private", "hello docs", "hello-docs")
            out = private / "docs" / "knowledge" / "product-matrix"
            out.mkdir()
            victim = root / "victim.txt"
            victim.write_text("keep", encoding="utf-8")
            (out / "snapshot.json").symlink_to(victim)
            with self.assertRaises(snapshot.SnapshotError):
                snapshot.safe_destination(out)
            with self.assertRaises(snapshot.SnapshotError):
                snapshot.write_snapshot(out / "snapshot.json", {"schema": "x"})
            self.assertEqual(victim.read_text(encoding="utf-8"), "keep")
            (out / "snapshot.json").unlink()
            snapshot.write_snapshot(snapshot.safe_destination(out), {"schema": "x"})
            self.assertEqual(json.loads((out / "snapshot.json").read_text(encoding="utf-8")), {"schema": "x"})

    def test_a_failed_read_never_echoes_row_data(self):
        def failing(args):
            if args[0] == "+table-list":
                return {"ok": True, "data": {"tables": [{"name": n, "id": n} for n in ("产品", "属性", "来源", "事实")]}}
            return {"ok": False, "error": {"code": 99, "message": "row JE-A/US P-FAKE-1 could not be read"}}

        with self.assertRaises(LoadError) as caught:
            snapshot.build_snapshot(failing)
        self.assertNotIn("P-FAKE", str(caught.exception))


    def test_cli_output_that_is_not_json_is_never_echoed(self):
        from tools.product_matrix_base.stage import lark_runner

        with TemporaryDirectory() as tmp:
            fake = Path(tmp) / "fake-cli"
            fake.write_text("#!/bin/sh\necho 'JE-A/US P-FAKE-1 partial row'\nexit 3\n", encoding="utf-8")
            fake.chmod(0o755)
            result = lark_runner("base", lark_cli=str(fake))(["+record-list"])
        self.assertFalse(result["ok"])
        self.assertNotIn("P-FAKE", json.dumps(result))


if __name__ == "__main__":
    unittest.main()
