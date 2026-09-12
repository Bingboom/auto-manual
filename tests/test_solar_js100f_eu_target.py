from __future__ import annotations

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

from tools.manual_ir import read_manual_ir
from tools.web_document_ir import render_document_fragments


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "config.solar-eu-en.yaml"
MANIFEST = ROOT / "docs" / "manifests" / "manual_solar-eu-en-JS-100F.yaml"
ILLUSTRATIONS = ROOT / "docs" / "renderers" / "web" / "js100f_eu_en_illustrations.json"
SOURCE_ROOT = ROOT / "data" / "manual_sources" / "JS-100F" / "EU" / "en" / "1.0"
DATA_ROOT = SOURCE_ROOT / "phase2"
SOURCE_MANIFEST = SOURCE_ROOT / "source_manifest.json"


class SolarJs100fEuTargetTests(unittest.TestCase):
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
                "JS-100F",
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
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode:
            raise AssertionError(
                "JS-100F formal Git-source build failed:\n"
                f"stdout:\n{result.stdout}\n"
                f"stderr:\n{result.stderr}"
            )
        cls.package = cls.staging / "docs" / "_build" / "JS-100F" / "EU" / "en" / "md"
        cls.ir = read_manual_ir(cls.package / "manual.ir.json")
        cls.markdown = (cls.package / "manual_js100f_eu_en.md").read_text(encoding="utf-8")
        cls.html = (cls.package / "manual_bundle.html").read_text(encoding="utf-8")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp.cleanup()

    def test_shared_config_selects_target_manifest_and_illustrations(self) -> None:
        config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
        self.assertIn({"model": "JS-100F", "region": "EU"}, config["build"]["targets"])
        self.assertEqual(
            "docs/manifests/manual_solar-eu-en-JS-100F.yaml",
            config["paths"]["page_manifests"]["JS-100F_EU"],
        )
        self.assertEqual(
            "docs/renderers/web/js100f_eu_en_illustrations.json",
            config["paths"]["web_illustration_manifests"]["JS-100F_EU"],
        )

    def test_source_manifest_locks_every_input_and_asset_contract(self) -> None:
        payload = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual("auto-manual-git-source-snapshot/v1", payload["schema_version"])
        self.assertEqual(
            ("JS-100F", "EU", "en", "1.0"),
            tuple(payload["target"][field] for field in ("model", "region", "lang", "version")),
        )
        self.assertEqual(
            "2074ddc390cf0e218a94a6ad267721c6f85cb5a34a29c96e45093791602f8952",
            payload["authority"]["source_master_sha256"],
        )
        inventory: list[str] = []
        for entry in payload["files"]:
            source = SOURCE_ROOT / entry["path"]
            data = source.read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            self.assertEqual(entry["size"], len(data), entry["path"])
            self.assertEqual(entry["sha256"], digest, entry["path"])
            if source.suffix == ".csv":
                inventory.append(f"{digest}  {source.name}\n")
        self.assertEqual(
            payload["build_input"]["snapshot_sha256"],
            hashlib.sha256("".join(sorted(inventory)).encode()).hexdigest(),
        )
        self.assertEqual(
            payload["assets"]["recipe_sha256"],
            hashlib.sha256((ROOT / payload["assets"]["recipe"]).read_bytes()).hexdigest(),
        )
        self.assertEqual(
            payload["assets"]["illustration_manifest_sha256"],
            hashlib.sha256(
                (ROOT / payload["assets"]["illustration_manifest"]).read_bytes()
            ).hexdigest(),
        )
        self.assertFalse(any(payload["online_dependencies"].values()))

    def test_manual_order_and_source_backed_scope(self) -> None:
        self.assertEqual("manual-ir/v2", self.ir.schema_version)
        self.assertEqual("JS-100F", self.ir.model)
        self.assertEqual("EU", self.ir.region)
        self.assertEqual("en", self.ir.language)
        self.assertEqual(
            [
                "specifications_en.rst",
                "safety_tips_en.rst",
                "how_to_use_en.rst",
                "sun_angle_indicator_en.rst",
                "power_your_device_en.rst",
                "warranty_en.rst",
            ],
            [page.page_id for page in self.ir.pages],
        )
        for forbidden in (
            "JS-100I",
            "SolarSaga 100 Air",
            "LCD DISPLAY",
            "UPS MODE",
            "APP CONTROL",
            "WHAT'S IN THE BOX",
            "==MISSING:",
        ):
            self.assertNotIn(forbidden, self.markdown)

    def test_semantic_specs_notes_warnings_and_warranty_are_preserved(self) -> None:
        for required in (
            "Jackery SolarSaga 100",
            "STC*: 100 W ± 5 W / BNPI*: 104 W ± 5 W",
            "-20°C to 65°C (-4°F to 149°F)",
            "IEC TS 63163 Consumer Product Category 2",
            "design load is 1600 Pa",
            "multiply the short-circuit current (Iₛ꜀) and open-circuit voltage (Vₒ꜀)",
            "DC8020-DC7909 adapter",
            "3 YEARS — Limited Warranty",
            "36 months",
            "2 YEARS — Extended Warranty",
            "hello.eu@jackery.com",
        ):
            self.assertIn(required, self.markdown)
        soup = BeautifulSoup(self.html, "html.parser")
        self.assertEqual(3, len(soup.select("table.manual-spec-table")))
        notes = soup.select("table.manual-callout-table")
        self.assertEqual(3, len(notes))
        self.assertTrue(
            all(note.select_one(".manual-callout-label").get_text(strip=True) == "NOTE" for note in notes)
        )
        self.assertEqual(4, len(soup.select("img.manual-finished-illustration")))

    def test_illustration_manifest_binds_exact_source_crops_and_hashes(self) -> None:
        payload = json.loads(ILLUSTRATIONS.read_text(encoding="utf-8"))
        self.assertEqual(
            ("JS-100F", "EU", "en"),
            (payload["model"], payload["region"], payload["language"]),
        )
        self.assertEqual([1712, 600, 2861, 1120], payload["english_panel_bbox_pt"])
        self.assertEqual(4, len(payload["illustrations"]))
        self.assertEqual(4, len(self.ir.asset_refs))
        for entry in payload["illustrations"]:
            asset = ILLUSTRATIONS.parent / entry["path"]
            self.assertEqual(entry["sha256"], hashlib.sha256(asset.read_bytes()).hexdigest())

    def test_public_ir_cold_replays_without_rst_or_csv_reads(self) -> None:
        relocated = Path(self.temp.name) / "relocated"
        shutil.copytree(self.package, relocated)
        script = r'''
from pathlib import Path
from unittest.mock import patch
import sys
original = Path.open
def guarded(path, *args, **kwargs):
    if path.suffix in {".rst", ".csv"}:
        raise AssertionError("source read during replay: " + str(path))
    return original(path, *args, **kwargs)
with patch.object(Path, "open", guarded):
    from tools.manual_ir import read_manual_ir
    from tools.web_document_ir import render_document_fragments
    package = Path(sys.argv[1])
    rendered = render_document_fragments(
        read_manual_ir(package / "manual.ir.json"), package_root=package
    )
    assert len(rendered) == 6
    assert "Jackery SolarSaga 100" in "".join(rendered)
'''
        subprocess.run(
            [sys.executable, "-c", script, str(relocated)],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

    def test_public_ir_fails_closed_when_packaged_art_changes(self) -> None:
        relocated = Path(self.temp.name) / "tampered"
        shutil.copytree(self.package, relocated)
        ir = read_manual_ir(relocated / "manual.ir.json")
        (relocated / ir.asset_refs[0]).write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "asset missing or changed"):
            render_document_fragments(ir, package_root=relocated)


if __name__ == "__main__":
    unittest.main()
