"""Regressions from the JP native screenshot review."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from xml.etree import ElementTree as ET

from tools.idml_rst_extract import _parse_text
from tools.idml.components.base import RenderContext
from tools.idml.components.prose_table import render_table_block
from tools.manual_ir.builder import _asset_refs
from tools.idml.inline_images import prepare_inline_images
from tools.idml.primitives import psr


SOURCE = '.. |energy_saving_12h_title| image:: _assets/templates/word_template/common_assets/operation/energy_saving_12h.png\n   :alt: 12H省エネアイコン\n   :width: 28px\n\n.. |energy_saving_12h_icon| image:: _assets/templates/word_template/common_assets/operation/energy_saving_12h.png\n   :alt: 12H省エネアイコン\n   :width: 16px\n\n省エネモード |energy_saving_12h_title|\n--------------------------------------\n\n省エネモードは、出力ボタンの消し忘れによる無駄なバッテリー消耗を防ぐための機能で、初期設定ではオンになっています。AC出力が25W以下、またはDC/USB出力が2W以下の状態が12時間続くと、自動的に出力がオフになります。ACまたはDC/USB出力がオンの状態では、画面に省エネアイコン |energy_saving_12h_icon| が表示されます。アイコンの表示時間は、設定された省エネ時間に応じて変わります。省エネ時間は、Jackeryアプリで1H、2H、8H、12H、24Hに設定できます。「オフにしない」に設定すると、省エネモードは無効になります。\n\n.. |es_ac| replace:: ≤25W\n.. |es_dc| replace:: ≤2W\n.. |es_auto| replace:: 12時間経つとすべての出力は自動的にオフになります。\n\n+----------------------+--------------+--------------------------------------------+\n| 出力ポートタイプ     | 電力設定値   | デフォルト設定                             |\n+======================+==============+============================================+\n| AC出力ポート         | |es_ac|      | |es_auto|                                  |\n+----------------------+--------------+                                            |\n| DC/USB出力ポート     | |es_dc|      |                                            |\n+----------------------+--------------+--------------------------------------------+\n\n| ※ 交流25Wおよび直流2W以下の低消費電力機器をご使用の場合、出力が途中で自動的にオフにならないように、省エネモードをオフにしてください。省エネモードをオフにすると、画面上の |energy_saving_12h_icon| アイコンは表示されなくなります。\n\n| AC出力ボタンがオンの状態で、AC出力ボタンと主電源ボタンを同時に長押しし、省エネアイコンの表示（オン）／非表示（オフ）が切り替わるまで押し続けてください。\n\n.. image:: _assets/templates/word_template/common_assets/operation/energy_saving.png\n   :alt: Energy saving mode diagram.\n   :width: 320px\n\nオン/オフ\n\n両方を3秒間長押し\n\n.. list-table::\n   :header-rows: 0\n   :widths: 10 90\n\n   * - 説明\n     - 省エネモードは電源投入後に前回の状態を維持します。モード変更には手動での切り替えが必要です。\n\nACおよびDC出力の復帰機能\n------------------------\n\n本機能は出力状態を記憶し、所定の条件下でACおよびDC出力を自動的に再開します。\n\n+------------------------------------------------------+----------------------------------------------+\n| 自動復帰する条件                                     | 自動復帰しない条件                           |\n+======================================================+==============================================+\n| シャットダウンまたは再起動後の電源オン／再起動       | 手動で出力をオフにした場合（ボタン／アプリ） |\n+------------------------------------------------------+----------------------------------------------+\n| バッテリーSOCが放電制限に達した後、制限値＋10％以上  | 省エネモードによる出力オフ                   |\n| に回復した場合                                       +----------------------------------------------+\n|                                                      | 保護動作による出力オフ                       |\n+------------------------------------------------------+----------------------------------------------+\n| OTAアップグレード完了後                              | 放電タイマーによる出力オフ                   |\n+------------------------------------------------------+----------------------------------------------+\n'


class JpPreparedContentTests(unittest.TestCase):
    def test_substitutions_and_display_width_columns_preserve_values(self):
        result = _parse_text(SOURCE)
        tables = [json.loads(t) for k, t in result.blocks if k == "table"]
        self.assertEqual(tables[0][0], ["出力ポートタイプ", "電力設定値", "デフォルト設定"])
        self.assertEqual(tables[0][1], ["AC出力ポート", "≤25W", "12時間経つとすべての出力は自動的にオフになります。"])
        self.assertEqual(tables[0][2], ["DC/USB出力ポート", "≤2W", ""])
        self.assertEqual(tables[1][0], ["自動復帰する条件", "自動復帰しない条件"])
        self.assertEqual(tables[1][1][1], "手動で出力をオフにした場合（ボタン／アプリ）")
        self.assertIn("に回復した場合", tables[1][2][0])
        self.assertEqual(tables[1][3], ["", "保護動作による出力オフ"])
        self.assertEqual(tables[1][-1], ["OTAアップグレード完了後", "放電タイマーによる出力オフ"])
        text = "\n".join(t for _, t in result.blocks)
        for residual in ("|energy_", "|es_", ":alt:", ":width:", "+---"):
            self.assertNotIn(residual, text)
        self.assertIn("![12H省エネアイコン]", text)

    def test_table_image_has_asset_provenance_and_a_native_link(self):
        rst = ".. list-table::\n\n   * - .. image:: icon.png\n     - 警告の説明\n"
        rows = json.loads(_parse_text(rst).blocks[0][1])
        self.assertEqual(_asset_refs(rows), ("icon.png",))
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            # An existing real image exercises the same asset resolver as export.
            import shutil
            asset = Path(__file__).resolve().parents[1] / "docs/templates/word_template/common_assets/symbols/warning_triangle.png"
            shutil.copy2(asset, root / "icon.png")
            ctx = RenderContext({}, 300, 20, 20, root, root, language="ja")
            xml, height = render_table_block(rows, ctx, tid="test", terminal=True)
            doc = ET.fromstring(xml)
            self.assertTrue(doc.findall(".//Link"))
            self.assertIn("警告の説明", "".join(doc.itertext()))
            self.assertNotIn("image::", xml)
            self.assertNotIn("![]", xml)
            self.assertGreater(height, 0)
            text, replacements = prepare_inline_images(
                "省エネ ![12H省エネアイコン](icon.png) 表示", ctx, tid="mixed",
            )
            xml = psr("HB Body", text, terminal=True, inline_replacements=replacements)
            self.assertTrue(ET.fromstring(xml).findall(".//Link"))
            self.assertNotIn("HBINLINEIMAGE", xml)
            self.assertNotIn("![", xml)


    def test_unresolved_names_are_not_silently_deleted_and_cycles_fail(self):
        result = _parse_text("Known |missing| value\n")
        self.assertEqual(result.blocks, [("body", "Known |missing| value")])
        with self.assertRaisesRegex(ValueError, "cyclic"):
            _parse_text(".. |a| replace:: |b|\n.. |b| replace:: |a|\n\nValue |a|\n")


class TargetTocTests(unittest.TestCase):
    def test_auto_toc_uses_collected_target_headings(self):
        from tools.idml.page_toc import TocCollector, _display_segments
        collector = TocCollector()
        collector.note("安全上のご注意", 2, "ja")
        collector.note("主な仕様", 22, "ja")
        title, segments = _display_segments(collector, {
            "title": "目次", "auto_entries": True,
            "languages": [{"code": "JP", "label": "日本語"}],
        })
        self.assertEqual(title, "目次")
        self.assertEqual(len(segments), 1)
        self.assertTrue(segments[0][0].startswith("JP"))
        self.assertEqual(segments[0][2], [("安全上のご注意", 1), ("主な仕様", 21)])


class JpFolioContractTests(unittest.TestCase):
    def test_front_matter_metadata_does_not_emit_a_reference_layout_plan(self):
        from tools.idml.ir_projection import emit_reference_page_plan

        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)
            self.assertIsNone(emit_reference_page_plan(
                {"front_matter_roles": ["cover", "toc"]}, out_dir=output))
            self.assertEqual([], list(output.iterdir()))

    def test_japanese_contents_and_footer_share_two_front_pages(self):
        from tools.idml.page_toc import TocCollector, _display_segments, _toc_slot
        from tools.idml.page_folio import _resolve_page_plan

        root = Path(__file__).resolve().parents[1]
        blocks = _parse_text((root / "docs/templates/page_jp/toc.rst").read_text(), tags={"idml"}).blocks
        source = next(json.loads(text) for kind, text in blocks if kind == "data")
        raw = {"front_matter_roles": source["front_matter_roles"]}
        plan = _resolve_page_plan(raw, physical_page_count=8, has_back_cover=True)
        self.assertIsNone(plan.physical_page(2).folio_number)
        self.assertEqual(1, plan.physical_page(3).folio_number)
        self.assertEqual(5, plan.physical_page(7).folio_number)
        self.assertIsNone(plan.physical_page(8).folio_number)
        collector = TocCollector(entries=[("ja", "安全上のご注意", 1), ("ja", "保証について", 4)])
        title, segments = _display_segments(collector, source, folio_plan=plan, toc_slot=_toc_slot(raw))
        self.assertEqual("目次", title)
        self.assertEqual("01-05", segments[0][1])
        self.assertEqual([("安全上のご注意", 1), ("保証について", 4)], segments[0][2])

    def test_assets_override_only_the_approved_product_and_region(self):
        from tools.asset_registry import load_registry, resolve_asset

        root = Path(__file__).resolve().parents[1]
        records = load_registry(root / "data/asset_registry.csv")
        for key in ("overview/front_product", "operation/ups_mode", "charging/ac_wall",
                    "charging/solar_direct", "charging/solar_adapter", "charging/car_charge"):
            jp = resolve_asset(records, repo_root=root, asset_key=key, model="JE-1000F", region="JP")
            us = resolve_asset(records, repo_root=root, asset_key=key, model="JE-1000F", region="US")
            self.assertIn("je1000f_jp_", Path(jp.path).name)
            self.assertNotIn("je1000f_jp_", Path(us.path).name)
