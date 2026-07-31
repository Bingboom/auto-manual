from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

from tools import release_tag
from tools.release_contract import release_tag_for_target


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout.strip()


class TestReleaseTag(unittest.TestCase):
    def test_release_tag_for_target_should_cover_all_build_languages(self) -> None:
        self.assertEqual(
            "manual-release/je-1000f/us/en-fr-es/0.8-rc1",
            release_tag_for_target(
                model="JE-1000F",
                region="US",
                languages=["en", "fr", "es"],
                version="0.8 RC1",
            ),
        )

    def test_release_tag_should_create_verify_and_reject_rebound_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _git(root, "init")
            _git(root, "config", "user.name", "Release Test")
            _git(root, "config", "user.email", "release@example.com")
            (root / "tracked.txt").write_text("release\n", encoding="utf-8")
            _git(root, "add", "tracked.txt")
            _git(root, "commit", "-m", "release source")
            git_sha = _git(root, "rev-parse", "HEAD")
            manifest_path = root / "release.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "release_tag": "manual-release/je-1000f/jp/ja/1.0",
                        "git_sha": git_sha,
                        "release_version": "1.0",
                        "model": "JE-1000F",
                        "region": "JP",
                        "build_languages": ["ja"],
                        "snapshot": {"snapshot_sha256": "a" * 64},
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            with mock.patch.object(release_tag, "ROOT", root):
                self.assertEqual(0, release_tag.main(["--manifest", str(manifest_path)]))
                self.assertFalse(
                    _git(root, "tag", "--list", "manual-release/je-1000f/jp/ja/1.0")
                )
                self.assertEqual(
                    0,
                    release_tag.main(["--manifest", str(manifest_path), "--write"]),
                )
                self.assertEqual(
                    0,
                    release_tag.main(["--manifest", str(manifest_path), "--write"]),
                )

                payload = json.loads(manifest_path.read_text(encoding="utf-8"))
                payload["extra"] = "rebound"
                manifest_path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
                self.assertEqual(
                    1,
                    release_tag.main(["--manifest", str(manifest_path), "--write"]),
                )

    def test_release_tag_should_require_frozen_snapshot_identity(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            manifest_path = Path(td) / "release.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "release_tag": "manual-release/je-1000f/us/en/1.0",
                        "git_sha": "a" * 40,
                        "release_version": "1.0",
                        "model": "JE-1000F",
                        "region": "US",
                        "build_languages": ["en"],
                        "snapshot": {"snapshot_sha256": ""},
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(RuntimeError, "snapshot_sha256"):
                release_tag.build_release_tag_plan(manifest_path)

    def test_release_tag_should_push_to_remote(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "repo"
            remote = Path(td) / "remote.git"
            root.mkdir()
            _git(root, "init")
            _git(root, "config", "user.name", "Release Test")
            _git(root, "config", "user.email", "release@example.com")
            (root / "tracked.txt").write_text("release\n", encoding="utf-8")
            _git(root, "add", "tracked.txt")
            _git(root, "commit", "-m", "release source")
            git_sha = _git(root, "rev-parse", "HEAD")
            subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
            _git(root, "remote", "add", "origin", str(remote))
            manifest_path = root / "release.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "release_tag": "manual-release/je-1000f/us/en/1.0",
                        "git_sha": git_sha,
                        "release_version": "1.0",
                        "model": "JE-1000F",
                        "region": "US",
                        "build_languages": ["en"],
                        "snapshot": {"snapshot_sha256": "b" * 64},
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            with mock.patch.object(release_tag, "ROOT", root):
                self.assertEqual(
                    0,
                    release_tag.main(
                        ["--manifest", str(manifest_path), "--write", "--push"]
                    ),
                )

            self.assertTrue(
                subprocess.run(
                    [
                        "git",
                        "--git-dir",
                        str(remote),
                        "show-ref",
                        "--verify",
                        "--quiet",
                        "refs/tags/manual-release/je-1000f/us/en/1.0",
                    ],
                    check=False,
                ).returncode
                == 0
            )


if __name__ == "__main__":
    unittest.main()
