from __future__ import annotations

import unittest

from tools.manual_index_query import (
    ManualIndexSettings,
    _extract_filters,
    infer_manual_index_intent,
    query_manual_index_records,
)


SETTINGS = ManualIndexSettings(
    base_token="base",
    table_id="tbl",
    view_id="view",
    identity="user",
)


RAW_RECORDS = [
    {
        "record_id": "rec_je2000f",
        "fields": {
            "No.": 19,
            "业务号": "Doc-006",
            "产品型号": ["JE-2000F"],
            "项目": ["HTE154"],
            "说明书链接": (
                "[Jackery Explorer 2000 User Manual V2.0-2026-04-30]"
                "(https://alidocs.example/je2000f)"
            ),
            "说明书名称": "Jackery Explorer 2000 User Manual V2.0-2026-04-30",
            "区域": ["美加规"],
            "源语言": ["EN"],
            "归档日期": "2026-04-30 00:00:00",
            "产品简称": ["E2000V2"],
            "产品名称_en": ["Jackery Explorer 2000"],
            "文档类型": ["User Manual"],
            "产品阶段": ["PVT"],
            "版本": ["V2.0"],
            "分类": ["便携储能-主机"],
            "是否显示": "TRUE",
        },
    },
    {
        "record_id": "rec_js100i",
        "fields": {
            "No.": 14,
            "业务号": "Doc-021",
            "产品型号": ["JS-100I"],
            "项目": ["HTS006"],
            "说明书链接": "[SolarSaga 100 Air](https://alidocs.example/js100i)",
            "说明书名称": "Jackery SolarSaga 100 Air User Manual V2.0-2026-04-01",
            "区域": ["欧英规"],
            "源语言": ["EN"],
            "归档日期": "2026-04-01 00:00:00",
            "产品名称_zh": ["电小二 100W Mini太阳能板"],
            "文档类型": ["User Manual"],
            "产品阶段": ["PVT"],
            "版本": ["V2.0"],
            "分类": ["光伏板"],
            "是否显示": "TRUE",
        },
    },
]


class TestManualIndexQuery(unittest.TestCase):
    def test_infer_should_not_capture_build_copy_requests(self) -> None:
        intent = infer_manual_index_intent("输出JE-1000F的所有欧规说明书文案")

        self.assertFalse(intent.matched)
        self.assertEqual("queue_copy_execution", intent.reason)

    def test_query_product_manual_by_model(self) -> None:
        result = query_manual_index_records(
            RAW_RECORDS,
            query_text="查 JE-2000F 的说明书链接",
            settings=SETTINGS,
            limit=5,
        )

        self.assertTrue(result.matched)
        self.assertEqual("lookup", result.query_type)
        self.assertEqual(1, result.matched_count)
        self.assertEqual("rec_je2000f", result.rows[0].record_id)
        self.assertEqual("https://alidocs.example/je2000f", result.rows[0].manual_link)

    def test_overview_counts_visible_view_rows(self) -> None:
        result = query_manual_index_records(
            RAW_RECORDS,
            query_text="获取说明书总览信息",
            settings=SETTINGS,
            limit=5,
        )

        self.assertTrue(result.matched)
        self.assertEqual("overview", result.query_type)
        self.assertEqual(2, result.overview["total_manuals"])
        self.assertEqual({"美加规": 1, "欧英规": 1}, result.overview["by_region"])
        self.assertEqual([], result.rows)


class TestExtractFilters(unittest.TestCase):
    def test_two_letter_alias_does_not_match_inside_a_word(self) -> None:
        # "us" in "backup plus", "ph" in "alpha", "en" in "energy" must NOT
        # trigger region/source-language filters.
        filters = _extract_filters("backup plus alpha energy 说明书")
        self.assertEqual((), filters.regions)
        self.assertEqual((), filters.source_langs)

    def test_standalone_region_alias_still_matches(self) -> None:
        self.assertEqual(("美加规",), _extract_filters("查 US 说明书").regions)
        self.assertEqual(("欧规",), _extract_filters("eu manual link").regions)

    def test_cjk_region_alias_still_matches(self) -> None:
        self.assertEqual(("美加规",), _extract_filters("美加规说明书链接").regions)

    def test_language_alias_boundary(self) -> None:
        self.assertEqual(("EN",), _extract_filters("查 en 说明书").source_langs)
        self.assertEqual((), _extract_filters("energy 说明书").source_langs)


if __name__ == "__main__":
    unittest.main()
