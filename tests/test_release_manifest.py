from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from tools import release_manifest


class TestReleaseManifest(unittest.TestCase):
    def test_build_release_manifest_should_write_json_and_csv(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            docs_dir = root / "docs"
            build_root = docs_dir / "_build" / "JE-1000F" / "US" / "en"
            (build_root / "rst").mkdir(parents=True)
            (build_root / "html").mkdir(parents=True)
            (build_root / "word").mkdir(parents=True)
            (build_root / "pdf").mkdir(parents=True)
            (docs_dir / "_review" / "JE-1000F" / "US" / "en").mkdir(parents=True)
            (build_root / "html" / "index.html").write_text("html\n", encoding="utf-8")
            (build_root / "word" / "manual_je1000f_us.docx").write_text("docx\n", encoding="utf-8")
            (build_root / "pdf" / "manual_je1000f_us.pdf").write_text("pdf\n", encoding="utf-8")

            data_dir = root / "data" / "phase1"
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
            self.assertEqual("JE-1000F", manifest["model"])
            self.assertEqual("US", manifest["region"])
            self.assertEqual(["en"], manifest["build_languages"])
            self.assertEqual("docs/_review/JE-1000F/US/en", manifest["tracked_review_dir"])
            self.assertEqual("docs/_build/JE-1000F/US/en/rst", manifest["runtime_bundle_dir"])
            self.assertEqual("Jackery Explorer 1000 Pro", manifest["product_name"])
            self.assertEqual("data/phase1/Spec_Notes.csv", manifest["spec_notes_csv"])
            self.assertEqual(
                "reports/releases/JE-1000F/US/en/manifests/20260315T100000Z.json",
                json_path.relative_to(root).as_posix(),
            )
            self.assertTrue(manifest["word_output"]["exists"])
            self.assertTrue(manifest["html_output"]["exists"])
            self.assertTrue(manifest["pdf_output"]["exists"])
            self.assertEqual(
                hashlib.sha256((build_root / "word" / "manual_je1000f_us.docx").read_bytes()).hexdigest(),
                manifest["word_output"]["sha256"],
            )

    def test_build_release_manifest_should_honor_data_root_override(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            docs_dir = root / "docs"
            build_root = docs_dir / "_build" / "JE-1000F" / "US" / "en"
            (build_root / "rst").mkdir(parents=True)
            (build_root / "html").mkdir(parents=True)
            (build_root / "word").mkdir(parents=True)
            (build_root / "pdf").mkdir(parents=True)
            (docs_dir / "_review" / "JE-1000F" / "US" / "en").mkdir(parents=True)
            (build_root / "html" / "index.html").write_text("html\n", encoding="utf-8")

            phase1_dir = root / "data" / "phase1"
            phase2_dir = root / "data" / "phase2"
            phase1_dir.mkdir(parents=True)
            phase2_dir.mkdir(parents=True)
            (phase1_dir / "Spec_Master.csv").write_text("Model,Region,Is_Latest,Page,Row_key,Value_source\n", encoding="utf-8")
            for data_dir, title in ((phase1_dir, "phase1"), (phase2_dir, "phase2")):
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
                        f"  spec_master_csv: {(phase1_dir / 'Spec_Master.csv').as_posix()}",
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
            (docs_dir / "_review" / "JE-1000F" / "US" / "en").mkdir(parents=True)
            (build_root / "html" / "index.html").write_text("html\n", encoding="utf-8")

            data_dir = root / "data" / "phase1"
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
