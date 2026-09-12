from __future__ import annotations

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
FIXTURE = ROOT / "data" / "manual_sources" / "ja_ca05b_eu_en"
RECIPE = ROOT / "data" / "asset_recipes" / "manual_ja_ca05b_eu_en_web.json"
ILLUSTRATIONS = (
    ROOT / "docs" / "renderers" / "web" / "charger_eu_en_JA-CA05B_illustrations.json"
)
SKELETON_DIR = ROOT / "docs" / "manifests" / "skeletons" / "charger-intl"
REGION_PROFILE = ROOT / "docs" / "manifests" / "region_profiles" / "charger-eu-en.yaml"
PRODUCT_PLAN = ROOT / "docs" / "manifests" / "product_plans" / "ja_ca05b_eu.yaml"
SOURCE_MANIFEST = FIXTURE / "source_manifest.json"


class JaCa05bEuEnTargetTests(unittest.TestCase):
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
                "JA-CA05B",
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
                "JA-CA05B Web fixture build failed:\n" + result.stdout + result.stderr
            )
        cls.package = cls.staging / "docs" / "_build" / "JA-CA05B" / "EU" / "en" / "md"
        cls.ir = read_manual_ir(cls.package / "manual.ir.json")
        cls.html = (cls.package / "manual_bundle.html").read_text(encoding="utf-8")

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def test_product_plan_selects_only_the_connection_guide(self) -> None:
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
            manifest_id="manual_charger_eu_en_ja_ca05b",
            product_plan=product_plan,
            slot_template_profiles=slot_profiles,
        )
        self.assertEqual(
            ["connection_guide_en"], [page["slot_id"] for page in plan["pages"]]
        )
        self.assertEqual("CHARGER", blueprint["skeleton_family"])

    def test_config_keeps_all_charger_family_targets(self) -> None:
        config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
        self.assertEqual(
            [
                {"model": "JA-AD01A", "region": "EU"},
                {"model": "JA-AD600A", "region": "EU"},
                {"model": "JAAC-WHE-100-EUA1", "region": "EU"},
                {"model": "JA-CA05B", "region": "EU"},
            ],
            config["build"]["targets"],
        )
        self.assertIn("connection_guide*", config["build"]["web_entry_source_patterns"])

    def test_recipe_registry_and_illustration_hashes_match(self) -> None:
        recipe = json.loads(RECIPE.read_text(encoding="utf-8"))
        illustrations = json.loads(ILLUSTRATIONS.read_text(encoding="utf-8"))
        source_hash = "f5359ac0da04a79175531f0b0cbc8a05e5b65d90a6dd653d47f487a101b6dee6"
        self.assertEqual(source_hash, recipe["source"]["expected_sha256"])
        self.assertEqual(source_hash, illustrations["source_pdf_sha256"])
        self.assertEqual(3, len(recipe["assets"]))
        self.assertEqual(3, len(illustrations["illustrations"]))
        self.assertTrue(all(asset["build_eligible"] for asset in recipe["assets"]))
        self.assertTrue(all(asset["gate"]["status"] == "approved" for asset in recipe["assets"]))

        registry = load_registry(ROOT / "data" / "asset_registry.csv")
        manifest_hashes = {
            item["path"]: item["sha256"] for item in illustrations["illustrations"]
        }
        for asset in recipe["assets"]:
            output = asset["outputs"][0]
            resolution = resolve_asset(
                registry,
                repo_root=ROOT,
                asset_key=asset["asset_key"],
                format_name="png",
                language="en",
                model="JA-CA05B",
                region="EU",
            )
            path = ROOT / resolution.path
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(output["expected_sha256"], digest)
            self.assertEqual(output["expected_sha256"], resolution.declared_hash)
            manifest_path = f"assets/ja_ca05b_eu_en/{path.name}"
            self.assertEqual(output["expected_sha256"], manifest_hashes[manifest_path])

    def test_source_snapshot_locks_exact_inputs(self) -> None:
        payload = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual("iQfwYCuoZ7", payload["authority"]["dingtalk_record"])
        self.assertEqual("5M延长线", payload["target"]["delivery_short_name"])
        lines = []
        for entry in payload["files"]:
            path = FIXTURE / entry["path"]
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(entry["sha256"], digest)
            lines.append(f"{digest}  {path.name}\n")
        self.assertEqual(
            payload["build_input"]["snapshot_sha256"],
            hashlib.sha256("".join(sorted(lines)).encode()).hexdigest(),
        )
        for key, path in (
            ("config_sha256", CONFIG),
            ("page_manifest_sha256", ROOT / payload["build_input"]["page_manifest"]),
            ("product_plan_sha256", PRODUCT_PLAN),
        ):
            self.assertEqual(
                payload["build_input"][key], hashlib.sha256(path.read_bytes()).hexdigest()
            )
        self.assertEqual(
            payload["assets"]["recipe_sha256"], hashlib.sha256(RECIPE.read_bytes()).hexdigest()
        )
        self.assertEqual(
            payload["assets"]["illustration_manifest_sha256"],
            hashlib.sha256(ILLUSTRATIONS.read_bytes()).hexdigest(),
        )

    def test_runtime_is_one_semantic_page_with_three_finished_panels(self) -> None:
        soup = BeautifulSoup(self.html, "html.parser")
        self.assertEqual(1, len(self.ir.pages))
        self.assertEqual("whole-document-components/v1", self.ir.metadata["projection"])
        self.assertEqual(1, len(soup.select("table.manual-callout-table")))
        self.assertEqual(3, len(soup.select("img.manual-finished-illustration")))
        self.assertEqual(0, len(soup.select(".hb-spec-table-composition")))
        text = soup.get_text(" ", strip=True)
        self.assertIn("Jackery Solar Generator Connection Guide", text)
        self.assertIn("does not allow current to flow", text)
        for forbidden in ("WHAT'S IN THE BOX", "WARRANTY", "LCD", "UPS", "APP"):
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
    assert len(result) == 1
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
