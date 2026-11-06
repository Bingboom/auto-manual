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
RELEASE = ROOT / "manual_sources/JE-3000C/JP/ja/git-20261106-b16b82c6-jp-release"
REVISION = ROOT / "manual_sources/JE-3000C/JP/ja/git-20261106-b16b82c6-jp-release-r2"
DRAFT = ROOT / "manual_sources/JE-3000C/JP/ja/git-20261019-b16b82c6-jp-native"
MARKDOWN = "manual_je3000c_jp_ja.md"


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class Je3000cJpWebTests(unittest.TestCase):
    package = RELEASE
    # Draft lines this edition drops before the footnote line is compared.
    dropped_title_lines = 0

    def test_manifest_binds_the_exact_inventory(self):
        manifest = read(self.package / "source_manifest.json")
        actual = list(_file_inventory(self.package, excluded_roots=(self.package / "source_manifest.json",)))
        self.assertEqual(manifest["inputs"], actual)
        self.assertEqual(manifest["publication_status"], "operator-approved-git-only-release")
        self.assertEqual(manifest["target"]["technical_version"], self.package.name)
        self.assertEqual((self.package / "source/original.pdf").read_bytes(),
                         (DRAFT / "source/original.pdf").read_bytes())

    def test_release_is_publishable_and_approved(self):
        require_publishable_manual_ir(self.package / "web/ja")
        approval = read(self.package / "source/approval.json")
        self.assertIn("上线提交发布：JE-3000C", approval["operator_quote"])
        self.assertEqual(approval["source_sha256"], read(self.package / "source_manifest.json")["original_source"]["sha256"])

    def test_only_the_approved_footnote_and_symbols_differ_from_the_draft(self):
        draft = (DRAFT / "web/ja" / MARKDOWN).read_text(encoding="utf-8").splitlines()
        release = (self.package / "web/ja" / MARKDOWN).read_text(encoding="utf-8").splitlines()
        if self.dropped_title_lines:
            self.assertTrue(draft[0].startswith("# Jackery ポータブル電源 3000 New"))
            self.assertFalse(release[0].startswith("# "))
            draft = draft[self.dropped_title_lines:]
        changed = [(a, b) for a, b in zip(draft, release, strict=True) if a != b]
        self.assertEqual(len(changed), 1)
        self.assertTrue(changed[0][1].endswith("給電することができます。</p>") or "できます。" in changed[0][1])
        errata = read(self.package / "web/ja/manual.ir.json")["metadata"]["source_errata"]
        self.assertEqual([e["status"] for e in errata], ["operator-approved"])

    def test_symbol_rows_admit_against_the_source_pdf(self):
        manifest = read(self.package / "source_manifest.json")
        report = require_symbol_asset_admission(self.package / "web/ja", self.package, manifest, "ja")
        self.assertEqual(len(report), 12)
        # Five canonicals print beyond 2% and are released by their confirmed
        # group caption; the sixth (WEEE) is within the fixed tolerance.
        released = {row["asset_ref"] for row in report if "canonical_group" in row}
        self.assertEqual(len(released), 5)

    def test_cold_replay_matches_stored_markdown(self):
        with tempfile.TemporaryDirectory() as temp:
            web = Path(temp) / "ja"
            shutil.copytree(self.package / "web/ja", web)
            (web / MARKDOWN).unlink()
            replay_package(web)
            self.assertEqual((web / MARKDOWN).read_bytes(), (self.package / "web/ja" / MARKDOWN).read_bytes())

    def test_seal_requires_matching_markdown(self):
        with tempfile.TemporaryDirectory() as temp:
            md = Path(temp) / "md"
            shutil.copytree(self.package / "web/ja", md)
            (md / MARKDOWN).write_text("tampered\n", encoding="utf-8")
            with self.assertRaises(RuntimeError):
                seal_frozen_web_evidence(
                    source_manifest_path=self.package / "source_manifest.json", source_root=self.package,
                    language="ja", markdown_dir=md, markdown_name=MARKDOWN,
                    html_dir=Path(temp) / "html", evidence_dir=Path(temp) / "ev", git_ref="test")


class Je3000cJpWebRevisionTests(Je3000cJpWebTests):
    """Revision 2 drops the standalone title heading (operator, 2026-11-06)."""
    package = REVISION
    dropped_title_lines = 2

    def test_page_opens_with_the_first_chapter(self):
        markdown = (self.package / "web/ja" / MARKDOWN).read_text(encoding="utf-8")
        headings = [line for line in markdown.splitlines() if line.startswith("#")]
        self.assertEqual(headings[0], "## 安全上のご注意")


if __name__ == "__main__":
    unittest.main()
