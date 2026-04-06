from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.config_loader import load_config_mapping


class TestConfigLoader(unittest.TestCase):
    def test_load_config_mapping_should_merge_extended_configs(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            base_path = root / "base.yaml"
            child_path = root / "child.yaml"

            base_path.write_text(
                "\n".join(
                    [
                        "doc_type: manual_bundle",
                        "build:",
                        "  family_id: base-family",
                        "  languages: [en, fr]",
                        "  targets:",
                        "    - model: BASE-1",
                        "      region: US",
                        "paths:",
                        "  docs_dir: docs",
                        "  nested:",
                        "    parent: yes",
                        "pages:",
                        "  - type: rst_include",
                        "    lang: en",
                        "    file: templates/base.rst",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            child_path.write_text(
                "\n".join(
                    [
                        "extends: base.yaml",
                        "build:",
                        "  family_id: child-family",
                        "  languages: [es]",
                        "  include_lang_in_output_path: true",
                        "paths:",
                        "  nested:",
                        "    child: yes",
                        "pages:",
                        "  - type: rst_include",
                        "    lang: es",
                        "    file: templates/child.rst",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            cfg = load_config_mapping(child_path)

            self.assertEqual("manual_bundle", cfg["doc_type"])
            self.assertEqual("child-family", cfg["build"]["family_id"])
            self.assertEqual(["es"], cfg["build"]["languages"])
            self.assertTrue(cfg["build"]["include_lang_in_output_path"])
            self.assertEqual([{"model": "BASE-1", "region": "US"}], cfg["build"]["targets"])
            self.assertEqual({"parent": True, "child": True}, cfg["paths"]["nested"])
            self.assertEqual(
                [{"type": "rst_include", "lang": "es", "file": "templates/child.rst"}],
                cfg["pages"],
            )
            self.assertNotIn("extends", cfg)

    def test_load_config_mapping_should_detect_extends_cycles(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            a_path = root / "a.yaml"
            b_path = root / "b.yaml"

            a_path.write_text("extends: b.yaml\nbuild: {}\n", encoding="utf-8")
            b_path.write_text("extends: a.yaml\nbuild: {}\n", encoding="utf-8")

            with self.assertRaisesRegex(RuntimeError, "Config extends cycle detected"):
                load_config_mapping(a_path)


if __name__ == "__main__":
    unittest.main()
