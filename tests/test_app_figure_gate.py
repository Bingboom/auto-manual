from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
RECIPES = ROOT / "data" / "asset_recipes"
MANIFESTS = ROOT / "docs" / "renderers" / "web"
# Source images that are App setup figures: store/QR download, add device,
# and the connection result.
APP_SOURCES = {"download.png", "add_device.png", "connect_result.png"}
# The English JE-2000E/EU App panels share files with the open JE-2000E
# add-device change (auto-manual #1258); reclassify them after it merges.
KNOWN_APPROVED = {
    ("je2000e_eu_en_illustrations.json", "assets/je2000e_eu_en/control_panel.png"),
    ("je2000e_eu_en_illustrations.json", "assets/je2000e_eu_en/connect_result.png"),
}


def _recipe_assets() -> dict[str, dict]:
    assets = {}
    for path in sorted(RECIPES.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for asset in data.get("assets", []):
            for output in asset.get("outputs", []):
                assets[output["path"]] = asset
    return assets


class AppFigureGateTests(unittest.TestCase):
    """The recipe gate keys off asset keys and risk tags, so a crop of App UI
    with a neutral key could be approved. Every Web figure that replaces an
    App setup image must therefore resolve to a quarantined recipe asset."""

    def test_manifest_bound_app_figures_are_quarantined(self) -> None:
        assets = _recipe_assets()
        checked, approved = 0, []
        for manifest_path in sorted(MANIFESTS.glob("*_illustrations.json")):
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            for entry in manifest.get("illustrations", []):
                is_app = str(entry.get("reference_id") or "").startswith("app-") or bool(
                    APP_SOURCES & set(entry.get("replaces", []))
                )
                if not is_app:
                    continue
                output = (manifest_path.parent / entry["path"]).resolve().relative_to(ROOT).as_posix()
                self.assertIn(output, assets, f"{manifest_path.name}: {entry['path']} has no recipe")
                checked += 1
                if assets[output]["gate"]["status"] != "quarantine":
                    approved.append((manifest_path.name, entry["path"]))
        self.assertGreaterEqual(checked, 50)
        self.assertEqual([], sorted(set(approved) - KNOWN_APPROVED))


if __name__ == "__main__":
    unittest.main()
