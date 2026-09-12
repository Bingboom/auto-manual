from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from bs4 import BeautifulSoup
import yaml

from tools.manual_ir import read_manual_ir
from tools.web_document_ir import render_document_fragments

from tools.asset_registry import load_registry, resolve_asset
from tools.skeleton_resolve import (
    load_blueprint,
    load_product_plan,
    load_region_profile,
    load_slot_template_catalog,
    resolve_plan,
)


ROOT = Path(__file__).resolve().parents[1]
SKELETON_DIR = ROOT / "docs" / "manifests" / "skeletons" / "charger-intl"
PROFILE = ROOT / "docs" / "manifests" / "region_profiles" / "charger-eu-en.yaml"
CONFIG = ROOT / "configs" / "config.charger-eu-en.yaml"
FIXTURE = ROOT / "data" / "manual_sources" / "ja_ad01a_eu_en"
ASSET_RECIPE = ROOT / "data" / "asset_recipes" / "manual_ja_ad01a_eu_en_web.json"
ILLUSTRATION_MANIFEST = (
    ROOT / "docs" / "renderers" / "web" / "charger_eu_en_JA-AD01A_illustrations.json"
)
PRODUCT_PLAN = ROOT / "docs" / "manifests" / "product_plans" / "ja_ad01a_eu.yaml"


class JaAd01aEuEnTargetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        cls.staging = Path(cls._tmp.name) / "staging"
        # This suite validates the upstream HTML/IR package, not Pandoc syntax.
        # Real Pandoc + Sphinx conversion is checked in target acceptance.
        fake_bin = Path(cls._tmp.name) / "bin"
        fake_bin.mkdir()
        fake_pandoc = fake_bin / "pandoc"
        fake_pandoc.write_text(
            "#!/usr/bin/env python3\n"
            "from pathlib import Path\n"
            "import sys\n"
            "if '--list-output-formats' in sys.argv:\n"
            "    print('myst')\n"
            "    raise SystemExit(0)\n"
            "source = Path(sys.argv[1])\n"
            "target = Path(sys.argv[sys.argv.index('-o') + 1])\n"
            "target.write_text(source.read_text(encoding='utf-8'), encoding='utf-8')\n",
            encoding="utf-8",
        )
        fake_pandoc.chmod(0o755)
        env = {
            **os.environ,
            "AUTO_MANUAL_PRESENTATION_PROFILE": "web",
            "PATH": str(fake_bin) + os.pathsep + os.environ.get("PATH", ""),
        }
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "build.py"),
                "md",
                "--config",
                str(CONFIG),
                "--model",
                "JA-AD01A",
                "--region",
                "EU",
                "--lang",
                "en",
                "--data-root",
                str(FIXTURE),
                "--staging-root",
                str(cls.staging),
            ],
            cwd=ROOT,
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode:
            raise AssertionError("JA-AD01A Web fixture build failed:\n" + result.stdout + result.stderr)
        cls.package = (
            cls.staging
            / "docs"
            / "_build"
            / "JA-AD01A"
            / "EU"
            / "en"
            / "md"
        )
        cls.ir = read_manual_ir(cls.package / "manual.ir.json")
        cls.html = (cls.package / "manual_bundle.html").read_text(encoding="utf-8")

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def test_charger_skeleton_is_compact_and_target_agnostic(self) -> None:
        blueprint = load_blueprint(SKELETON_DIR / "blueprint.yaml")
        slots, slot_profiles = load_slot_template_catalog(
            SKELETON_DIR / "slot_templates.yaml", blueprint
        )
        profile = load_region_profile(PROFILE, blueprint)
        product_plan = load_product_plan(PRODUCT_PLAN, blueprint)
        plan = resolve_plan(
            blueprint,
            slots,
            profile,
            manifest_id="manual_charger_eu_en",
            product_plan=product_plan,
            slot_template_profiles=slot_profiles,
        )

        slot_ids = [page["slot_id"] for page in plan["pages"]]
        self.assertEqual(
            [
                "box_contents_en",
                "product_overview_en",
                "specifications_en",
                "using_product_en",
                "warning_en",
                "warranty_en",
                "legal_tail",
            ],
            slot_ids,
        )
        self.assertEqual("CHARGER", blueprint["skeleton_family"])
        self.assertFalse(any("lcd" in slot or "ups" in slot or "app" in slot for slot in slot_ids))
        self.assertNotIn("JA-AD01A", (SKELETON_DIR / "blueprint.yaml").read_text())

    def test_config_binds_only_the_eu_english_target_and_box_entry(self) -> None:
        config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
        build = config["build"]
        self.assertEqual(["en"], build["languages"])
        self.assertEqual(
            [
                {"model": "JA-AD01A", "region": "EU"},
                {"model": "JA-AD600A", "region": "EU"},
                {"model": "JAAC-WHE-100-EUA1", "region": "EU"},
                {"model": "JA-CA05B", "region": "EU"},
                {"model": "JA-CA3SA", "region": "EU"},
            ],
            build["targets"],
        )
        self.assertEqual(
            ["box_contents*", "disclaimer*", "connection_guide*", "product_overview*"],
            build["web_entry_source_patterns"],
        )
        self.assertEqual(
            "docs/renderers/web/charger_eu_en_{model}_illustrations.json",
            config["paths"]["web_illustration_manifest"],
        )
        self.assertEqual(
            "docs/manifests/manual_charger-eu-en-{model}.yaml",
            config["paths"]["page_manifest"],
        )

    def test_spec_fixture_preserves_source_values_without_invented_totals(self) -> None:
        with (FIXTURE / "Spec_Master.csv").open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))

        self.assertEqual(21, len(rows))
        self.assertEqual({"JA-AD01A_EU"}, {row["document_key"] for row in rows})
        text = "\n".join(
            f'{row["Row_label_source"]} {row["Param_source"]} {row["Value_source"]}'
            for row in rows
        )
        for expected in (
            "100-240V~50/60Hz, 1.8A Max",
            "20V⎓ 5A",
            "20V⎓ 3.25A",
            "5V-11V⎓ 2.7A",
            "20V⎓ 4.35A",
            "USB-C2+USB-A output  5V⎓ 3A",
        ):
            self.assertIn(expected, text)
        self.assertNotIn("Combined", text)
        self.assertNotIn("102W Max", text)
        self.assertTrue(all(not row["Param_source"].endswith(":") for row in rows))

    def test_source_copy_retains_warning_warranty_and_legal_tail(self) -> None:
        warning = (ROOT / "docs" / "templates" / "page_charger" / "en" / "safety_warning.rst").read_text(encoding="utf-8")
        warranty = (ROOT / "docs" / "templates" / "page_charger" / "en" / "warranty.rst").read_text(encoding="utf-8")
        legal = (ROOT / "docs" / "templates" / "page_charger" / "en" / "legal_tail.rst").read_text(encoding="utf-8")

        self.assertEqual(11, warning.count("<li>"))
        self.assertIn("The max ambient temperature should not exceed 25°C.", warning)
        self.assertIn("For indoor use only.", warning)
        self.assertIn("must be paired with a 100W charging cable", warning)
        self.assertIn("24 months from the date of purchase", warranty)
        self.assertIn("hello.eu@jackery.com", warranty)
        self.assertIn("JACKERY TECHNOLOGY GMBH", legal)
        self.assertIn("L LAB CORPORATION (HUIZHOU)LIMITED", legal)
        self.assertNotIn("QR", warning + warranty + legal)

    def test_recipe_and_web_manifest_bind_verified_assets(self) -> None:
        recipe = json.loads(ASSET_RECIPE.read_text(encoding="utf-8"))
        manifest = json.loads(ILLUSTRATION_MANIFEST.read_text(encoding="utf-8"))
        source_hash = "0252cb5db68fb67b3fe0947824de4655e13e26f90b3dde1f6bada3b64aa390fc"
        self.assertEqual(source_hash, recipe["source"]["expected_sha256"])
        self.assertEqual(source_hash, manifest["source_pdf_sha256"])
        quarantined = {
            page["page"]
            for page in recipe["page_catalog"]
            if page["gate"]["status"] == "quarantine"
        }
        self.assertEqual({1, 9}, quarantined)

        registry = load_registry(ROOT / "data" / "asset_registry.csv")
        for asset in recipe["assets"]:
            output = asset["outputs"][0]
            resolution = resolve_asset(
                registry,
                repo_root=ROOT,
                asset_key=asset["asset_key"],
                format_name="png",
                language="en",
                model="JA-AD01A",
                region="EU",
            )
            path = ROOT / resolution.path
            self.assertTrue(path.is_file())
            self.assertEqual(output["expected_sha256"], resolution.declared_hash)
            self.assertEqual(
                output["expected_sha256"],
                hashlib.sha256(path.read_bytes()).hexdigest(),
            )

        self.assertEqual(5, len(manifest["illustrations"]))
        manifest_assets = {
            item["path"]: item["sha256"] for item in manifest["illustrations"]
            if not Path(item["path"]).name.startswith("inbox_")
        }
        self.assertEqual(
            {
                "assets/ja_ad01a_eu_en/product_overview.png": "d05f6b83b300a74601b84d82705d771def9e701682d5bc0fcc22b697a649af7f",
                "assets/ja_ad01a_eu_en/using_product.png": "e72a51b3fe88ee3ec0a029c171935d753daa1d4e45be7765e957dc62aa5b38a8",
            },
            manifest_assets,
        )

    def test_runtime_uses_shared_components_and_all_manifest_assets(self) -> None:
        soup = BeautifulSoup(self.html, "html.parser")
        self.assertEqual(3, len(soup.select(".hb-inbox-card")))
        self.assertIsNotNone(soup.select_one(".hb-inbox-tip"))
        self.assertEqual(4, len(soup.select(".hb-spec-table-composition")))
        self.assertEqual(11, len(soup.select(".manual-callout-body li")))
        self.assertEqual(7, len(self.ir.pages))
        self.assertEqual("box_contents_en.rst", self.ir.pages[0].page_id)
        self.assertEqual("whole-document-components/v1", self.ir.metadata["projection"])
        components = [
            block.payload["component_spec"]["component_id"]
            for page in self.ir.pages for block in page.blocks
            if "component_spec" in block.payload
        ]
        self.assertIn("HB-SPECIAL-INBOX", components)
        self.assertIn("HB-CALLOUT-STRIP", components)
        manifest = json.loads(ILLUSTRATION_MANIFEST.read_text(encoding="utf-8"))
        sources = [str(node.get("src", "")) for node in soup.select("img")]
        self.assertEqual(5, len(sources))
        for entry in manifest["illustrations"]:
            self.assertTrue(any(entry["sha256"] in src for src in sources), entry["path"])
        spec_text = " ".join(node.get_text(" ", strip=True) for node in soup.select(".hb-spec-table-composition"))
        for value in ("20V⎓ 5A", "20V⎓ 3.25A", "20V⎓ 4.35A", "5V-11V⎓ 2.7A", "USB-C2+USB-A output"):
            self.assertIn(value, spec_text)
        self.assertNotIn("102W Max", spec_text)
        for forbidden in ("LCD DISPLAY", "UPS MODE", "APP CONTROL"):
            self.assertNotIn(forbidden, soup.get_text().upper())

    def test_public_ir_cold_replay_reads_no_rst_or_csv(self) -> None:
        script = r'''
from pathlib import Path
from unittest.mock import patch
import sys
original = Path.open
def guarded(path, *args, **kwargs):
    if path.suffix in {".rst", ".csv"} or "contracts" in path.parts:
        raise AssertionError("source read during replay: " + str(path))
    return original(path, *args, **kwargs)
with patch.object(Path, "open", guarded):
    from tools.manual_ir import read_manual_ir
    from tools.web_document_ir import render_document_fragments
    package = Path(sys.argv[1])
    result = render_document_fragments(
        read_manual_ir(package / "manual.ir.json"), package_root=package
    )
    assert len(result) == 7
'''
        subprocess.run(
            [sys.executable, "-c", script, str(self.package)],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

    def test_public_ir_rejects_changed_packaged_asset(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            copied = Path(td) / "package"
            shutil.copytree(self.package, copied)
            ir = read_manual_ir(copied / "manual.ir.json")
            relative = next(iter(ir.metadata["asset_sha256"]))
            (copied / relative).write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "asset missing or changed"):
                render_document_fragments(ir, package_root=copied)



if __name__ == "__main__":
    unittest.main()
