from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from tools import content_assembly


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "content_assembly"
CONTRACT_PATH = REPO_ROOT / "docs" / "templates" / "assembly_contracts" / "03_product_overview.yaml"


class ContentAssemblyTests(unittest.TestCase):
    def _substitutions(self) -> dict[str, str]:
        return {
            "PRODUCT_NAME": "Jackery Explorer 1000 Plus",
            "MODEL_NO": "JE-1000F",
            "MAIN_POWER_BUTTON_LABEL": "Main Power Button",
            "FRONT_DC12_PORT_LABEL": "DC 12V Port",
            "FRONT_DC12_PORT_SPEC": "12V/10A Max",
            "DC_USB_POWER_BUTTON_LABEL": "DC/USB Power Button",
            "FRONT_USB_C_LOW_LABEL": "USB-C 30W Output",
            "FRONT_USB_C_LOW_SPEC": "30W Max",
            "FRONT_USB_C_HIGH_LABEL": "USB-C 100W Output",
            "FRONT_USB_C_HIGH_SPEC": "100W Max",
            "AC_POWER_BUTTON_LABEL": "AC Power Button",
            "FRONT_USB_A_LABEL": "USB-A 18W Output",
            "FRONT_USB_A_SPEC": "18W Max",
            "FRONT_AC_OUTPUT_LABEL": "AC Output",
            "FRONT_AC_OUTPUT_SPEC": "120V~60Hz",
            "FRONT_TOTAL_OUTPUT_LABEL": "Total Output",
            "FRONT_TOTAL_OUTPUT_SPEC": "1500W Rated",
            "SIDE_AC_INPUT_LABEL": "AC Input",
            "SIDE_AC_INPUT_SPEC": "100V-120V~60Hz",
            "SIDE_DC_INPUT_LABEL": "DC Input",
            "SIDE_DC_INPUT_PV_SPEC": "PV Input",
            "SIDE_DC_INPUT_CAR_SPEC": "Car Input",
        }

    def _copy_fixtures(self, root: Path) -> Path:
        fixtures_dir = root / "content_assembly"
        shutil.copytree(FIXTURE_DIR, fixtures_dir)
        return fixtures_dir

    def _bad_contract(self, root: Path) -> Path:
        path = root / "bad_contract.yaml"
        path.write_text(
            "\n".join(
                [
                    "page_id: 03_product_overview",
                    "product_family: JE-1000F",
                    "regions: [US, JP]",
                    "langs: [en, ja]",
                    "fallback:",
                    "  lang: en",
                    "blocks:",
                    "  - product_identity",
                    "required_fields:",
                    "  - product_name",
                    "  - serial_number",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        return path

    def test_render_us_en_should_generate_stable_noop_rst(self) -> None:
        rendered = content_assembly.render_content_assembly(
            contract_path=CONTRACT_PATH,
            fixtures_dir=FIXTURE_DIR,
            region="US",
            lang="en",
            repo_root=REPO_ROOT,
        )

        self.assertIn(".. content-assembly:: 03_product_overview", rendered)
        self.assertIn(":region: US", rendered)
        self.assertIn(":lang: en", rendered)
        self.assertIn(".. content-block:: feature_front", rendered)
        self.assertIn(":title-key: FRONT_VIEW", rendered)
        self.assertIn(".. content-block:: asset_front", rendered)
        self.assertIn("docs/templates/word_template/common_assets/overview/front_product.jpg", rendered)
        self.assertIn(".. content-block:: spec_front_total", rendered)
        self.assertIn("FRONT_TOTAL_OUTPUT_LABEL", rendered)

    def test_render_jp_ja_should_use_language_row_and_fallback_block(self) -> None:
        rendered = content_assembly.render_content_assembly(
            contract_path=CONTRACT_PATH,
            fixtures_dir=FIXTURE_DIR,
            region="JP",
            lang="ja",
            repo_root=REPO_ROOT,
        )

        self.assertIn(":lang: ja", rendered)
        self.assertIn(":fallback-lang: en", rendered)
        self.assertIn(":title-key: FRONT_VIEW_JA", rendered)
        self.assertIn(":title-key: RIGHT_SIDE_VIEW", rendered)
        self.assertIn(".. content-block:: asset_front", rendered)
        self.assertNotIn(".. content-block:: spec_front_total", rendered)

    def test_render_page_should_expand_block_templates_into_product_overview(self) -> None:
        rendered = content_assembly.render_content_assembly_page(
            contract_path=CONTRACT_PATH,
            fixtures_dir=FIXTURE_DIR,
            block_template_dir=REPO_ROOT / "docs" / "templates" / "assembly_blocks" / "03_product_overview",
            region="US",
            lang="en",
            substitutions=self._substitutions(),
            repo_root=REPO_ROOT,
        )

        self.assertNotIn("{{ product_overview }}", rendered)
        self.assertNotIn("product-overview-fields", rendered)
        self.assertIn(r"\HBOverviewPanel{FRONT VIEW}{front_product.jpg}{%", rendered)
        self.assertIn("PRODUCT OVERVIEW", rendered)
        self.assertIn("USB-A 18W Output", rendered)

    def test_render_page_should_fail_when_required_substitution_is_missing(self) -> None:
        substitutions = self._substitutions()
        substitutions.pop("FRONT_DC12_PORT_LABEL")

        with self.assertRaisesRegex(RuntimeError, "FRONT_DC12_PORT_LABEL"):
            content_assembly.render_content_assembly_page(
                contract_path=CONTRACT_PATH,
                fixtures_dir=FIXTURE_DIR,
                block_template_dir=REPO_ROOT / "docs" / "templates" / "assembly_blocks" / "03_product_overview",
                region="US",
                lang="en",
                substitutions=substitutions,
                repo_root=REPO_ROOT,
            )

    def test_render_page_should_use_ja_layout_for_jp(self) -> None:
        rendered = content_assembly.render_content_assembly_page(
            contract_path=CONTRACT_PATH,
            fixtures_dir=FIXTURE_DIR,
            block_template_dir=REPO_ROOT / "docs" / "templates" / "assembly_blocks" / "03_product_overview",
            region="JP",
            lang="ja",
            substitutions=self._substitutions(),
            repo_root=REPO_ROOT,
        )

        self.assertIn("各部の名称", rendered)
        self.assertIn("正面", rendered)
        self.assertIn("右側面", rendered)
        self.assertNotIn("FRONT_TOTAL_OUTPUT_LABEL", rendered)

    def test_missing_field_should_fail_before_rendering(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            contract_path = self._bad_contract(root)

            with self.assertRaisesRegex(RuntimeError, "serial_number"):
                content_assembly.render_content_assembly(
                    contract_path=contract_path,
                    fixtures_dir=FIXTURE_DIR,
                    region="US",
                    lang="en",
                    repo_root=REPO_ROOT,
                )

    def test_cli_render_should_write_only_requested_temp_output(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            output_path = Path(td) / "03_product_overview.us-en.rst"
            rc = content_assembly.run(
                [
                    "render",
                    "--contract",
                    str(CONTRACT_PATH),
                    "--fixtures",
                    str(FIXTURE_DIR),
                    "--region",
                    "US",
                    "--lang",
                    "en",
                    "--output",
                    str(output_path),
                ]
            )

            self.assertEqual(0, rc)
            rendered = output_path.read_text(encoding="utf-8")
            self.assertIn(".. content-assembly:: 03_product_overview", rendered)

    def test_cli_render_should_reject_managed_build_outputs(self) -> None:
        output_path = REPO_ROOT / "docs" / "_build" / "content_assembly_should_not_write.rst"
        self.assertFalse(output_path.exists())

        rc = content_assembly.run(
            [
                "render",
                "--contract",
                str(CONTRACT_PATH),
                "--fixtures",
                str(FIXTURE_DIR),
                "--region",
                "US",
                "--lang",
                "en",
                "--output",
                str(output_path),
            ]
        )

        self.assertEqual(1, rc)
        self.assertFalse(output_path.exists())


if __name__ == "__main__":
    unittest.main()
