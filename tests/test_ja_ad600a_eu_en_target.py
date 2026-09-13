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

from tools.asset_registry import load_registry, resolve_asset
from tools.manual_ir import read_manual_ir
from tools.skeleton_resolve import (
    load_blueprint,
    load_product_plan,
    load_region_profile,
    load_slot_template_catalog,
    resolve_plan,
)
from tools.web_document_ir import render_document_fragments


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "config.charger-eu-en.yaml"
FIXTURE = ROOT / "data" / "manual_sources" / "ja_ad600a_eu_en"
RECIPE = ROOT / "data" / "asset_recipes" / "manual_ja_ad600a_eu_en_web.json"
ILLUSTRATIONS = (
    ROOT / "docs" / "renderers" / "web" / "charger_eu_en_JA-AD600A_illustrations.json"
)
SKELETON_DIR = ROOT / "docs" / "manifests" / "skeletons" / "charger-intl"
REGION_PROFILE = ROOT / "docs" / "manifests" / "region_profiles" / "charger-eu-en.yaml"
PRODUCT_PLAN = ROOT / "docs" / "manifests" / "product_plans" / "ja_ad600a_eu.yaml"
SOURCE_MANIFEST = FIXTURE / "source_manifest.json"


class JaAd600aEuEnTargetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        cls.staging = Path(cls._tmp.name) / "staging"
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
            "AUTO_MANUAL_OSS_ARCHIVE_CONFIG": "off",
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
                "JA-AD600A",
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
            raise AssertionError(
                "JA-AD600A Web fixture build failed:\n" + result.stdout + result.stderr
            )
        cls.package = (
            cls.staging / "docs" / "_build" / "JA-AD600A" / "EU" / "en" / "md"
        )
        cls.ir = read_manual_ir(cls.package / "manual.ir.json")
        cls.html = (cls.package / "manual_bundle.html").read_text(encoding="utf-8")

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def test_product_plan_selects_only_dc_dc_charger_slots(self) -> None:
        blueprint = load_blueprint(SKELETON_DIR / "blueprint.yaml")
        slots, slot_profiles = load_slot_template_catalog(
            SKELETON_DIR / "slot_templates.yaml", blueprint
        )
        profile = load_region_profile(REGION_PROFILE, blueprint)
        product_plan = load_product_plan(PRODUCT_PLAN, blueprint)
        plan = resolve_plan(
            blueprint,
            slots,
            profile,
            manifest_id="manual_charger_eu_en_ja_ad600a",
            product_plan=product_plan,
            slot_template_profiles=slot_profiles,
        )
        self.assertEqual(
            [
                "disclaimer_en",
                "specifications_en",
                "dimensions_en",
                "box_contents_en",
                "product_overview_en",
                "important_safety_en",
                "faq_en",
                "installation_en",
                "warranty_en",
            ],
            [page["slot_id"] for page in plan["pages"]],
        )
        serialized = json.dumps(plan)
        for forbidden in ("lcd", "ups", "app"):
            self.assertNotIn(forbidden, serialized.casefold())

    def test_spec_source_preserves_the_pdf_values(self) -> None:
        with (FIXTURE / "Spec_Master.csv").open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(13, len(rows))
        self.assertEqual({"JA-AD600A_EU"}, {row["document_key"] for row in rows})
        values = {row["Row_label_source"]: row["Value_source"] for row in rows}
        self.assertEqual("11.8V–32V⎓, 60A", values["DC Input"])
        self.assertEqual("50V⎓", values["Output Voltage"])
        self.assertEqual("12A Max", values["Output Current"])
        self.assertEqual("600W Max", values["Output Power"])
        self.assertEqual("IP40", values["Protection Rating"])
        self.assertEqual("259 × 154.5 × 39.3 mm", values["Dimensions"])

    def test_approved_recipe_registry_and_manifest_hashes_match(self) -> None:
        recipe = json.loads(RECIPE.read_text(encoding="utf-8"))
        manifest = json.loads(ILLUSTRATIONS.read_text(encoding="utf-8"))
        source_pdf_hash = "72da87b9a88f3029a144f11f44fd1270e6e991977cf5ca3deb6be53656e544d9"
        artwork_hash = "d89f145176c0c8ca10fa8c81768718ee32d52cb7a41a17b318df559a38e4f385"
        self.assertEqual(artwork_hash, recipe["source"]["expected_sha256"])
        self.assertEqual(source_pdf_hash, manifest["source_pdf_sha256"])
        self.assertEqual(artwork_hash, manifest["source_artwork_sha256"])
        self.assertEqual(15, manifest["source_artwork_page_count"])
        self.assertEqual(16, len(recipe["assets"]))
        self.assertEqual(16, len(manifest["illustrations"]))
        self.assertTrue(all(asset["build_eligible"] for asset in recipe["assets"]))
        self.assertTrue(all(asset["gate"]["status"] == "approved" for asset in recipe["assets"]))
        self.assertEqual(
            4,
            sum(
                any(transform["op"] == "redact_text" for transform in asset["transforms"])
                for asset in recipe["assets"]
            ),
        )

        registry = load_registry(ROOT / "data" / "asset_registry.csv")
        for asset in recipe["assets"]:
            output = asset["outputs"][0]
            resolution = resolve_asset(
                registry,
                repo_root=ROOT,
                asset_key=asset["asset_key"],
                format_name="png",
                language="en",
                model="JA-AD600A",
                region="EU",
            )
            path = ROOT / resolution.path
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(output["expected_sha256"], resolution.declared_hash)
            self.assertEqual(output["expected_sha256"], digest)

    def test_source_snapshot_locks_exact_pdf_and_git_inputs(self) -> None:
        payload = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual("auto-manual-git-source-snapshot/v1", payload["schema_version"])
        self.assertEqual("Gl6Pm2Db8D39waXaU9LzewOeJxLq0Ee4", payload["authority"]["dingtalk_node"])
        self.assertEqual("4-17", payload["authority"]["source_pdf_english_physical_pages"])
        lines = []
        for entry in payload["files"]:
            path = FIXTURE / entry["path"]
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(entry["sha256"], digest)
            lines.append(f"{digest}  {path.name}\n")
        snapshot = hashlib.sha256("".join(sorted(lines)).encode()).hexdigest()
        self.assertEqual(payload["build_input"]["snapshot_sha256"], snapshot)

        recipe_hash = hashlib.sha256(RECIPE.read_bytes()).hexdigest()
        illustration_hash = hashlib.sha256(ILLUSTRATIONS.read_bytes()).hexdigest()
        self.assertEqual(payload["assets"]["recipe_sha256"], recipe_hash)
        self.assertEqual(
            payload["assets"]["illustration_manifest_sha256"], illustration_hash
        )

    def test_runtime_has_native_copy_and_complete_finished_figures(self) -> None:
        soup = BeautifulSoup(self.html, "html.parser")
        self.assertEqual(9, len(self.ir.pages))
        self.assertEqual(9, len(soup.select(".hb-inbox-card")))
        self.assertEqual(1, len(soup.select(".hb-spec-table-composition")))
        self.assertEqual(5, len(soup.select(".hb-operation-figure")))
        self.assertEqual(5, len(soup.select('[data-component-id="HB-SPECIAL-OPERATION"]')))
        self.assertEqual(1, len(soup.select('[data-component-id="HB-WARRANTY-YEARS"]')))
        self.assertEqual(5, len(soup.select('[data-component-id="HB-WARRANTY-SECTION"]')))
        self.assertEqual(2, len(soup.select(".manual-callout-table, .hb-callout-strip")))
        self.assertEqual(16, len(soup.find_all("img")))

        coverage = self.ir.metadata["web_figure_coverage"]
        operation = coverage["summary"]["by_section"]["operation"]
        self.assertEqual(5, operation["total"])
        self.assertEqual(5, operation["by_status"]["finished-panel"])
        self.assertEqual(0, operation["by_status"]["editable-fallback"])
        self.assertEqual(0, operation["by_status"]["missing"])

        text = soup.get_text(" ", strip=True)
        for required in (
            "11.8V–32V⎓, 60A",
            "600W Max",
            "Explorer 3000 v2",
            "2 YEARS",
            "3–4 N·m",
        ):
            self.assertIn(required, text)
        for forbidden in ("LCD DISPLAY", "UPS MODE", "APP CONTROL"):
            self.assertNotIn(forbidden, text.upper())

    def test_public_ir_cold_replay_reads_no_rst_csv_or_contract(self) -> None:
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
    assert len(result) == 9
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
