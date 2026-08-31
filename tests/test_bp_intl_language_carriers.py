from __future__ import annotations

import hashlib
import unittest
from pathlib import Path

import yaml

from tools import check_docs
from tools.skeleton_resolve import (
    load_blueprint,
    load_region_profile,
    load_slot_templates,
    resolve_plan,
)


ROOT = Path(__file__).resolve().parents[1]
BP_ROOT = ROOT / "docs" / "templates" / "page_bp"
SKELETON_DIR = ROOT / "docs" / "manifests" / "skeletons" / "bp-intl"
US_PROFILE = ROOT / "docs" / "manifests" / "region_profiles" / "us.yaml"
US_MANIFEST = ROOT / "docs" / "manifests" / "manual_bp-us.yaml"

LONG_TAIL_LANGS = ("de", "it", "uk")
ALL_LANGS = ("en", "fr", "es", *LONG_TAIL_LANGS)
CONNECTION_LOCKING_ASSET_SUBSTITUTIONS = {
    "de": "BP_CONNECTION_LOCKING_ASSET_DE",
    "it": "BP_CONNECTION_LOCKING_ASSET_IT",
    "uk": "BP_CONNECTION_LOCKING_ASSET_UK",
}
BODY_CARRIERS = (
    "01_safety.rst",
    "02_whats_in_the_box.rst",
    "03_product_overview_placeholder.rst",
    "04_connections.rst",
    "05_operation_guide_placeholder.rst",
    "08_charging_methods.rst",
    "09_storage.rst",
    "11_warranty.rst",
)
FROZEN_US_MANIFEST_SHA256 = (
    "94e7276ab3f20bbd804eb66864b360dd5780c886b3d29ed5377161162da5cc8b"
)


class BpIntlLanguageCarrierTests(unittest.TestCase):
    def test_long_tail_languages_have_all_family_body_carriers(self) -> None:
        for lang in LONG_TAIL_LANGS:
            with self.subTest(lang=lang):
                actual = {path.name for path in (BP_ROOT / lang).glob("*.rst")}
                self.assertEqual(set(BODY_CARRIERS), actual)

    def test_six_language_front_carriers_are_family_owned(self) -> None:
        preface = (BP_ROOT / "intl" / "00_preface_six_language.rst").read_text(
            encoding="utf-8"
        )
        toc = (BP_ROOT / "intl" / "00_toc_six_language.rst").read_text(
            encoding="utf-8"
        )
        for badge, title in (
            ("US", "IMPORTANT"),
            ("FR", "IMPORTANT"),
            ("ES", "IMPORTANTE"),
            ("DE", "WICHTIG"),
            ("IT", "IMPORTANTE"),
            ("UK", "ВАЖЛИВО"),
        ):
            self.assertIn(rf"\HBLangTagLine{{{badge}}}{{{title}}}", preface)
            self.assertIn(rf"\HBTocLanguageBlock{{{badge}}}", toc)
        for text in (preface, toc):
            self.assertNotIn("JBP-2000B_EU", text)
            self.assertNotIn("HTP017", text)

    def test_toc_normalizes_only_the_recorded_source_defects(self) -> None:
        toc = (BP_ROOT / "intl" / "00_toc_six_language.rst").read_text(
            encoding="utf-8"
        )
        self.assertIn(r"\HBTocEntry{LCD-ANZEIGE}{27}", toc)
        self.assertIn(r"\HBTocEntry{PRECAUZIONI DI SICUREZZA}{33}", toc)
        self.assertIn(r"\HBTocEntry{COLLEGAMENTI}{36}", toc)
        self.assertNotIn(r"\HBTocEntry{PANTALLA LCD}{27}", toc)
        self.assertNotIn(r"\HBTocEntry{COME SI USA}{36}", toc)

    def test_paired_host_name_is_target_data_not_page_logic(self) -> None:
        for lang in ALL_LANGS:
            for name in (
                "04_connections.rst",
                "05_operation_guide_placeholder.rst",
                "08_charging_methods.rst",
            ):
                with self.subTest(lang=lang, name=name):
                    text = (BP_ROOT / lang / name).read_text(encoding="utf-8")
                    self.assertIn("|BP_HOST_PRODUCT_NAME|", text)
                    self.assertNotIn("HomePower 2000 Plus", text)
                    self.assertNotIn("Explorer 2000 Plus", text)

        config = yaml.safe_load(
            (ROOT / "configs" / "config.bp-us.yaml").read_text(encoding="utf-8")
        )
        substitutions = config["build"]["rst_substitutions"]
        self.assertEqual(
            "Jackery HomePower 2000 Plus",
            substitutions["BP_HOST_PRODUCT_NAME"],
        )
        self.assertEqual(
            "HomePower 2000 Plus",
            substitutions["BP_HOST_PRODUCT_SHORT_NAME"],
        )

    def test_generated_page_checker_accepts_config_owned_substitutions(self) -> None:
        cfg = check_docs.load_config(ROOT / "configs" / "config.bp-us.yaml")
        issues = check_docs.collect_generated_page_issues(
            cfg,
            docs_dir=check_docs.resolve_docs_dir(cfg),
            target=check_docs.BuildTarget(model="JBP-2000B", region="US"),
            langs=["en", "fr", "es"],
            data_root=str(ROOT / "tests" / "fixtures" / "phase2"),
        )
        unknown = [
            issue for issue in issues if issue.code == "UNKNOWN_RECIPE_PLACEHOLDERS"
        ]
        self.assertEqual([], unknown)

    def test_long_tail_connection_assets_are_target_data(self) -> None:
        for lang, substitution in CONNECTION_LOCKING_ASSET_SUBSTITUTIONS.items():
            with self.subTest(lang=lang):
                text = (BP_ROOT / lang / "04_connections.rst").read_text(
                    encoding="utf-8"
                )
                self.assertIn(f".. image:: |{substitution}|", text)
                self.assertNotIn(
                    f"asset:connections/jbp2000b/locking_{lang}",
                    text,
                )

    def test_italian_snippet_is_exact_and_de_uk_stay_source_specific(self) -> None:
        snippet = (
            ROOT
            / "docs"
            / "templates"
            / "snippets"
            / "battery_long_storage_advisory"
            / "it.rst"
        ).read_text(encoding="utf-8").strip()
        host = (
            ROOT
            / "docs"
            / "templates"
            / "page_shared"
            / "it"
            / "09_storage_and_maintenance.rst"
        ).read_text(encoding="utf-8")
        self.assertIn(snippet, host)
        self.assertIn(
            "{{snippet:battery_long_storage_advisory}}",
            (BP_ROOT / "it" / "09_storage.rst").read_text(encoding="utf-8"),
        )
        for lang in ("de", "uk"):
            text = (BP_ROOT / lang / "09_storage.rst").read_text(encoding="utf-8")
            self.assertNotIn("{{snippet:", text)

    def test_uk_warranty_uses_approved_ukrainian_exchange_copy(self) -> None:
        text = (BP_ROOT / "uk" / "11_warranty.rst").read_text(encoding="utf-8")
        self.assertIn("Обмін", text)
        self.assertIn("Jackery замінить", text)
        self.assertNotIn("Umtausch", text)
        self.assertNotIn("Jackery tauscht", text)

    def test_synthetic_six_language_plan_resolves_from_bp_intl(self) -> None:
        blueprint = load_blueprint(SKELETON_DIR / "blueprint.yaml")
        slot_templates = load_slot_templates(
            SKELETON_DIR / "slot_templates.yaml", blueprint
        )
        profile = load_region_profile(US_PROFILE, blueprint)
        profile = {
            **profile,
            "region": "synthetic-six-language",
            "language_set": list(ALL_LANGS),
            "terminal_slots": ["regulatory_compliance"],
            "slot_overrides": {
                **profile["slot_overrides"],
                "preface_important": {
                    "file": "templates/page_bp/intl/00_preface_six_language.rst"
                },
                "toc": {"file": "templates/page_bp/intl/00_toc_six_language.rst"},
                "safety_info": {"file": "templates/page_bp/{lang}/01_safety.rst"},
                "regulatory_compliance": {
                    "file": "templates/page_bp/intl/99_regulatory_placeholder.rst"
                },
            },
            "compliance": [],
        }
        plan = resolve_plan(
            blueprint, slot_templates, profile, manifest_id="synthetic_bp_intl_six"
        )
        self.assertEqual("bp-intl", blueprint["skeleton_id"])
        self.assertEqual("synthetic_bp_intl_six", plan["manifest_id"])
        for entry in plan["pages"]:
            lang = entry.get("lang") or (entry.get("langs") or [None])[0]
            if lang not in LONG_TAIL_LANGS:
                continue
            carrier = entry.get("file") or entry.get("template")
            if carrier and carrier.startswith("templates/page_bp/"):
                self.assertTrue((ROOT / "docs" / carrier).is_file(), carrier)

    def test_us_resolved_manifest_identity_is_frozen(self) -> None:
        digest = hashlib.sha256(US_MANIFEST.read_bytes()).hexdigest()
        self.assertEqual(FROZEN_US_MANIFEST_SHA256, digest)

    def test_new_carriers_do_not_embed_target_identity(self) -> None:
        paths = [
            *(BP_ROOT / "intl").glob("*.rst"),
            *(
                path
                for lang in LONG_TAIL_LANGS
                for path in (BP_ROOT / lang).glob("*.rst")
            ),
        ]
        for path in paths:
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                self.assertNotIn("JBP-2000B_EU", text)
                self.assertNotIn("HTP017", text)


if __name__ == "__main__":
    unittest.main()
