from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
FORMAL_SOURCE = ROOT / "manual_sources" / "JE-1000F" / "EU" / "en-fr" / "2.0"
FORMAL_DATA_ROOT = FORMAL_SOURCE / "phase2"
SOURCE_MANIFEST = FORMAL_SOURCE / "source_manifest.json"
APP_PANEL_KEY = "web-composite/je1000f_eu/reference.app-connect-result"
APP_PANEL_SHA256 = "a41b6db31865f5091511b0d8ca830221cf328b45efdb4454fd864dba0132f059"


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


if __name__ == "__main__":
    unittest.main()
