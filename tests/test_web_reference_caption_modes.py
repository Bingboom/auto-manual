from __future__ import annotations

from pathlib import Path
import unittest

from bs4 import BeautifulSoup

from tools.frozen_pdf_app import artwork_node
from tools.web_embedded_components import render_embedded_web_component
from tools.web_reference_components import prepare_reference_caption_data


class WebReferenceCaptionModesTests(unittest.TestCase):
    def _prepare(self, config, markup='<img src="asset.png"/>'):
        soup = BeautifulSoup(markup, "html.parser")
        return prepare_reference_caption_data(image=soup.img, spec={"id": "example", **config},
                                               source_path=Path("example.rst"), error_type=ValueError)

    def test_none_is_an_explicit_captionless_mode(self):
        self.assertEqual((None, []), self._prepare({"caption_mode": "none"}))

    def test_legacy_and_live_still_require_labels(self):
        for config in ({}, {"caption_mode": "live"}, {"caption_mode": "invalid"}):
            with self.subTest(config=config), self.assertRaisesRegex(ValueError, "requires labels"):
                self._prepare(config)
        with self.assertRaisesRegex(ValueError, "must be followed by a line-block"):
            self._prepare({"caption_mode": "live", "capture_following_lines": 1})

    def test_existing_embedded_and_live_caption_paths_remain_supported(self):
        self.assertEqual((None, []), self._prepare({"captions_embedded": True}))
        self.assertEqual((None, ["Caption"]), self._prepare({"caption_labels": ["Caption"]}))
        block, labels = self._prepare({"capture_following_lines": 1},
                                     '<img src="asset.png"/><div class="line-block"><div class="line">Caption</div></div>')
        self.assertEqual("Caption", block.get_text())
        self.assertEqual([], labels)

    def test_registered_captionless_artwork_replays_with_verified_semantic_hash(self):
        node = artwork_node("assets/qr.png", "download-qr", "pl", "source.pdf#qr",
                            accessibility_label="Kod QR")
        spec = node["component_spec"]
        self.assertEqual("semantic-fallback", spec["variant"])
        self.assertEqual(1, len(spec["assets"]))
        self.assertNotIn("approved_composite", spec["metadata"])
        html = render_embedded_web_component(
            node, source_path=Path("source.rst"), model="Example", region="EU", language="pl",
            composite_manifest=None, contract={},
        )
        soup = BeautifulSoup(html, "html.parser")
        figure = soup.select_one(".hb-reference-figure")
        self.assertEqual(spec["metadata"]["source_fragment_sha256"], figure["data-source-fragment-sha256"])
        self.assertEqual("assets/qr.png", figure.img["src"])
        self.assertFalse(figure.find("figcaption"))
        self.assertNotIn("data-step-captions", figure.attrs)
        rebased = artwork_node("file:///new/package/qr.png", "download-qr", "pl", "source.pdf#qr",
                               accessibility_label="Kod QR")
        self.assertEqual(spec["metadata"]["source_fragment_sha256"],
                         rebased["component_spec"]["metadata"]["source_fragment_sha256"])


if __name__ == "__main__":
    unittest.main()
