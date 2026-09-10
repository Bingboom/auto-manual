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
FIXTURE = ROOT / "data" / "manual_sources" / "jaac_whe100_eu_en"
SOURCE = ROOT / "manual_sources" / "JAAC-WHE-100-EUA1" / "EU" / "en" / "source.ai"
RECIPE = ROOT / "data" / "asset_recipes" / "manual_jaac_whe100_eu_en_web.json"
ILLUSTRATIONS = (
    ROOT
    / "docs"
    / "renderers"
    / "web"
    / "charger_eu_en_JAAC-WHE-100-EUA1_illustrations.json"
)
SKELETON_DIR = ROOT / "docs" / "manifests" / "skeletons" / "charger-intl"
REGION_PROFILE = ROOT / "docs" / "manifests" / "region_profiles" / "charger-eu-en.yaml"
PRODUCT_PLAN = ROOT / "docs" / "manifests" / "product_plans" / "jaac_whe100_eu.yaml"
SOURCE_MANIFEST = FIXTURE / "source_manifest.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class JaacWhe100EuEnTargetTests(unittest.TestCase):
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
                "JAAC-WHE-100-EUA1",
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
                "JAAC-WHE-100-EUA1 Web fixture build failed:\n"
                + result.stdout
                + result.stderr
            )
        cls.package = (
            cls.staging
            / "docs"
            / "_build"
            / "JAAC-WHE-100-EUA1"
            / "EU"
            / "en"
            / "md"
        )
        cls.ir = read_manual_ir(cls.package / "manual.ir.json")
        cls.html = (cls.package / "manual_bundle.html").read_text(encoding="utf-8")

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def test_accessory_plan_selects_only_source_backed_slots(self) -> None:
        blueprint = load_blueprint(SKELETON_DIR / "blueprint.yaml")
        slots, profiles = load_slot_template_catalog(
            SKELETON_DIR / "slot_templates.yaml", blueprint
        )
        region = load_region_profile(REGION_PROFILE, blueprint)
        product = load_product_plan(PRODUCT_PLAN, blueprint)
        plan = resolve_plan(
            blueprint,
            slots,
            region,
            manifest_id="manual_charger_eu_en_jaac_whe100",
            product_plan=product,
            slot_template_profiles=profiles,
        )
        self.assertEqual(
            ["box_contents_en", "specifications_en", "using_product_en"],
            [page["slot_id"] for page in plan["pages"]],
        )
        serialized = json.dumps(plan).casefold()
        for forbidden in ("warranty", "lcd", "ups", "app", "faq", "installation"):
            self.assertNotIn(forbidden, serialized)

    def test_family_config_has_one_additional_accessory_target(self) -> None:
        config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
        self.assertIn(
            {"model": "JAAC-WHE-100-EUA1", "region": "EU"},
            config["build"]["targets"],
        )
        self.assertEqual("charger-eu-en", config["build"]["family_id"])
        self.assertEqual(
            "docs/manifests/manual_charger-eu-en-{model}.yaml",
            config["paths"]["page_manifest"],
        )

    def test_specs_and_description_notes_preserve_source_copy(self) -> None:
        with (FIXTURE / "Spec_Master.csv").open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(7, len(rows))
        self.assertEqual({"JAAC-WHE-100-EUA1_EU"}, {row["document_key"] for row in rows})
        values = {row["Row_label_source"]: row["Value_source"] for row in rows}
        self.assertEqual("Aluminum Tube + Iron Tube", values["Material"])
        self.assertEqual("80 kg", values["Maximum Load"])
        self.assertEqual("Approx. 94x50x40cm", values["Unfolded Dimensions"])
        self.assertEqual("Approx. 50x50x25cm", values["Folded Dimensions"])
        with (FIXTURE / "Spec_Notes.csv").open(encoding="utf-8", newline="") as handle:
            notes = list(csv.DictReader(handle))
        self.assertEqual(3, len(notes))
        self.assertIn("more than 72 hours", notes[-1]["Text_en"])

    def test_git_source_snapshot_and_same_manual_association_are_locked(self) -> None:
        payload = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(
            "58e84bd618d17b37e67a32a18f987c750756019bfd2e53a8a07b835dc7244694",
            sha256(SOURCE),
        )
        self.assertFalse(payload["authority"]["published_pdf_link_present"])
        self.assertEqual("QKRfBknCr9", payload["authority"]["dingtalk_record"])
        self.assertEqual("e6lR7qNTJd", payload["scope_snapshot"]["same_manual_record"])
        self.assertEqual(sha256(FIXTURE / "scope_snapshot.json"), payload["scope_snapshot"]["sha256"])
        scope = json.loads((FIXTURE / "scope_snapshot.json").read_text(encoding="utf-8"))
        by_id = {row["recordId"]: row for row in scope["rows"]}
        self.assertEqual(["JAAC-WHE-100-EUA1"], by_id["QKRfBknCr9"]["models"])
        self.assertEqual("和折叠小推车 是一样的", by_id["e6lR7qNTJd"]["note"])

        lines = []
        for entry in payload["files"]:
            path = FIXTURE / entry["path"]
            digest = sha256(path)
            self.assertEqual(entry["sha256"], digest)
            lines.append(f"{digest}  {path.name}\n")
        self.assertEqual(
            payload["build_input"]["snapshot_sha256"],
            hashlib.sha256("".join(sorted(lines)).encode()).hexdigest(),
        )
        for path_key, hash_key in (
            ("config", "config_sha256"),
            ("page_manifest", "page_manifest_sha256"),
            ("product_plan", "product_plan_sha256"),
            ("skeleton_blueprint", "skeleton_blueprint_sha256"),
            ("slot_templates", "slot_templates_sha256"),
        ):
            self.assertEqual(
                payload["build_input"][hash_key],
                sha256(ROOT / payload["build_input"][path_key]),
            )

    def test_recipe_registry_manifest_and_cold_ai_replay_match(self) -> None:
        recipe = json.loads(RECIPE.read_text(encoding="utf-8"))
        manifest = json.loads(ILLUSTRATIONS.read_text(encoding="utf-8"))
        self.assertEqual(7, len(recipe["assets"]))
        self.assertEqual(7, len(manifest["illustrations"]))
        self.assertEqual(1, manifest["source_artwork_page_count"])
        self.assertTrue(all(asset["gate"]["status"] == "approved" for asset in recipe["assets"]))

        registry = load_registry(ROOT / "data" / "asset_registry.csv")
        for asset in recipe["assets"]:
            output = asset["outputs"][0]
            resolved = resolve_asset(
                registry,
                repo_root=ROOT,
                asset_key=asset["asset_key"],
                format_name="png",
                language="en",
                model="JAAC-WHE-100-EUA1",
                region="EU",
            )
            self.assertEqual(output["expected_sha256"], resolved.declared_hash)
            self.assertEqual(output["expected_sha256"], sha256(ROOT / resolved.path))

        with tempfile.TemporaryDirectory() as td:
            output_root = Path(td) / "intake"
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "build.py"),
                    "asset-intake",
                    "--asset-source-key",
                    recipe["source"]["source_key"],
                    "--asset-source-file",
                    str(SOURCE),
                    "--asset-recipe",
                    str(RECIPE),
                    "--asset-output-root",
                    str(output_root),
                ],
                cwd=ROOT,
                env={**os.environ, "AUTO_MANUAL_OSS_ARCHIVE_CONFIG": "off"},
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                0,
                result.returncode,
                result.stdout + result.stderr,
            )
            summary = json.loads(result.stdout.split("\n[build.py]", 1)[0])
            self.assertEqual(9, summary["artifact_count"])
            self.assertEqual(
                "c1d13084d540d5e89be546c2dd4a0ba790b2958dc52b89ab62ce5250bc8fc9ed",
                summary["package_sha256"],
            )

    def test_runtime_is_native_and_does_not_duplicate_panel_copy(self) -> None:
        soup = BeautifulSoup(self.html, "html.parser")
        self.assertEqual(3, len(self.ir.pages))
        self.assertEqual(5, len(soup.select(".hb-inbox-card")))
        self.assertEqual(1, len(soup.select(".hb-inbox-tip")))
        self.assertEqual(1, len(soup.select(".hb-spec-table-composition")))
        self.assertEqual(7, len(soup.find_all("img")))
        text = soup.get_text(" ", strip=True)
        for required in (
            "Jackery Foldable Trolley",
            "JAAC-WHE-100-EUA1",
            "Aluminum Tube + Iron Tube",
            "80 kg",
            "more than 72 hours",
            "Wheel Mounting Screws ×10",
        ):
            self.assertIn(required, text)
        for source_owned_or_forbidden in (
            "Remove the main frame",
            "Press this button to retract",
            "JA-ST01A",
            "LCD DISPLAY",
            "UPS MODE",
            "APP CONTROL",
            "WARRANTY",
        ):
            self.assertNotIn(source_owned_or_forbidden, text.upper() if source_owned_or_forbidden.isupper() else text)

    def test_public_ir_cold_replay_reads_no_rst_csv_or_contracts(self) -> None:
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
    assert len(result) == 3
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
