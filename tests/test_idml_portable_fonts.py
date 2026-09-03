from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path
import zipfile

from tools.idml.font_assets import portable_font_assets_for_idml


ROOT = Path(__file__).resolve().parents[1]
FONT_ROOT = (
    ROOT
    / "docs"
    / "templates"
    / "word_template"
    / "common_assets"
    / "fonts"
    / "idml_portable"
)


class IdmlPortableFontsTest(unittest.TestCase):
    def test_open_font_binaries_are_exact_and_repo_local(self) -> None:
        expected = {
            "NanumGothic-Regular.ttf": (
                "76f45ef4a6bcff344c837c95a7dcc26e017e38b5846d5ae0cdcb5b86be2e2d31"
            ),
            "NotoSans-Regular.ttf": (
                "b85c38ecea8a7cfb39c24e395a4007474fa5a4fc864f6ee33309eb4948d232d5"
            ),
            "HBManualSansJP-Regular.ttf": (
                "f9f17753c415ad76e82ae317c17e2260523deb73406d6baad14a817e5be957dd"
            ),
            # Three further weights instanced from the same variable source the
            # Regular came from, because the shipped book sets 57% of its
            # Japanese characters in a non-Regular weight.
            "HBManualSansJP-DemiLight.ttf": (
                "e23045b95f654af21d8b823b0ec1d15a27af23771da336a8b368911ad349bc2a"
            ),
            "HBManualSansJP-Medium.ttf": (
                "1e8a2e2d0718e1bcb472b94ff4cd4b9dba4db3d299d3482be32cf177bc8d4fe4"
            ),
            "HBManualSansJP-Bold.ttf": (
                "f579205a74cdec9d092205c9f2bdf14f5c69f93565202bc4e3eeb6a0881e3e43"
            ),
            "NotoSansSymbols-Regular.ttf": (
                "8f02f31959bbdf6061547a188248e13f84dc5fdd940326ec494675f453f072bb"
            ),
            "NotoSansSymbols2-Regular.ttf": (
                "630846d528dbe4c4981370a4d0a9475a1fd1491a129bb411f8e157cdb5de13c6"
            ),
        }
        self.assertEqual(
            set(expected),
            {
                path.name
                for suffix in ("*.ttf", "*.otf")
                for path in FONT_ROOT.glob(suffix)
            },
        )
        for filename, digest in expected.items():
            with self.subTest(filename=filename):
                payload = (FONT_ROOT / filename).read_bytes()
                self.assertEqual(digest, hashlib.sha256(payload).hexdigest())

    def test_each_upstream_has_a_redistribution_notice(self) -> None:
        for filename, copyright_text in (
            ("OFL-Noto.txt", "The Noto Project Authors"),
            ("OFL-NanumGothic.txt", "NHN Corporation"),
        ):
            with self.subTest(filename=filename):
                text = (FONT_ROOT / filename).read_text(encoding="utf-8")
                self.assertIn("SIL OPEN FONT LICENSE Version 1.1", text)
                self.assertIn(copyright_text, text)

    def test_legacy_zip_without_fonts_resource_declares_no_portable_fonts(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "legacy.idml"
            with zipfile.ZipFile(path, "w") as package:
                package.writestr("mimetype", "application/vnd.adobe.indesign-idml-package")
            self.assertEqual((), portable_font_assets_for_idml(path))


if __name__ == "__main__":
    unittest.main()
