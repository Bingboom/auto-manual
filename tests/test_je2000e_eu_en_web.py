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

from tools.build_paths import resolve_web_illustration_manifest
from tools.manual_ir import read_manual_ir
from tools.web_document_ir import render_document_fragments


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "config.eu-en.yaml"
FORMAL_SOURCE = ROOT / "manual_sources" / "JE-2000E" / "EU" / "en" / "2.0"
FORMAL_DATA_ROOT = FORMAL_SOURCE / "phase2"
SOURCE_MANIFEST = FORMAL_SOURCE / "source_manifest.json"


def storage_labels(data_root: Path) -> dict[str, tuple[str, str]]:
    """Line order -> (Param_es, Param_de) of the storage temperature rows."""
    with (data_root / "Spec_Master.csv").open(encoding="utf-8", newline="") as handle:
        return {row["Line_order"]: (row["Param_es"], row["Param_de"])
                for row in csv.DictReader(handle) if row["Row_key"] == "storage_temperature"}


# Each print block's storage durations; the es and de cells were once swapped.
STORAGE_LABELS = {"1": ("1 mes", "1 Monat"), "2": ("3 meses", "3 Monate"), "3": ("12 meses", "12 Monate")}
ILLUSTRATIONS = ROOT / "docs" / "renderers" / "web" / "je2000e_eu_en_illustrations.json"
APP_RECIPE = ROOT / "data" / "asset_recipes" / "manual_je2000e_eu_web_app.json"
SINGLE_LANGUAGES = ("fr", "es", "de", "it", "uk")
# replaced source image -> (shared panel file, reference id)
APP_PANELS = {
    "add_device.png": ("app_add_device.png", "app-add-device"),
    "connect_result.png": ("app_connect_result.png", "app-connect-result"),
}


def _build_web_package(tmp: Path, *, config: Path, lang: str) -> Path:
    staging = tmp / "staging"
    fake_bin = tmp / "bin"
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
            str(config),
            "--model",
            "JE-2000E",
            "--region",
            "EU",
            "--lang",
            lang,
            "--data-root",
            str(FORMAL_DATA_ROOT),
            "--staging-root",
            str(staging),
        ],
        cwd=ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        raise AssertionError(
            f"JE-2000E/{lang} formal-source Web build failed:\n" + result.stdout + result.stderr
        )
    return staging / "docs" / "_build" / "JE-2000E" / "EU" / lang / "md"


class Je2000eEuStorageLabelTests(unittest.TestCase):
    def test_storage_durations_follow_each_print_block(self) -> None:
        """es printed German '1 monat…' and de Spanish '1 mes…' until 2026-09-26."""
        self.assertEqual(STORAGE_LABELS, storage_labels(FORMAL_DATA_ROOT))


class Je2000eEuEnWebTests(unittest.TestCase):
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
                "JE-2000E",
                "--region",
                "EU",
                "--lang",
                "en",
                "--data-root",
                str(FORMAL_DATA_ROOT),
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
                "JE-2000E formal-source Web build failed:\n"
                + result.stdout
                + result.stderr
            )
        cls.package = cls.staging / "docs" / "_build" / "JE-2000E" / "EU" / "en" / "md"
        cls.ir = read_manual_ir(cls.package / "manual.ir.json")
        cls.html = (cls.package / "manual_bundle.html").read_text(encoding="utf-8")

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def test_frozen_source_matches_current_paper_manual(self) -> None:
        with (FORMAL_DATA_ROOT / "Spec_Master.csv").open(
            encoding="utf-8", newline=""
        ) as handle:
            rows = list(csv.DictReader(handle))
        values = {
            (row["Row_key"], row["Slot_key"], row["Line_order"]): row["Value_source"]
            for row in rows
            if row["document_key"] == "JE-2000E_EU"
        }
        self.assertEqual("About 19.1 kg", values[("weight", "", "1")])
        self.assertEqual("10 ms", values[("ups_transfer_time", "value", "1")])
        self.assertEqual("16 V-60 V", values[("pv_input_range", "value", "1")])
        self.assertEqual("DC8020", values[("dc_input_connector", "value", "1")])
        self.assertEqual(
            "36.8 V-57.6 V⎓75 A max.",
            values[("dc_expansion_input", "", "1")],
        )
        self.assertEqual(
            "36.8 V-57.6 V⎓55 A max.",
            values[("dc_expansion_output", "", "1")],
        )

    def test_specification_ports_match_released_pdf(self) -> None:
        soup = BeautifulSoup(self.html, "html.parser")
        rows = [
            (cell.get_text(" ", strip=True),
             cell.parent.select_one("td").get_text(" ", strip=True))
            for cell in soup.select("th.hb-spec-label")
        ]
        output_start = next(i for i, (label, _) in enumerate(rows)
                            if label == "3 × AC Output")
        outputs = rows[output_start:output_start + 7]
        self.assertEqual(
            [label.rstrip("① ") for label, _ in outputs],
            ["3 × AC Output", "AC Output in Bypass Mode", "1 × USB-A Output",
             "1 × USB-C 30W Output", "1 × USB-C 140W Output",
             "1 × DC 12V Port", "1 × DC Expansion Port"],
        )
        self.assertEqual("230 V~ 50 Hz, 10 A max.", outputs[1][1])
        self.assertTrue(outputs[3][1].startswith("30 W max."))
        self.assertTrue(outputs[4][1].startswith("140 W max."))
        inputs = dict(rows[:output_start])
        self.assertEqual(
            "PV: 16 V-60 V⎓12 A, Double to 21 A / 800 W max. "
            "Car: 11 V-16 V⎓8 A max., Double to 8 A max.",
            inputs["2 × DC8020 Ports"],
        )
        self.assertEqual(2, inputs["1 × AC Input"].count(
            "220 V-240 V~ 50 Hz, 10 A max."))

    def test_source_manifest_locks_every_frozen_input(self) -> None:
        manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
        self.assertFalse(manifest["live_bitable_dependency"])
        self.assertEqual("V2.0-2026-08-03", manifest["authority"]["published_revision"])
        self.assertEqual(
            "734f89ad824d2436d2c79c7ac1231d2dc111dd83ef43e8ee6326674124c396d0",
            manifest["authority"]["published_pdf_sha256"],
        )
        for binding in ("asset_recipe", "app_asset_recipe", "web_illustration_manifest"):
            bound = manifest[binding]
            self.assertEqual(
                bound["sha256"],
                hashlib.sha256((ROOT / bound["path"]).read_bytes()).hexdigest(),
            )
        for record in manifest["files"]:
            data = (FORMAL_SOURCE / record["path"]).read_bytes()
            self.assertEqual(record["size"], len(data))
            self.assertEqual(record["sha256"], hashlib.sha256(data).hexdigest())

    def test_web_output_is_target_isolated_and_complete(self) -> None:
        soup = BeautifulSoup(self.html, "html.parser")
        self.assertEqual(18, len(self.ir.pages))
        self.assertEqual(15, len(soup.select(".manual-finished-illustration")))
        coverage = self.ir.metadata["web_figure_coverage"]
        self.assertEqual(12, coverage["summary"]["total"])
        self.assertEqual(0, coverage["summary"]["by_status"]["missing"])
        self.assertEqual(11, coverage["summary"]["by_status"]["finished-panel"])
        self.assertEqual(1, coverage["summary"]["by_status"]["editable-fallback"])
        self.assertEqual(3, len(soup.select(".hb-inbox-card")))
        self.assertIsNotNone(soup.select_one("figure.hb-lcd-mode-composition"))
        self.assertIsNotNone(soup.select_one("table.hb-lcd-mode-table"))
        for expected in (
            "Jackery Explorer 2000 Plus",
            "About 19.1 kg",
            "6000 cycles to 70%+ capacity",
            "2400 W rated total, 4800 W surge peak",
            "within 10 ms",
            "36.8 V-57.6 V⎓75 A max.",
            "36.8 V-57.6 V⎓55 A max.",
            "support up to 5 battery packs",
            "AC1 Power Button",
            "AC2 Power Button",
            "2011/65/EU",
        ):
            self.assertIn(expected, self.html)
        for forbidden in (
            "JE-2000F",
            "About 18.8 kg",
            "2200 W rated",
            "4000 cycles to 70%+ capacity",
            "|UPS_TRANSFER_TIME|",
            "|PV_INPUT_RANGE|",
            "|DC_INPUT_CONNECTOR|",
        ):
            self.assertNotIn(forbidden, self.html)

    def test_illustrations_are_hash_locked_and_use_source_crops(self) -> None:
        manifest = json.loads(ILLUSTRATIONS.read_text(encoding="utf-8"))
        recipe = json.loads((ROOT / manifest["recipe"]).read_text(encoding="utf-8"))
        self.assertEqual(19, len(recipe["assets"]))
        self.assertEqual(16, len(manifest["illustrations"]))
        output_hashes = {
            output["path"]: output["expected_sha256"]
            for asset in recipe["assets"]
            for output in asset["outputs"]
        }
        for asset in recipe["assets"]:
            self.assertTrue(asset["build_eligible"])
            self.assertFalse(asset["visual_review_required"])
            self.assertEqual("approved", asset["gate"]["status"])
            self.assertEqual([12], [output["scale"] for output in asset["outputs"]])
        for illustration in manifest["illustrations"]:
            path = ILLUSTRATIONS.parent / illustration["path"]
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(illustration["sha256"], digest)
            self.assertEqual(
                digest,
                output_hashes[path.relative_to(ROOT).as_posix()],
            )

    def test_single_language_routes_bind_the_shared_app_panels(self) -> None:
        """The fr/es/de/it/uk blocks of the print place the same App bitmaps."""
        self.assertEqual(
            "a2ba163364d9764a8f61a1be393ff6f0bef5015e22e0c5ad21c981f2f03cae65",
            hashlib.sha256(APP_RECIPE.read_bytes()).hexdigest(),
        )
        app_recipe = json.loads(APP_RECIPE.read_text(encoding="utf-8"))
        self.assertEqual(2, len(app_recipe["assets"]))
        outputs = {}
        for asset in app_recipe["assets"]:
            # App screenshots stay quarantined in their recipe (the App/QR/URL/
            # localized-UI gate); the illustration manifests are their only
            # route onto the page. English keeps its own approved panels.
            self.assertFalse(asset["build_eligible"])
            self.assertTrue(asset["visual_review_required"])
            self.assertEqual("quarantine", asset["gate"]["status"])
            self.assertIn("app-ui", asset["risk_tags"])
            self.assertEqual(list(SINGLE_LANGUAGES), asset["scope"]["locales"])
            (output,) = asset["outputs"]
            self.assertEqual(12, output["scale"])
            outputs[Path(output["path"]).name] = (asset, output)
        for lang in SINGLE_LANGUAGES:
            path = resolve_web_illustration_manifest(
                ROOT / "configs" / f"config.eu-{lang}.yaml",
                repo_root=ROOT,
                model="JE-2000E",
                region="EU",
            )
            self.assertEqual(
                ILLUSTRATIONS.parent / f"je2000e_eu_{lang}_illustrations.json", path, lang
            )
            manifest = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(lang, manifest["language"])
            self.assertEqual(
                sorted(APP_PANELS),
                sorted(item["replaces"][0] for item in manifest["illustrations"]),
                lang,
            )
            for item in manifest["illustrations"]:
                panel_name, reference_id = APP_PANELS[item["replaces"][0]]
                asset, output = outputs[panel_name]
                panel = path.parent / item["path"]
                self.assertEqual(output["path"], panel.relative_to(ROOT).as_posix(), lang)
                self.assertEqual(output["expected_sha256"], item["sha256"], lang)
                self.assertEqual(
                    item["sha256"], hashlib.sha256(panel.read_bytes()).hexdigest(), lang
                )
                self.assertEqual(asset["page"], item["source_page"], lang)
                self.assertEqual(asset["transforms"][0]["bbox_pt"], item["bbox_pt"], lang)
                self.assertEqual(APP_RECIPE.relative_to(ROOT).as_posix(), item["recipe"], lang)
                self.assertTrue(item["consume_before_presentation"], lang)
                self.assertEqual(reference_id, item["reference_id"], lang)

    def test_public_ir_replay_and_tamper_detection(self) -> None:
        fragments = render_document_fragments(self.ir, package_root=self.package)
        self.assertEqual(18, len(fragments))
        with tempfile.TemporaryDirectory() as td:
            copied = Path(td) / "package"
            shutil.copytree(self.package, copied)
            ir = read_manual_ir(copied / "manual.ir.json")
            relative = next(iter(ir.metadata["asset_sha256"]))
            (copied / relative).write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "asset missing or changed"):
                render_document_fragments(ir, package_root=copied)



class Je2000eEuGermanAppPanelTests(unittest.TestCase):
    """The German route shows the print's App screens, not the JP screenshots."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        package = _build_web_package(
            Path(cls._tmp.name), config=ROOT / "configs" / "config.eu-de.yaml", lang="de"
        )
        cls.html = (package / "manual_bundle.html").read_text(encoding="utf-8")

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def test_app_figures_are_the_shared_print_panels(self) -> None:
        soup = BeautifulSoup(self.html, "html.parser")
        for panel_name, reference_id in APP_PANELS.values():
            image = soup.select_one(
                f'img.manual-finished-illustration[data-reference-id="{reference_id}"]'
            )
            self.assertIsNotNone(image, reference_id)
            self.assertEqual(
                f"assets/je2000e_eu_shared/{panel_name}",
                image["data-web-finished-panel-path"],
            )
        self.assertEqual(
            [],
            [
                image["src"]
                for image in soup.find_all("img")
                if Path(str(image.get("src", ""))).name in APP_PANELS
            ],
        )
        # The control-panel button labels and the reference sentence are
        # translated per language, so they stay live text.
        for text in (
            "Haupt-POWER-Taste",
            "AC1-Einschalttaste",
            "AC2-Einschalttaste",
            "DC / USB-Einschalttaste",
            "Die oben gezeigten Screenshots dienen nur als Referenz.",
        ):
            self.assertIn(text, self.html)


if __name__ == "__main__":
    unittest.main()
