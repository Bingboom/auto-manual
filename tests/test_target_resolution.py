from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools import build_docs
from tools import gen_index_bundle


class TestTargetResolution(unittest.TestCase):
    def _tokenized_cfg(self) -> dict:
        return {
            "build": {},
            "pages": [
                {
                    "type": "csv_page",
                    "page": "safety",
                    "include_dir": "generated/{model}/{region}",
                }
            ],
        }

    def test_build_docs_should_prefer_explicit_model_and_region(self) -> None:
        cfg = {"build": {"default_model": "M-OLD", "default_region": "EU"}}
        self.assertEqual("M-NEW", build_docs.resolve_build_model(cfg, "M-NEW"))
        self.assertEqual("US", build_docs.resolve_build_region(cfg, "US"))

    def test_build_docs_should_fallback_to_default_model_and_region(self) -> None:
        cfg = {"build": {"default_model": "JHP-2000A", "default_region": "US"}}
        self.assertEqual("JHP-2000A", build_docs.resolve_build_model(cfg, None))
        self.assertEqual("US", build_docs.resolve_build_region(cfg, None))

    def test_gen_index_should_render_model_region_tokens(self) -> None:
        cfg = self._tokenized_cfg()
        text = gen_index_bundle.build_index_from_pages(
            cfg,
            model="JHP-2000A",
            region="US",
        )
        self.assertIn("generated/JHP-2000A/US/safety_en.rst", text)

    def test_gen_index_should_reject_unsupported_sku_token(self) -> None:
        cfg = self._tokenized_cfg()
        cfg["pages"][0]["include_dir"] = "generated/{sku}"
        with self.assertRaises(RuntimeError):
            gen_index_bundle.build_index_from_pages(
                cfg,
                model="JHP-2000A",
                region="US",
            )

    def test_with_product_name_epilog_should_inject_plain_and_bold_variables(self) -> None:
        cmd = ["sphinx-build", "-b", "latex", ".", "_build/latex"]
        out = build_docs._with_product_name_epilog(cmd, "Demo Product")
        self.assertEqual("-D", out[-2])
        self.assertIn(".. |PRODUCT_NAME| replace:: Demo Product", out[-1])
        self.assertIn(".. |PRODUCT_NAME_BOLD| replace:: **Demo Product**", out[-1])

    def test_with_product_name_epilog_should_keep_cmd_when_name_is_empty(self) -> None:
        cmd = ["sphinx-build", "-b", "latex", ".", "_build/latex"]
        self.assertEqual(cmd, build_docs._with_product_name_epilog(cmd, ""))

    def test_resolve_product_name_for_build_should_read_from_spec_master(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            spec_master_csv = Path(td) / "Spec_Master.csv"
            spec_master_csv.write_text(
                "Section,Row_key,Line_order,Page,Model,Region,Is_Latest,enabled,Value_en,Value_ja\n"
                "GENERAL INFO,product_name,1,spec,JHP-2000A,US,1,1,Jackery HomePower 2000 Plus v2,\n"
                "GENERAL INFO,product_name,1,spec,JE-2000F,Japan,1,1,,Jackery ポータブル電源 2000 New\n",
                encoding="utf-8",
            )
            cfg = {"paths": {"spec_master_csv": str(spec_master_csv)}}

            en_name = build_docs.resolve_product_name_for_build(
                cfg,
                model="JHP-2000A",
                region="US",
                lang="en",
            )
            ja_name = build_docs.resolve_product_name_for_build(
                cfg,
                model="JE-2000F",
                region="Japan",
                lang="ja",
            )

            self.assertEqual("Jackery HomePower 2000 Plus v2", en_name)
            self.assertEqual("Jackery ポータブル電源 2000 New", ja_name)

    def test_resolve_product_name_for_build_should_return_none_without_model(self) -> None:
        cfg = {"paths": {"spec_master_csv": "data/phase1/Spec_Master.csv"}}
        self.assertIsNone(build_docs.resolve_product_name_for_build(cfg, model=None, region="US", lang="en"))

    def test_resolve_rst_substitutions_for_build_should_include_custom_template_vars(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            spec_master_csv = Path(td) / "Spec_Master.csv"
            spec_master_csv.write_text(
                "Section,Row_key,Line_order,Page,Model,Region,Is_Latest,enabled,Value_en\n"
                "GENERAL INFO,product_name,1,specifications,JHP-2000A,US,1,1,Jackery HomePower 2000 Plus v2\n"
                "GENERAL INFO,model_no,1,specifications,JHP-2000A,US,1,1,JHP-2000A\n"
                "TEMPLATE VARS,tpl_main_power_button_label,1,specifications,JHP-2000A,US,1,1,Main POWER Button\n",
                encoding="utf-8",
            )
            cfg = {"paths": {"spec_master_csv": str(spec_master_csv)}}

            substitutions = build_docs.resolve_rst_substitutions_for_build(
                cfg,
                model="JHP-2000A",
                region="US",
                lang="en",
            )

            self.assertEqual("Jackery HomePower 2000 Plus v2", substitutions["PRODUCT_NAME"])
            self.assertEqual("HomePower 2000 Plus v2", substitutions["PRODUCT_SHORT_NAME"])
            self.assertEqual("JHP-2000A", substitutions["MODEL_NO"])
            self.assertEqual("Main POWER Button", substitutions["MAIN_POWER_BUTTON_LABEL"])
            self.assertEqual("main POWER button", substitutions["MAIN_POWER_BUTTON_LABEL_LOWER"])


if __name__ == "__main__":
    unittest.main()
