from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock

from tools import publish_branch_assembly
from tests.web_language_evidence_fixture import seal_language_evidence_fixture


class PublishBranchAssemblyTests(unittest.TestCase):
    def _write_target(
        self,
        root: Path,
        *,
        model: str,
        region: str,
        lang: str,
        version: str,
        git_ref: str,
        manual_stem: str | None = None,
        legacy_default: bool | None = None,
        language_scope: str | None = None,
    ) -> Path:
        lang_root = root / "reports" / "releases" / model / region / lang
        web_root = lang_root / "versions" / version / "web"
        md_root = web_root / "md"
        html_root = web_root / "html"
        metadata_root = lang_root / "latest" / "web"
        for directory in (md_root, html_root, metadata_root):
            directory.mkdir(parents=True, exist_ok=True)

        manual_stem = manual_stem or (
            f"manual_{model.lower().replace('-', '')}_{region.lower()}_{lang}_web_publish_{version}"
        )
        markdown_path = md_root / f"{manual_stem}.md"
        markdown_path.write_text(
            '# Manual\n\n<img src="assets/demo.png" />\n',
            encoding="utf-8",
        )
        (md_root / "assets").mkdir()
        (md_root / "assets" / "demo.png").write_bytes(b"png")
        (md_root / "conf.py").write_text('extensions = ["myst_parser"]\n', encoding="utf-8")
        (md_root / "index.md").write_text(
            "\n".join(
                (
                    f"# {model} {region}",
                    "",
                    "```{toctree}",
                    ":maxdepth: 2",
                    "",
                    manual_stem,
                    "```",
                    "",
                )
            ),
            encoding="utf-8",
        )
        (html_root / "index.html").write_text("<html>verified</html>\n", encoding="utf-8")

        relative = lambda path: path.relative_to(root).as_posix()
        payload = {
            "schema_version": "auto-manual-web-publish/v1",
            "model": model,
            "region": region,
            "lang": lang,
            "version": version,
            "git_ref": git_ref,
            "workflow_action": "Web Publish",
            "built_at": "2026-08-02T12:00:00+00:00",
            "md_output_path": relative(markdown_path),
            "html_dir": relative(html_root),
            "html_index": relative(html_root / "index.html"),
            "queue_record_ids": ["rec_web"],
        }
        if legacy_default is not None:
            payload["legacy_default"] = legacy_default
        if language_scope is not None:
            payload["language_scope"] = language_scope
        if language_scope == "single":
            (md_root / "manual.ir.json").write_text('{"schema": "manual-ir/v2"}\n', encoding="utf-8")
            (md_root / "manual_bundle.html").write_text("<article>Manual</article>\n", encoding="utf-8")
            receipt, receipt_sha256 = seal_language_evidence_fixture(
                markdown_dir=md_root,
                markdown_name=markdown_path.name,
                html_dir=html_root,
                evidence_dir=web_root / "evidence",
                model=model,
                region=region,
                language=lang,
                version=version,
                git_ref=git_ref,
            )
            payload.update(
                language_projection_evidence_path=relative(receipt),
                language_projection_evidence_sha256=receipt_sha256,
            )
        (metadata_root / "publish_meta.json").write_text(
            json.dumps(payload)
            + "\n",
            encoding="utf-8",
        )
        return lang_root

    def test_assemble_should_materialize_only_web_source_below_docs_publish(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._write_target(
                root,
                model="JE-1000F",
                region="US",
                lang="en",
                version="2.0",
                git_ref="review/JE-1000F-US",
            )
            output_dir = root / "publish-worktree" / "docs" / "publish"

            manifest_path = publish_branch_assembly.assemble_web_publish_branch(
                repo_root=root,
                releases_root=root / "reports" / "releases",
                output_dir=output_dir,
                title="Manual Library",
            )

            stored_source = output_dir / "sources" / "web" / "JE-1000F" / "US" / "en" / "md"
            self.assertTrue(stored_source.joinpath("publish_meta.json").is_file())
            self.assertTrue(
                output_dir.joinpath(
                    "web", "JE-1000F", "US", "en", "md", "manual_je1000f_us_en_web_publish_2.0.md"
                ).is_file()
            )
            web_markdown = output_dir.joinpath(
                "web", "JE-1000F", "US", "en", "md", "manual_je1000f_us_en_web_publish_2.0.md"
            ).read_text(encoding="utf-8")
            self.assertIn("../../../../_static/manual-assets/JE-1000F/US/en/md/assets/demo.png", web_markdown)
            short_alias = output_dir.joinpath(
                "web", "manual_je1000f_us_en_web_publish_2.0.md"
            ).read_text(encoding="utf-8")
            self.assertIn("orphan: true", short_alias)
            self.assertIn(
                'url=JE-1000F/US/en/md/manual_je1000f_us_en_web_publish_2.0.html',
                short_alias,
            )
            legacy_route = output_dir.joinpath(
                "web", "JE-1000F", "US", "md", "manual_je1000f_us_en_web_publish_2.0.md"
            ).read_text(encoding="utf-8")
            self.assertIn(
                "../en/md/manual_je1000f_us_en_web_publish_2.0.html",
                legacy_route,
            )
            self.assertFalse(output_dir.joinpath("releases").exists())
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual("auto-manual-web-publish-branch/v2", manifest["schema_version"])
            self.assertEqual(1, len(manifest["targets"]))
            self.assertTrue(manifest["targets"][0]["legacy_default"])
            self.assertEqual("legacy_unspecified", manifest["targets"][0]["language_scope"])
            self.assertNotIn("publish_manifest.json", {entry["path"] for entry in manifest["files"]})
            # REV-07: the queue-row ids thread through assembly into the stored
            # metadata and manifest so the post-merge receipt lane can locate
            # the Document_link rows after the queue run's releases tree is gone.
            self.assertEqual(["rec_web"], manifest["targets"][0]["queue_record_ids"])
            stored_meta = json.loads(
                stored_source.joinpath("publish_meta.json").read_text(encoding="utf-8")
            )
            self.assertEqual(["rec_web"], stored_meta["queue_record_ids"])

    def test_unsafe_queue_record_id_should_fail_assembly(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            lang_root = self._write_target(
                root,
                model="JE-1000F",
                region="US",
                lang="en",
                version="2.0",
                git_ref="review/JE-1000F-US",
            )
            metadata_path = lang_root / "latest" / "web" / "publish_meta.json"
            payload = json.loads(metadata_path.read_text(encoding="utf-8"))
            payload["queue_record_ids"] = ["rec_ok", "../escape"]
            metadata_path.write_text(json.dumps(payload) + "\n", encoding="utf-8")

            with self.assertRaisesRegex(RuntimeError, "unsafe queue record id"):
                publish_branch_assembly.assemble_web_publish_branch(
                    repo_root=root,
                    releases_root=root / "reports" / "releases",
                    output_dir=root / "publish-worktree" / "docs" / "publish",
                    title="Manual Library",
                )

    def test_incremental_assembly_should_preserve_existing_web_targets(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            releases_root = root / "reports" / "releases"
            us_root = self._write_target(
                root,
                model="JE-1000F",
                region="US",
                lang="en",
                version="2.0",
                git_ref="review/JE-1000F-US",
            )
            output_dir = root / "publish-worktree" / "docs" / "publish"
            publish_branch_assembly.assemble_web_publish_branch(
                repo_root=root,
                releases_root=releases_root,
                output_dir=output_dir,
                title="Manual Library",
            )

            shutil.rmtree(us_root)
            self._write_target(
                root,
                model="JE-1000F",
                region="JP",
                lang="ja",
                version="1.0",
                git_ref="review/JE-1000F-JP",
            )
            manifest_path = publish_branch_assembly.assemble_web_publish_branch(
                repo_root=root,
                releases_root=releases_root,
                output_dir=output_dir,
                title="Manual Library",
            )

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            target_keys = {
                (target["model"], target["region"], target["lang"])
                for target in manifest["targets"]
            }
            self.assertEqual(
                {("JE-1000F", "JP", "ja"), ("JE-1000F", "US", "en")},
                target_keys,
            )
            self.assertTrue(output_dir.joinpath("web", "JE-1000F", "US", "en", "md").is_dir())
            self.assertTrue(output_dir.joinpath("web", "JE-1000F", "JP", "ja", "md").is_dir())

    def test_same_model_region_locales_should_coexist_and_preserve_legacy_default(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for lang, default in (("en", True), ("fr", False)):
                self._write_target(
                    root,
                    model="JE-1000F",
                    region="EU",
                    lang=lang,
                    version="2.0",
                    git_ref="review/JE-1000F-EU",
                    legacy_default=default,
                )
            output_dir = root / "publish-worktree" / "docs" / "publish"

            manifest_path = publish_branch_assembly.assemble_web_publish_branch(
                repo_root=root,
                releases_root=root / "reports" / "releases",
                output_dir=output_dir,
                title="Manual Library",
            )

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(
                {("JE-1000F", "EU", "en"), ("JE-1000F", "EU", "fr")},
                {(item["model"], item["region"], item["lang"]) for item in manifest["targets"]},
            )
            for lang in ("en", "fr"):
                stem = f"manual_je1000f_eu_{lang}_web_publish_2.0"
                self.assertTrue(output_dir.joinpath("web", "JE-1000F", "EU", lang, "md", f"{stem}.md").is_file())
                self.assertTrue(output_dir.joinpath("web", f"{stem}.md").is_file())
            self.assertTrue(output_dir.joinpath("web", "JE-1000F", "EU", "md", "index.md").is_file())

    @unittest.skipUnless(shutil.which("sphinx-build"), "sphinx-build is required")
    def test_locale_and_legacy_routes_should_build_with_sphinx(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for lang, default in (("en", True), ("fr", False)):
                self._write_target(
                    root,
                    model="JE-1000F",
                    region="EU",
                    lang=lang,
                    version="2.0",
                    git_ref="review/JE-1000F-EU",
                    legacy_default=default,
                )
            output_dir = root / "publish-worktree" / "docs" / "publish"
            publish_branch_assembly.assemble_web_publish_branch(
                repo_root=root,
                releases_root=root / "reports" / "releases",
                output_dir=output_dir,
                title="Manual Library",
            )

            html_dir = root / "sphinx-html"
            subprocess.run(
                ["sphinx-build", "-W", "-b", "html", str(output_dir / "web"), str(html_dir)],
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertTrue(
                html_dir.joinpath(
                    "JE-1000F", "EU", "en", "md", "manual_je1000f_eu_en_web_publish_2.0.html"
                ).is_file()
            )
            self.assertTrue(html_dir.joinpath("JE-1000F", "EU", "md", "index.html").is_file())
            self.assertTrue(
                html_dir.joinpath("manual_je1000f_eu_en_web_publish_2.0.html").is_file()
            )

    def test_identity_mismatch_should_leave_existing_publish_tree_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            output_dir = root / "publish-worktree" / "docs" / "publish"
            output_dir.mkdir(parents=True)
            sentinel = output_dir / "sources" / "web" / "sentinel.txt"
            sentinel.parent.mkdir(parents=True)
            sentinel.write_text("original", encoding="utf-8")
            lang_root = self._write_target(
                root,
                model="JE-1000F",
                region="EU",
                lang="en",
                version="2.0",
                git_ref="review/JE-1000F-EU",
            )
            metadata = lang_root / "latest" / "web" / "publish_meta.json"
            payload = json.loads(metadata.read_text(encoding="utf-8"))
            payload["lang"] = "fr"
            metadata.write_text(json.dumps(payload) + "\n", encoding="utf-8")

            with self.assertRaisesRegex(RuntimeError, "metadata identity does not match path"):
                publish_branch_assembly.assemble_web_publish_branch(
                    repo_root=root,
                    releases_root=root / "reports" / "releases",
                    output_dir=output_dir,
                    title="Manual Library",
                )

            self.assertEqual("original", sentinel.read_text(encoding="utf-8"))

    def test_duplicate_locale_key_should_fail_without_replacing_output(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            output_dir = root / "publish-worktree" / "docs" / "publish"
            output_dir.mkdir(parents=True)
            sentinel = output_dir / "sources" / "web" / "sentinel.txt"
            sentinel.parent.mkdir(parents=True)
            sentinel.write_text("original", encoding="utf-8")
            first_root = self._write_target(
                root,
                model="JE-1000F",
                region="EU",
                lang="en",
                version="2.0",
                git_ref="review/JE-1000F-EU",
            )
            target = publish_branch_assembly.load_web_publish_target(
                first_root / "latest" / "web" / "publish_meta.json",
                repo_root=root,
                releases_root=root / "reports" / "releases",
            )

            with self.assertRaisesRegex(RuntimeError, "duplicate Web Publish identity"):
                publish_branch_assembly._ensure_unique_targets([target, target])
            self.assertEqual("original", sentinel.read_text(encoding="utf-8"))

    def test_alias_conflict_should_fail_without_replacing_existing_output(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            output_dir = root / "publish-worktree" / "docs" / "publish"
            output_dir.mkdir(parents=True)
            sentinel = output_dir / "sources" / "web" / "sentinel.txt"
            sentinel.parent.mkdir(parents=True)
            sentinel.write_text("original", encoding="utf-8")
            for lang, default in (("en", True), ("fr", False)):
                self._write_target(
                    root,
                    model="JE-1000F",
                    region="EU",
                    lang=lang,
                    version="2.0",
                    git_ref="review/JE-1000F-EU",
                    manual_stem="manual_shared",
                    legacy_default=default,
                )

            with self.assertRaisesRegex(RuntimeError, "duplicate RTD short alias"):
                publish_branch_assembly.assemble_web_publish_branch(
                    repo_root=root,
                    releases_root=root / "reports" / "releases",
                    output_dir=output_dir,
                    title="Manual Library",
                )
            self.assertEqual("original", sentinel.read_text(encoding="utf-8"))

    def test_multiple_new_locales_should_require_explicit_legacy_default(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for lang in ("en", "fr"):
                self._write_target(
                    root,
                    model="JE-1000F",
                    region="EU",
                    lang=lang,
                    version="2.0",
                    git_ref="review/JE-1000F-EU",
                )

            with self.assertRaisesRegex(RuntimeError, "requires one explicit legacy_default"):
                publish_branch_assembly.assemble_web_publish_branch(
                    repo_root=root,
                    releases_root=root / "reports" / "releases",
                    output_dir=root / "publish-worktree" / "docs" / "publish",
                    title="Manual Library",
                )

    def test_single_locale_explicit_non_default_should_not_be_promoted(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._write_target(
                root,
                model="JE-1000F",
                region="EU",
                lang="fr",
                version="2.0",
                git_ref="review/JE-1000F-EU",
                legacy_default=False,
            )

            with self.assertRaisesRegex(RuntimeError, "requires one explicit legacy_default"):
                publish_branch_assembly.assemble_web_publish_branch(
                    repo_root=root,
                    releases_root=root / "reports" / "releases",
                    output_dir=root / "publish-worktree" / "docs" / "publish",
                    title="Manual Library",
                )

    def test_normalized_release_version_path_should_match_existing_producer(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            lang_root = self._write_target(
                root,
                model="JE-1000F",
                region="EU",
                lang="en",
                version="1.0",
                git_ref="review/JE-1000F-EU",
            )
            old_version = lang_root / "versions" / "1.0"
            normalized_version = lang_root / "versions" / "V-0.2-RC1"
            old_version.rename(normalized_version)
            metadata = lang_root / "latest" / "web" / "publish_meta.json"
            payload = json.loads(metadata.read_text(encoding="utf-8"))
            payload["version"] = "V 0.2 / RC1"
            for field in ("md_output_path", "html_dir", "html_index"):
                payload[field] = payload[field].replace("/versions/1.0/", "/versions/V-0.2-RC1/")
            metadata.write_text(json.dumps(payload) + "\n", encoding="utf-8")

            target = publish_branch_assembly.load_web_publish_target(
                metadata,
                repo_root=root,
                releases_root=root / "reports" / "releases",
            )

            self.assertEqual("V 0.2 / RC1", target.version)

    def test_non_string_identity_should_be_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            lang_root = self._write_target(
                root,
                model="JE-1000F",
                region="EU",
                lang="en",
                version="2.0",
                git_ref="review/JE-1000F-EU",
            )
            metadata = lang_root / "latest" / "web" / "publish_meta.json"
            payload = json.loads(metadata.read_text(encoding="utf-8"))
            payload["model"] = 123
            metadata.write_text(json.dumps(payload) + "\n", encoding="utf-8")

            with self.assertRaisesRegex(RuntimeError, "metadata missing model"):
                publish_branch_assembly.load_web_publish_target(
                    metadata,
                    repo_root=root,
                    releases_root=root / "reports" / "releases",
                )

    def test_dangerous_output_boundaries_should_be_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            releases_root = root / "reports" / "releases"
            releases_root.mkdir(parents=True)
            for output_dir in (
                Path(root.anchor),
                root,
                releases_root,
                releases_root / "publish",
                releases_root.parent,
            ):
                with self.subTest(output_dir=output_dir), self.assertRaises(RuntimeError):
                    publish_branch_assembly._validate_publish_boundaries(
                        repo_root=root,
                        releases_root=releases_root,
                        output_dir=output_dir,
                    )

    def test_symlink_output_or_source_should_be_rejected_without_touching_target(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            releases_root = root / "reports" / "releases"
            lang_root = self._write_target(
                root,
                model="JE-1000F",
                region="EU",
                lang="en",
                version="2.0",
                git_ref="review/JE-1000F-EU",
            )
            real_output = root / "real-publish"
            real_output.mkdir()
            sentinel = real_output / "sentinel.txt"
            sentinel.write_text("original", encoding="utf-8")
            linked_output = root / "linked-publish"
            linked_output.symlink_to(real_output, target_is_directory=True)
            with self.assertRaisesRegex(RuntimeError, "must not be a symbolic link"):
                publish_branch_assembly.assemble_web_publish_branch(
                    repo_root=root,
                    releases_root=releases_root,
                    output_dir=linked_output,
                    title="Manual Library",
                )
            self.assertEqual("original", sentinel.read_text(encoding="utf-8"))

            source_assets = lang_root / "versions" / "2.0" / "web" / "md" / "assets"
            shutil.rmtree(source_assets)
            outside_assets = root / "outside-assets"
            outside_assets.mkdir()
            (outside_assets / "demo.png").write_bytes(b"png")
            source_assets.symlink_to(outside_assets, target_is_directory=True)
            safe_output = root / "safe-publish"
            with self.assertRaisesRegex(RuntimeError, "must not contain symbolic links"):
                publish_branch_assembly.assemble_web_publish_branch(
                    repo_root=root,
                    releases_root=releases_root,
                    output_dir=safe_output,
                    title="Manual Library",
                )
            self.assertFalse(safe_output.exists())

    def test_failed_candidate_promotion_should_restore_original_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            output_dir = root / "publish"
            candidate = root / "candidate"
            output_dir.mkdir()
            candidate.mkdir()
            original = output_dir / "manual.bin"
            original.write_bytes(b"original\x00bytes")
            (candidate / "manual.bin").write_bytes(b"replacement")
            real_replace = publish_branch_assembly.os.replace

            def fail_promotion(source: Path, destination: Path) -> None:
                if Path(source) == candidate and Path(destination) == output_dir:
                    raise OSError("injected promotion failure")
                real_replace(source, destination)

            with mock.patch.object(
                publish_branch_assembly.os,
                "replace",
                side_effect=fail_promotion,
            ), self.assertRaisesRegex(OSError, "injected promotion failure"):
                publish_branch_assembly._promote_candidate(
                    candidate=candidate,
                    output_dir=output_dir,
                )

            self.assertEqual(b"original\x00bytes", original.read_bytes())
            self.assertFalse(list(root.glob(".publish-backup-*")))

    def test_failed_restore_should_preserve_original_bytes_in_backup(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            output_dir = root / "publish"
            candidate = root / "candidate"
            output_dir.mkdir()
            candidate.mkdir()
            (output_dir / "manual.bin").write_bytes(b"original\x00bytes")
            (candidate / "manual.bin").write_bytes(b"replacement")
            real_replace = publish_branch_assembly.os.replace

            def fail_promotion_and_restore(source: Path, destination: Path) -> None:
                source_path = Path(source)
                destination_path = Path(destination)
                if destination_path == output_dir and (
                    source_path == candidate or source_path.parent.name.startswith(".publish-backup-")
                ):
                    raise OSError("injected replace failure")
                real_replace(source, destination)

            with mock.patch.object(
                publish_branch_assembly.os,
                "replace",
                side_effect=fail_promotion_and_restore,
            ), self.assertRaisesRegex(RuntimeError, "previous bytes are preserved"):
                publish_branch_assembly._promote_candidate(
                    candidate=candidate,
                    output_dir=output_dir,
                )

            backups = list(root.glob(".publish-backup-*/publish/manual.bin"))
            self.assertEqual(1, len(backups))
            self.assertEqual(b"original\x00bytes", backups[0].read_bytes())

    def test_legacy_v1_target_should_migrate_and_keep_old_alias_after_default_update(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            releases_root = root / "reports" / "releases"
            old_stem = "manual_je1000f_eu_web_publish_1.0"
            old_release = self._write_target(
                root,
                model="JE-1000F",
                region="EU",
                lang="en",
                version="1.0",
                git_ref="review/JE-1000F-EU",
                manual_stem=old_stem,
            )
            output_dir = root / "publish-worktree" / "docs" / "publish"
            publish_branch_assembly.assemble_web_publish_branch(
                repo_root=root,
                releases_root=releases_root,
                output_dir=output_dir,
                title="Manual Library",
            )

            locale_source = output_dir / "sources" / "web" / "JE-1000F" / "EU" / "en" / "md"
            legacy_source = output_dir / "sources" / "web" / "JE-1000F" / "EU" / "md"
            legacy_source.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(locale_source), str(legacy_source))
            metadata = legacy_source / "publish_meta.json"
            payload = json.loads(metadata.read_text(encoding="utf-8"))
            payload["schema_version"] = "auto-manual-web-publish-target/v1"
            payload["route"] = "JE-1000F/EU/md"
            for field in ("legacy_default", "legacy_route", "legacy_aliases"):
                payload.pop(field, None)
            metadata.write_text(json.dumps(payload) + "\n", encoding="utf-8")

            shutil.rmtree(old_release)
            new_stem = "manual_je1000f_eu_en_web_publish_2.0"
            self._write_target(
                root,
                model="JE-1000F",
                region="EU",
                lang="en",
                version="2.0",
                git_ref="review/JE-1000F-EU",
                manual_stem=new_stem,
            )
            self._write_target(
                root,
                model="JE-1000F",
                region="EU",
                lang="fr",
                version="2.0",
                git_ref="review/JE-1000F-EU",
                legacy_default=False,
            )

            publish_branch_assembly.assemble_web_publish_branch(
                repo_root=root,
                releases_root=releases_root,
                output_dir=output_dir,
                title="Manual Library",
            )

            old_root_alias = (output_dir / "web" / f"{old_stem}.md").read_text(encoding="utf-8")
            self.assertIn(f"JE-1000F/EU/en/md/{new_stem}.html", old_root_alias)
            old_nested_alias = (
                output_dir / "web" / "JE-1000F" / "EU" / "md" / f"{old_stem}.md"
            ).read_text(encoding="utf-8")
            self.assertIn(f"../en/md/{new_stem}.html", old_nested_alias)
            stored = json.loads(
                (output_dir / "sources" / "web" / "JE-1000F" / "EU" / "en" / "md" / "publish_meta.json").read_text(encoding="utf-8")
            )
            self.assertTrue(stored["legacy_default"])
            self.assertEqual([old_stem], stored["legacy_aliases"])
            self.assertEqual("legacy_unspecified", stored["language_scope"])

    def test_language_scope_should_be_explicit_in_stored_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for lang, scope in (("en", None), ("fr", "single")):
                self._write_target(
                    root,
                    model="JE-1000F",
                    region=lang.upper(),
                    lang=lang,
                    version="2.0",
                    git_ref=f"review/JE-1000F-{lang.upper()}",
                    language_scope=scope,
                )
            output_dir = root / "publish-worktree" / "docs" / "publish"

            publish_branch_assembly.assemble_web_publish_branch(
                repo_root=root,
                releases_root=root / "reports" / "releases",
                output_dir=output_dir,
                title="Manual Library",
            )

            for lang, expected in (("en", "legacy_unspecified"), ("fr", "single")):
                metadata = next(
                    (output_dir / "sources" / "web" / "JE-1000F" / lang.upper() / lang).rglob(
                        "publish_meta.json"
                    )
                )
                stored = json.loads(metadata.read_text(encoding="utf-8"))
                self.assertEqual(expected, stored["language_scope"])
                if expected == "single":
                    self.assertEqual(
                        '{"schema": "manual-ir/v2"}\n',
                        (metadata.parent / "manual.ir.json").read_text(encoding="utf-8"),
                    )
                    self.assertEqual(
                        "<article>Manual</article>\n",
                        (metadata.parent / "manual_bundle.html").read_text(encoding="utf-8"),
                    )
                    manifest = json.loads(
                        (output_dir / "publish_manifest.json").read_text(encoding="utf-8")
                    )
                    inventory = {entry["path"] for entry in manifest["files"]}
                    for filename in ("manual.ir.json", "manual_bundle.html"):
                        self.assertIn(
                            (metadata.parent / filename).relative_to(output_dir).as_posix(),
                            inventory,
                        )

    def test_invalid_language_scope_should_be_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._write_target(
                root,
                model="JE-1000F",
                region="EU",
                lang="en",
                version="2.0",
                git_ref="review/JE-1000F-EU",
                language_scope="mixed",
            )

            with self.assertRaisesRegex(RuntimeError, "language_scope must be one of"):
                publish_branch_assembly.assemble_web_publish_branch(
                    repo_root=root,
                    releases_root=root / "reports" / "releases",
                    output_dir=root / "publish-worktree" / "docs" / "publish",
                    title="Manual Library",
                )

    def test_single_language_scope_without_receipt_should_be_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            lang_root = self._write_target(
                root,
                model="MODEL",
                region="EU",
                lang="fr",
                version="2.0",
                git_ref="review/MODEL-EU",
                language_scope="single",
            )
            metadata = lang_root / "latest" / "web" / "publish_meta.json"
            payload = json.loads(metadata.read_text(encoding="utf-8"))
            payload.pop("language_projection_evidence_path")
            payload.pop("language_projection_evidence_sha256")
            metadata.write_text(json.dumps(payload) + "\n", encoding="utf-8")

            with self.assertRaisesRegex(RuntimeError, "language_projection_evidence_path"):
                publish_branch_assembly.assemble_web_publish_branch(
                    repo_root=root,
                    releases_root=root / "reports" / "releases",
                    output_dir=root / "publish" / "docs",
                    title="Manual Library",
                )

    def test_assembly_should_reject_print_artifacts_inside_web_assets(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            lang_root = self._write_target(
                root,
                model="JE-1000F",
                region="US",
                lang="en",
                version="2.0",
                git_ref="review/JE-1000F-US",
            )
            assets = lang_root / "versions" / "2.0" / "web" / "md" / "assets"
            (assets / "manual.idml").write_bytes(b"idml")
            (assets / "layout.tex").write_text("print-only", encoding="utf-8")

            with self.assertRaisesRegex(RuntimeError, "cannot contain print/source artifacts"):
                publish_branch_assembly.assemble_web_publish_branch(
                    repo_root=root,
                    releases_root=root / "reports" / "releases",
                    output_dir=root / "publish-worktree" / "docs" / "publish",
                    title="Manual Library",
                )

    def test_assembly_should_reject_non_web_top_level_content(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._write_target(
                root,
                model="JE-1000F",
                region="US",
                lang="en",
                version="2.0",
                git_ref="review/JE-1000F-US",
            )
            output_dir = root / "publish-worktree" / "docs" / "publish"
            (output_dir / "idml").mkdir(parents=True)
            (output_dir / "idml" / "manual.idml").write_bytes(b"idml")

            with self.assertRaisesRegex(RuntimeError, "unexpected top-level paths: idml"):
                publish_branch_assembly.assemble_web_publish_branch(
                    repo_root=root,
                    releases_root=root / "reports" / "releases",
                    output_dir=output_dir,
                    title="Manual Library",
                )

    def test_metadata_path_must_stay_inside_release_root(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._write_target(
                root,
                model="JE-1000F",
                region="US",
                lang="en",
                version="2.0",
                git_ref="review/JE-1000F-US",
            )
            metadata_path = (
                root
                / "reports"
                / "releases"
                / "JE-1000F"
                / "US"
                / "en"
                / "latest"
                / "web"
                / "publish_meta.json"
            )
            payload = json.loads(metadata_path.read_text(encoding="utf-8"))
            payload["md_output_path"] = "outside.md"
            metadata_path.write_text(json.dumps(payload) + "\n", encoding="utf-8")

            with self.assertRaisesRegex(RuntimeError, "escapes releases root"):
                publish_branch_assembly.assemble_web_publish_branch(
                    repo_root=root,
                    releases_root=root / "reports" / "releases",
                    output_dir=root / "publish-worktree" / "docs" / "publish",
                    title="Manual Library",
                )


if __name__ == "__main__":
    unittest.main()
