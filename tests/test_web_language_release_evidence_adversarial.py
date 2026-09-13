"""Independent negative tests for the sealed language evidence trust boundary."""

import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from tools.web_language_release_evidence import (
    capture_projection,
    seal_release_evidence,
    verify_release_evidence,
)


def digest(value):
    return hashlib.sha256(json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()).hexdigest()


class LanguageEvidenceAdversarialTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bundle = self.root / "canonical"
        self.bundle.mkdir()
        (self.bundle / "index.rst").write_text(".. include:: operation.rst\n")
        page = self.bundle / "operation.rst"
        page.write_text(".. include:: label.txt\n")
        (self.bundle / "label.txt").write_text("Press ON/OFF\n")
        row = {"path": page.name, "sha256": hashlib.sha256(page.read_bytes()).hexdigest()}
        self.manifest = self.bundle / "bundle_manifest.json"
        self.manifest.write_text(json.dumps({
            "schema_version": "web-language-bundle/v1", "model": "JE-TEST",
            "region": "EU", "language": "en", "source_index_sha256": "a" * 64,
            "source_pages": [row], "pages": [row],
        }))
        self.md = self.root / "md"
        self.html = self.root / "html"
        self.md.mkdir()
        self.html.mkdir()
        (self.md / "manual.md").write_text("# Manual\n")
        (self.md / "a").mkdir()
        (self.md / "a" / "x.png").write_bytes(b"image")
        (self.md / "a.png").write_bytes(b"other image")
        (self.html / "index.html").write_text("<html>Manual</html>")

    def captures(self):
        return [capture_projection(
            self.manifest, action=action, model="JE-TEST", region="EU", language="en"
        ) for action in ("check", "md", "html")]

    def seal(self, captures=None):
        return seal_release_evidence(
            captures=self.captures() if captures is None else captures,
            markdown_dir=self.md, markdown_name="manual.md", html_dir=self.html,
            evidence_dir=self.root / "evidence", version="1.0", git_ref="main",
        )

    def verify(self, receipt, **overrides):
        args = dict(
            expected_sha256=hashlib.sha256(receipt.read_bytes()).hexdigest(),
            model="JE-TEST", region="EU", language="en", version="1.0", git_ref="main",
            markdown_dir=self.md, markdown_name="manual.md", html_dir=self.html,
        )
        args.update(overrides)
        return verify_release_evidence(receipt, **args)

    def test_path_prefix_sorting_roundtrip(self):
        self.verify(self.seal())

    def test_equal_but_detached_action_hashes_rejected(self):
        receipt = self.seal()
        payload = json.loads(receipt.read_text())
        payload["actions"] = dict.fromkeys(("check", "md", "html"), "b" * 64)
        receipt.write_text(json.dumps(payload))
        with self.assertRaisesRegex(RuntimeError, "detached"):
            self.verify(receipt)

    def test_canonical_page_detached_even_with_recomputed_fingerprints(self):
        receipt = self.seal()
        payload = json.loads(receipt.read_text())
        for row in payload["canonical_source"]["files"]:
            if row["path"] == "operation.rst":
                row["sha256"] = "c" * 64
        payload["canonical_source"]["sha256"] = digest(payload["canonical_source"]["files"])
        fingerprint = digest({
            "manifest_sha256": payload["projection_manifest"]["sha256"],
            "source_sha256": payload["canonical_source"]["sha256"],
        })
        payload["actions"] = dict.fromkeys(("check", "md", "html"), fingerprint)
        receipt.write_text(json.dumps(payload))
        with self.assertRaisesRegex(RuntimeError, "detached"):
            self.verify(receipt)

    def test_unlisted_index_include_rejected(self):
        (self.bundle / "foreign.rst").write_text("Foreign language")
        (self.bundle / "index.rst").write_text(".. include:: foreign.rst\n")
        with self.assertRaisesRegex(RuntimeError, "index"):
            self.captures()

    def test_source_changed_after_last_capture_rejected(self):
        captures = self.captures()
        (self.bundle / "label.txt").write_text("Changed after HTML")
        with self.assertRaisesRegex(RuntimeError, "changed"):
            self.seal(captures)

    def test_identity_mismatches_rejected(self):
        receipt = self.seal()
        for override in ({"language": "fr"}, {"version": "2.0"}, {"git_ref": "other"}):
            with self.subTest(override=override), self.assertRaises(RuntimeError):
                self.verify(receipt, **override)

    def test_stored_markdown_tamper_rejected(self):
        receipt = self.seal()
        shutil.copytree(receipt.parent, self.md / "evidence")
        stored = self.md / "evidence" / receipt.name
        self.verify(stored, html_dir=None, stored=True)
        (self.md / "manual.md").write_text("Changed")
        with self.assertRaisesRegex(RuntimeError, "Markdown files differ"):
            self.verify(stored, html_dir=None, stored=True)

    def test_stored_evidence_directory_cannot_hide_extra_markdown(self):
        receipt = self.seal()
        shutil.copytree(receipt.parent, self.md / "evidence")
        stored = self.md / "evidence" / receipt.name
        (stored.parent / "rogue.md").write_text("Untracked shipped content")
        with self.assertRaises(RuntimeError):
            self.verify(stored, html_dir=None, stored=True)
