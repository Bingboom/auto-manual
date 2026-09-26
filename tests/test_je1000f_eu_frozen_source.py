from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import unittest

from tools.asset_registry import load_registry, resolve_asset


ROOT = Path(__file__).resolve().parents[1]
FORMAL_SOURCE = ROOT / "manual_sources" / "JE-1000F" / "EU" / "en-fr" / "2.0"
FORMAL_DATA_ROOT = FORMAL_SOURCE / "phase2"
SOURCE_MANIFEST = FORMAL_SOURCE / "source_manifest.json"
APP_PANEL_KEY = "web-composite/je1000f_eu/reference.app-connect-result"
APP_PANEL_SHA256 = "a41b6db31865f5091511b0d8ca830221cf328b45efdb4454fd864dba0132f059"
BLOCK_ART_RECIPE = ROOT / "data" / "asset_recipes" / "manual_je1000f_eu_uk_20260618_block_art.json"
BLOCK_ART_SLOTS = ("in_the_box/main_unit1", "operation/lcd_mode", "operation/ups_mode")


def storage_labels(data_root: Path) -> dict[str, tuple[str, str]]:
    """Line order -> (Param_es, Param_de) of the storage temperature rows."""
    with (data_root / "Spec_Master.csv").open(encoding="utf-8", newline="") as handle:
        return {row["Line_order"]: (row["Param_es"], row["Param_de"])
                for row in csv.DictReader(handle) if row["Row_key"] == "storage_temperature"}


# Each print block's storage durations; the es and de cells were once swapped.
STORAGE_LABELS = {"1": ("1 mes", "1 Monat"), "2": ("3 meses", "3 Monate"), "3": ("12 meses", "12 Monate")}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Je1000fEuFrozenSourceTests(unittest.TestCase):
    def test_source_manifest_locks_every_frozen_input(self) -> None:
        manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(
            "0b4424aff74b3feee08208b1fc0e1d3dde0d2400315ccb72475f6cb2b4d11cfe",
            manifest["authority"]["published_pdf_sha256"],
        )
        for record in manifest["files"]:
            data = (FORMAL_SOURCE / record["path"]).read_bytes()
            self.assertEqual(record["size"], len(data), record["path"])
            self.assertEqual(record["sha256"], hashlib.sha256(data).hexdigest(), record["path"])
        for record in manifest["review_files"]:
            data = (ROOT / record["path"]).read_bytes()
            self.assertEqual(record["size"], len(data), record["path"])
            self.assertEqual(record["sha256"], hashlib.sha256(data).hexdigest(), record["path"])

    def test_every_frozen_phase2_file_is_inventoried(self) -> None:
        manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
        listed = {record["path"] for record in manifest["files"]}
        on_disk = {
            path.relative_to(FORMAL_SOURCE).as_posix()
            for path in FORMAL_DATA_ROOT.rglob("*")
            if path.is_file()
        }
        self.assertEqual(on_disk, listed)

    def test_one_shared_app_panel_serves_all_five_languages(self) -> None:
        composites = json.loads(
            (FORMAL_DATA_ROOT / "web_composite_manifest.json").read_text(encoding="utf-8")
        )["entries"]
        locales: dict[str, set[str]] = {}
        for entry in composites:
            locales.setdefault(entry["web_replace_key"], set()).add(entry["locale"])
        self.assertEqual({"shared"}, locales["reference.app-connect-result"])
        self.assertTrue(
            all(
                found == {"en", "fr", "es", "de", "it"}
                for key, found in locales.items()
                if key != "reference.app-connect-result"
            )
        )

        (panel,) = [entry for entry in composites if entry["asset_key"] == APP_PANEL_KEY]
        self.assertEqual(APP_PANEL_SHA256, panel["content_sha256"])
        self.assertEqual(22, panel["source_page"])
        attachment = FORMAL_DATA_ROOT / panel["path"]
        self.assertEqual(APP_PANEL_SHA256, _sha256(attachment))
        fixture = ROOT / "tests" / "fixtures" / "phase2" / panel["path"]
        self.assertEqual(attachment.read_bytes(), fixture.read_bytes())

        with (ROOT / "data" / "asset_registry.csv").open(encoding="utf-8") as handle:
            registry = {row["asset_key"]: row for row in csv.DictReader(handle)}
        row = registry[APP_PANEL_KEY]
        self.assertEqual(("JE-1000F", "EU", "shared"), (row["适用机型"], row["适用区域"], row["语言变体"]))
        self.assertIn(f"{attachment.name}:{APP_PANEL_SHA256}", row["内容哈希"])

    def test_locked_review_pages_reference_the_reviewed_app_screens(self) -> None:
        """Raw shared paths would bypass je1000f-eu-app-ui-v1 and pull the JP screenshots."""
        manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
        app_setup = []
        for record in manifest["review_files"]:
            if not record["path"].endswith(".rst"):
                continue
            text = (ROOT / record["path"]).read_text(encoding="utf-8")
            for screen in ("add_device", "connect_result"):
                self.assertNotIn(f"common_assets/app/{screen}.png", text, record["path"])
            if "12_app_setup" in record["path"]:
                app_setup.append(record["path"])
                self.assertIn(".. image:: asset:app/add_device\n", text, record["path"])
                self.assertIn(".. image:: asset:app/connect_result\n", text, record["path"])
        # Six language pages plus their six generated drafts.
        self.assertEqual(12, len(app_setup))


    def test_locked_review_pages_resolve_block_art_through_the_registry(self) -> None:
        """Raw shared paths would pull a US-outlet unit and another model's LCD/UPS art."""
        manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
        found = {"inbox": 0, "lcd": 0, "ups": 0}
        for record in manifest["review_files"]:
            path = record["path"]
            if not path.endswith(".rst") or path.endswith("charging.rst"):
                # The charging pages' main_unit1 sits in a JE-2000E-only block.
                continue
            text = (ROOT / path).read_text(encoding="utf-8")
            for shared in ("in_the_box/main_unit1.png", "operation/lcd_mode.png", "operation/ups_mode.png"):
                self.assertNotIn(f"common_assets/{shared}", text, path)
            self.assertNotIn("{main_unit1.png}", text, path)
            self.assertNotIn("{lcd_mode.png}", text, path)
            if "02_whats_in_the_box" in path:
                found["inbox"] += 1
                self.assertIn("\\HBInBoxThree{asset:in_the_box/main_unit1}", text, path)
                self.assertIn(".. image:: asset:in_the_box/main_unit1\n", text, path)
            if "05_operation_guide" in path:
                found["lcd"] += 1
                self.assertIn('<img src="asset:operation/lcd_mode"', text, path)
                self.assertIn("{asset:operation/lcd_mode}", text, path)
            if "06_ups_mode" in path:
                found["ups"] += 1
                self.assertIn(".. image:: asset:operation/ups_mode\n", text, path)
        # Six language pages each; the operation guide also has six generated drafts.
        self.assertEqual({"inbox": 6, "lcd": 12, "ups": 6}, found)

    def test_block_art_overrides_resolve_per_language_to_the_locked_crops(self) -> None:
        """EN takes the English block (BS 1363 sockets); the other languages the French block (EU)."""
        recipe = json.loads(BLOCK_ART_RECIPE.read_text(encoding="utf-8"))
        self.assertEqual(
            manifest_sha := json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))["authority"]["published_pdf_sha256"],
            recipe["source"]["expected_sha256"],
        )
        locked = {
            output["path"]: output["expected_sha256"]
            for asset in recipe["assets"]
            for output in asset["outputs"]
        }
        self.assertEqual(12, len(locked), manifest_sha)
        for path, digest in locked.items():
            self.assertEqual(digest, _sha256(ROOT / path), path)
        records = load_registry(ROOT / "data" / "asset_registry.csv")
        for slot in BLOCK_ART_SLOTS:
            for language in ("en", "fr", "es", "de", "it", "uk"):
                resolved = resolve_asset(
                    records,
                    repo_root=ROOT,
                    asset_key=slot,
                    format_name="png",
                    language=language,
                    model="JE-1000F",
                    region="EU",
                )
                suffix = "_je1000f_eu_en.png" if language == "en" else "_je1000f_eu.png"
                self.assertTrue(resolved.path.endswith(suffix), (slot, language, resolved.path))
                self.assertEqual(locked[resolved.path], resolved.content_hash, (slot, language))
            other = resolve_asset(
                records, repo_root=ROOT, asset_key=slot, format_name="png", language="en", model="JE-2000E", region="EU"
            )
            self.assertEqual(slot, other.asset_key)

    def test_storage_durations_follow_each_print_block(self) -> None:
        """es printed German '1 monat…' and de Spanish '1 mes…' until 2026-09-26."""
        self.assertEqual(STORAGE_LABELS, storage_labels(FORMAL_DATA_ROOT))
        pages = ROOT / "docs/_review/JE-1000F/EU/page"
        spanish = (pages / "p42_09_storage_and_maintenance.rst").read_text(encoding="utf-8")
        german = (pages / "p57_09_storage_and_maintenance.rst").read_text(encoding="utf-8")
        for es, de in STORAGE_LABELS.values():
            self.assertIn(f"- {es}: ", spanish)
            self.assertIn(f"- {de}: ", german)
        self.assertNotIn("monat", spanish.lower())
        self.assertNotIn("- 1 mes:", german)


if __name__ == "__main__":
    unittest.main()
