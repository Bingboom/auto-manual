"""Reviewed JP App labels enter the common component without losing nearby copy."""
from pathlib import Path
import unittest

from bs4 import BeautifulSoup

from tools.component_specs.app_html import parse_app_add_device_html
from tools.web.app_component import render_app_component
from tools.web.presentation import load_web_manual_contract


class JapaneseAppSourceTests(unittest.TestCase):
    def setUp(self):
        self.config = load_web_manual_contract(model="JE-1000F", region="JP")["reference_figures"]["figures"][0]
        self.labels = ["主電源ボタン", "AC出力ボタン", "DC/USB出力ボタン"]
        self.markup = ('<img src="app/add_device.png"/><img src="overview/front_controls.png"/>'
                       + ''.join(f'<p>{label}</p>' for label in self.labels)
                       + '<p>2.3 接続手順はここに残す</p>')

    def parse(self, markup, config=None):
        soup = BeautifulSoup(markup, "html.parser")
        parsed = parse_app_add_device_html(soup, source_path=Path("12_app_setup_placeholder.rst"),
                                          config=config or self.config, language="ja")
        return soup, parsed

    def test_two_images_and_three_paragraphs_replay_with_correct_button_roles(self):
        soup, (spec, owned, _tags, _paths) = self.parse(self.markup)
        self.assertEqual([label["role"] for label in spec.slot("labels").content],
                         ["main-power", "ac-power", "dc-usb"])
        self.assertEqual(3, len(owned))
        rendered = BeautifulSoup(render_app_component(spec, ''.join(str(n) for n in owned)), "html.parser")
        self.assertCountEqual([n.get_text(strip=True) for n in rendered.select('.hb-app-add-device-live-label')], self.labels)
        self.assertIn("2.3 接続手順はここに残す", soup.get_text())
        self.assertNotIn("2.3 接続手順はここに残す", rendered.get_text())

    def test_unapproved_or_incomplete_shape_still_fails(self):
        for change in (self.markup.replace("front_controls", "unrelated"),
                       self.markup.replace("<p>DC/USB出力ボタン</p>", "")):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.parse(change)
        config = dict(self.config)
        del config["control_image_key"]
        with self.assertRaisesRegex(ValueError, "live labels"):
            self.parse(self.markup, config)
