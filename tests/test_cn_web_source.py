"""Reviewed CN source shapes preserve copy through shared components."""
from pathlib import Path
import unittest

from bs4 import BeautifulSoup

from tools.component_specs.app_html import parse_app_add_device_html, parse_app_download_html
from tools.component_specs.app_adapters import latex_app_projection
from tools.component_specs.lcd_mode_html import parse_lcd_mode_html
from tools.component_specs.plain_inventory import is_plain_inventory, plain_inventory_spec
from tools.manual_ir.whole_document_components import discover_registered_components
from tools.web.app_component import render_app_component
from tools.web.figure_captions import align_caption_centers
from tools.web.presentation import load_web_manual_contract
from tools.word.inbox_component import transform_word_inbox_html


class ChineseWebSourceTests(unittest.TestCase):
    def test_native_caption_centers_reject_incomplete_reversed_or_invalid_positions(self):
        markup = '<figure><figcaption class="hb-reference-caption-grid"><span class="hb-reference-caption">2.1</span><span class="hb-reference-caption">2.2</span></figcaption></figure>'
        for centers in ([20], [80, 20], [20, 100], [True, 80], [20, float('nan')]):
            with self.subTest(centers=centers), self.assertRaisesRegex(ValueError, 'caption centers'):
                align_caption_centers(BeautifulSoup(markup, 'html.parser').figure, centers)

    def test_list_inventory_keeps_items_emphasis_and_external_note(self):
        fragment = '<h1>包装清单</h1><ul><li>主机</li><li><strong>AC</strong>线</li><li>用户指南</li></ul><p>车充线另购。</p>'
        soup = BeautifulSoup(fragment, 'html.parser')
        spec = plain_inventory_spec(soup, source_path=Path('02_whats_in_the_box.rst'), language='zh')
        self.assertEqual(spec.variant, 'plain-inventory')
        self.assertEqual([c['text'] for c in spec.slot('rows').content[0]], ['主机', 'AC\n线', '用户指南'])
        self.assertIn('<strong>AC</strong>', spec.slot('rows').content[0][1]['html'])
        self.assertEqual(transform_word_inbox_html(fragment, source_path=Path('02_whats_in_the_box.rst'),
                         config=load_web_manual_contract()['in_the_box'], language='zh'), fragment)

    def test_incomplete_illustrated_nested_and_tip_lists_fail_closed(self):
        for body in ('<li>主机</li><li>线</li>', '<li>主机</li><li>线</li><li></li>',
                     '<li><img src="x.png">主机</li><li>线</li><li>书</li>',
                     '<li>主机<ul><li>附属品</li></ul></li><li>线</li><li>书</li>'):
            with self.subTest(body=body):
                self.assertFalse(is_plain_inventory(BeautifulSoup('<h1>清单</h1><ul>'+body+'</ul>', 'html.parser')))

    def matrix(self):
        rows = '<tr><th></th><th>分类</th><th>操作</th><th>说明</th></tr>'
        for i in range(6):
            state = '短亮' if i == 0 else '常亮' if i == 3 else ''
            rows += f'<tr><td></td><td>{state}</td><td>动作{i}</td><td><strong>说明{i}</strong></td></tr>'
        return '<img src="operation/lcd_mode.png" alt="屏幕显示"><table>'+rows+'</table><p>后文</p>'

    def test_external_lcd_keeps_headers_actions_and_single_source_image(self):
        soup = BeautifulSoup(self.matrix(), 'html.parser')
        spec, table, image = parse_lcd_mode_html(soup, source_path=Path('operation.rst'),
                           image_key='operation/lcd_mode', expected_body_rows=6, language='zh')
        self.assertEqual(spec.component_id, 'HB-TABLE-REFERENCE')
        self.assertEqual(spec.variant, 'lcd-actions')
        self.assertEqual([x['text'] for x in spec.slot('headers').content], ['分类', '操作', '说明'])
        self.assertEqual(len(spec.slot('rows').content), 6)
        self.assertEqual(spec.assets, ())
        self.assertIs(table.find_previous_sibling(), image)
        self.assertIn('<strong>说明5</strong>', spec.slot('rows').content[-1][-1]['html'])

    def test_external_lcd_cannot_drop_nonempty_art_column_or_bad_geometry(self):
        for markup in (self.matrix().replace('<td></td>', '<td>不可丢失</td>', 1),
                       self.matrix().replace('<td>动作5</td>', ''),
                       self.matrix().replace('<table>', '<p>间隔</p><table>')):
            with self.subTest(markup=markup), self.assertRaises(ValueError):
                parse_lcd_mode_html(BeautifulSoup(markup, 'html.parser'), source_path=Path('operation.rst'),
                                    image_key='operation/lcd_mode', expected_body_rows=6, language='zh')

    def test_app_note_survives_combined_panel_and_labels_keep_button_roles(self):
        labels = ['总电源开关键', 'AC 输出按键', 'DC/USB输出按键']
        markup = ('<h1>APP操作</h1><img src="app/add_device.png">'
                  '<table><tr><td>备注</td><td>两小时未连接会关闭无线。</td></tr></table>'
                  '<img src="overview/front_controls.png"><div class="line-block">'
                  + ''.join(f'<div class="line">{x}</div>' for x in labels)
                  + '</div><p>2.3 搜索设备</p>')
        contract = load_web_manual_contract(model='JE-2000F', region='CN')
        soup = BeautifulSoup(markup, 'html.parser')
        spec, owned, _, _ = parse_app_add_device_html(soup, source_path=Path('12_app_setup_placeholder.rst'),
                                                     config=contract['reference_figures']['figures'][0], language='zh')
        self.assertEqual([x['role'] for x in spec.slot('labels').content], ['main-power', 'ac-power', 'dc-usb'])
        rendered = BeautifulSoup(render_app_component(spec, ''.join(str(x) for x in owned)), 'html.parser')
        self.assertCountEqual([x.get_text(strip=True) for x in rendered.select('.hb-app-add-device-live-label')], labels)
        self.assertEqual(soup.get_text().count('两小时未连接会关闭无线。'), 1)
        note = rendered.select_one('.hb-app-add-device-note')
        self.assertEqual(rendered.get_text().count('两小时未连接会关闭无线。'), 1)
        self.assertIn('hb-reference-caption-grid', note.find_previous_sibling()['class'])
        self.assertIn('hb-app-add-device-control-panel', note.find_next_sibling()['class'])
        self.assertEqual([node.name for node in owned], ['img', 'table', 'img', 'div'])
        with self.assertRaisesRegex(ValueError, 'interstitial note disagrees'):
            render_app_component(spec, ''.join(str(x) for x in owned).replace('两小时', '三小时'))
        full_source = ('<img src="app/download.png" alt="下载二维码"><p>扫码下载。</p>'
                       '<p>2.1 在App内点击<strong>+</strong>添加设备。</p>' + markup
                       + '<img src="app/connect_result.png" alt="连接结果">')
        claims = discover_registered_components(BeautifulSoup(full_source, 'html.parser'),
                 source_path=Path('12_app_setup_placeholder.rst'), contract=contract,
                 model='JE-2000F', region='CN', language='zh')
        self.assertTrue(any(c.spec.component_id == 'HB-SPECIAL-APP' for c in claims))
        self.assertTrue(any(c.spec.variant == 'inline-control' for c in claims))
        result = next(c for c in claims if c.spec.component_id == 'HB-SPECIAL-REFERENCE-FIGURE')
        self.assertEqual([x['text'] for x in result.spec.slot('captions').content], ['2.3', '2.4', '2.5'])

    def test_qr_download_preserves_one_code_and_live_copy_in_shared_app_component(self):
        contract = load_web_manual_contract(model='JE-2000F', region='CN')
        markup = '<img src="app/download.png" alt="下载二维码" width="320"><p>在应用商店搜索<strong>电小二</strong>，或扫码下载。</p>'
        spec, owned, assets, paths = parse_app_download_html(
            BeautifulSoup(markup, 'html.parser'), source_path=Path('app.rst'),
            config=contract['app_download'], language='zh', model='JE-2000F', region='CN',
        )
        self.assertEqual(spec.variant, 'download-qr-only')
        self.assertEqual(len(assets), 1)
        self.assertEqual(paths, ())
        soup = BeautifulSoup(render_app_component(spec, ''.join(str(x) for x in owned)), 'html.parser')
        self.assertEqual(len(soup.find_all('img')), 1)
        self.assertEqual([x.name for x in soup.figure.children], ['p', 'img'])
        self.assertIsNotNone(soup.select_one('.hb-app-download-qr-only > .hb-app-download-art-qr'))
        self.assertEqual(soup.get_text().count('电小二'), 1)
        self.assertIsNotNone(soup.strong)
        self.assertNotIn('width', soup.img.attrs)
        with self.assertRaisesRegex(ValueError, 'not applicable'):
            latex_app_projection(spec)
        with self.assertRaisesRegex(ValueError, 'disagrees with source slots'):
            render_app_component(spec, markup.replace('或扫码下载', '另一段内容'))


if __name__ == '__main__':
    unittest.main()
