from __future__ import annotations

import argparse
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.asset_commands import run_asset_command


class TestAssetCommands(unittest.TestCase):
    def test_routes_asset_check_to_registry_runner(self) -> None:
        args = argparse.Namespace(action="asset-check")
        root = Path("/repo")

        with patch("tools.asset_commands.run_asset_check") as runner:
            run_asset_command(args, repo_root=root)

        runner.assert_called_once_with(args, repo_root=root)

    def test_routes_complete_asset_intake_to_intake_runner(self) -> None:
        args = argparse.Namespace(
            action="asset-intake",
            asset_source_key="source/master",
            asset_source_file=Path("master.ai"),
            asset_recipe=Path("recipe.json"),
            asset_output_root=Path("output"),
        )
        root = Path("/repo")

        with patch("tools.asset_commands.run_asset_intake") as runner:
            run_asset_command(args, repo_root=root)

        runner.assert_called_once_with(args, repo_root=root)

    def test_asset_intake_lists_every_missing_required_flag(self) -> None:
        args = argparse.Namespace(action="asset-intake")

        with self.assertRaisesRegex(
            RuntimeError,
            "--asset-source-key, --asset-source-file, --asset-recipe, --asset-output-root",
        ):
            run_asset_command(args, repo_root=Path("/repo"))

    def test_rejects_unknown_asset_action(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "unsupported asset action"):
            run_asset_command(
                argparse.Namespace(action="asset-promote"),
                repo_root=Path("/repo"),
            )


if __name__ == "__main__":
    unittest.main()
