from __future__ import annotations

import hashlib
import json
import struct
import unittest
from pathlib import Path

from tools.asset_pipeline.recipe import load_recipe


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "data" / "asset_evidence" / "back_cover_qr_candidates.json"
RECIPE = ROOT / "data" / "asset_recipes" / "manual_je1000f_us_master.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class BackCoverQrCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def test_two_sources_have_explicit_conflicting_payloads(self) -> None:
        self.assertEqual("quarantine", self.evidence["evidence_status"])
        self.assertEqual(
            "unresolved-source-mismatch",
            self.evidence["decision"]["status"],
        )
        candidates = self.evidence["candidates"]
        self.assertEqual(2, len(candidates))
        self.assertEqual(
            {"160102000404", "160102000161"},
            {candidate["decoded_payload"] for candidate in candidates},
        )
        self.assertEqual(
            {59, 58},
            {candidate["page"] for candidate in candidates},
        )
        for candidate in candidates:
            with self.subTest(asset_key=candidate["asset_key"]):
                self.assertEqual(64, len(candidate["source_sha256"]))
                self.assertEqual(1, candidate["qr_contract"]["version"])
                self.assertEqual("L", candidate["qr_contract"]["error_correction"])
                self.assertEqual(2, candidate["qr_contract"]["data_mask"])
                self.assertEqual("byte", candidate["qr_contract"]["encoding_mode"])
                self.assertEqual(21, candidate["verification"]["matrix_size"])
                self.assertEqual(0, candidate["verification"]["matrix_mismatches"])

    def test_candidate_exports_are_hash_bound_qr_only_files(self) -> None:
        for candidate in self.evidence["candidates"]:
            for output in candidate["outputs"]:
                with self.subTest(asset_key=candidate["asset_key"], path=output["path"]):
                    path = ROOT / output["path"]
                    self.assertTrue(path.is_file())
                    self.assertEqual(output["sha256"], _sha256(path))
                    self.assertNotIn("back_cover-en", path.name)
                    if output["format"] == "png":
                        data = path.read_bytes()
                        self.assertEqual(b"\x89PNG\r\n\x1a\n", data[:8])
                        width, height = struct.unpack(">II", data[16:24])
                        self.assertEqual(
                            (output["width_px"], output["height_px"]),
                            (width, height),
                        )
                        self.assertLess(width, 300)
                        self.assertLess(height, 300)

    def test_design_master_recipe_owns_only_its_candidate(self) -> None:
        recipe = load_recipe(RECIPE)
        by_key = {asset.asset_key: asset for asset in recipe.assets}
        candidate = by_key["qr/back_cover_ai_candidate"]
        self.assertEqual("quarantine", candidate.gate.status)
        self.assertFalse(candidate.build_eligible)
        self.assertTrue(candidate.visual_review_required)
        self.assertNotIn("qr/back_cover_reference_candidate", by_key)
        evidence = {
            row["asset_key"]: row for row in self.evidence["candidates"]
        }[candidate.asset_key]
        self.assertEqual(evidence["bbox_pt"], list(candidate.crop_bbox))
        self.assertEqual(
            {output["sha256"] for output in evidence["outputs"]},
            {output.expected_sha256 for output in candidate.outputs},
        )


if __name__ == "__main__":
    unittest.main()
