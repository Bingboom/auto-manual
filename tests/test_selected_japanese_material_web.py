"""Keep the seven operator-selected Japanese attachments and variants distinct."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest

import fitz

from tools.utils.path_utils import PathSegments

ROOT = Path(__file__).resolve().parents[1]
# Attachment identities read back from the publishing Base on2026-11-12.
# Material000348 is intentionally excluded by the operator's later selection.
CASES = (
    ('38-0001-000512', 'JSG-0304B', 'git-20261112-fe9f1b56-m000512', 'fe9f1b561a9f75af52e1af738f9da00492302a55f43ddc0122e366744fb9e452', 20),
    ('38-0001-000491', 'JSG-2404A', 'git-20261112-e59cc1bc-m000491', 'e59cc1bc778eb5cea4ec0b77f3d3598d2703dc94a809108c8b4336709519bdb7', 20),
    ('38-0001-000464', 'JS-40A', 'git-20261112-1a96bf34-m000464', '1a96bf348255cc47caf18b3df296ced0ccbc28269b1863c442e9e98d8d631b4c', 28),
    ('38-0001-000034', 'PTB021', 'git-20261112-c1f0f04e-material-web', 'c1f0f04e5ee672bb1c82f3d0b5ca009dc4459db3a6152d74a96acd489caff67c', 12),
    ('38-0001-000035', 'PTB041', 'git-20261112-1fc3e6ff-material-web', '1fc3e6fffee4d29b3c6ecba999def59a9526722af8c2dfb87025254a62a743ef', 12),
    ('38-0001-000036', 'PTB071', 'git-20261112-ab6bd123-material-web', 'ab6bd12341101e45dbb6b57f03132bc8b55a6ecb57533c282ec9779c2c5b9ba3', 12),
    ('38-0001-000027', 'BN-RB15', 'git-20261112-f2421529-material-web', 'f24215296cf4a3544d48dbbce5df3c6cf489ec829ad4b2a192926d94afaff670', 16),
)


def package_path(model: str, version: str) -> Path:
    return ROOT / PathSegments.MANUAL_SOURCES / model / "JP" / "ja" / version


def manifest_at(package: Path) -> dict:
    return json.loads((package / "source_manifest.json").read_text(encoding="utf-8"))


class SelectedJapaneseAttachmentTests(unittest.TestCase):
    def test_each_material_keeps_its_authoritative_attachment_and_target(self) -> None:
        self.assertEqual(len(CASES), 7)
        self.assertNotIn("38-0001-000348", [case[0] for case in CASES])
        for material, model, version, digest, pages in CASES:
            with self.subTest(material=material):
                package = package_path(model, version)
                manifest = manifest_at(package)
                self.assertEqual(manifest["target"]["model"], model)
                self.assertEqual(manifest["target"]["region"], "JP")
                self.assertEqual(manifest["target"]["languages"], ["ja"])
                self.assertEqual(manifest["language_scope"], "single")
                original = manifest["original_source"]
                self.assertEqual(original["sha256"], digest)
                self.assertEqual(original["physical_page_count"], pages)
                original_path = package / original.get("path", original["filename"])
                self.assertTrue(original_path.resolve().is_relative_to(package.resolve()))
                self.assertEqual(hashlib.sha256(original_path.read_bytes()).hexdigest(), digest)

    def test_a_web_candidate_cannot_silently_gain_release_approval(self) -> None:
        for material, model, version, digest, _ in CASES:
            with self.subTest(material=material):
                package = package_path(model, version)
                manifest = manifest_at(package)
                approval = package / "source" / "approval.json"
                if manifest["publication_status"] == "review-candidate-no-release-authorization":
                    self.assertFalse(manifest["publication_eligible"])
                    self.assertFalse(approval.exists())
                else:
                    accepted = json.loads(approval.read_text(encoding="utf-8"))
                    self.assertTrue(accepted.get("operator_quote"))
                    self.assertEqual(accepted["original_source_sha256"], digest)
                    self.assertEqual(accepted["target"]["model"], model)

    def test_standalone_recycling_marks_reuse_the_shared_canonical(self) -> None:
        library = ROOT / "docs" / "renderers" / "web" / "assets" / "shared" / "symbols"
        catalog = json.loads((library / "manifest.json").read_text(encoding="utf-8"))
        group = next(row for row in catalog["canonical_groups"] if row["id"] == "li-ion")
        self.assertEqual(group["status"], "operator-confirmed")
        canonical = next(row for row in catalog["assets"] if row["key"] == group["canonical"])
        shared_bytes = (library / canonical["path"]).read_bytes()
        self.assertEqual(hashlib.sha256(shared_bytes).hexdigest(), canonical["sha256"])
        for material, model, version, _, _ in CASES:
            if model not in {"PTB021", "PTB041", "PTB071", "BN-RB15"}:
                continue
            with self.subTest(material=material):
                web = package_path(model, version) / "web" / "ja"
                art = web / "assets" / "recycle.svg"
                self.assertEqual(art.read_bytes(), shared_bytes)
                with fitz.open(art) as document:
                    pixels = document[0].get_pixmap(matrix=fitz.Matrix(2, 2), alpha=True)
                    self.assertEqual(pixels.n, 4)
                    self.assertEqual((min(pixels.samples[3::4]), max(pixels.samples[3::4])), (0, 255))
                markdown = web / ("manual_" + model.replace("-", "").lower() + "_jp_ja.md")
                self.assertIn("recycle.svg", markdown.read_text(encoding="utf-8"))

    def test_solar_variant_dimensions_do_not_bleed_across_materials(self) -> None:
        expected = {
            "38-0001-000512": ("source/ja/content.json", "970*300*2.5mm"),
            "38-0001-000491": ("source/ja/content.json", "1020*300*18.5mm"),
            "38-0001-000464": ("source/content.json", "1020*300*18.5mm"),
        }
        for material, model, version, _, _ in CASES:
            if material not in expected:
                continue
            with self.subTest(material=material):
                filename, dimensions = expected[material]
                raw = (package_path(model, version) / filename).read_text(encoding="utf-8")
                compact = "".join(raw.split())
                self.assertIn(dimensions, compact)
                if material in {"38-0001-000491", "38-0001-000464"}:
                    self.assertNotIn("消費財タイプ1", compact)
                if material == "38-0001-000491":
                    self.assertNotIn("20ms", compact.lower())
                    self.assertNotRegex(compact, r"OFF[（(]dispalyに")
                if material in {"38-0001-000512", "38-0001-000491"}:
                    self.assertNotIn("詳細は、『機器共有』をご参照ください。", compact)
                if material in {"38-0001-000512", "38-0001-000491"}:
                    self.assertNotIn("600Plus", compact)
                    self.assertNotIn("45℃以上", compact)
                    self.assertNotIn("45°C以上", compact)


class ApprovedJapaneseReleaseTests(unittest.TestCase):
    def test_release_snapshots_keep_candidates_and_bind_every_input(self) -> None:
        for material, model, version, digest, _ in CASES:
            with self.subTest(material=material):
                candidate = package_path(model, version)
                release = package_path(model, version + "-release")
                manifest = manifest_at(release)
                self.assertFalse(manifest_at(candidate)["publication_eligible"])
                self.assertTrue(manifest["publication_eligible"])
                self.assertFalse(manifest["pending_source_review"])
                self.assertEqual(manifest["original_source"]["sha256"], digest)
                approval = json.loads((release / "source" / "approval.json").read_text())
                self.assertEqual(approval["original_source_sha256"], digest)
                self.assertEqual(approval["reviewed_candidate"]["manifest_sha256"],
                                 hashlib.sha256((candidate / "source_manifest.json").read_bytes()).hexdigest())
                for row in manifest["inputs"]:
                    self.assertEqual(hashlib.sha256((release / row["path"]).read_bytes()).hexdigest(),
                                     row["sha256"], row["path"])

    def test_old_power_station_symbol_tables_have_complete_source_bindings(self) -> None:
        library = ROOT / "docs" / "renderers" / "web" / "assets" / "shared" / "symbols"
        catalog = json.loads((library / "manifest.json").read_text())
        symbols = {row["key"]: row for row in catalog["assets"]}
        for model, count in (("PTB021", 6), ("PTB041", 6), ("PTB071", 6), ("BN-RB15", 3)):
            version = next(case[2] for case in CASES if case[1] == model)
            package = package_path(model, version + "-release")
            manifest = manifest_at(package)
            rows = manifest["symbol_asset_admission"]["locales"]["ja"]
            self.assertEqual(len(rows), count, model)
            for row in rows:
                shared = symbols[row["shared_symbol_key"]]
                self.assertEqual(row["asset_sha256"], shared["sha256"])
                self.assertEqual((package / "web" / "ja" / row["asset_ref"]).read_bytes(),
                                 (library / shared["path"]).read_bytes())
                self.assertTrue(row["drawing_indices"])
                self.assertEqual(len(row["caption_sha256"]), 64)
            if model == "BN-RB15":
                self.assertEqual([row["asset_ref"] for row in rows], [
                    "assets/symbol-prohibited.svg", "assets/symbol-mandatory.svg", "assets/symbol-unplug.svg"])


if __name__ == "__main__":
    unittest.main()
