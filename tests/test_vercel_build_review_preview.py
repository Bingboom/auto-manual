from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.process_docs import vercel_build_review_preview


class TestVercelBuildReviewPreview(unittest.TestCase):
    def test_discover_default_preview_configs_should_match_current_defaults(self) -> None:
        self.assertEqual(
            {
                "US": "configs/config.us.yaml",
                "JP": "configs/config.ja.yaml",
                "CN": "configs/config.zh.yaml",
            },
            vercel_build_review_preview.discover_default_preview_configs(),
        )

    def test_discover_default_preview_target_from_configs_should_resolve_first_family_target(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            configs_dir = Path(td)
            (configs_dir / "config.us.yaml").write_text(
                "build:\n  default_model: MODEL-US\n  default_region: US\n  languages: [en, fr]\n",
                encoding="utf-8",
            )
            (configs_dir / "config.ja.yaml").write_text(
                "build:\n  default_model: MODEL-JP\n  default_region: JP\n  languages: [ja]\n",
                encoding="utf-8",
            )
            (configs_dir / "config.zh.yaml").write_text(
                "build:\n  default_model: MODEL-CN\n  default_region: CN\n  languages: [zh]\n",
                encoding="utf-8",
            )

            target = vercel_build_review_preview.discover_default_preview_target_from_configs(configs_dir)

        self.assertEqual(("MODEL-US", "US"), target)

    def test_discover_default_preview_target_should_return_first_sorted_target(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            review_root = Path(td)
            (review_root / "JE-2000A" / "US").mkdir(parents=True)
            (review_root / "JE-1000F" / "JP").mkdir(parents=True)

            target = vercel_build_review_preview.discover_default_preview_target(review_root)

            self.assertEqual(("JE-1000F", "JP"), target)

    def test_resolve_preview_target_should_prefer_environment(self) -> None:
        with mock.patch.dict(
            "os.environ",
            {"PREVIEW_MODEL": "MODEL-X", "PREVIEW_REGION": "EU"},
            clear=False,
        ):
            target = vercel_build_review_preview.resolve_preview_target(Path("missing"))

        self.assertEqual(("MODEL-X", "EU"), target)

    def test_resolve_preview_target_should_fallback_to_review_tree(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            review_root = Path(td)
            (review_root / "JE-1000F" / "US").mkdir(parents=True)
            with mock.patch.dict("os.environ", {"PREVIEW_MODEL": "", "PREVIEW_REGION": ""}, clear=False):
                target = vercel_build_review_preview.resolve_preview_target(review_root)

        self.assertEqual(("JE-1000F", "US"), target)

    def test_resolve_preview_target_should_fallback_to_config_scan(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            configs_dir = Path(td)
            for filename, model, region, languages in (
                ("config.us.yaml", "MODEL-US", "US", "en, fr"),
                ("config.ja.yaml", "MODEL-JP", "JP", "ja"),
                ("config.zh.yaml", "MODEL-CN", "CN", "zh"),
            ):
                (configs_dir / filename).write_text(
                    f"build:\n  default_model: {model}\n  default_region: {region}\n  languages: [{languages}]\n",
                    encoding="utf-8",
                )

            with mock.patch.dict("os.environ", {"PREVIEW_MODEL": "", "PREVIEW_REGION": ""}, clear=False):
                target = vercel_build_review_preview.resolve_preview_target(
                    Path(td) / "missing-review",
                    configs_dir=configs_dir,
                )

        self.assertEqual(("MODEL-US", "US"), target)

    def test_default_preview_config_should_map_family_defaults(self) -> None:
        self.assertEqual("configs/config.us.yaml", vercel_build_review_preview.default_preview_config("US"))
        self.assertEqual("configs/config.ja.yaml", vercel_build_review_preview.default_preview_config("jp"))

    def test_build_preview_command_should_derive_target_without_hardcoded_model(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            review_root = Path(td)
            (review_root / "EXPLORER-500" / "US").mkdir(parents=True)

            with mock.patch.dict("os.environ", {}, clear=True):
                cmd = vercel_build_review_preview.build_preview_command(
                    Path("/python"),
                    review_root=review_root,
                )

        self.assertEqual("python", Path(cmd[0]).name)
        self.assertIn("--model", cmd)
        self.assertIn("EXPLORER-500", cmd)
        self.assertIn("--region", cmd)
        self.assertIn("US", cmd)
        self.assertIn("--config", cmd)
        self.assertIn("configs/config.us.yaml", cmd)
        self.assertIn("--data-root", cmd)
        self.assertIn("tests/fixtures/phase2", cmd)

    def test_build_preview_command_should_allow_data_root_override(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            review_root = Path(td)
            (review_root / "EXPLORER-500" / "US").mkdir(parents=True)

            with mock.patch.dict("os.environ", {"PREVIEW_DATA_ROOT": "data/phase2"}, clear=True):
                cmd = vercel_build_review_preview.build_preview_command(
                    Path("/python"),
                    review_root=review_root,
                )

        self.assertIn("--data-root", cmd)
        self.assertIn("data/phase2", cmd)
