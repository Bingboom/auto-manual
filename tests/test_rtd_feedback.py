from __future__ import annotations

import unittest
import json
import shutil
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.rtd_feedback import context_text, manual_feedback_markup, normalize_channels
from tests.web_language_evidence_fixture import seal_language_evidence_fixture


class RtdFeedbackTests(unittest.TestCase):
    def test_empty_channels_disable_markup(self) -> None:
        self.assertEqual([], normalize_channels([]))
        self.assertEqual("", manual_feedback_markup(channels=[], context="context"))

    def test_context_contains_only_frozen_publication_identity(self) -> None:
        value = context_text(model="JE-TEST", region="EU", lang="fr", version="1.2", page="JE-TEST/EU/fr/md/manual.html")
        self.assertIn("Page: JE-TEST/EU/fr/md/manual.html", value)
        self.assertNotIn("location", value)
        self.assertNotIn("?", value)
        self.assertNotIn("#", value)

    def test_channels_require_fixed_https_without_query_or_credentials(self) -> None:
        valid = normalize_channels([{"label": "Support", "url": "https://support.example.test/report"}])
        self.assertEqual("Support", valid[0]["label"])
        for url in (
            "http://support.example.test/report",
            "https://user:secret@support.example.test/report",
            "https://support.example.test/report?token=secret",
            "https://support.example.test/report#private",
            "https://support.example.test/\nreport",
            "https://[not-an-ip]/report",
            "https://support.example.test\\report",
            "https://%65xample.test/report",
            " https://support.example.test/report\n",
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                normalize_channels([{"label": "Support", "url": url}])

    def test_sphinx_default_and_explicit_empty_feedback_are_byte_identical(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            source, _ = self._fixture(root / "default", channels=None)
            first = self._build(source, root / "first")
            source, _ = self._fixture(root / "explicit", channels=[])
            second = self._build(source, root / "second")
            self.assertEqual(
                (first / "JE-TEST/EU/fr/md/manual.html").read_bytes(),
                (second / "JE-TEST/EU/fr/md/manual.html").read_bytes(),
            )
            for output in (first, second):
                html = (output / "JE-TEST/EU/fr/md/manual.html").read_text(encoding="utf-8")
                self.assertNotIn("manual-feedback", html)

    def test_sphinx_enabled_feedback_is_local_and_legacy_is_not_injected(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            source, _ = self._fixture(
                root,
                channels=[{"label": "Support", "url": "https://support.example.test/report"}],
                include_legacy=True,
            )
            output = self._build(source, root / "enabled")
            page = (output / "JE-TEST/EU/fr/md/manual.html").read_text(encoding="utf-8")
            self.assertIn("Model: JE-TEST", page)
            self.assertIn("Page: JE-TEST/EU/fr/md/manual.html", page)
            self.assertIn("manual-feedback.js", page)
            self.assertIn("Copy context", page)
            self.assertIn("https://support.example.test/report", page)
            self.assertNotIn("?model=", page)
            legacy = (output / "JE-TEST/EU/md/manual_legacy.html").read_text(encoding="utf-8")
            self.assertNotIn("manual-feedback", legacy)

    @staticmethod
    def _fixture(root: Path, *, channels: list[dict[str, str]] | None, include_legacy: bool = False) -> tuple[Path, Path]:
        source = root / "web"
        single = source / "JE-TEST/EU/fr/md"
        single.mkdir(parents=True)
        (single / "manual.md").write_text("# French manual\n", encoding="utf-8")
        links = ["- [Jackery French User Manual](JE-TEST/EU/fr/md/manual.md)"]
        if include_legacy:
            legacy = source / "JE-TEST/EU/md"
            legacy.mkdir(parents=True)
            (legacy / "manual_legacy.md").write_text("# Legacy manual\n", encoding="utf-8")
            links.append("- [Jackery Legacy User Manual](JE-TEST/EU/md/manual_legacy.md)")
        toctree = "\nJE-TEST/EU/fr/md/manual"
        if include_legacy:
            toctree += "\nJE-TEST/EU/md/manual_legacy"
        (source / "index.md").write_text("\n".join(links) + f"\n\n```{{toctree}}\n{toctree}\n```\n", encoding="utf-8")
        metadata = root / "sources/web/JE-TEST/EU/fr/md"
        metadata.mkdir(parents=True)
        (metadata / "manual.md").write_bytes((single / "manual.md").read_bytes())
        verification_html = root / "verification-html"
        verification_html.mkdir()
        (verification_html / "index.html").write_text("<html></html>\n", encoding="utf-8")
        receipt, receipt_sha256 = seal_language_evidence_fixture(
            markdown_dir=metadata,
            markdown_name="manual.md",
            html_dir=verification_html,
            evidence_dir=metadata / "evidence",
            model="JE-TEST",
            region="EU",
            language="fr",
            version="1.2",
            git_ref="review/JE-TEST-EU",
        )
        (metadata / "publish_meta.json").write_text(json.dumps({
            "schema_version": "auto-manual-web-publish-target/v2", "model": "JE-TEST",
            "region": "EU", "lang": "fr", "version": "1.2", "route": "JE-TEST/EU/fr/md",
            "git_ref": "review/JE-TEST-EU", "manual": "manual.md", "legacy_default": True,
            "language_scope": "single",
            "language_projection_evidence_path": "evidence/" + receipt.name,
            "language_projection_evidence_sha256": receipt_sha256,
        }), encoding="utf-8")
        assets = root / "portal-assets"
        shutil.copytree(Path(__file__).parents[1] / "tools/rtd_portal_assets", assets)
        settings = json.loads((assets / "settings.json").read_text(encoding="utf-8"))
        if channels is None:
            settings.pop("feedback_channels", None)
        else:
            settings["feedback_channels"] = channels
        (assets / "settings.json").write_text(json.dumps(settings), encoding="utf-8")
        (source / "conf.py").write_text(
            "from pathlib import Path\n"
            "import tools.rtd_portal as portal\n"
            f"portal.ASSETS = Path({str(assets)!r})\n"
            "extensions = ['myst_parser', 'tools.rtd_portal']\nhtml_theme = 'furo'\n",
            encoding="utf-8",
        )
        return source, assets

    @staticmethod
    def _build(source: Path, output: Path) -> Path:
        result = subprocess.run(
            [sys.executable, "-m", "sphinx", "-q", "-b", "html", str(source), str(output)],
            cwd=Path(__file__).parents[1], capture_output=True, text=True,
        )
        if result.returncode:
            raise AssertionError(result.stdout + result.stderr)
        return output

    def test_markup_has_no_js_copy_fallback_and_escapes_values(self) -> None:
        markup = manual_feedback_markup(
            channels=[{"label": "<Support>", "url": "https://support.example.test/report"}],
            context="Page: JE-TEST/EU/fr/md/manual.html",
        )
        self.assertIn("manual-feedback-context", markup)
        self.assertIn("Copy context", markup)
        self.assertIn("&lt;Support&gt;", markup)
        self.assertIn("rel=\"noreferrer\"", markup)


if __name__ == "__main__":
    unittest.main()
