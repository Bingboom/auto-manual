from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from tools.web_language_release_evidence import (
    PROJECTION_MANIFEST_FILENAME,
    RECEIPT_FILENAME,
    capture_projection,
    require_consistent_captures,
    seal_release_evidence,
    verify_release_evidence,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class WebLanguageReleaseEvidenceTests(unittest.TestCase):
    def _projection(self, root: Path) -> Path:
        bundle = root / "rst"
        page = bundle / "page" / "manual_en.rst"
        snippet = bundle / "snippets" / "detail.inc"
        spaced = bundle / "snippets" / "legal include.txt"
        page.parent.mkdir(parents=True)
        snippet.parent.mkdir(parents=True)
        spaced.write_text("A legal include path with spaces.\n", encoding="utf-8")
        (bundle / "index.rst").write_text(
            ".. include:: page/manual_en.rst\n", encoding="utf-8"
        )
        page.write_text(
            "\\HBApplyLang{en}\n\n.. include:: ../snippets/detail.inc\n",
            encoding="utf-8",
        )
        snippet.write_text(
            "Complete English detail.\n\n.. include:: legal include.txt\n",
            encoding="utf-8",
        )
        manifest = bundle / "bundle_manifest.json"
        manifest.write_text(
            json.dumps(
                {
                    "schema_version": "web-language-bundle/v1",
                    "model": "MODEL",
                    "region": "US",
                    "language": "en",
                    "source_index_sha256": "a" * 64,
                    "source_pages": [
                        {"path": "page/manual_en.rst", "sha256": _sha256(page)}
                    ],
                    "pages": [
                        {"path": "page/manual_en.rst", "sha256": _sha256(page)}
                    ],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return manifest

    def _outputs(self, root: Path) -> tuple[Path, Path]:
        md = root / "web" / "md"
        html = root / "web" / "html"
        md.mkdir(parents=True)
        html.mkdir(parents=True)
        (md / "manual.md").write_text("# Manual\n", encoding="utf-8")
        (md / "index.md").write_text("# Index\n", encoding="utf-8")
        (html / "index.html").write_text("<html></html>\n", encoding="utf-8")
        return md, html

    def _captures(self, manifest: Path):
        return tuple(
            capture_projection(
                manifest,
                action=action,
                model="MODEL",
                region="US",
                language="en",
            )
            for action in ("check", "md", "html")
        )

    def test_seal_and_verify_should_bind_complete_source_and_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = self._projection(root)
            md, html = self._outputs(root)
            evidence_dir = root / "web" / "evidence"
            receipt = seal_release_evidence(
                captures=self._captures(manifest),
                markdown_dir=md,
                markdown_name="manual.md",
                html_dir=html,
                evidence_dir=evidence_dir,
                version="2.0",
                git_ref="review/MODEL-US",
            )

            payload = json.loads(receipt.read_text(encoding="utf-8"))
            self.assertEqual(
                [
                    "index.rst",
                    "page/manual_en.rst",
                    "snippets/detail.inc",
                    "snippets/legal include.txt",
                ],
                [item["path"] for item in payload["canonical_source"]["files"]],
            )
            verified = verify_release_evidence(
                receipt,
                expected_sha256=_sha256(receipt),
                model="MODEL",
                region="US",
                language="en",
                version="2.0",
                git_ref="review/MODEL-US",
                markdown_dir=md,
                markdown_name="manual.md",
                html_dir=html,
            )
            self.assertEqual(_sha256(receipt), verified.sha256)
            self.assertTrue((evidence_dir / PROJECTION_MANIFEST_FILENAME).is_file())
            with self.assertRaisesRegex(RuntimeError, "requires HTML"):
                verify_release_evidence(
                    receipt,
                    expected_sha256=_sha256(receipt),
                    model="MODEL",
                    region="US",
                    language="en",
                    version="2.0",
                    git_ref="review/MODEL-US",
                    markdown_dir=md,
                    markdown_name="manual.md",
                    html_dir=None,
                )

    def test_non_rst_include_drift_between_actions_should_fail(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = self._projection(root)
            check = capture_projection(
                manifest, action="check", model="MODEL", region="US", language="en"
            )
            (manifest.parent / "snippets" / "detail.inc").write_text(
                "Changed after check.\n", encoding="utf-8"
            )
            md = capture_projection(
                manifest, action="md", model="MODEL", region="US", language="en"
            )
            html = capture_projection(
                manifest, action="html", model="MODEL", region="US", language="en"
            )

            with self.assertRaisesRegex(RuntimeError, "changed across"):
                require_consistent_captures((check, md, html))

    def test_verify_should_reject_release_identity_or_output_drift(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = self._projection(root)
            md, html = self._outputs(root)
            receipt = seal_release_evidence(
                captures=self._captures(manifest),
                markdown_dir=md,
                markdown_name="manual.md",
                html_dir=html,
                evidence_dir=root / "web" / "evidence",
                version="2.0",
                git_ref="review/MODEL-US",
            )
            common = dict(
                receipt_path=receipt,
                expected_sha256=_sha256(receipt),
                model="MODEL",
                region="US",
                language="en",
                markdown_dir=md,
                markdown_name="manual.md",
                html_dir=html,
            )
            with self.assertRaisesRegex(RuntimeError, "version|identity|release"):
                verify_release_evidence(
                    **common, version="3.0", git_ref="review/MODEL-US"
                )
            with self.assertRaisesRegex(RuntimeError, "git_ref|identity|release"):
                verify_release_evidence(
                    **common, version="2.0", git_ref="review/CHANGED"
                )
            (html / "index.html").write_text("tampered\n", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "HTML files differ"):
                verify_release_evidence(
                    **common, version="2.0", git_ref="review/MODEL-US"
                )

    def test_stored_verification_should_recheck_markdown_without_html(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = self._projection(root)
            md, html = self._outputs(root)
            receipt = seal_release_evidence(
                captures=self._captures(manifest),
                markdown_dir=md,
                markdown_name="manual.md",
                html_dir=html,
                evidence_dir=root / "web" / "evidence",
                version="2.0",
                git_ref="review/MODEL-US",
            )
            stored_md = root / "stored" / "md"
            shutil.copytree(md, stored_md)
            shutil.copytree(receipt.parent, stored_md / "evidence")
            (stored_md / "publish_meta.json").write_text("{}\n", encoding="utf-8")

            verify_release_evidence(
                stored_md / "evidence" / RECEIPT_FILENAME,
                expected_sha256=_sha256(receipt),
                model="MODEL",
                region="US",
                language="en",
                version="2.0",
                git_ref="review/MODEL-US",
                markdown_dir=stored_md,
                markdown_name="manual.md",
                html_dir=None,
                stored=True,
            )
            rogue = stored_md / "evidence" / "rogue.md"
            rogue.write_text("untracked body\n", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "unexpected files"):
                verify_release_evidence(
                    stored_md / "evidence" / RECEIPT_FILENAME,
                    expected_sha256=_sha256(receipt),
                    model="MODEL",
                    region="US",
                    language="en",
                    version="2.0",
                    git_ref="review/MODEL-US",
                    markdown_dir=stored_md,
                    markdown_name="manual.md",
                    html_dir=None,
                    stored=True,
                )
            rogue.unlink()
            (stored_md / "manual.md").write_text("tampered\n", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "Markdown files differ"):
                verify_release_evidence(
                    stored_md / "evidence" / RECEIPT_FILENAME,
                    expected_sha256=_sha256(receipt),
                    model="MODEL",
                    region="US",
                    language="en",
                    version="2.0",
                    git_ref="review/MODEL-US",
                    markdown_dir=stored_md,
                    markdown_name="manual.md",
                    html_dir=None,
                    stored=True,
                )


if __name__ == "__main__":
    unittest.main()
