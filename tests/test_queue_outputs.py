from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from tools import queue_outputs


class QueueOutputsTests(unittest.TestCase):
    def test_immutable_release_traceability_copy_should_refuse_drift(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source"
            destination = root / "destination"
            source.mkdir()
            (source / "identity.json").write_text('{"sha": "a"}\n', encoding="utf-8")

            queue_outputs.copy_immutable_tree(source, destination)
            queue_outputs.copy_immutable_tree(source, destination)
            (destination / "identity.json").write_text('{"sha": "b"}\n', encoding="utf-8")

            with self.assertRaisesRegex(RuntimeError, "immutable"):
                queue_outputs.copy_immutable_tree(source, destination)

    def test_immutable_tree_copy_failure_should_leave_no_partial_destination(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source"
            destination = root / "destination"
            source.mkdir()
            (source / "identity.json").write_text('{"sha": "a"}\n', encoding="utf-8")

            original_copytree = queue_outputs.shutil.copytree

            def fail_after_copy(src: Path, dst: Path, *args: object, **kwargs: object) -> None:
                original_copytree(src, dst, *args, **kwargs)
                raise OSError("injected copy failure")

            with mock.patch.object(queue_outputs.shutil, "copytree", side_effect=fail_after_copy):
                with self.assertRaisesRegex(OSError, "injected"):
                    queue_outputs.copy_immutable_tree(source, destination)

            self.assertFalse(destination.exists())

    def test_immutable_tree_replace_race_should_reject_symlink_destination(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source"
            destination = root / "destination"
            source.mkdir()
            (source / "identity.json").write_text('{"sha": "a"}\n', encoding="utf-8")

            def lose_race(_temporary_tree: Path, target: Path) -> None:
                target.symlink_to(source, target_is_directory=True)
                raise OSError("injected race")

            with mock.patch.object(Path, "replace", autospec=True, side_effect=lose_race):
                with self.assertRaisesRegex(RuntimeError, "immutable"):
                    queue_outputs.copy_immutable_tree(source, destination)

            self.assertTrue(destination.is_symlink())

    def test_web_publish_metadata_should_preserve_first_seal_time_on_retry(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            version_dir = root / "versions" / "2.0"
            latest_dir = root / "latest"
            md_path = version_dir / "web" / "md" / "manual.md"
            html_dir = version_dir / "web" / "html"
            first_time = datetime(2026, 9, 13, 8, 0, tzinfo=timezone.utc)

            def write(built_at: datetime) -> Path:
                return queue_outputs.write_web_publish_metadata(
                    config_path=root / "config.yaml",
                    model="MODEL",
                    region="US",
                    version="2.0",
                    git_ref="review/MODEL-US",
                    built_at=built_at,
                    md_output_path=md_path,
                    html_dir=html_dir,
                    queue_record_ids=("rec1",),
                    publish_release_version_dir_for_target=lambda **_: version_dir,
                    publish_release_latest_dir_for_target=lambda **_: latest_dir,
                    release_lang_for_config=lambda _: "en",
                    repo_relative=lambda path: path.relative_to(root).as_posix(),
                )

            latest_path = write(first_time)
            version_path = version_dir / "web_publish_meta.json"
            first_version_bytes = version_path.read_bytes()
            first_version_mtime = version_path.stat().st_mtime_ns
            first_latest_mtime = latest_path.stat().st_mtime_ns
            write(first_time + timedelta(hours=1))

            self.assertEqual(first_version_bytes, version_path.read_bytes())
            self.assertEqual(first_version_mtime, version_path.stat().st_mtime_ns)
            self.assertEqual(first_version_bytes, latest_path.read_bytes())
            self.assertEqual(first_latest_mtime, latest_path.stat().st_mtime_ns)

            with self.assertRaisesRegex(RuntimeError, "immutable"):
                queue_outputs.write_web_publish_metadata(
                    config_path=root / "config.yaml",
                    model="MODEL",
                    region="US",
                    version="2.0",
                    git_ref="review/CHANGED",
                    built_at=first_time,
                    md_output_path=md_path,
                    html_dir=html_dir,
                    queue_record_ids=("rec1",),
                    publish_release_version_dir_for_target=lambda **_: version_dir,
                    publish_release_latest_dir_for_target=lambda **_: latest_dir,
                    release_lang_for_config=lambda _: "en",
                    repo_relative=lambda path: path.relative_to(root).as_posix(),
                )
            self.assertEqual(first_version_bytes, latest_path.read_bytes())

            with self.assertRaisesRegex(RuntimeError, "immutable"):
                queue_outputs.write_web_publish_metadata(
                    config_path=root / "config.yaml",
                    model="MODEL",
                    region="US",
                    version="2.0",
                    git_ref="review/MODEL-US",
                    built_at=first_time,
                    md_output_path=md_path,
                    html_dir=html_dir,
                    queue_record_ids=("rec2",),
                    publish_release_version_dir_for_target=lambda **_: version_dir,
                    publish_release_latest_dir_for_target=lambda **_: latest_dir,
                    release_lang_for_config=lambda _: "en",
                    repo_relative=lambda path: path.relative_to(root).as_posix(),
                )
            self.assertEqual(first_version_bytes, latest_path.read_bytes())

    def test_new_web_version_should_advance_latest_without_changing_old_version(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            latest_dir = root / "latest"

            def write(version: str) -> bytes:
                version_dir = root / "versions" / version
                queue_outputs.write_web_publish_metadata(
                    config_path=root / "config.yaml",
                    model="MODEL",
                    region="US",
                    version=version,
                    git_ref=f"review/MODEL-US-{version}",
                    built_at=datetime(2026, 9, 13, tzinfo=timezone.utc),
                    md_output_path=version_dir / "web" / "md" / "manual.md",
                    html_dir=version_dir / "web" / "html",
                    publish_release_version_dir_for_target=lambda **_: version_dir,
                    publish_release_latest_dir_for_target=lambda **_: latest_dir,
                    release_lang_for_config=lambda _: "en",
                    repo_relative=lambda path: path.relative_to(root).as_posix(),
                )
                return (version_dir / "web_publish_meta.json").read_bytes()

            old_bytes = write("2.0")
            new_bytes = write("3.0")

            self.assertEqual(old_bytes, (root / "versions" / "2.0" / "web_publish_meta.json").read_bytes())
            self.assertNotEqual(old_bytes, new_bytes)
            self.assertEqual(new_bytes, (latest_dir / "web" / "publish_meta.json").read_bytes())

    def test_web_publish_metadata_failure_should_preserve_previous_latest(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            latest_dir = root / "latest"
            latest_path = latest_dir / "web" / "publish_meta.json"
            latest_path.parent.mkdir(parents=True)
            latest_path.write_bytes(b"old latest\n")
            version_dir = root / "versions" / "3.0"

            with mock.patch.object(
                queue_outputs,
                "_atomic_replace_text",
                side_effect=OSError("injected latest failure"),
            ):
                with self.assertRaisesRegex(OSError, "injected"):
                    queue_outputs.write_web_publish_metadata(
                        config_path=root / "config.yaml",
                        model="MODEL",
                        region="US",
                        version="3.0",
                        git_ref="review/MODEL-US",
                        built_at=datetime(2026, 9, 13, tzinfo=timezone.utc),
                        md_output_path=version_dir / "web" / "md" / "manual.md",
                        html_dir=version_dir / "web" / "html",
                        publish_release_version_dir_for_target=lambda **_: version_dir,
                        publish_release_latest_dir_for_target=lambda **_: latest_dir,
                        release_lang_for_config=lambda _: "en",
                        repo_relative=lambda path: path.relative_to(root).as_posix(),
                    )

            self.assertEqual(b"old latest\n", latest_path.read_bytes())
            self.assertTrue((version_dir / "web_publish_meta.json").is_file())

    def test_web_publish_metadata_should_reject_version_and_latest_symlinks(self) -> None:
        for symlink_case in ("version", "latest"):
            with self.subTest(symlink_case=symlink_case), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                version_dir = root / "versions" / "2.0"
                latest_dir = root / "latest"
                version_dir.mkdir(parents=True)
                target = root / "metadata-target.json"
                target.write_text("preserve me\n", encoding="utf-8")
                if symlink_case == "version":
                    (version_dir / "web_publish_meta.json").symlink_to(target)
                else:
                    (latest_dir / "web").mkdir(parents=True)
                    (latest_dir / "web" / "publish_meta.json").symlink_to(target)

                with self.assertRaisesRegex(RuntimeError, "symlink"):
                    queue_outputs.write_web_publish_metadata(
                        config_path=root / "config.yaml",
                        model="MODEL",
                        region="US",
                        version="2.0",
                        git_ref="review/MODEL-US",
                        built_at=datetime(2026, 9, 13, tzinfo=timezone.utc),
                        md_output_path=version_dir / "web" / "md" / "manual.md",
                        html_dir=version_dir / "web" / "html",
                        publish_release_version_dir_for_target=lambda **_: version_dir,
                        publish_release_latest_dir_for_target=lambda **_: latest_dir,
                        release_lang_for_config=lambda _: "en",
                        repo_relative=lambda path: path.relative_to(root).as_posix(),
                    )

                self.assertEqual("preserve me\n", target.read_text(encoding="utf-8"))

    def test_web_publish_metadata_should_reject_version_and_latest_directory_symlinks(self) -> None:
        for symlink_case in ("version_dir", "latest_dir", "latest_web_dir"):
            with self.subTest(symlink_case=symlink_case), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                version_dir = root / "versions" / "2.0"
                latest_dir = root / "latest"
                outside = root / "outside"
                outside.mkdir()
                if symlink_case == "version_dir":
                    version_dir.parent.mkdir()
                    version_dir.symlink_to(outside, target_is_directory=True)
                elif symlink_case == "latest_dir":
                    version_dir.mkdir(parents=True)
                    latest_dir.symlink_to(outside, target_is_directory=True)
                else:
                    version_dir.mkdir(parents=True)
                    latest_dir.mkdir()
                    (latest_dir / "web").symlink_to(outside, target_is_directory=True)

                with self.assertRaisesRegex(RuntimeError, "symlink"):
                    queue_outputs.write_web_publish_metadata(
                        config_path=root / "config.yaml",
                        model="MODEL",
                        region="US",
                        version="2.0",
                        git_ref="review/MODEL-US",
                        built_at=datetime(2026, 9, 13, tzinfo=timezone.utc),
                        md_output_path=version_dir / "web" / "md" / "manual.md",
                        html_dir=version_dir / "web" / "html",
                        publish_release_version_dir_for_target=lambda **_: version_dir,
                        publish_release_latest_dir_for_target=lambda **_: latest_dir,
                        release_lang_for_config=lambda _: "en",
                        repo_relative=lambda path: path.relative_to(root).as_posix(),
                    )
                self.assertEqual([], list(outside.iterdir()))

    def test_stage_draft_md_output_should_copy_myst_sidecars(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            built_md = root / "worktree" / "docs" / "_build" / "MODEL" / "US" / "en" / "md" / "manual.md"
            built_md.parent.mkdir(parents=True)
            built_md.write_text("# Manual\n<img src=\"assets/demo.png\" />\n", encoding="utf-8")
            (built_md.parent / "assets").mkdir()
            (built_md.parent / "assets" / "demo.png").write_bytes(b"png")
            (built_md.parent / "conf.py").write_text('extensions = ["myst_parser"]\n', encoding="utf-8")
            (built_md.parent / "index.md").write_text("# Demo\n\nmanual\n", encoding="utf-8")
            host_md = root / "host" / "docs" / "_build" / "MODEL" / "US" / "en" / "md" / "manual.md"

            staged = queue_outputs.stage_draft_md_output_to_host_repo(
                built_md_output_path=built_md,
                host_config_path=root / "host" / "config.us-en.yaml",
                model="MODEL",
                region="US",
                version="0.2",
                doc_phase="draft",
                resolve_md_output_path_for_target=lambda **_: host_md,
                versioned_md_output_path=lambda path, *, version, doc_phase: path.with_name("manual_0.2.md"),
            )

            self.assertEqual(host_md.with_name("manual_0.2.md"), staged)
            self.assertEqual(built_md.read_text(encoding="utf-8"), staged.read_text(encoding="utf-8"))
            self.assertTrue((staged.parent / "assets" / "demo.png").exists())
            self.assertTrue((staged.parent / "conf.py").exists())
            self.assertIn("manual_0.2", (staged.parent / "index.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
