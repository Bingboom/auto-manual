from __future__ import annotations

import io
import os
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from tools import release_manifest, release_rebuild
from tools.utils import log


class ReleaseLoggingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.addCleanup(log.configure)

    def test_manifest_result_is_complete_at_default_and_warning_levels(self) -> None:
        for level in (None, "WARNING"):
            with self.subTest(level=level):
                stdout, stderr = io.StringIO(), io.StringIO()
                with mock.patch.dict(os.environ, {}, clear=True):
                    if level is not None:
                        os.environ[log.LEVEL_ENV] = level
                    log.configure()
                    with mock.patch.object(
                        release_manifest,
                        "build_release_manifest",
                        return_value=(Path("release.json"), Path("release.csv")),
                    ), redirect_stdout(stdout), redirect_stderr(stderr):
                        result = release_manifest.main(
                            ["--config", "config.yaml", "--model", "test", "--region", "test"]
                        )
                self.assertEqual(result, 0)
                self.assertEqual(
                    stdout.getvalue(),
                    "[release-manifest] JSON: release.json\n[release-manifest] CSV: release.csv\n",
                )
                self.assertEqual(stderr.getvalue(), "")

    def test_rebuild_result_is_complete_at_default_and_warning_levels(self) -> None:
        for level in (None, "WARNING"):
            with self.subTest(level=level):
                stdout, stderr = io.StringIO(), io.StringIO()
                with mock.patch.dict(os.environ, {}, clear=True):
                    if level is not None:
                        os.environ[log.LEVEL_ENV] = level
                    log.configure()
                    with mock.patch.object(
                        release_rebuild,
                        "verify_release_rebuild",
                        return_value=(Path("verification.json"), {}),
                    ), redirect_stdout(stdout), redirect_stderr(stderr):
                        result = release_rebuild.main(["--manifest", "release.json"])
                self.assertEqual(result, 0)
                self.assertEqual(
                    stdout.getvalue(),
                    "[release-rebuild] byte-equivalence verified: verification.json\n",
                )
                self.assertEqual(stderr.getvalue(), "")

    def test_errors_preserve_text_newlines_stderr_and_exit_code(self) -> None:
        cases = (
            (
                release_manifest,
                "build_release_manifest",
                ["--config", "config.yaml", "--model", "test", "--region", "test"],
                "release-manifest",
            ),
            (release_rebuild, "verify_release_rebuild", ["--manifest", "release.json"], "release-rebuild"),
        )
        for module, boundary, args, component in cases:
            for level in (None, "WARNING"):
                for message in ("failed", "first\nsecond\n"):
                    with self.subTest(component=component, level=level, message=message):
                        stdout, stderr = io.StringIO(), io.StringIO()
                        with mock.patch.dict(os.environ, {}, clear=True):
                            if level is not None:
                                os.environ[log.LEVEL_ENV] = level
                            log.configure()
                            with mock.patch.object(
                                module, boundary, side_effect=RuntimeError(message)
                            ), redirect_stdout(stdout), redirect_stderr(stderr):
                                result = module.main(args)
                        self.assertEqual(result, 1)
                        self.assertEqual(stdout.getvalue(), "")
                        self.assertEqual(stderr.getvalue(), f"[{component}] ERROR: {message}\n")


if __name__ == "__main__":
    unittest.main()
