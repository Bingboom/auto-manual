from __future__ import annotations

import importlib.util
import os
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "local_build.py"
MODULE_SPEC = importlib.util.spec_from_file_location("local_build_script", MODULE_PATH)
local_build = importlib.util.module_from_spec(MODULE_SPEC)
assert MODULE_SPEC is not None
assert MODULE_SPEC.loader is not None
MODULE_SPEC.loader.exec_module(local_build)


class TestLocalBuild(unittest.TestCase):
    def test_resolve_build_command_should_inject_default_staging_root(self) -> None:
        cmd = local_build.resolve_build_command(
            ["check", "--config", "config.us-en.yaml", "--model", "JE-1000F", "--region", "US"],
            python_exe="python",
            repo_root=Path("/repo"),
        )

        self.assertEqual(
            [
                "python",
                str(Path("/repo") / "build.py"),
                "check",
                "--staging-root",
                ".tmp/staging",
                "--config",
                "config.us-en.yaml",
                "--model",
                "JE-1000F",
                "--region",
                "US",
            ],
            cmd,
        )

    def test_resolve_build_command_should_preserve_explicit_staging_root(self) -> None:
        cmd = local_build.resolve_build_command(
            ["publish", "--staging-root", ".tmp/custom", "--config", "config.ja.yaml"],
            python_exe="python",
            repo_root=Path("/repo"),
        )

        self.assertEqual(
            [
                "python",
                str(Path("/repo") / "build.py"),
                "publish",
                "--staging-root",
                ".tmp/custom",
                "--config",
                "config.ja.yaml",
            ],
            cmd,
        )

    def test_resolve_build_command_should_respect_staging_env(self) -> None:
        original = os.environ.get("AUTO_MANUAL_STAGING_ROOT")
        os.environ["AUTO_MANUAL_STAGING_ROOT"] = ".tmp/from-env"
        try:
            cmd = local_build.resolve_build_command(
                ["diff-report", "--config", "config.us.yaml"],
                python_exe="python",
                repo_root=Path("/repo"),
            )
        finally:
            if original is None:
                os.environ.pop("AUTO_MANUAL_STAGING_ROOT", None)
            else:
                os.environ["AUTO_MANUAL_STAGING_ROOT"] = original

        self.assertEqual(
            [
                "python",
                str(Path("/repo") / "build.py"),
                "diff-report",
                "--config",
                "config.us.yaml",
            ],
            cmd,
        )

    def test_resolve_build_command_should_reject_review(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "staging-safe local actions"):
            local_build.resolve_build_command(["review"], python_exe="python", repo_root=Path("/repo"))


if __name__ == "__main__":
    unittest.main()
