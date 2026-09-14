from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.build_paths import (
    resolve_web_illustration_manifest_from_config,
    resolve_web_illustration_manifests_from_config,
)


def _config(binding: object) -> dict:
    return {
        "build": {"default_model": "JE-2000F", "default_region": "EU"},
        "paths": {"web_illustration_manifests": {"JE-2000F_EU": binding}},
    }


class PerLanguageManifestResolutionTests(unittest.TestCase):
    """A merged book binds one manifest per language; a single book keeps one."""

    def test_scalar_binding_stays_a_single_manifest(self) -> None:
        cfg = _config("docs/renderers/web/je2000f_eu_en_illustrations.json")
        root = Path("/repo")
        self.assertEqual(
            resolve_web_illustration_manifest_from_config(cfg, repo_root=root),
            root / "docs/renderers/web/je2000f_eu_en_illustrations.json",
        )
        # The scalar form is not a per-language binding.
        self.assertEqual(
            resolve_web_illustration_manifests_from_config(cfg, repo_root=root), {}
        )

    def test_language_mapping_resolves_every_language(self) -> None:
        cfg = _config({lang: f"art/{lang}.json" for lang in ("en", "fr", "uk")})
        root = Path("/repo")
        self.assertEqual(
            resolve_web_illustration_manifests_from_config(cfg, repo_root=root),
            {lang: root / f"art/{lang}.json" for lang in ("en", "fr", "uk")},
        )
        # A merged document has no single manifest, so the scalar resolver
        # must decline rather than pick one language arbitrarily.
        self.assertIsNone(
            resolve_web_illustration_manifest_from_config(cfg, repo_root=root)
        )

    def test_rejects_empty_and_malformed_language_mappings(self) -> None:
        root = Path("/repo")
        for binding in ({}, {"en": ""}, {"": "art/en.json"}, {"en": 5}):
            with self.subTest(binding=binding):
                with self.assertRaises(ValueError):
                    resolve_web_illustration_manifests_from_config(
                        _config(binding), repo_root=root
                    )

    def test_rejects_case_insensitive_duplicate_languages(self) -> None:
        with self.assertRaises(ValueError):
            resolve_web_illustration_manifests_from_config(
                _config({"en": "art/en.json", "EN": "art/en2.json"}),
                repo_root=Path("/repo"),
            )


class _Materialized:
    def __init__(self, languages: tuple[str, ...], lang: str = "") -> None:
        self.model = "JE-2000F"
        self.region = "EU"
        self.lang = lang
        self.languages = languages


class PerLanguageManifestBindingTests(unittest.TestCase):
    """The same source filename resolves to a different panel per language."""

    def _manifest(self, root: Path, lang: str) -> Path:
        art = root / f"panel_{lang}.png"
        art.write_bytes(f"finished-{lang}".encode())
        manifest = root / f"{lang}.json"
        manifest.write_text(
            json.dumps(
                {
                    "schema_version": "web-illustrations/v1",
                    "model": "JE-2000F",
                    "region": "EU",
                    "language": lang,
                    "illustrations": [
                        {
                            "replaces": ["front_product.jpg"],
                            "path": art.name,
                            "sha256": hashlib.sha256(art.read_bytes()).hexdigest(),
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        return manifest

    def test_merged_document_accepts_one_manifest_per_language(self) -> None:
        from tools.web_document_source import load_web_document

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifests = {lang: self._manifest(root, lang) for lang in ("en", "fr")}
            # Binding both forms at once is ambiguous and must fail closed.
            with self.assertRaises(ValueError):
                load_web_document(
                    _Materialized(("en", "fr")),
                    page_paths=[],
                    declarations={},
                    page_languages={},
                    active_tags=set(),
                    output_dir=root / "out",
                    composite_manifest=None,
                    illustration_manifest=manifests["en"],
                    illustration_manifests=manifests,
                )

    def test_rejects_a_language_the_document_never_declares(self) -> None:
        from tools.web_document_source import load_web_document

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifests = {"de": self._manifest(root, "de")}
            with self.assertRaises(ValueError):
                load_web_document(
                    _Materialized(("en", "fr")),
                    page_paths=[],
                    declarations={},
                    page_languages={},
                    active_tags=set(),
                    output_dir=root / "out",
                    composite_manifest=None,
                    illustration_manifests=manifests,
                )

    def test_rejects_a_manifest_filed_under_the_wrong_language(self) -> None:
        from tools.web_document_source import load_web_document

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # The manifest declares "en" but is bound as the French entry.
            mismatched = {"fr": self._manifest(root, "en")}
            with self.assertRaises(ValueError):
                load_web_document(
                    _Materialized(("en", "fr")),
                    page_paths=[],
                    declarations={},
                    page_languages={},
                    active_tags=set(),
                    output_dir=root / "out",
                    composite_manifest=None,
                    illustration_manifests=mismatched,
                )


if __name__ == "__main__":
    unittest.main()
