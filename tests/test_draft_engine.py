from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.draft_engine import render_generated_page


class TestDraftEngine(unittest.TestCase):
    def test_render_generated_page_should_apply_field_map_and_snippets(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            docs_dir = root / "docs"
            (docs_dir / "templates" / "recipes").mkdir(parents=True)
            (docs_dir / "templates" / "snippets" / "en").mkdir(parents=True)
            (docs_dir / "templates" / "page_us-en").mkdir(parents=True)

            recipe_path = docs_dir / "templates" / "recipes" / "demo.yaml"
            recipe_path.write_text(
                "\n".join(
                    [
                        "page_id: demo_page",
                        "template: templates/page_us-en/demo.rst",
                        "field_map:",
                        "  PRODUCT_NAME: product_name",
                        "  MAIN_POWER_BUTTON_LABEL: tpl_main_power_button_label",
                        "required_row_keys:",
                        "  - product_name",
                        "snippet_slots:",
                        "  intro: intro_snippet",
                        "contracts: []",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            template_path = docs_dir / "templates" / "page_us-en" / "demo.rst"
            template_path.write_text(
                "\n".join(
                    [
                        "Demo",
                        "====",
                        "",
                        "{{snippet:intro}}",
                        "",
                        "|MAIN_POWER_BUTTON_LABEL|",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            registry_path = docs_dir / "templates" / "snippets" / "registry.yaml"
            registry_path.write_text(
                "\n".join(
                    [
                        "snippets:",
                        "  - snippet_id: intro_snippet",
                        "    file: templates/snippets/en/intro_snippet.rst",
                        "    lang: en",
                        "    required_placeholders:",
                        "      - PRODUCT_NAME",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            (docs_dir / "templates" / "snippets" / "en" / "intro_snippet.rst").write_text(
                "Welcome to |PRODUCT_NAME|.\n",
                encoding="utf-8",
            )

            spec_master_csv = root / "Spec_Master.csv"
            spec_master_csv.write_text(
                "\n".join(
                    [
                        "Model,Region,Is_Latest,Page,Row_key,Value_en",
                        "JE-1000F,US,TRUE,specifications,product_name,Jackery Explorer 1000 v2",
                        "JE-1000F,US,TRUE,specifications,model_no,JE-1000F",
                        "JE-1000F,US,TRUE,specifications,tpl_main_power_button_label,Main Power Button",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            rendered_source = root / "generated" / "demo_page_en.rst"
            result = render_generated_page(
                docs_dir=docs_dir,
                recipe_path=recipe_path,
                template_path=template_path,
                spec_master_csv=spec_master_csv,
                registry_path=registry_path,
                vars_map={"model": "JE-1000F", "region": "US"},
                base_substitutions={},
                model="JE-1000F",
                region="US",
                lang="en",
                rendered_source_path=rendered_source,
            )

            self.assertIn("Welcome to Jackery Explorer 1000 v2.", result.text)
            self.assertIn("Main Power Button", result.text)
            self.assertEqual(("intro_snippet",), result.used_snippet_ids)
            self.assertTrue(rendered_source.exists())

    def test_render_generated_page_should_support_field_map_pages(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            docs_dir = root / "docs"
            (docs_dir / "templates" / "recipes").mkdir(parents=True)
            (docs_dir / "templates" / "snippets").mkdir(parents=True)
            (docs_dir / "templates" / "page_us-en").mkdir(parents=True)

            recipe_path = docs_dir / "templates" / "recipes" / "demo.yaml"
            recipe_path.write_text(
                "\n".join(
                    [
                        "page_id: demo_page",
                        "template: templates/page_us-en/demo.rst",
                        "field_map:",
                        "  MAIN_POWER_BUTTON_LABEL:",
                        "    row_key: tpl_main_power_button_label",
                        "    pages: Product overview",
                        "required_row_keys:",
                        "  - tpl_main_power_button_label",
                        "snippet_slots: {}",
                        "contracts: []",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            template_path = docs_dir / "templates" / "page_us-en" / "demo.rst"
            template_path.write_text(
                "Demo\n====\n\n|MAIN_POWER_BUTTON_LABEL|\n",
                encoding="utf-8",
            )

            registry_path = docs_dir / "templates" / "snippets" / "registry.yaml"
            registry_path.write_text("snippets: []\n", encoding="utf-8")

            spec_master_csv = root / "Spec_Master.csv"
            spec_master_csv.write_text(
                "\n".join(
                    [
                        "Model,Region,Is_Latest,Page,Row_key,Value_en",
                        "JE-1000F,US,TRUE,Product overview,tpl_main_power_button_label,Main Power Button",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            rendered_source = root / "generated" / "demo_page_en.rst"
            result = render_generated_page(
                docs_dir=docs_dir,
                recipe_path=recipe_path,
                template_path=template_path,
                spec_master_csv=spec_master_csv,
                registry_path=registry_path,
                vars_map={"model": "JE-1000F", "region": "US"},
                base_substitutions={},
                model="JE-1000F",
                region="US",
                lang="en",
                rendered_source_path=rendered_source,
            )

            self.assertIn("Main Power Button", result.text)


if __name__ == "__main__":
    unittest.main()
