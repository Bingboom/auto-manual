from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.draft_engine import render_generated_page


class TestDraftEngine(unittest.TestCase):
    def _render_numbered_heading_fixture(self, *, recipe_extra_lines: list[str] | None = None) -> str:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            docs_dir = root / "docs"
            (docs_dir / "templates" / "recipes").mkdir(parents=True)
            (docs_dir / "templates" / "snippets").mkdir(parents=True)
            (docs_dir / "templates" / "page_shared" / "en").mkdir(parents=True)

            recipe_path = docs_dir / "templates" / "recipes" / "app_setup.yaml"
            recipe_lines = [
                "page_id: 12_app_setup",
                "template: templates/page_shared/en/12_app_setup_placeholder.rst",
                "field_map: {}",
                "required_row_keys: []",
                "snippet_slots: {}",
            ]
            recipe_lines.extend(recipe_extra_lines or [])
            recipe_lines.append("contracts: []")
            recipe_path.write_text("\n".join(recipe_lines) + "\n", encoding="utf-8")

            template_path = docs_dir / "templates" / "page_shared" / "en" / "12_app_setup_placeholder.rst"
            template_path.write_text(
                "\n".join(
                    [
                        "APP SETUP",
                        "=========",
                        "",
                        "**1. Download the App and log in**",
                        "",
                        "Body text.",
                        "",
                        "**4.1 To turn on Wi-Fi and Bluetooth**",
                        "",
                        "Nested body.",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            registry_path = docs_dir / "templates" / "snippets" / "registry.yaml"
            registry_path.write_text("snippets: []\n", encoding="utf-8")
            spec_master_csv = root / "Spec_Master.csv"
            spec_master_csv.write_text(
                "Model,Region,Is_Latest,Page,Row_key,Slot_key,Value_source\n",
                encoding="utf-8",
            )

            result = render_generated_page(
                docs_dir=docs_dir,
                recipe_path=recipe_path,
                template_path=template_path,
                spec_master_csv=spec_master_csv,
                registry_path=registry_path,
                vars_map={},
                base_substitutions={},
                model="JE-1000F",
                region="US",
                lang="en",
            )
            return result.text

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
                        "  MAIN_POWER_BUTTON_LABEL:",
                        "    row_key: main_power_button",
                        "    pages: [Product overview]",
                        "    usage_type: page_value",
                        "    value_role: label",
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
                        "Model,Region,Is_Latest,Page,Row_key,Slot_key,Value_source",
                        "JE-1000F,US,TRUE,specifications,product_name,,Jackery Explorer 1000 v2",
                        "JE-1000F,US,TRUE,specifications,model_no,,JE-1000F",
                        "JE-1000F,US,TRUE,Product overview,main_power_button,label,Main Power Button",
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
                        "    row_key: main_power_button",
                        "    pages: Product overview",
                        "    usage_type: page_value",
                        "    value_role: label",
                        "required_row_keys: []",
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
                        "Model,Region,Is_Latest,Page,Row_key,Slot_key,Value_source",
                        "JE-1000F,US,TRUE,Product overview,main_power_button,label,Main Power Button",
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

    def test_render_generated_page_should_resolve_field_map_page_copy_key(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            docs_dir = root / "docs"
            (docs_dir / "templates" / "recipes").mkdir(parents=True)
            (docs_dir / "templates" / "snippets").mkdir(parents=True)
            (docs_dir / "templates" / "page_shared" / "en").mkdir(parents=True)

            recipe_path = docs_dir / "templates" / "recipes" / "copy_demo.yaml"
            recipe_path.write_text(
                "\n".join(
                    [
                        "page_id: copy_demo",
                        "template: templates/page_shared/en/copy_demo.rst",
                        "field_map:",
                        "  INTRO_COPY:",
                        "    row_key: intro_copy",
                        "    page_copy_page_id: copy_demo",
                        "    page_copy_lang: en",
                        "    page_copy_key: intro",
                        "required_row_keys: []",
                        "snippet_slots: {}",
                        "contracts: []",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            template_path = docs_dir / "templates" / "page_shared" / "en" / "copy_demo.rst"
            template_path.write_text("COPY DEMO\n=========\n\n|INTRO_COPY|\n", encoding="utf-8")
            registry_path = docs_dir / "templates" / "snippets" / "registry.yaml"
            registry_path.write_text("snippets: []\n", encoding="utf-8")
            spec_master_csv = root / "Spec_Master.csv"
            spec_master_csv.write_text(
                "Model,Region,Is_Latest,Page,Row_key,Slot_key,Value_source\n",
                encoding="utf-8",
            )
            page_copy = root / "page_copy.csv"
            page_copy.write_text(
                "page_id,lang,copy_key,text,enabled,order\n"
                "copy_demo,en,intro,Intro from copy.,TRUE,1\n",
                encoding="utf-8",
            )

            result = render_generated_page(
                docs_dir=docs_dir,
                recipe_path=recipe_path,
                template_path=template_path,
                spec_master_csv=spec_master_csv,
                registry_path=registry_path,
                vars_map={},
                base_substitutions={},
                model="JE-1000F",
                region="US",
                lang="en",
                page_copy_csv=page_copy,
            )

            self.assertIn("Intro from copy.", result.text)

    def test_render_generated_page_should_promote_configured_numbered_steps_to_headings(self) -> None:
        text = self._render_numbered_heading_fixture(
            recipe_extra_lines=[
                "postprocess:",
                "  - promote_standalone_bold_numbered_headings",
            ]
        )

        self.assertIn("1. Download the App and log in\n------------------------------", text)
        self.assertIn("4.1 To turn on Wi-Fi and Bluetooth\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~", text)
        self.assertNotIn("**1. Download the App and log in**", text)

    def test_render_generated_page_should_not_promote_numbered_steps_by_default(self) -> None:
        text = self._render_numbered_heading_fixture()

        self.assertIn("**1. Download the App and log in**", text)
        self.assertIn("**4.1 To turn on Wi-Fi and Bluetooth**", text)
        self.assertNotIn("1. Download the App and log in\n------------------------------", text)


if __name__ == "__main__":
    unittest.main()
