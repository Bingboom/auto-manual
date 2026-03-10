from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

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

    def test_resolve_build_targets_should_expand_configured_targets(self) -> None:
        cfg = {
            "build": {
                "default_region": "US",
                "targets": [
                    {"model": "JE-2000F", "region": "US"},
                    {"model": "JE-1000F"},
                ],
            }
        }

        targets = build_docs.resolve_build_targets(
            cfg,
            arg_model=None,
            arg_region=None,
            all_targets=True,
        )

        self.assertEqual(
            [
                build_docs.BuildTarget(model="JE-2000F", region="US"),
                build_docs.BuildTarget(model="JE-1000F", region="US"),
            ],
            targets,
        )

    def test_resolve_build_targets_should_reject_explicit_target_with_all_targets(self) -> None:
        cfg = {"build": {"targets": [{"model": "JE-2000F", "region": "US"}]}}

        with self.assertRaisesRegex(RuntimeError, "Cannot combine --all-targets"):
            build_docs.resolve_build_targets(
                cfg,
                arg_model="JE-2000F",
                arg_region=None,
                all_targets=True,
            )

    def test_resolve_requested_formats_should_honor_cli(self) -> None:
        cfg = {"build": {"build_word": True}}
        self.assertEqual(["html", "word"], build_docs.resolve_requested_formats(cfg, "html,word"))

    def test_resolve_requested_formats_should_use_legacy_flags(self) -> None:
        cfg = {"build": {"build_word": True, "build_html": False}}
        self.assertEqual(["word"], build_docs.resolve_requested_formats(cfg, None))

    def test_gen_index_should_render_model_region_tokens(self) -> None:
        cfg = self._tokenized_cfg()
        text = gen_index_bundle.build_index_from_pages(
            cfg,
            model="JHP-2000A",
            region="US",
        )
        self.assertIn(".. include:: page/safety_en.rst", text)

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

    def test_materialize_bundle_should_write_resolved_page_rst_under_model_region(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            docs_dir = root / "docs"
            template_dir = docs_dir / "templates" / "page_en"
            static_dir = docs_dir / "_static"
            data_dir = root / "data" / "phase1"
            template_dir.mkdir(parents=True)
            static_dir.mkdir(parents=True)
            data_dir.mkdir(parents=True)

            (docs_dir / "conf_base.py").write_text(
                ".. |PRODUCT_NAME| replace:: Default Product\n",
                encoding="utf-8",
            )
            (static_dir / "demo.png").write_bytes(b"demo")
            (template_dir / "demo.rst").write_text(
                "Hello |PRODUCT_NAME|\n\n.. image:: _static/demo.png\n   :width: 40px\n",
                encoding="utf-8",
            )
            (data_dir / "Spec_Master.csv").write_text(
                "Section,Row_key,Line_order,Page,Model,Region,Is_Latest,enabled,Value_en\n"
                "GENERAL INFO,product_name,1,specifications,M1,US,1,1,Demo Product\n",
                encoding="utf-8",
            )

            cfg = {
                "build": {"languages": ["en"], "default_model": "M1", "default_region": "US"},
                "paths": {"spec_master_csv": "data/phase1/Spec_Master.csv"},
                "pages": [
                    {
                        "type": "rst_include",
                        "lang": "en",
                        "file": "templates/page_en/demo.rst",
                    }
                ],
            }

            bundle = gen_index_bundle.materialize_bundle(
                cfg,
                docs_dir=docs_dir,
                repo_root=root,
            )

            self.assertEqual(docs_dir / "_build" / "M1" / "US" / "rst", bundle.bundle_dir)
            self.assertTrue(bundle.index_path.exists())
            self.assertTrue(bundle.wrapper_index_path.exists())
            self.assertEqual("Demo Product User Manual", bundle.title)

            index_text = bundle.index_path.read_text(encoding="utf-8")
            self.assertIn(".. include:: page/demo.rst", index_text)

            page_text = (bundle.page_dir / "demo.rst").read_text(encoding="utf-8")
            self.assertIn("Hello Demo Product", page_text)
            self.assertNotIn("|PRODUCT_NAME|", page_text)
            self.assertIn("_static/demo.png", page_text)

            wrapper_text = bundle.wrapper_index_path.read_text(encoding="utf-8")
            self.assertIn(".. include:: _build/M1/US/rst/index", wrapper_text)

    def test_materialize_bundle_should_copy_csv_rst_into_target_page_dir(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            docs_dir = root / "docs"
            docs_dir.mkdir(parents=True)
            (docs_dir / "conf_base.py").write_text("", encoding="utf-8")
            spec_master = root / "data" / "phase1" / "Spec_Master.csv"
            spec_master.parent.mkdir(parents=True)
            spec_master.write_text(
                "Section,Row_key,Line_order,Page,Model,Region,Is_Latest,enabled,Value_en\n"
                "GENERAL INFO,product_name,1,specifications,M1,US,1,1,Demo Product\n",
                encoding="utf-8",
            )

            cfg = {
                "build": {"languages": ["en"], "default_model": "M1", "default_region": "US"},
                "paths": {"spec_master_csv": "data/phase1/Spec_Master.csv"},
                "pages": [
                    {
                        "type": "csv_page",
                        "page": "safety",
                        "source": "phase1",
                        "langs": ["en"],
                        "include_dir": "generated/{model}",
                    }
                ],
            }

            fake_builder = mock.Mock()
            fake_builder.paths.spec_master_csv = spec_master
            fake_builder.paths.output_dir = docs_dir / "_build" / "M1" / "US" / "rst" / "generated"

            def write_generated_csv(*args, **kwargs) -> None:
                generated_dir = fake_builder.paths.output_dir / "M1"
                generated_dir.mkdir(parents=True, exist_ok=True)
                (generated_dir / "safety_en.rst").write_text("CSV page body\n", encoding="utf-8")

            with mock.patch("tools.gen_index_bundle.load_word_context", return_value=fake_builder):
                with mock.patch("tools.gen_index_bundle.ensure_csv_page_rsts", side_effect=write_generated_csv):
                    bundle = gen_index_bundle.materialize_bundle(
                        cfg,
                        docs_dir=docs_dir,
                        repo_root=root,
                    )

            page_text = (bundle.page_dir / "safety_en.rst").read_text(encoding="utf-8")
            self.assertIn("CSV page body", page_text)
            self.assertIn(".. include:: page/safety_en.rst", bundle.index_path.read_text(encoding="utf-8"))

    def test_materialize_bundle_should_remove_legacy_rst_directories(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            docs_dir = root / "docs"
            legacy_bundle_dir = docs_dir / "M1" / "US"
            legacy_generated_dir = docs_dir / "generated" / "M1"
            template_dir = docs_dir / "templates" / "page_en"
            data_dir = root / "data" / "phase1"

            legacy_bundle_dir.mkdir(parents=True)
            legacy_generated_dir.mkdir(parents=True)
            template_dir.mkdir(parents=True)
            data_dir.mkdir(parents=True)

            (legacy_bundle_dir / "stale.rst").write_text("old bundle", encoding="utf-8")
            (legacy_generated_dir / "stale.rst").write_text("old generated", encoding="utf-8")
            (docs_dir / "conf_base.py").write_text("", encoding="utf-8")
            (template_dir / "demo.rst").write_text("Hello\n", encoding="utf-8")
            (data_dir / "Spec_Master.csv").write_text(
                "Section,Row_key,Line_order,Page,Model,Region,Is_Latest,enabled,Value_en\n"
                "GENERAL INFO,product_name,1,specifications,M1,US,1,1,Demo Product\n",
                encoding="utf-8",
            )

            cfg = {
                "build": {"languages": ["en"], "default_model": "M1", "default_region": "US"},
                "paths": {"spec_master_csv": "data/phase1/Spec_Master.csv"},
                "pages": [
                    {
                        "type": "rst_include",
                        "lang": "en",
                        "file": "templates/page_en/demo.rst",
                    }
                ],
            }

            bundle = gen_index_bundle.materialize_bundle(
                cfg,
                docs_dir=docs_dir,
                repo_root=root,
            )

            self.assertEqual(docs_dir / "_build" / "M1" / "US" / "rst", bundle.bundle_dir)
            self.assertFalse(legacy_bundle_dir.exists())
            self.assertFalse(legacy_generated_dir.exists())

    def test_discover_existing_bundle_targets_should_find_all_built_targets(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            docs_dir = Path(td) / "docs"
            (docs_dir / "_build" / "M1" / "US" / "rst").mkdir(parents=True)
            (docs_dir / "_build" / "M2" / "JP" / "rst").mkdir(parents=True)
            (docs_dir / "_build" / "M1" / "US" / "rst" / "index.rst").write_text("", encoding="utf-8")
            (docs_dir / "_build" / "M2" / "JP" / "rst" / "index.rst").write_text("", encoding="utf-8")

            targets = build_docs.discover_existing_bundle_targets(docs_dir=docs_dir)

            self.assertEqual(
                [
                    build_docs.BuildTarget(model="M1", region="US"),
                    build_docs.BuildTarget(model="M2", region="JP"),
                ],
                targets,
            )

    def test_clean_build_targets_should_only_remove_requested_target_output(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            docs_dir = Path(td) / "docs"
            keep_dir = docs_dir / "_build" / "M2" / "JP" / "rst"
            drop_dir = docs_dir / "_build" / "M1" / "US" / "rst"
            drop_dir.mkdir(parents=True)
            keep_dir.mkdir(parents=True)
            (drop_dir / "index.rst").write_text("", encoding="utf-8")
            (keep_dir / "index.rst").write_text("", encoding="utf-8")

            build_docs.clean_build_targets(
                [build_docs.BuildTarget(model="M1", region="US")],
                docs_dir=docs_dir,
            )

            self.assertFalse((docs_dir / "_build" / "M1" / "US").exists())
            self.assertTrue((docs_dir / "_build" / "M2" / "JP" / "rst" / "index.rst").exists())


if __name__ == "__main__":
    unittest.main()
