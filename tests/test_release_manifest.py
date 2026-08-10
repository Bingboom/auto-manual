from __future__ import annotations

import csv
import hashlib
import json
import shutil
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from tools import release_manifest
from tools.release_reproducibility import ReviewOverlayProvenance


class TestReleaseManifest(unittest.TestCase):
    def test_versioned_manifest_should_bind_to_frozen_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            docs_dir = root / "docs"
            build_root = docs_dir / "_build" / "JE-1000F" / "US" / "en"
            for child in ("rst", "html", "word", "pdf", "md", "idml"):
                (build_root / child).mkdir(parents=True, exist_ok=True)
            (docs_dir / "_review" / "JE-1000F" / "US" / "en").mkdir(parents=True)
            data_root = root / "data" / "phase2"
            shutil.copytree(Path(__file__).parent / "fixtures" / "phase2", data_root)
            config_path = root / "config.yaml"
            config_path.write_text(
                "\n".join(
                    [
                        "build:",
                        "  languages: [en]",
                        "  include_lang_in_output_path: true",
                        "paths:",
                        f"  docs_dir: {docs_dir.as_posix()}",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            built_at = datetime(2026, 7, 31, 3, 4, tzinfo=timezone.utc)

            with mock.patch.object(release_manifest, "ROOT", root), mock.patch.object(
                release_manifest, "_read_git_sha", return_value="a" * 40
            ), mock.patch.object(
                release_manifest,
                "review_overlay_from_environment",
                return_value=ReviewOverlayProvenance(
                    source_ref="review/JE-1000F-US",
                    source_sha="b" * 40,
                    target_path="docs/_review/JE-1000F/US",
                    tree_sha="c" * 40,
                ),
            ):
                json_path, csv_path = release_manifest.build_release_manifest(
                    config_path=config_path,
                    model="JE-1000F",
                    region="US",
                    data_root=str(data_root),
                    release_version="1.2",
                    source_date_epoch=1_785_513_828,
                    built_at=built_at,
                )

            manifest = json.loads(json_path.read_text(encoding="utf-8"))
            snapshot_path = root / manifest["snapshot"]["path"]
            self.assertEqual("1.2", manifest["release_version"])
            self.assertEqual(
                "manual-release/je-1000f/us/en/1.2",
                manifest["release_tag"],
            )
            self.assertEqual(
                "reports/releases/JE-1000F/US/en/versions/1.2/snapshot",
                manifest["snapshot"]["path"],
            )
            self.assertEqual(
                "reports/releases/JE-1000F/US/en/versions/1.2/snapshot/Spec_Master.csv",
                manifest["spec_master_csv"],
            )
            self.assertTrue((snapshot_path / "release_snapshot_identity.json").exists())
            self.assertEqual(
                1_785_513_828,
                manifest["reproducibility"]["source_date_epoch"],
            )
            self.assertEqual(
                "b" * 40,
                manifest["reproducibility"]["review_overlay"]["source_sha"],
            )
            with csv_path.open(encoding="utf-8", newline="") as handle:
                csv_row = next(csv.DictReader(handle))
            self.assertEqual(manifest["snapshot"]["snapshot_sha256"], csv_row["snapshot_sha256"])
            self.assertIn('"lang": "en"', csv_row["snapshot_target_matrix"])
            self.assertEqual("1785513828", csv_row["source_date_epoch"])
            self.assertEqual("review/JE-1000F-US", csv_row["review_overlay_ref"])
            self.assertEqual("c" * 40, csv_row["review_overlay_tree_sha"])
            self.assertEqual(manifest["release_tag"], csv_row["release_tag"])

    def test_build_release_manifest_should_write_json_and_csv(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            docs_dir = root / "docs"
            build_root = docs_dir / "_build" / "JE-1000F" / "US" / "en"
            (build_root / "rst").mkdir(parents=True)
            (build_root / "html").mkdir(parents=True)
            (build_root / "word").mkdir(parents=True)
            (build_root / "pdf").mkdir(parents=True)
            (build_root / "md").mkdir(parents=True)
            (build_root / "idml").mkdir(parents=True)
            (docs_dir / "_review" / "JE-1000F" / "US" / "en").mkdir(parents=True)
            (build_root / "html" / "index.html").write_text("html\n", encoding="utf-8")
            (build_root / "word" / "manual_je1000f_us.docx").write_text("docx\n", encoding="utf-8")
            (build_root / "pdf" / "manual_je1000f_us.pdf").write_text("pdf\n", encoding="utf-8")
            (build_root / "md" / "manual_je1000f_us.md").write_text("# Manual\n", encoding="utf-8")
            (build_root / "idml" / "manual_je1000f_us.idml").write_text(
                "idml\n", encoding="utf-8"
            )
            (build_root / "idml" / "finalize_report.json").write_text(
                json.dumps({
                    "success": True,
                    "page_count": 42,
                    "overset_stories": [],
                    "missing_fonts": [],
                    "bad_links": [],
                }),
                encoding="utf-8",
            )

            data_dir = root / "data" / "phase2"
            data_dir.mkdir(parents=True)
            (data_dir / "Spec_Master.csv").write_text(
                "\n".join(
                    [
                        "Model,Region,Is_Latest,Page,Row_key,Value_source",
                        "JE-1000F,US,TRUE,specifications,product_name,Jackery Explorer 1000 Pro",
                        "JE-1000F,US,TRUE,specifications,model_no,JE-1000F",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (data_dir / "Spec_Footnotes.csv").write_text("id,note\n", encoding="utf-8")
            (data_dir / "Spec_Notes.csv").write_text("id,note\n", encoding="utf-8")
            (data_dir / "spec_titles.csv").write_text("page,title_en\n", encoding="utf-8")

            config_path = root / "config.yaml"
            config_path.write_text(
                "\n".join(
                    [
                        "build:",
                        "  languages: [en]",
                        "  include_lang_in_output_path: true",
                        "  word_output: manual_{model_slug}_{region_slug}.docx",
                        "  output_pdf: manual_{model_slug}_{region_slug}.pdf",
                        "paths:",
                        f"  docs_dir: {docs_dir.as_posix()}",
                        f"  spec_master_csv: {(data_dir / 'Spec_Master.csv').as_posix()}",
                        f"  spec_footnotes_csv: {(data_dir / 'Spec_Footnotes.csv').as_posix()}",
                        f"  spec_notes_csv: {(data_dir / 'Spec_Notes.csv').as_posix()}",
                        f"  spec_titles_csv: {(data_dir / 'spec_titles.csv').as_posix()}",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            built_at = datetime(2026, 3, 15, 10, 0, tzinfo=timezone.utc)
            with mock.patch.object(release_manifest, "ROOT", root), \
                mock.patch.object(release_manifest, "_read_git_sha", return_value="abc123"):
                json_path, csv_path = release_manifest.build_release_manifest(
                    config_path=config_path,
                    model="JE-1000F",
                    region="US",
                    built_at=built_at,
                )

            self.assertTrue(json_path.exists())
            self.assertTrue(csv_path.exists())

            manifest = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual("abc123", manifest["git_sha"])
            self.assertEqual(1, manifest["toolchain"]["schema_version"])
            self.assertIn("python", manifest["toolchain"])
            csv_header = csv_path.read_text(encoding="utf-8").splitlines()[0]
            self.assertIn("toolchain_python", csv_header)
            self.assertEqual("JE-1000F", manifest["model"])
            self.assertEqual("US", manifest["region"])
            self.assertEqual(["en"], manifest["build_languages"])
            self.assertEqual("docs/_review/JE-1000F/US/en", manifest["tracked_review_dir"])
            self.assertEqual("docs/_build/JE-1000F/US/en/rst", manifest["runtime_bundle_dir"])
            self.assertEqual("Jackery Explorer 1000 Pro", manifest["product_name"])
            self.assertEqual("data/phase2/Spec_Notes.csv", manifest["spec_notes_csv"])
            self.assertEqual(
                "reports/releases/JE-1000F/US/en/manifests/20260315T100000Z.json",
                json_path.relative_to(root).as_posix(),
            )
            self.assertTrue(manifest["word_output"]["exists"])
            self.assertTrue(manifest["md_output"]["exists"])
            self.assertTrue(manifest["html_output"]["exists"])
            self.assertTrue(manifest["pdf_output"]["exists"])
            self.assertEqual(
                hashlib.sha256((build_root / "word" / "manual_je1000f_us.docx").read_bytes()).hexdigest(),
                manifest["word_output"]["sha256"],
            )
            self.assertEqual(
                hashlib.sha256((build_root / "md" / "manual_je1000f_us.md").read_bytes()).hexdigest(),
                manifest["md_output"]["sha256"],
            )
            self.assertEqual(42, manifest["indesign_package"]["preflight"]["page_count"])
            self.assertEqual(
                0, manifest["indesign_package"]["preflight"]["overset_stories"]
            )
            with csv_path.open(encoding="utf-8", newline="") as handle:
                csv_row = next(csv.DictReader(handle))
            self.assertEqual("42", csv_row["indesign_preflight_page_count"])
            self.assertEqual("0", csv_row["indesign_preflight_overset_stories"])

    def test_build_release_manifest_should_honor_data_root_override(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            docs_dir = root / "docs"
            build_root = docs_dir / "_build" / "JE-1000F" / "US" / "en"
            (build_root / "rst").mkdir(parents=True)
            (build_root / "html").mkdir(parents=True)
            (build_root / "word").mkdir(parents=True)
            (build_root / "pdf").mkdir(parents=True)
            (build_root / "md").mkdir(parents=True)
            (docs_dir / "_review" / "JE-1000F" / "US" / "en").mkdir(parents=True)
            (build_root / "html" / "index.html").write_text("html\n", encoding="utf-8")

            configured_dir = root / "data" / "configured"
            phase2_dir = root / "data" / "phase2"
            configured_dir.mkdir(parents=True)
            phase2_dir.mkdir(parents=True)
            (configured_dir / "Spec_Master.csv").write_text("Model,Region,Is_Latest,Page,Row_key,Value_source\n", encoding="utf-8")
            for data_dir, title in ((configured_dir, "configured"), (phase2_dir, "phase2")):
                (data_dir / "Spec_Footnotes.csv").write_text("id,note\n", encoding="utf-8")
                (data_dir / "Spec_Notes.csv").write_text("id,note\n", encoding="utf-8")
                (data_dir / "spec_titles.csv").write_text(f"title_en\n{title}\n", encoding="utf-8")
            (phase2_dir / "Spec_Master.csv").write_text(
                "\n".join(
                    [
                        "Model,Region,Is_Latest,Page,Row_key,Value_source",
                        "JE-1000F,US,TRUE,specifications,product_name,Phase2 Product",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            config_path = root / "config.yaml"
            config_path.write_text(
                "\n".join(
                    [
                        "build:",
                        "  languages: [en]",
                        "  include_lang_in_output_path: true",
                        "paths:",
                        f"  docs_dir: {docs_dir.as_posix()}",
                        f"  spec_master_csv: {(configured_dir / 'Spec_Master.csv').as_posix()}",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            with mock.patch.object(release_manifest, "ROOT", root), \
                mock.patch.object(release_manifest, "_read_git_sha", return_value="abc123"):
                json_path, _csv_path = release_manifest.build_release_manifest(
                    config_path=config_path,
                    model="JE-1000F",
                    region="US",
                    data_root="data/phase2",
                )

            manifest = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual("data/phase2/Spec_Master.csv", manifest["spec_master_csv"])
            self.assertEqual("Phase2 Product", manifest["product_name"])
            self.assertEqual("docs/_review/JE-1000F/US/en", manifest["tracked_review_dir"])

    def test_build_release_manifest_should_support_staging_build_and_release_roots(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            docs_dir = root / "docs"
            staging_docs_build_dir = root / ".tmp" / "staging" / "docs" / "_build"
            build_root = staging_docs_build_dir / "JE-1000F" / "US" / "en"
            (build_root / "rst").mkdir(parents=True)
            (build_root / "html").mkdir(parents=True)
            (build_root / "word").mkdir(parents=True)
            (build_root / "pdf").mkdir(parents=True)
            (build_root / "md").mkdir(parents=True)
            (docs_dir / "_review" / "JE-1000F" / "US" / "en").mkdir(parents=True)
            (build_root / "html" / "index.html").write_text("html\n", encoding="utf-8")

            data_dir = root / "data" / "phase2"
            data_dir.mkdir(parents=True)
            (data_dir / "Spec_Master.csv").write_text(
                "Model,Region,Is_Latest,Page,Row_key,Value_source\nJE-1000F,US,TRUE,specifications,product_name,Stage Product\n",
                encoding="utf-8",
            )
            (data_dir / "Spec_Footnotes.csv").write_text("id,note\n", encoding="utf-8")
            (data_dir / "Spec_Notes.csv").write_text("id,note\n", encoding="utf-8")
            (data_dir / "spec_titles.csv").write_text("page,title_en\n", encoding="utf-8")

            config_path = root / "config.yaml"
            config_path.write_text(
                "\n".join(
                    [
                        "build:",
                        "  languages: [en]",
                        "  include_lang_in_output_path: true",
                        "paths:",
                        f"  docs_dir: {docs_dir.as_posix()}",
                        f"  spec_master_csv: {(data_dir / 'Spec_Master.csv').as_posix()}",
                        f"  spec_footnotes_csv: {(data_dir / 'Spec_Footnotes.csv').as_posix()}",
                        f"  spec_notes_csv: {(data_dir / 'Spec_Notes.csv').as_posix()}",
                        f"  spec_titles_csv: {(data_dir / 'spec_titles.csv').as_posix()}",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            releases_root = root / ".tmp" / "staging" / "reports" / "releases"
            with mock.patch.object(release_manifest, "ROOT", root), \
                mock.patch.object(release_manifest, "_read_git_sha", return_value="abc123"):
                json_path, _csv_path = release_manifest.build_release_manifest(
                    config_path=config_path,
                    model="JE-1000F",
                    region="US",
                    docs_build_dir=staging_docs_build_dir,
                    releases_root=releases_root,
                )

            manifest = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual((releases_root / "JE-1000F" / "US" / "en" / "manifests").resolve(), json_path.parent.resolve())
            self.assertEqual(".tmp/staging/docs/_build/JE-1000F/US/en/rst", manifest["runtime_bundle_dir"])
