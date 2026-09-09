from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.build_paths import resolve_web_illustration_manifest


class WebIllustrationManifestPathTests(unittest.TestCase):
    def test_resolves_document_key_selected_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = root / "config.yaml"
            resolved = resolve_web_illustration_manifest(
                config,
                repo_root=root,
                model="JE-2000F",
                region="EU",
                config_loader=lambda _: {
                    "paths": {
                        "web_illustration_manifests": {
                            "JE-2000F_EU": "docs/renderers/web/illustrations.json"
                        }
                    }
                },
            )
            self.assertEqual(
                resolved,
                root / "docs/renderers/web/illustrations.json",
            )

    def test_expands_model_and_region_in_family_manifest(self) -> None:
        for model in ("JA-AD01A", "JA-AD600A", "JA-CA3SA"):
            with self.subTest(model=model):
                resolved = resolve_web_illustration_manifest(
                    Path("config.yaml"), repo_root=Path("/repo"),
                    model=model, region="EU",
                    config_loader=lambda _: {"paths": {
                        "web_illustration_manifest": "art/{region}/{model}.json"
                    }},
                )
                self.assertEqual(Path(f"/repo/art/EU/{model}.json"), resolved)

    def test_unselected_target_has_no_manifest(self) -> None:
        resolved = resolve_web_illustration_manifest(
            Path("config.yaml"),
            repo_root=Path("/repo"),
            model="JE-1000F",
            region="EU",
            config_loader=lambda _: {
                "paths": {
                    "web_illustration_manifests": {
                        "JE-2000F_EU": "docs/renderers/web/illustrations.json"
                    }
                }
            },
        )
        self.assertIsNone(resolved)

    def test_rejects_global_and_target_mapping_together(self) -> None:
        with self.assertRaisesRegex(ValueError, "mutually exclusive"):
            resolve_web_illustration_manifest(
                Path("config.yaml"),
                repo_root=Path("/repo"),
                model="JE-2000F",
                region="EU",
                config_loader=lambda _: {
                    "paths": {
                        "web_illustration_manifest": "one.json",
                        "web_illustration_manifests": {
                            "JE-2000F_EU": "two.json"
                        },
                    }
                },
            )

    def test_rejects_case_insensitive_duplicate_target_keys(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicate case-insensitive"):
            resolve_web_illustration_manifest(
                Path("config.yaml"),
                repo_root=Path("/repo"),
                model="JE-2000F",
                region="EU",
                config_loader=lambda _: {
                    "paths": {
                        "web_illustration_manifests": {
                            "JE-2000F_EU": "one.json",
                            "je-2000f_eu": "two.json",
                        }
                    }
                },
            )


if __name__ == "__main__":
    unittest.main()
