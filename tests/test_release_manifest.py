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
            build_root = docs_dir / "_build" / "JE-1000F" / "US"
            (build_root / "rst").mkdir(parents=True)
            (build_root / "html").mkdir(parents=True)
            (build_root / "word").mkdir(parents=True)
            (build_root / "pdf").mkdir(parents=True)
            (docs_dir / "_review" / "JE-1000F" / "US").mkdir(parents=True)
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
            self.assertEqual("Jackery Explorer 1000 Pro", manifest["product_name"])
            self.assertEqual("data/phase1/Spec_Notes.csv", manifest["spec_notes_csv"])
            self.assertEqual("reports/releases/JE-1000F/US/20260315T100000Z.json", json_path.relative_to(root).as_posix())
            self.assertTrue(manifest["word_output"]["exists"])
            self.assertTrue(manifest["html_output"]["exists"])
            self.assertTrue(manifest["pdf_output"]["exists"])
            self.assertEqual(
                hashlib.sha256((build_root / "word" / "manual_je1000f_us.docx").read_bytes()).hexdigest(),
                manifest["word_output"]["sha256"],
            )
