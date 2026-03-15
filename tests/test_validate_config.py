from __future__ import annotations

import unittest

from tools.validate_config import validate


class TestValidateConfig(unittest.TestCase):
    def test_validate_should_accept_build_targets(self) -> None:
        cfg = {
            "build": {
                "languages": ["en"],
                "default_region": "US",
                "targets": [
                    {"model": "JE-2000F", "region": "US"},
                    {"model": "JE-1000F"},
                ],
            },
            "paths": {},
            "pages": [{"type": "rst_include", "lang": "en", "file": "templates/page_en/00_preface.rst"}],
        }

        issues = validate(cfg, strict_files=False)
        errors = [issue.msg for issue in issues if issue.level == "ERROR"]
        self.assertEqual([], errors)

    def test_validate_should_reject_invalid_build_targets(self) -> None:
        cfg = {
            "build": {
                "languages": ["en"],
                "targets": [{"region": "US"}],
            },
            "paths": {},
            "pages": [{"type": "rst_include", "lang": "en", "file": "templates/page_en/00_preface.rst"}],
        }

        issues = validate(cfg, strict_files=False)
        errors = [issue.msg for issue in issues if issue.level == "ERROR"]
        self.assertTrue(any("build.targets[1].model" in msg for msg in errors))

    def test_validate_should_accept_allowed_foreign_identity_literals(self) -> None:
        cfg = {
            "build": {"languages": ["en"]},
            "checks": {"allowed_foreign_identity_literals": ["Jackery Explorer 2000 Pro"]},
            "paths": {},
            "pages": [{"type": "rst_include", "lang": "en", "file": "templates/page_en/00_preface.rst"}],
        }

        issues = validate(cfg, strict_files=False)
        errors = [issue.msg for issue in issues if issue.level == "ERROR"]
        self.assertEqual([], errors)

    def test_validate_should_reject_invalid_allowed_foreign_identity_literals(self) -> None:
        cfg = {
            "build": {"languages": ["en"]},
            "checks": {"allowed_foreign_identity_literals": ["", 123]},
            "paths": {},
            "pages": [{"type": "rst_include", "lang": "en", "file": "templates/page_en/00_preface.rst"}],
        }

        issues = validate(cfg, strict_files=False)
        errors = [issue.msg for issue in issues if issue.level == "ERROR"]
        self.assertTrue(any("checks.allowed_foreign_identity_literals" in msg for msg in errors))


if __name__ == "__main__":
    unittest.main()
