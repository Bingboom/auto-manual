from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from bs4 import BeautifulSoup
import yaml

from tools.asset_registry import load_registry, resolve_asset
from tools.manual_ir import read_manual_ir
from tools.web_document_ir import render_document_fragments


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "config.solar-eu-en.yaml"
MANIFEST = ROOT / "docs" / "manifests" / "manual_js200e_solar-eu-en.yaml"
SOURCE_ROOT = ROOT / "data" / "manual_sources" / "JS-200E" / "EU" / "en" / "2.0"
DATA_ROOT = SOURCE_ROOT / "phase2"
SOURCE_MANIFEST = SOURCE_ROOT / "source_manifest.json"
RECIPE = ROOT / "data" / "asset_recipes" / "manual_js200e_eu_en_web.json"
ILLUSTRATIONS = ROOT / "docs" / "renderers" / "web" / "js200e_eu_en_illustrations.json"


class SolarJs200eEuTargetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp = tempfile.TemporaryDirectory()
        cls.staging = Path(cls.temp.name) / "staging"
        fake_bin = Path(cls.temp.name) / "bin"
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
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "build.py"),
                "md",
                "--config",
                str(CONFIG),
                "--model",
                "JS-200E",
                "--region",
                "EU",
                "--lang",
                "en",
                "--data-root",
                str(DATA_ROOT),
                "--staging-root",
                str(cls.staging),
            ],
            cwd=ROOT,
            env={
                **os.environ,
                "AUTO_MANUAL_OSS_ARCHIVE_CONFIG": "off",
                "AUTO_MANUAL_PRESENTATION_PROFILE": "web",
                "PATH": str(fake_bin) + os.pathsep + os.environ.get("PATH", ""),
            },
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode:
            raise AssertionError(
                "JS-200E formal Git-source build failed:\n"
                f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            )
        cls.package = cls.staging / "docs" / "_build" / "JS-200E" / "EU" / "en" / "md"
        cls.ir = read_manual_ir(cls.package / "manual.ir.json")
        cls.html = (cls.package / "manual_bundle.html").read_text(encoding="utf-8")
        cls.soup = BeautifulSoup(cls.html, "html.parser")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp.cleanup()

    def test_shared_solar_config_selects_target_manifest_and_art(self) -> None:
        config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
        self.assertIn({"model": "JS-200E", "region": "EU"}, config["build"]["targets"])
        self.assertEqual(
            str(MANIFEST.relative_to(ROOT)),
            config["paths"]["page_manifests"]["JS-200E_EU"],
        )
        self.assertEqual(
            str(ILLUSTRATIONS.relative_to(ROOT)),
            config["paths"]["web_illustration_manifests"]["JS-200E_EU"],
        )
        self.assertNotIn("PRODUCT_NAME", config["build"]["rst_substitutions"])

    def test_manifest_expresses_the_six_source_pages_as_seven_semantic_blocks(self) -> None:
        payload = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual("manual_js200e_solar_eu_en", payload["manifest_id"])
        self.assertEqual(
            [
                "safety_tips_en",
                "box_contents_en",
                "basic_use_en",
                "connector_use_en",
                "angle_and_device_en",
                "specifications_en",
                "warranty_en",
            ],
            [page["slot_id"] for page in payload["pages"]],
        )

    def test_source_snapshot_locks_exact_target_and_every_csv(self) -> None:
        payload = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual("auto-manual-git-source-snapshot/v1", payload["schema_version"])
        self.assertEqual(
            ("JS-200E", "EU", "en", "2.0"),
            tuple(payload["target"][key] for key in ("model", "region", "lang", "version")),
        )
        self.assertEqual(
            "db150930c307590ad45daf236d1ed54ecbe05ca64e92b8b105abf5e058ff0f70",
            payload["authority"]["source_master_sha256"],
        )
        self.assertEqual(6, payload["authority"]["english_panel_page_count"])
        lines: list[str] = []
        for entry in payload["files"]:
            path = SOURCE_ROOT / entry["path"]
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(entry["sha256"], digest, entry["path"])
            self.assertEqual(entry["size"], len(path.read_bytes()), entry["path"])
            lines.append(f"{digest}  {path.name}\n")
        self.assertEqual(
            payload["build_input"]["snapshot_sha256"],
            hashlib.sha256("".join(sorted(lines)).encode()).hexdigest(),
        )

    def test_structured_spec_values_are_source_scoped(self) -> None:
        with (DATA_ROOT / "Spec_Master.csv").open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual({"JS-200E_EU"}, {row["document_key"] for row in rows})
        values = {row["Row_label_source"]: row["Value_source"] for row in rows}
        self.assertEqual("STC*: 200 W ± 5% / BNPI*: 225 W ± 5%", values["Maximum Power (Pₘₐₓ)"])
        self.assertEqual("60 V", values["Maximum System Voltage"])
        self.assertEqual("2279 × 597 × 25 mm", values["Dimensions (unfolded)"])
        self.assertEqual("5 V⎓3 A", values["USB-C Output"])

    def test_recipe_manifest_registry_and_export_hashes_match(self) -> None:
        recipe = json.loads(RECIPE.read_text(encoding="utf-8"))
        manifest = json.loads(ILLUSTRATIONS.read_text(encoding="utf-8"))
        self.assertEqual(recipe["source"]["expected_sha256"], manifest["source_artwork_sha256"])
        self.assertEqual(10, len(recipe["assets"]))
        self.assertEqual(10, len(manifest["illustrations"]))
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
                model="JS-200E",
                region="EU",
            )
            digest = hashlib.sha256((ROOT / resolution.path).read_bytes()).hexdigest()
            self.assertEqual(output["expected_sha256"], resolution.declared_hash)
            self.assertEqual(output["expected_sha256"], digest)

    def test_runtime_uses_shared_semantics_and_exact_source_copy(self) -> None:
        self.assertEqual("manual-ir/v2", self.ir.schema_version)
        self.assertEqual(("JS-200E", "EU", "en"), (self.ir.model, self.ir.region, self.ir.language))
        self.assertEqual(7, len(self.ir.pages))
        self.assertEqual(10, len(self.ir.asset_refs))
        self.assertEqual(10, len(self.soup.find_all("img")))
        self.assertEqual(3, len(self.soup.select(".hb-inbox-card")))
        self.assertEqual(1, len(self.soup.select('[data-component-id="HB-SPECIAL-INBOX"]')))
        self.assertEqual(4, len(self.soup.select(".hb-spec-table-composition")))
        self.assertEqual(1, len(self.soup.select('[data-component-id="HB-WARRANTY-YEARS"]')))
        self.assertEqual(2, len(self.soup.select(".hb-warranty-year-badge")))
        self.assertEqual(2, len(self.soup.select('[data-component-id="HB-WARRANTY-SECTION"]')))
        text = self.soup.get_text(" ", strip=True)
        for required in (
            "Jackery SolarSaga 200",
            "JS-200E",
            "200 W ± 5%",
            "225 W ± 5%",
            "Pₘₐₓ > 70%",
            "IEC TS 63163 Consumer Product Category 2",
            "3 YEARS — Standard Warranty",
            "2 YEARS — Extended Warranty",
            "uk.jackery.com",
        ):
            self.assertIn(required, text)
        for forbidden in ("JS-100I", "SolarSaga 100 Air", "JE-2000F", "2000 Plus", "==MISSING:"):
            self.assertNotIn(forbidden, self.html)
        for forbidden in ("LCD DISPLAY", "UPS MODE", "APP CONTROL"):
            self.assertNotIn(forbidden, text.upper())

    def test_public_ir_cold_replays_without_source_reads(self) -> None:
        relocated = Path(self.temp.name) / "relocated"
        shutil.copytree(self.package, relocated)
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
    rendered = render_document_fragments(
        read_manual_ir(package / "manual.ir.json"), package_root=package
    )
    assert len(rendered) == 7
    assert "Jackery SolarSaga 200" in "".join(rendered)
'''
        subprocess.run(
            [sys.executable, "-c", script, str(relocated)],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

    def test_public_ir_rejects_tampered_art(self) -> None:
        relocated = Path(self.temp.name) / "tampered"
        shutil.copytree(self.package, relocated)
        ir = read_manual_ir(relocated / "manual.ir.json")
        (relocated / ir.asset_refs[0]).write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "asset missing or changed"):
            render_document_fragments(ir, package_root=relocated)


if __name__ == "__main__":
    unittest.main()
