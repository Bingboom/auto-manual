from __future__ import annotations

import argparse
import csv
import hashlib
import json
import unittest
import zipfile
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

try:
    import pymupdf as fitz
except ImportError:  # pragma: no cover - exercised only without declared test deps
    try:
        import fitz  # type: ignore[no-redef]
    except ImportError:
        fitz = None  # type: ignore[assignment]

from tests.test_asset_recipe import sample_recipe_payload
from tools.asset_intake import run_asset_intake
from tools.asset_pipeline.extract import (
    pymupdf_versions,
    scan_pdf_private_markers,
    sha256_file,
)
from tools.asset_pipeline.models import (
    ArtifactValidationError,
    AssetIntakeError,
    SourceValidationError,
)
from tools.asset_pipeline.package import result_summary, run_intake
from tools.asset_pipeline.recipe import load_recipe


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@unittest.skipIf(fitz is None, "PyMuPDF not installed")
class TestAssetIntake(unittest.TestCase):
    def _make_source(
        self,
        path: Path,
        *,
        page_count: int = 59,
        label_prefix: str = "label",
    ) -> str:
        document = fitz.open()
        for page_index in range(page_count):
            if page_index == 0 and page_count == 59:
                width, height = 800, 500
            else:
                width, height = 120, 180
            page = document.new_page(width=width, height=height)
            page.draw_rect(fitz.Rect(10, 10, min(110, width - 5), min(100, height - 5)))
            page.insert_text((20, 40), f"{label_prefix}-{page_index + 1}", fontsize=9)
        document.save(
            str(path),
            garbage=4,
            clean=True,
            deflate=True,
            no_new_id=True,
        )
        document.close()
        with path.open("ab") as handle:
            handle.write(b"\n% /AIPrivateData /AIMetaData /PieceInfo\n")
        return sha256_file(path)

    def _runtime_payload(self, source_sha256: str) -> dict[str, object]:
        payload = deepcopy(sample_recipe_payload(source_sha256=source_sha256))
        for asset in payload["assets"]:  # type: ignore[union-attr]
            asset["gate"] = {"status": "quarantine", "reasons": ["synthetic fixture"]}
            asset["build_eligible"] = False
            asset["visual_review_required"] = True
            for output in asset["outputs"]:
                output.pop("expected_sha256", None)
        return payload

    def _write_recipe(self, path: Path, payload: dict[str, object]):
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return load_recipe(path)

    def _single_page_payload(self, source_sha256: str) -> dict[str, object]:
        payload = self._runtime_payload(source_sha256)
        payload["source"]["expected_page_count"] = 1  # type: ignore[index]
        payload["archive"]["pages"]["last"] = 1  # type: ignore[index]
        payload["page_catalog"] = [  # type: ignore[index]
            {
                "page": 1,
                "page_key": "manual_page_1",
                "role": "manual_page",
                "locale": "und",
                "build_eligible": False,
                "gate": {"status": "archive", "reasons": []},
                "risk_tags": [],
            }
        ]
        asset = payload["assets"][0]  # type: ignore[index]
        asset["page"] = 1
        asset["outputs"] = [
            {
                "format": "png",
                "path": "docs/assets/single.png",
                "scale": 1,
            }
        ]
        payload["assets"] = [asset]
        return payload

    def _tree_hashes(self, root: Path) -> dict[str, str]:
        return {
            path.relative_to(root).as_posix(): _sha256(path)
            for path in sorted(root.rglob("*"))
            if path.is_file()
        }

    def test_two_complete_runs_are_byte_identical(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "master.ai"
            source_sha256 = self._make_source(source)
            recipe = self._write_recipe(
                root / "recipe.json",
                self._runtime_payload(source_sha256),
            )
            first = run_intake(
                source_path=source,
                recipe=recipe,
                output_root=root / "run-one",
            )
            second = run_intake(
                source_path=source,
                recipe=recipe,
                output_root=root / "run-two",
            )

            self.assertEqual(source_sha256, sha256_file(source))
            self.assertEqual(self._tree_hashes(first.output_root), self._tree_hashes(second.output_root))
            self.assertEqual(_sha256(first.manifest_path), _sha256(second.manifest_path))
            self.assertEqual(_sha256(first.package_path), _sha256(second.package_path))
            self.assertEqual(
                _sha256(first.manifest_path),
                result_summary(first)["manifest_sha256"],
            )

            manifest_bytes = first.manifest_path.read_bytes()
            manifest = json.loads(manifest_bytes)
            self.assertNotIn(str(root).encode(), manifest_bytes)
            self.assertNotIn(b"created_at", manifest_bytes)
            self.assertEqual(1, manifest["source"]["ai_private_data_count"])
            self.assertEqual(1, manifest["source"]["ai_metadata_count"])
            self.assertEqual(1, manifest["source"]["piece_info_count"])
            self.assertEqual(59, manifest["source"]["page_count"])
            self.assertEqual(138, len(manifest["artifacts"]))
            self.assertTrue(all(len(row["sha256"]) == 64 for row in manifest["artifacts"]))
            self.assertEqual(
                _sha256(first.artifacts_csv_path),
                manifest["indexes"]["artifacts_csv"]["sha256"],
            )
            self.assertEqual(pymupdf_versions()[0], manifest["runtime"]["pymupdf_version"])
            self.assertEqual(pymupdf_versions()[1], manifest["runtime"]["mupdf_version"])
            app_asset = next(row for row in manifest["assets"] if row["asset_key"] == "app/qr_setup")
            self.assertEqual("quarantine", app_asset["gate"]["status"])

            with first.artifacts_csv_path.open(encoding="utf-8", newline="") as handle:
                csv_rows = list(csv.DictReader(handle))
            self.assertEqual(138, len(csv_rows))
            self.assertEqual(
                sorted(row["path"] for row in csv_rows),
                [row["path"] for row in csv_rows],
            )

            overview = fitz.Pixmap(
                str(first.output_root / "artifacts/archive/previews/page-0001.png")
            )
            normal = fitz.Pixmap(
                str(first.output_root / "artifacts/archive/previews/page-0002.png")
            )
            self.assertEqual((200, 125), (overview.width, overview.height))
            self.assertEqual((120, 180), (normal.width, normal.height))

            cropped_pdf = first.output_root / "artifacts/docs/assets/figure_1.pdf"
            with fitz.open(str(cropped_pdf)) as document:
                self.assertNotIn("label-2", document[0].get_text())
            self.assertEqual((0, 0, 0), scan_pdf_private_markers(cropped_pdf))
            self.assertEqual(
                (0, 0, 0),
                scan_pdf_private_markers(
                    first.output_root / "artifacts/archive/pages/page-0001.pdf"
                ),
            )

            with zipfile.ZipFile(first.package_path) as bundle:
                names = bundle.namelist()
                self.assertEqual(sorted(names), names)
                self.assertIn("manifest.json", names)
                self.assertIn("artifacts.csv", names)
                self.assertTrue(all(info.date_time == (1980, 1, 1, 0, 0, 0) for info in bundle.infolist()))

    def test_expected_output_hash_fails_atomically(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "single.ai"
            source_sha256 = self._make_source(source, page_count=1)
            payload = self._single_page_payload(source_sha256)
            payload["assets"][0]["outputs"][0]["expected_sha256"] = "0" * 64  # type: ignore[index]
            recipe = self._write_recipe(root / "recipe.json", payload)
            output_root = root / "failed-run"

            with self.assertRaisesRegex(ArtifactValidationError, "artifact SHA-256 mismatch"):
                run_intake(source_path=source, recipe=recipe, output_root=output_root)

            self.assertFalse(output_root.exists())

    def test_render_pixel_budget_fails_atomically(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "single.ai"
            source_sha256 = self._make_source(source, page_count=1)
            payload = self._single_page_payload(source_sha256)
            payload["normalization"]["max_render_pixels"] = 100  # type: ignore[index]
            recipe = self._write_recipe(root / "recipe.json", payload)
            output_root = root / "failed-run"

            with self.assertRaisesRegex(ArtifactValidationError, "exceeds max_render_pixels"):
                run_intake(source_path=source, recipe=recipe, output_root=output_root)

            self.assertFalse(output_root.exists())

    def test_runtime_version_mismatch_fails_before_output(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "single.ai"
            source_sha256 = self._make_source(source, page_count=1)
            recipe = self._write_recipe(
                root / "recipe.json",
                self._single_page_payload(source_sha256),
            )
            output_root = root / "failed-run"

            with patch(
                "tools.asset_pipeline.extract.pymupdf_versions",
                return_value=("1.27.0", "1.29.0"),
            ):
                with self.assertRaisesRegex(SourceValidationError, "PyMuPDF version mismatch"):
                    run_intake(source_path=source, recipe=recipe, output_root=output_root)

            self.assertFalse(output_root.exists())

    def test_source_hash_mismatch_fails_before_output(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "master.ai"
            self._make_source(source)
            recipe = self._write_recipe(root / "recipe.json", self._runtime_payload("0" * 64))
            output_root = root / "failed-run"

            with self.assertRaisesRegex(SourceValidationError, "source SHA-256 mismatch"):
                run_intake(source_path=source, recipe=recipe, output_root=output_root)

            self.assertFalse(output_root.exists())

    def test_non_regular_source_is_rejected_before_staging(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            recipe = self._write_recipe(
                root / "recipe.json",
                self._single_page_payload("0" * 64),
            )
            output_root = root / "failed-run"

            with self.assertRaisesRegex(SourceValidationError, "not regular"):
                run_intake(source_path=root, recipe=recipe, output_root=output_root)

            self.assertFalse(output_root.exists())
            self.assertEqual([], list(root.glob(".failed-run.tmp-*")))

    def test_private_marker_scan_inspects_decoded_pdf_streams(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "compressed.pdf"
            document = fitz.open()
            page = document.new_page(width=200, height=100)
            page.insert_text((20, 40), "AIPrivateData PieceInfo AIMetaData")
            document.save(str(path), garbage=4, clean=True, deflate=True, no_new_id=True)
            document.close()

            self.assertNotIn(b"AIPrivateData", path.read_bytes())
            counts = scan_pdf_private_markers(path)

            self.assertTrue(all(count >= 1 for count in counts), counts)

    def test_intake_reads_only_verified_private_source_snapshot(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.ai"
            replacement = root / "replacement.ai"
            source_sha256 = self._make_source(
                source,
                page_count=1,
                label_prefix="SOURCE-A",
            )
            self._make_source(
                replacement,
                page_count=1,
                label_prefix="SOURCE-B",
            )
            source_bytes = source.read_bytes()
            recipe = self._write_recipe(
                root / "recipe.json",
                self._single_page_payload(source_sha256),
            )
            output_root = root / "complete-run"

            from tools.asset_pipeline import package as asset_package

            original_extract = asset_package.extract_artifacts

            def swap_external_source(snapshot_path, loaded_recipe, artifact_root):
                source.write_bytes(replacement.read_bytes())
                try:
                    return original_extract(snapshot_path, loaded_recipe, artifact_root)
                finally:
                    source.write_bytes(source_bytes)

            with patch(
                "tools.asset_pipeline.package.extract_artifacts",
                side_effect=swap_external_source,
            ):
                run_intake(
                    source_path=source,
                    recipe=recipe,
                    output_root=output_root,
                )

            archive_page = output_root / "artifacts/archive/pages/page-0001.pdf"
            with fitz.open(str(archive_page)) as document:
                archive_text = document[0].get_text()
            self.assertIn("SOURCE-A-1", archive_text)
            self.assertNotIn("SOURCE-B-1", archive_text)
            self.assertEqual(source_sha256, sha256_file(source))

    def test_keyboard_interrupt_removes_private_staging_directory(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.ai"
            source_sha256 = self._make_source(source, page_count=1)
            recipe = self._write_recipe(
                root / "recipe.json",
                self._single_page_payload(source_sha256),
            )
            output_root = root / "interrupted-run"

            with patch(
                "tools.asset_pipeline.package.extract_artifacts",
                side_effect=KeyboardInterrupt,
            ):
                with self.assertRaises(KeyboardInterrupt):
                    run_intake(
                        source_path=source,
                        recipe=recipe,
                        output_root=output_root,
                    )

            self.assertFalse(output_root.exists())
            self.assertEqual([], list(root.glob(".interrupted-run.tmp-*")))

    def test_stable_dispatcher_rejects_promotion(self) -> None:
        args = argparse.Namespace(
            asset_source_key="source/manual_test_master",
            asset_source_file=Path("missing.ai"),
            asset_recipe=Path("missing.json"),
            asset_output_root=Path("missing-output"),
            asset_promote=True,
        )

        with self.assertRaisesRegex(AssetIntakeError, "package-only"):
            run_asset_intake(args, repo_root=Path.cwd())


if __name__ == "__main__":
    unittest.main()
