from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.process_docs import vercel_build_review_preview


class TestVercelBuildReviewPreview(unittest.TestCase):
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

    def test_default_preview_config_should_map_family_defaults(self) -> None:
        self.assertEqual("config.us.yaml", vercel_build_review_preview.default_preview_config("US"))
        self.assertEqual("config.ja.yaml", vercel_build_review_preview.default_preview_config("jp"))

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
        self.assertIn("config.us.yaml", cmd)
