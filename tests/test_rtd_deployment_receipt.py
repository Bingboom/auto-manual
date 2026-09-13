from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tools import rtd_deployment_receipt as receipt


class DeploymentReceiptTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.web = root / "publish/web"
        self.web.mkdir(parents=True)
        (self.web.parent / "publish_manifest.json").write_text('{"record_id":"private"}')
        (self.web / "index.md").write_text("released version")
        self.output = root / "html"
        self.output.mkdir()
        (self.output / "manual.html").write_text('<link rel="stylesheet" href="theme.css"><img src="image.png">')
        (self.output / "theme.css").write_text('body{background:url(background.png)}')
        (self.output / "image.png").write_bytes(b"image")
        (self.output / "background.png").write_bytes(b"background")
        (self.output / "unrelated.png").write_bytes(b"unrelated")
        self.app = SimpleNamespace(srcdir=self.web, outdir=self.output,
                                   builder=SimpleNamespace(format="html"))
        receipt.write_deployment_receipt(self.app, None)

    def fetch(self, url):
        return (self.output / url.removeprefix("https://example.org/")).read_bytes()

    def verify(self):
        with patch.object(receipt, "_fetch", side_effect=self.fetch):
            return receipt.verify_deployment(self.web, "https://example.org", ["manual.html"])

    def test_valid_recursive_resources_exclude_unrelated(self):
        self.assertEqual(self.verify()["verified_files"], 4)
        self.assertNotIn("private", (self.output / receipt.RECEIPT).read_text())

    def test_stale_source_rejected(self):
        (self.web / "index.md").write_text("different version")
        with self.assertRaisesRegex(ValueError, "frozen source"):
            self.verify()

    def test_changed_image_rejected(self):
        (self.output / "image.png").write_bytes(b"wrong")
        with self.assertRaisesRegex(ValueError, "bytes differ"):
            self.verify()

    def test_missing_dependency_rejected(self):
        (self.output / "image.png").unlink()
        with self.assertRaises(FileNotFoundError):
            self.verify()

    def test_dependency_not_in_receipt_rejected(self):
        payload = json.loads((self.output / receipt.RECEIPT).read_text())
        del payload["files"]["image.png"]
        (self.output / receipt.RECEIPT).write_text(json.dumps(payload))
        with self.assertRaisesRegex(ValueError, "referenced resource"):
            self.verify()

    def test_partial_routes_rejected(self):
        with patch.object(receipt, "_fetch", side_effect=self.fetch):
            with self.assertRaisesRegex(ValueError, "selected routes"):
                receipt.verify_deployment(self.web, "https://example.org", ["manual.html", "absent.html"])

    def test_failed_and_unrelated_builds_do_not_write(self):
        target = self.output / receipt.RECEIPT
        target.unlink()
        receipt.write_deployment_receipt(self.app, RuntimeError("failed"))
        self.assertFalse(target.exists())
        self.app.srcdir = self.output
        receipt.write_deployment_receipt(self.app, None)
        self.assertFalse(target.exists())

    def test_source_symlink_rejected(self):
        (self.web / "link").symlink_to(self.web / "index.md")
        with self.assertRaisesRegex(ValueError, "symlinks"):
            receipt.source_fingerprint(self.web)

    def test_unsafe_base_and_route_rejected_before_network(self):
        for base, routes in [("http://example.org", ["manual.html"]),
                             ("https://a:b@example.org", ["manual.html"]),
                             ("https://example.org?x=y", ["manual.html"]),
                             ("https://example.org", ["../manual.html"]),
                             ("https://example.org", ["%2e%2e/manual.html"])]:
            with self.subTest(base=base, routes=routes), patch.object(receipt, "_fetch") as fetch:
                with self.assertRaises(ValueError):
                    receipt.verify_deployment(self.web, base, routes)
                fetch.assert_not_called()

    def test_limits_fail_closed(self):
        with patch.object(receipt, "MAX_FILES", 1):
            with self.assertRaises(ValueError):
                self.verify()

    def test_real_frozen_sphinx_build_emits_verifiable_receipt(self):
        (self.web / "conf.py").write_text(
            "project='Receipt fixture'\n"
            "extensions=['myst_parser', 'tools.rtd_portal']\n"
            "html_static_path=['_static']\n"
            "from pathlib import Path\n"
            "def copy_late_asset(app, exception):\n"
            "    if exception is None:\n"
            "        (Path(app.outdir) / 'late.svg').write_text(\"<svg/>\")\n"
            "def setup(app):\n"
            "    app.connect('build-finished', copy_late_asset)\n"
        )
        static = self.web / "_static"
        static.mkdir()
        (static / "figure.svg").write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="2" height="2"/>'
        )
        (self.web / "index.md").write_text(
            '# Frozen manual\n\n<img src="_static/figure.svg" alt="Figure"/>\n'
            '<img src="late.svg" alt="Late copied asset"/>\n'
        )
        before = receipt.source_fingerprint(self.web)
        built = self.output.parent / "sphinx-html"
        result = subprocess.run(
            [sys.executable, "-m", "sphinx", "-q", "-W", "-b", "html",
             str(self.web), str(built)],
            cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(before, receipt.source_fingerprint(self.web))
        payload = json.loads((built / receipt.RECEIPT).read_text())
        self.assertEqual(payload["source_sha256"], before)
        self.assertIn("index.html", payload["files"])
        self.assertIn("_static/figure.svg", payload["files"])
        self.assertIn("late.svg", payload["files"])
        self.assertNotIn(receipt.RECEIPT, payload["files"])
        self.assertFalse(any(p.startswith(".doctrees/") for p in payload["files"]))
        base = "https://example.org/en/latest/"
        with patch.object(receipt, "_fetch", side_effect=lambda url:
                          (built / url.removeprefix(base)).read_bytes()):
            evidence = receipt.verify_deployment(self.web, base, ["index.html"])
        self.assertEqual(evidence["status"], "verified")
        self.assertGreater(evidence["verified_files"], 2)
        (built / "_static/figure.svg").write_text("stale artwork")
        with patch.object(receipt, "_fetch", side_effect=lambda url:
                          (built / url.removeprefix(base)).read_bytes()):
            with self.assertRaisesRegex(ValueError, "bytes differ"):
                receipt.verify_deployment(self.web, base, ["index.html"])

    def test_non_html_build_does_not_write(self):
        target = self.output / receipt.RECEIPT
        target.unlink()
        self.app.builder.format = "latex"
        receipt.write_deployment_receipt(self.app, None)
        self.assertFalse(target.exists())

    def test_html_base_override_rejected(self):
        (self.output / "manual.html").write_text('<base href="https://other.org/">')
        receipt.write_deployment_receipt(self.app, None)
        with self.assertRaisesRegex(ValueError, "base URL overrides"):
            self.verify()

    def test_dependency_cannot_escape_publication_prefix(self):
        with self.assertRaisesRegex(ValueError, "escapes the publication root"):
            receipt._dependencies("manual.html", b'<img src="/outside.png">',
                                  "https://example.org/en/latest")

    def test_cross_origin_redirect_rejected(self):
        req = SimpleNamespace(full_url="https://example.org/file")
        with self.assertRaisesRegex(ValueError, "Cross-origin"):
            receipt._Redirect().redirect_request(req, None, 302, "", {}, "https://other.org/file")


if __name__ == "__main__":
    unittest.main()
