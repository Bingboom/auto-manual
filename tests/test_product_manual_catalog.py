from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

_SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / ".agents" / "skills" / "product-manual-catalog" / "scripts" / "query_product_manuals.py"
)
_SPEC = importlib.util.spec_from_file_location("query_product_manuals", _SCRIPT_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(f"Unable to load {_SCRIPT_PATH}")
query_product_manuals = importlib.util.module_from_spec(_SPEC)
sys.modules["query_product_manuals"] = query_product_manuals
_SPEC.loader.exec_module(query_product_manuals)


class TestProductManualCatalogArgs(unittest.TestCase):
    def test_search_flag_sets_query(self) -> None:
        # Regression: --search must not be clobbered to None by the absent
        # positional's default (they previously shared an argparse dest).
        self.assertEqual("HTE153", query_product_manuals.parse_args(["--search", "HTE153"]).query)

    def test_positional_sets_query(self) -> None:
        self.assertEqual("HTE153", query_product_manuals.parse_args(["HTE153"]).query)

    def test_query_defaults_to_none(self) -> None:
        self.assertIsNone(query_product_manuals.parse_args([]).query)

    def test_explicit_table_override_tracks_flag(self) -> None:
        default_args = query_product_manuals.parse_args([])
        self.assertFalse(default_args.explicit_table_override)
        self.assertEqual(query_product_manuals.DEFAULT_TABLE_ID, default_args.table_id)
        override_args = query_product_manuals.parse_args(["--table-id", "tblCustom"])
        self.assertTrue(override_args.explicit_table_override)
        self.assertEqual("tblCustom", override_args.table_id)
        self.assertEqual("", override_args.view_id)


class TestProductManualCatalogMatching(unittest.TestCase):
    def test_matches_project_code_field(self) -> None:
        # The 项目 (project) column must be searchable, e.g. HTE153 -> JE-1000F row.
        row = {"产品型号": "JE-1000F", "项目": "HTE153"}
        self.assertTrue(query_product_manuals.matches(row, "HTE153"))
        self.assertTrue(query_product_manuals.matches(row, "je-1000f"))
        self.assertFalse(query_product_manuals.matches(row, "JBP-2000B"))

    def test_project_and_business_no_are_rendered(self) -> None:
        # Regression: a result block must surface the project code so a project
        # lookup is verifiable in the output.
        self.assertIn("项目", query_product_manuals.DETAIL_FIELDS)
        self.assertIn("业务号", query_product_manuals.DETAIL_FIELDS)
        rendered = query_product_manuals.render_record_markdown(
            {"产品型号": "JE-1000F", "项目": "HTE153", "业务号": "Doc-016"}
        )
        self.assertIn("HTE153", rendered)

    def test_region_alias_matching(self) -> None:
        args = query_product_manuals.parse_args(["--region", "日规"])
        self.assertTrue(query_product_manuals.passes_filters({"区域": "JP"}, args))
        self.assertTrue(query_product_manuals.passes_filters({"区域": "日规"}, args))
        self.assertFalse(query_product_manuals.passes_filters({"区域": "欧英规"}, args))

        eu_args = query_product_manuals.parse_args(["--region", "EU"])
        self.assertTrue(query_product_manuals.passes_filters({"区域": "欧英规"}, eu_args))

    def test_normalize_web_record_extracts_markdown_url_and_fields(self) -> None:
        raw = {
            "record_id": "recWeb1",
            "fields": {
                "型号": "JE-2000F",
                "商品简称": "E2000 v2",
                "项目号": "HTE154",
                "市场": "日规",
                "语言": "日语",
                "文档类型": ["产品说明书"],
                "产品类别": "便携储能",
                "产品系列": "Plus",
                "超链接": "[https://ht-docs-ht-manuals.readthedocs-hosted.com/en/latest/JE-2000F/JP/ja/md/manual_je2000f_jp_ja.html](https://ht-docs-ht-manuals.readthedocs-hosted.com/en/latest/JE-2000F/JP/ja/md/manual_je2000f_jp_ja.html)",
            },
        }
        norm = query_product_manuals.normalize_web_record(raw)
        fields = norm["fields"]
        self.assertEqual("JE-2000F", fields["产品型号"])
        self.assertEqual("HTE154", fields["项目"])
        self.assertEqual("便携储能 / Plus", fields["分类"])
        self.assertEqual("True", fields["Is_latest"])
        anchor, url = query_product_manuals.link_of(fields)
        self.assertEqual("JE-2000F E2000 v2 (日规 · 日语)", anchor)
        self.assertEqual(
            "https://ht-docs-ht-manuals.readthedocs-hosted.com/en/latest/JE-2000F/JP/ja/md/manual_je2000f_jp_ja.html",
            url,
        )


    def test_normalize_web_record_handles_search_api_lookup_wrappers(self) -> None:
        raw = {
            "record_id": "recLookup1",
            "fields": {
                "型号": [{"text": "JE-1000F", "type": "text"}],
                "商品简称": [{"text": "E1000 v2", "type": "text"}],
                "项目号": [{"text": "HTE153", "type": "text"}],
                "客户型号(关联)": {"type": 1, "value": [{"text": "JE-1000F", "type": "text"}]},
                "产品类别": {"type": 3, "value": ["便携储能"]},
                "产品系列": {"type": 3, "value": ["标准"]},
                "容量档": {"type": 3, "value": ["1度电"]},
                "市场": [{"text": "欧英规", "type": "text"}],
                "语言": [{"text": "英语", "type": "text"}],
                "文档类型": "产品说明书",
                "超链接": {
                    "link": "https://ht-docs-ht-manuals.readthedocs-hosted.com/en/latest/JE-1000F/EU/en/md/manual_je1000f_eu_en.html",
                    "text": "https://ht-docs-ht-manuals.readthedocs-hosted.com/en/latest/JE-1000F/EU/en/md/manual_je1000f_eu_en.html",
                    "type": "url",
                },
            },
        }
        norm = query_product_manuals.normalize_web_record(raw)
        fields = norm["fields"]
        self.assertEqual("便携储能 / 标准", fields["分类"])
        self.assertEqual("1度电", fields["容量档"])
        self.assertEqual("JE-1000F", fields["客户型号"])
        anchor, url = query_product_manuals.link_of(fields)
        self.assertEqual("JE-1000F E1000 v2 (欧英规 · 英语)", anchor)
        self.assertTrue(url.endswith("manual_je1000f_eu_en.html"))


class TestProductManualCatalogFallback(unittest.TestCase):
    def test_falls_back_to_web_docs_table_when_default_table_inaccessible(self) -> None:
        def fake_fetch(*, cli, base_token, table_id, view_id, identity, max_records):
            if table_id == query_product_manuals.DEFAULT_TABLE_ID:
                raise RuntimeError(json.dumps({"ok": False, "code": 1254004, "message": "WrongTableId"}))
            if table_id == query_product_manuals.WEB_DOCS_TABLE_ID:
                self.assertEqual("", view_id)
                return [
                    {
                        "record_id": "recWeb1",
                        "fields": {
                            "型号": "JE-2000F",
                            "项目号": "HTE154",
                            "市场": "美加规",
                            "语言": "英语",
                            "文档类型": ["产品说明书"],
                            "产品类别": "便携储能",
                            "超链接": "[https://example.invalid/je2000f](https://example.invalid/je2000f)",
                        },
                    }
                ]
            raise AssertionError(f"Unexpected table_id: {table_id}")

        with mock.patch.object(query_product_manuals, "fetch_records", side_effect=fake_fetch):
            records, active_table, note = query_product_manuals.load_catalog_records(
                cli="lark-cli",
                base_token="WGVwb2HctauRi7sEiKqcIzTRn1c",
                table_id=query_product_manuals.DEFAULT_TABLE_ID,
                view_id=query_product_manuals.DEFAULT_VIEW_ID,
                identity="bot",
                explicit_table_override=False,
                no_fallback=False,
            )
        self.assertEqual(query_product_manuals.WEB_DOCS_TABLE_ID, active_table)
        self.assertIn(query_product_manuals.WEB_DOCS_TABLE_ID, note)
        self.assertEqual(1, len(records))
        self.assertEqual("JE-2000F", records[0]["fields"]["产品型号"])

    def test_explicit_table_override_does_not_fall_back(self) -> None:
        with mock.patch.object(
            query_product_manuals,
            "fetch_records",
            side_effect=RuntimeError(json.dumps({"ok": False, "code": 1254004, "message": "WrongTableId"})),
        ):
            with self.assertRaises(RuntimeError):
                query_product_manuals.load_catalog_records(
                    cli="lark-cli",
                    base_token="WGVwb2HctauRi7sEiKqcIzTRn1c",
                    table_id="tblExplicit",
                    view_id="",
                    identity="bot",
                    explicit_table_override=True,
                    no_fallback=False,
                )


if __name__ == "__main__":
    unittest.main()
