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
FIXTURE = ROOT / "data" / "manual_sources" / "ja_ca3sa_eu_en"
RECIPE = ROOT / "data" / "asset_recipes" / "manual_ja_ca3sa_eu_en_web.json"
ILLUSTRATIONS = (
    ROOT / "docs" / "renderers" / "web" / "charger_eu_en_JA-CA3SA_illustrations.json"
)
SKELETON_DIR = ROOT / "docs" / "manifests" / "skeletons" / "charger-intl"
REGION_PROFILE = ROOT / "docs" / "manifests" / "region_profiles" / "charger-eu-en.yaml"
PRODUCT_PLAN = ROOT / "docs" / "manifests" / "product_plans" / "ja_ca3sa_eu.yaml"
SOURCE_MANIFEST = FIXTURE / "source_manifest.json"
GIT_SOURCE = (
    ROOT
    / "manual_sources"
    / "JA-CA3SA"
    / "EU"
    / "en"
    / "git-20260909-88f1fa0d"
    / "source"
    / "JA-CA3SA-eu-source.ai"
)


def _snapshot_hash(paths: list[Path]) -> str:
    lines = [f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n" for path in paths]
    return hashlib.sha256("".join(sorted(lines)).encode()).hexdigest()


class JaCa3saEuEnTargetTests(unittest.TestCase):
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
                "JA-CA3SA",
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
                "JA-CA3SA Web fixture build failed:\n" + result.stdout + result.stderr
            )
        cls.package = cls.staging / "docs" / "_build" / "JA-CA3SA" / "EU" / "en" / "md"
        cls.ir = read_manual_ir(cls.package / "manual.ir.json")
        cls.html = (cls.package / "manual_bundle.html").read_text(encoding="utf-8")

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def test_product_plan_emits_only_source_supported_accessory_slots(self) -> None:
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
            manifest_id="manual_charger_eu_en_ja_ca3sa",
            product_plan=product_plan,
            slot_template_profiles=slot_profiles,
        )
        self.assertEqual(
            ["product_overview_en", "using_product_en", "warning_en"],
            [page["slot_id"] for page in plan["pages"]],
        )
        serialized = json.dumps(plan).casefold()
        for forbidden in ("specifications", "box_contents", "warranty", "lcd", "ups", "app"):
            self.assertNotIn(forbidden, serialized)

    def test_config_registers_target_without_a_model_specific_config(self) -> None:
        config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
        self.assertIn(
            {"model": "JA-CA3SA", "region": "EU"},
            config["build"]["targets"],
        )
        self.assertEqual(["en"], config["build"]["languages"])
        self.assertEqual(
            "docs/manifests/manual_charger-eu-en-{model}.yaml",
            config["paths"]["page_manifest"],
        )

    def test_structured_source_contains_identity_only_and_no_invented_specs(self) -> None:
        with (FIXTURE / "Spec_Master.csv").open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(2, len(rows))
        self.assertEqual({"JA-CA3SA_EU"}, {row["document_key"] for row in rows})
        self.assertEqual({"identity"}, {row["Page"] for row in rows})
        self.assertEqual(
            {"Solar Generator Connector", "JA-CA3SA"},
            {row["Value_source"] for row in rows},
        )

    def test_git_source_recipe_registry_and_manifest_hashes_match(self) -> None:
        recipe = json.loads(RECIPE.read_text(encoding="utf-8"))
        manifest = json.loads(ILLUSTRATIONS.read_text(encoding="utf-8"))
        source_hash = "88f1fa0dd86fd8e7457b50942be52e2a558acecaf5f9bc70edc9f7dbecd311ab"
        self.assertEqual(source_hash, hashlib.sha256(GIT_SOURCE.read_bytes()).hexdigest())
        self.assertEqual(source_hash, recipe["source"]["expected_sha256"])
        self.assertEqual(source_hash, manifest["source_pdf_sha256"])
        self.assertEqual([8], manifest["excluded_duplicate_pages"])
        self.assertEqual({4, 5, 6, 7}, {item["source_page"] for item in manifest["illustrations"]})
        self.assertEqual(10, len(recipe["assets"]))
        self.assertTrue(all(asset["build_eligible"] for asset in recipe["assets"]))
        self.assertTrue(all(asset["gate"]["status"] == "approved" for asset in recipe["assets"]))

        registry = load_registry(ROOT / "data" / "asset_registry.csv")
        for asset in recipe["assets"]:
            output = asset["outputs"][0]
            resolution = resolve_asset(
                registry,
                repo_root=ROOT,
                asset_key=asset["asset_key"],
                format_name="png",
                language="en",
                model="JA-CA3SA",
                region="EU",
            )
            path = ROOT / resolution.path
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(output["expected_sha256"], resolution.declared_hash)
            self.assertEqual(output["expected_sha256"], digest)

    def test_source_snapshot_locks_git_inputs_and_is_offline_replayable(self) -> None:
        payload = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual("auto-manual-git-source-snapshot/v1", payload["schema_version"])
        self.assertEqual("tQDWZr68hK", payload["authority"]["source_record"])
        self.assertEqual("4-7", payload["authority"]["source_pdf_english_physical_pages"])
        self.assertFalse(payload["online_dependencies"]["dingtalk_read_required_for_reproduction"])
        self.assertFalse(payload["online_dependencies"]["artwork_source_current_location_outside_git"])
        self.assertEqual(payload["git_source"]["size_bytes"], GIT_SOURCE.stat().st_size)
        for path_key, hash_key in (
            ("config", "config_sha256"),
            ("page_manifest", "page_manifest_sha256"),
            ("product_plan", "product_plan_sha256"),
        ):
            path = ROOT / payload["build_input"][path_key]
            self.assertEqual(
                payload["build_input"][hash_key],
                hashlib.sha256(path.read_bytes()).hexdigest(),
            )

        csv_paths = [FIXTURE / entry["path"] for entry in payload["files"]]
        for entry, path in zip(payload["files"], csv_paths, strict=True):
            self.assertEqual(entry["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual(payload["build_input"]["snapshot_sha256"], _snapshot_hash(csv_paths))

        templates = sorted((ROOT / payload["build_input"]["structured_copy"]).glob("*.rst"))
        assets = sorted((ROOT / payload["assets"]["asset_directory"]).glob("*.png"))
        self.assertEqual(
            payload["build_input"]["structured_copy_snapshot_sha256"],
            _snapshot_hash(templates),
        )
        self.assertEqual(payload["assets"]["asset_snapshot_sha256"], _snapshot_hash(assets))
        self.assertEqual(
            payload["assets"]["recipe_sha256"], hashlib.sha256(RECIPE.read_bytes()).hexdigest()
        )
        self.assertEqual(
            payload["assets"]["illustration_manifest_sha256"],
            hashlib.sha256(ILLUSTRATIONS.read_bytes()).hexdigest(),
        )

    def test_runtime_is_native_three_page_web_manual_with_all_assets(self) -> None:
        soup = BeautifulSoup(self.html, "html.parser")
        self.assertEqual(3, len(self.ir.pages))
        self.assertEqual(10, len(soup.find_all("img")))
        self.assertEqual(1, len(soup.select(".manual-callout-table, .hb-callout-strip")))
        self.assertEqual(0, len(soup.select(".hb-inbox-card")))
        self.assertEqual("Solar Generator Connector User Manual", soup.title.get_text(strip=True))
        text = soup.get_text(" ", strip=True)
        for expected in (
            "FUNCTIONS OF MAIN PORTS",
            "DC8020 male",
            "keep the switch OFF",
            "HOW TO USE",
            "Connection Operation Instructions",
            "SOLAR PANELS CONNECTION GUIDE",
            "CAUTION",
            "inconsistent voltages",
        ):
            self.assertIn(expected, text)
        for forbidden in ("SPECIFICATIONS", "WHAT'S IN THE BOX", "WARRANTY", "LCD DISPLAY", "UPS MODE", "APP CONTROL"):
            self.assertNotIn(forbidden, text.upper())
        manifest = json.loads(ILLUSTRATIONS.read_text(encoding="utf-8"))
        sources = [str(node.get("src", "")) for node in soup.find_all("img")]
        for entry in manifest["illustrations"]:
            self.assertTrue(any(entry["sha256"] in src for src in sources), entry["path"])

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
