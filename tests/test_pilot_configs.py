from __future__ import annotations

import unittest
from pathlib import Path

from tools import check_docs
from tools.config_pages import CoverPdfPage, CsvPage, GeneratedPage, RstIncludePage
from tools.page_manifest import resolve_config_pages_or_raise


ROOT = Path(__file__).resolve().parents[1]


class TestPilotConfigs(unittest.TestCase):
    def _assert_pilot_config_ready(self, *, config_name: str, model: str, region: str) -> None:
        cfg = check_docs.load_config(ROOT / config_name)
        docs_dir = check_docs.resolve_docs_dir(cfg)
        langs = [str(item).strip() for item in cfg.get("build", {}).get("languages", ["en"]) if str(item).strip()] or ["en"]

        resolved = resolve_config_pages_or_raise(
            cfg,
            default_languages=langs,
            root=ROOT,
            model=model,
            region=region,
            error_prefix="config.pages",
        )
        generated_pages = [page for page in resolved.pages if isinstance(page, GeneratedPage)]

        self.assertEqual(
            {"03_product_overview", "05_operation_guide", "12_app_setup"},
            {page.page for page in generated_pages},
        )

        issues = check_docs.collect_generated_page_issues(
            cfg,
            docs_dir=docs_dir,
            target=check_docs.BuildTarget(model=model, region=region),
            langs=langs,
        )
        self.assertEqual([], issues)

    def test_us_pilot_config_should_resolve_generated_pages_without_issues(self) -> None:
        self._assert_pilot_config_ready(
            config_name="config.us.yaml",
            model="JE-1000F",
            region="US",
        )

    def test_jp_pilot_config_should_resolve_generated_pages_without_issues(self) -> None:
        self._assert_pilot_config_ready(
            config_name="config.ja.yaml",
            model="JE-1000F",
            region="JP",
        )

    def test_us_single_language_configs_should_resolve_manifest_backed_pages_without_issues(self) -> None:
        cases = (
            ("config.us-en.yaml", "en", "us-en", "docs/manifests/manual_us-single-en.yaml", 17),
            ("config.us-es.yaml", "es", "us-es", "docs/manifests/manual_us-single-es.yaml", 16),
            ("config.us-fr.yaml", "fr", "us-fr", "docs/manifests/manual_us-single-fr.yaml", 16),
        )

        for config_name, expected_lang, expected_family, expected_manifest, expected_page_count in cases:
            with self.subTest(config_name=config_name):
                cfg = check_docs.load_config(ROOT / config_name)
                self.assertEqual(expected_family, cfg.get("build", {}).get("family_id"))
                self.assertEqual([expected_lang], cfg.get("build", {}).get("languages"))
                self.assertTrue(cfg.get("build", {}).get("include_lang_in_output_path"))
                self.assertEqual(expected_manifest, cfg.get("paths", {}).get("page_manifest"))

                resolved = resolve_config_pages_or_raise(
                    cfg,
                    default_languages=[expected_lang],
                    root=ROOT,
                    model="JE-1000F",
                    region="US",
                    error_prefix="config.pages",
                )
                generated_pages = [page for page in resolved.pages if isinstance(page, GeneratedPage)]
                csv_pages = [page for page in resolved.pages if isinstance(page, CsvPage)]

                self.assertEqual({"12_app_setup"}, {page.page for page in generated_pages})
                self.assertEqual({"lcd_icons", "symbols", "spec"}, {page.page for page in csv_pages})
                self.assertEqual(expected_page_count, len(resolved.pages))

                issues = check_docs.collect_generated_page_issues(
                    cfg,
                    docs_dir=check_docs.resolve_docs_dir(cfg),
                    target=check_docs.BuildTarget(model="JE-1000F", region="US", lang=expected_lang),
                    langs=[expected_lang],
                )
                self.assertEqual([], issues)

    def test_us_safety_pages_should_remain_two_column(self) -> None:
        for lang in ("en", "fr", "es"):
            with self.subTest(lang=lang):
                safety_path = ROOT / "docs" / "templates" / f"page_us-{lang}" / f"safety_{lang}.rst"
                text = safety_path.read_text(encoding="utf-8")

                self.assertIn("safetytwocol", text)
                self.assertIn("hb-two-col", text)
                self.assertNotIn("safetysinglecol", text)
                self.assertNotIn("hb-single-col", text)

    def test_pt_br_templates_should_mirror_us_source_template_layout(self) -> None:
        us_specific_files = {
            "safety_pt-BR.rst",
            "01_fcc.rst",
            "03_product_overview_placeholder.rst",
            "05_operation_guide_placeholder.rst",
        }
        shared_files = {
            "00_preface.rst",
            "01_user_maintenance_instructions.rst",
            "02_whats_in_the_box.rst",
            "06_ups_mode.rst",
            "charging.rst",
            "08_charging_methods.rst",
            "09_storage_and_maintenance.rst",
            "10_troubleshooting.rst",
            "11_warranty.rst",
            "12_app_setup_placeholder.rst",
        }

        for file_name in us_specific_files:
            with self.subTest(file_name=file_name):
                path = ROOT / "docs" / "templates" / "page_us-pt-br" / file_name
                self.assertTrue(path.exists(), path)
                self.assertTrue(path.read_text(encoding="utf-8").strip())

        for file_name in shared_files:
            with self.subTest(file_name=file_name):
                path = ROOT / "docs" / "templates" / "page_shared" / "pt-BR" / file_name
                self.assertTrue(path.exists(), path)
                self.assertTrue(path.read_text(encoding="utf-8").strip())

        charging_text = (ROOT / "docs" / "templates" / "page_shared" / "pt-BR" / "charging.rst").read_text(encoding="utf-8")
        methods_text = (
            ROOT / "docs" / "templates" / "page_shared" / "pt-BR" / "08_charging_methods.rst"
        ).read_text(encoding="utf-8")
        self.assertIn("CARREGAMENTO VIA TOMADA DA REDE ELÉTRICA CA", charging_text)
        self.assertNotIn("CARREGAMENTO VIA PAINÉIS SOLARES", charging_text)
        self.assertIn("CARREGAMENTO VIA PAINÉIS SOLARES", methods_text)
        product_overview_text = (
            ROOT / "docs" / "templates" / "page_us-pt-br" / "03_product_overview_placeholder.rst"
        ).read_text(encoding="utf-8")
        operation_text = (
            ROOT / "docs" / "templates" / "page_us-pt-br" / "05_operation_guide_placeholder.rst"
        ).read_text(encoding="utf-8")
        app_text = (
            ROOT / "docs" / "templates" / "page_shared" / "pt-BR" / "12_app_setup_placeholder.rst"
        ).read_text(encoding="utf-8")
        self.assertIn("{{ product_overview }}", product_overview_text)
        self.assertNotIn("JE-1500D", product_overview_text)
        self.assertIn("|DEFAULT_STANDBY_DURATION|", operation_text)
        self.assertIn("|ENERGY_SAVING_AUTO_OFF_DURATION|", operation_text)
        self.assertIn("|ADD_DEVICE_STEP|", app_text)
        self.assertIn("|MAIN_POWER_BUTTON_LABEL|", app_text)

    def test_pt_br_config_should_preserve_us_source_pages_and_append_pt_br_templates(self) -> None:
        cfg = check_docs.load_config(ROOT / "config.pt-br.yaml")
        self.assertEqual("pt-br", cfg.get("build", {}).get("family_id"))
        self.assertEqual("JE-1500D", cfg.get("build", {}).get("default_model"))
        self.assertEqual("pt-BR", cfg.get("build", {}).get("default_region"))
        self.assertEqual([{"model": "JE-1500D", "region": "pt-BR"}], cfg.get("build", {}).get("targets"))
        self.assertEqual(["en", "pt-BR"], cfg.get("build", {}).get("languages"))
        self.assertFalse(cfg.get("build", {}).get("include_lang_in_output_path"))
        self.assertTrue(cfg.get("build", {}).get("queue_by_document_key"))
        self.assertEqual("docs/manifests/manual_pt-br.yaml", cfg.get("paths", {}).get("page_manifest"))

        source_pages = resolve_config_pages_or_raise(
            {"paths": {"page_manifest": "docs/manifests/manual_us-en.yaml"}},
            default_languages=["en"],
            root=ROOT,
            model="JE-1500D",
            region="pt-BR",
            error_prefix="config.pages",
        ).pages
        resolved = resolve_config_pages_or_raise(
            cfg,
            default_languages=["en", "pt-BR"],
            root=ROOT,
            model="JE-1500D",
            region="pt-BR",
            error_prefix="config.pages",
        )

        self.assertEqual(source_pages, resolved.pages[: len(source_pages)])
        pt_br_pages = resolved.pages[len(source_pages) :]
        self.assertEqual(17, len(pt_br_pages))
        self.assertTrue(all(not isinstance(page, CoverPdfPage) for page in pt_br_pages))

        for page in pt_br_pages:
            with self.subTest(page=page):
                if isinstance(page, RstIncludePage):
                    self.assertEqual("pt-BR", page.lang)
                    self.assertNotIn("templates/page_us-en/", page.file)
                    self.assertNotIn("templates/page_shared/en/", page.file)
                elif isinstance(page, CsvPage):
                    self.assertEqual(("pt-BR",), page.langs)
                elif isinstance(page, GeneratedPage):
                    self.assertEqual(("pt-BR",), page.langs)

        generated_pages = [page for page in resolved.pages if isinstance(page, GeneratedPage)]
        self.assertEqual(
            {
                ("03_product_overview", ("en",), "templates/page_us-en/03_product_overview_placeholder.rst"),
                ("05_operation_guide", ("en",), "templates/page_us-en/05_operation_guide_placeholder.rst"),
                ("12_app_setup", ("en",), "templates/page_shared/en/12_app_setup_placeholder.rst"),
                ("03_product_overview", ("pt-BR",), "templates/page_us-pt-br/03_product_overview_placeholder.rst"),
                ("05_operation_guide", ("pt-BR",), "templates/page_us-pt-br/05_operation_guide_placeholder.rst"),
                ("12_app_setup", ("pt-BR",), "templates/page_shared/pt-BR/12_app_setup_placeholder.rst"),
            },
            {(page.page, page.langs, page.template) for page in generated_pages},
        )
        csv_pages = [page for page in resolved.pages if isinstance(page, CsvPage)]
        self.assertEqual(
            {
                ("symbols", ("en",)),
                ("lcd_icons", ("en",)),
                ("spec", ("en",)),
                ("symbols", ("pt-BR",)),
                ("lcd_icons", ("pt-BR",)),
                ("spec", ("pt-BR",)),
            },
            {(page.page, page.langs) for page in csv_pages},
        )

    def test_user_maintenance_page_should_precede_symbols_page_in_shared_manifests(self) -> None:
        cases = (
            ("config.us.yaml", "US", ("en", "fr", "es")),
            ("config.eu.yaml", "EU", ("en", "fr", "es", "de", "it", "uk")),
        )

        for config_name, region, langs in cases:
            with self.subTest(config_name=config_name):
                cfg = check_docs.load_config(ROOT / config_name)
                resolved = resolve_config_pages_or_raise(
                    cfg,
                    default_languages=list(langs),
                    root=ROOT,
                    model="JE-1000F",
                    region=region,
                    error_prefix="config.pages",
                )

                for lang in langs:
                    maintenance_idx = next(
                        idx
                        for idx, page in enumerate(resolved.pages)
                        if isinstance(page, RstIncludePage)
                        and page.lang == lang
                        and page.file == f"templates/page_shared/{lang}/01_user_maintenance_instructions.rst"
                    )
                    symbols_idx = next(
                        idx
                        for idx, page in enumerate(resolved.pages)
                        if isinstance(page, CsvPage) and page.page == "symbols" and page.langs == (lang,)
                    )

                    self.assertLess(maintenance_idx, symbols_idx)

    def test_eu_single_language_configs_should_resolve_manifest_backed_pages_without_issues(self) -> None:
        cases = (
            ("config.eu-en.yaml", "en", "eu-en", "docs/manifests/manual_eu-en.yaml", 16),
            ("config.eu-fr.yaml", "fr", "eu-fr", "docs/manifests/manual_eu-single-fr.yaml", 15),
            ("config.eu-es.yaml", "es", "eu-es", "docs/manifests/manual_eu-single-es.yaml", 15),
        )

        for config_name, expected_lang, expected_family, expected_manifest, expected_page_count in cases:
            with self.subTest(config_name=config_name):
                cfg = check_docs.load_config(ROOT / config_name)
                self.assertEqual(expected_family, cfg.get("build", {}).get("family_id"))
                self.assertEqual("JE-1000F", cfg.get("build", {}).get("default_model"))
                self.assertEqual("EU", cfg.get("build", {}).get("default_region"))
                self.assertEqual([{"model": "JE-1000F", "region": "EU"}], cfg.get("build", {}).get("targets"))
                self.assertEqual([expected_lang], cfg.get("build", {}).get("languages"))
                self.assertTrue(cfg.get("build", {}).get("include_lang_in_output_path"))
                self.assertEqual(expected_manifest, cfg.get("paths", {}).get("page_manifest"))
                self.assertEqual(["占位符"], cfg.get("checks", {}).get("allowed_foreign_identity_literals"))
                self.assertEqual(
                    "tbl7Kxyq8AaDKwsn",
                    cfg.get("sync", {}).get("phase2", {}).get("tables", {}).get("spec_master", {}).get("table_id"),
                )
                self.assertEqual(
                    "vewbjo4Zfz",
                    cfg.get("sync", {}).get("phase2", {}).get("tables", {}).get("spec_master", {}).get("view_id"),
                )

                resolved = resolve_config_pages_or_raise(
                    cfg,
                    default_languages=[expected_lang],
                    root=ROOT,
                    model="JE-1000F",
                    region="EU",
                    error_prefix="config.pages",
                )
                generated_pages = [page for page in resolved.pages if isinstance(page, GeneratedPage)]
                csv_pages = [page for page in resolved.pages if isinstance(page, CsvPage)]

                self.assertEqual({"03_product_overview", "05_operation_guide", "12_app_setup"}, {page.page for page in generated_pages})
                self.assertEqual({"lcd_icons", "symbols", "spec"}, {page.page for page in csv_pages})
                self.assertEqual(expected_page_count, len(resolved.pages))

                issues = check_docs.collect_generated_page_issues(
                    cfg,
                    docs_dir=check_docs.resolve_docs_dir(cfg),
                    target=check_docs.BuildTarget(model="JE-1000F", region="EU", lang=expected_lang),
                    langs=[expected_lang],
                )
                self.assertEqual([], issues)

    def test_eu_safety_pages_should_use_eu_safety_content(self) -> None:
        cases = (
            ("en", "SAFETY PRECAUTIONS FOR USE", "USER MAINTENANCE INSTRUCTIONS"),
            ("fr", "PRÉCAUTIONS DE SÉCURITÉ POUR L'UTILISATION", "INSTRUCTIONS D'ENTRETIEN PAR L'UTILISATEUR"),
            ("es", "PRECAUCIONES DE SEGURIDAD PARA EL USO", "INSTRUCCIONES DE MANTENIMIENTO PARA EL USUARIO"),
            ("de", "SICHERHEITSVORKEHRUNGEN BEI DER VERWENDUNG", "ANWEISUNGEN ZUR BENUTZERWARTUNG"),
            ("it", "PRECAUZIONI DI SICUREZZA", "ISTRUZIONI PER LA MANUTENZIONE DA PARTE DELL'UTENTE"),
            ("uk", "ЗАХОДИ БЕЗПЕКИ ПІД ЧАС ВИКОРИСТАННЯ", "ІНСТРУКЦІЇ З ТЕХНІЧНОГО ОБСЛУГОВУВАННЯ КОРИСТУВАЧЕМ"),
        )
        us_only_markers = (
            "SAVE THESE INSTRUCTIONS",
            "CONSERVEZ CES INSTRUCTIONS",
            "GUARDE ESTAS INSTRUCCIONES",
            "ЗБЕРЕЖІТЬ ЦІ ВКАЗІВКИ",
            "MISE À LA TERRE",
            "CONEXIÓN A TIERRA",
            "GROUNDING",
            "457 mm",
            "18 pouces",
            "18 pulgadas",
            "|CHARGING_TEMPERATURE_VALUE_1|",
            "|DISCHARGING_TEMPERATURE_VALUE_1|",
        )

        for lang, expected_title, expected_maintenance_heading in cases:
            with self.subTest(lang=lang):
                safety_path = ROOT / "docs" / "templates" / f"page_eu-{lang}" / f"safety_{lang}.rst"
                text = safety_path.read_text(encoding="utf-8")
                maintenance_path = (
                    ROOT
                    / "docs"
                    / "templates"
                    / "page_shared"
                    / lang
                    / "01_user_maintenance_instructions.rst"
                )
                maintenance_text = maintenance_path.read_text(encoding="utf-8")

                self.assertIn(expected_title, text)
                self.assertNotIn(expected_maintenance_heading, text)
                self.assertIn(expected_maintenance_heading, maintenance_text)
                self.assertIn("safetysinglecol", text)
                self.assertIn("hb-single-col", text)
                self.assertNotIn("safetytwocol", text)
                self.assertNotIn("hb-two-col", text)
                for marker in us_only_markers:
                    self.assertNotIn(marker, text)

    def test_eu_merged_config_should_resolve_manifest_backed_pages_without_issues(self) -> None:
        cfg = check_docs.load_config(ROOT / "config.eu.yaml")
        self.assertEqual("eu-merged", cfg.get("build", {}).get("family_id"))
        self.assertEqual("JE-1000F", cfg.get("build", {}).get("default_model"))
        self.assertEqual("EU", cfg.get("build", {}).get("default_region"))
        self.assertEqual([{"model": "JE-1000F", "region": "EU"}], cfg.get("build", {}).get("targets"))
        self.assertEqual(["en", "fr", "es", "de", "it", "uk"], cfg.get("build", {}).get("languages"))
        self.assertFalse(cfg.get("build", {}).get("include_lang_in_output_path"))
        self.assertTrue(cfg.get("build", {}).get("queue_by_document_key"))
        self.assertEqual("docs/manifests/manual_eu.yaml", cfg.get("paths", {}).get("page_manifest"))
        self.assertEqual(["占位符"], cfg.get("checks", {}).get("allowed_foreign_identity_literals"))
        self.assertEqual(
            "tbl7Kxyq8AaDKwsn",
            cfg.get("sync", {}).get("phase2", {}).get("tables", {}).get("spec_master", {}).get("table_id"),
        )
        self.assertEqual(
            "vewbjo4Zfz",
            cfg.get("sync", {}).get("phase2", {}).get("tables", {}).get("spec_master", {}).get("view_id"),
        )

        resolved = resolve_config_pages_or_raise(
            cfg,
            default_languages=["en", "fr", "es", "de", "it", "uk"],
            root=ROOT,
            model="JE-1000F",
            region="EU",
            error_prefix="config.pages",
        )
        generated_pages = [page for page in resolved.pages if isinstance(page, GeneratedPage)]
        csv_pages = [page for page in resolved.pages if isinstance(page, CsvPage)]

        self.assertEqual(91, len(resolved.pages))
        self.assertEqual(18, len(generated_pages))
        self.assertEqual(18, len(csv_pages))
        self.assertEqual({"lcd_icons", "symbols", "spec"}, {page.page for page in csv_pages})

        issues = check_docs.collect_generated_page_issues(
            cfg,
            docs_dir=check_docs.resolve_docs_dir(cfg),
            target=check_docs.BuildTarget(model="JE-1000F", region="EU"),
            langs=["en", "fr", "es", "de", "it", "uk"],
        )
        self.assertEqual([], issues)


if __name__ == "__main__":
    unittest.main()
