from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from PIL import Image

from tools.asset_pipeline.recipe import load_recipe


ROOT = Path(__file__).resolve().parents[1]
RECIPE = ROOT / "data" / "asset_recipes" / "manual_je1000f_us_master.json"
EVIDENCE = ROOT / "data" / "asset_evidence" / "app_ui_candidates.json"


class AppUiAssetCandidateTests(unittest.TestCase):
    def test_candidates_are_deterministic_and_remain_quarantined(self) -> None:
        evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        recipe = load_recipe(RECIPE)
        by_key = {asset.asset_key: asset for asset in recipe.assets}

        self.assertEqual("quarantine", evidence["evidence_status"])
        self.assertEqual(5, len(evidence["candidates"]))
        for row in evidence["candidates"]:
            with self.subTest(asset_key=row["asset_key"]):
                asset = by_key[row["asset_key"]]
                output = asset.outputs[0]
                path = ROOT / row["output_path"]

                self.assertEqual("quarantine", asset.gate.status)
                self.assertFalse(asset.build_eligible)
                self.assertTrue(asset.visual_review_required)
                self.assertEqual(("JE-1000F",), asset.scope.models)
                self.assertEqual(("US",), asset.scope.regions)
                self.assertEqual(("en", "fr", "es"), asset.scope.locales)
                self.assertEqual(tuple(row["bbox_pt"]), asset.crop_bbox)
                self.assertEqual(row["output_path"], output.path)
                self.assertEqual(row["output_sha256"], output.expected_sha256)
                self.assertTrue(path.is_file())
                self.assertEqual(
                    row["output_sha256"],
                    hashlib.sha256(path.read_bytes()).hexdigest(),
                )
                with Image.open(path) as image:
                    self.assertEqual(tuple(row["output_dimensions_px"]), image.size)
                self.assertLess(row["page_crop_rgb_mad_normalized"], 0.03)
                self.assertLess(row["changed_pixel_ratio_gt_16"], 0.04)

    def test_candidates_do_not_replace_the_production_app_composites(self) -> None:
        evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))

        for row in evidence["superseded_production_candidates"]:
            with self.subTest(path=row["path"]):
                path = ROOT / row["path"]
                self.assertEqual("ja", row["observed_ui_language"])
                self.assertEqual(
                    row["sha256"],
                    hashlib.sha256(path.read_bytes()).hexdigest(),
                )
        self.assertTrue(all(
            row["output_path"].startswith("data/asset_evidence/app_ui/")
            for row in evidence["candidates"]
        ))


if __name__ == "__main__":
    unittest.main()
