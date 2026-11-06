"""JE-3000C JP/ja Git-only Web release (from the reviewed 2026-10-19 draft)."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from tools.web.frozen_ai_web import replay_package
from tools.web.frozen_source_evidence import seal_frozen_web_evidence
from tools.web.language_release_evidence import _file_inventory, require_publishable_manual_ir
from tools.web.symbol_asset_admission import require_symbol_asset_admission

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "manual_sources/JE-3000C/JP/ja/git-20261106-b16b82c6-jp-release"
DRAFT = ROOT / "manual_sources/JE-3000C/JP/ja/git-20261019-b16b82c6-jp-native"
MARKDOWN = "manual_je3000c_jp_ja.md"


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class Je3000cJpWebTests(unittest.TestCase):
    def test_manifest_binds_the_exact_inventory(self):
        manifest = read(PACKAGE / "source_manifest.json")
        actual = list(_file_inventory(PACKAGE, excluded_roots=(PACKAGE / "source_manifest.json",)))
        self.assertEqual(manifest["inputs"], actual)
        self.assertEqual(manifest["publication_status"], "operator-approved-git-only-release")
        self.assertEqual(manifest["target"]["technical_version"], PACKAGE.name)
        self.assertEqual((PACKAGE / "source/original.pdf").read_bytes(),
                         (DRAFT / "source/original.pdf").read_bytes())

    def test_release_is_publishable_and_approved(self):
        require_publishable_manual_ir(PACKAGE / "web/ja")
        approval = read(PACKAGE / "source/approval.json")
        self.assertIn("上线提交发布：JE-3000C", approval["operator_quote"])
        self.assertEqual(approval["source_sha256"], read(PACKAGE / "source_manifest.json")["original_source"]["sha256"])

    def test_only_the_approved_footnote_and_symbols_differ_from_the_draft(self):
        draft = (DRAFT / "web/ja" / MARKDOWN).read_text(encoding="utf-8").splitlines()
        release = (PACKAGE / "web/ja" / MARKDOWN).read_text(encoding="utf-8").splitlines()
        changed = [(a, b) for a, b in zip(draft, release, strict=True) if a != b]
        self.assertEqual(len(changed), 1)
        self.assertTrue(changed[0][1].endswith("給電することができます。</p>") or "できます。" in changed[0][1])
        errata = read(PACKAGE / "web/ja/manual.ir.json")["metadata"]["source_errata"]
        self.assertEqual([e["status"] for e in errata], ["operator-approved"])

    def test_symbol_rows_admit_against_the_source_pdf(self):
        manifest = read(PACKAGE / "source_manifest.json")
        report = require_symbol_asset_admission(PACKAGE / "web/ja", PACKAGE, manifest, "ja")
        self.assertEqual(len(report), 12)
        # Five canonicals print beyond 2% and are released by their confirmed
        # group caption; the sixth (WEEE) is within the fixed tolerance.
        released = {row["asset_ref"] for row in report if "canonical_group" in row}
        self.assertEqual(len(released), 5)

    def test_cold_replay_matches_stored_markdown(self):
        with tempfile.TemporaryDirectory() as temp:
            web = Path(temp) / "ja"
            shutil.copytree(PACKAGE / "web/ja", web)
            (web / MARKDOWN).unlink()
            replay_package(web)
            self.assertEqual((web / MARKDOWN).read_bytes(), (PACKAGE / "web/ja" / MARKDOWN).read_bytes())

    def test_seal_requires_matching_markdown(self):
        with tempfile.TemporaryDirectory() as temp:
            md = Path(temp) / "md"
            shutil.copytree(PACKAGE / "web/ja", md)
            (md / MARKDOWN).write_text("tampered\n", encoding="utf-8")
            with self.assertRaises(RuntimeError):
                seal_frozen_web_evidence(
                    source_manifest_path=PACKAGE / "source_manifest.json", source_root=PACKAGE,
                    language="ja", markdown_dir=md, markdown_name=MARKDOWN,
                    html_dir=Path(temp) / "html", evidence_dir=Path(temp) / "ev", git_ref="test")


if __name__ == "__main__":
    unittest.main()
