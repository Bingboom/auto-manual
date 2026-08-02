from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from tools import publish_branch_assembly


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
    ) -> Path:
        lang_root = root / "reports" / "releases" / model / region / lang
        web_root = lang_root / "versions" / version / "web"
        md_root = web_root / "md"
        html_root = web_root / "html"
        metadata_root = lang_root / "latest" / "web"
        for directory in (md_root, html_root, metadata_root):
            directory.mkdir(parents=True, exist_ok=True)

        manual_stem = f"manual_{model.lower().replace('-', '')}_{region.lower()}_web_publish_{version}"
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
        (metadata_root / "publish_meta.json").write_text(
            json.dumps(
                {
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
            )
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

            stored_source = output_dir / "sources" / "web" / "JE-1000F" / "US" / "md"
            self.assertTrue(stored_source.joinpath("publish_meta.json").is_file())
            self.assertTrue(
                output_dir.joinpath(
                    "web", "JE-1000F", "US", "md", "manual_je1000f_us_web_publish_2.0.md"
                ).is_file()
            )
            web_markdown = output_dir.joinpath(
                "web", "JE-1000F", "US", "md", "manual_je1000f_us_web_publish_2.0.md"
            ).read_text(encoding="utf-8")
            self.assertIn("../../../_static/manual-assets/JE-1000F/US/md/assets/demo.png", web_markdown)
            short_alias = output_dir.joinpath(
                "web", "manual_je1000f_us_web_publish_2.0.md"
            ).read_text(encoding="utf-8")
            self.assertIn("orphan: true", short_alias)
            self.assertIn(
                'url=JE-1000F/US/md/manual_je1000f_us_web_publish_2.0.html',
                short_alias,
            )
            self.assertFalse(output_dir.joinpath("releases").exists())
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual("auto-manual-web-publish-branch/v1", manifest["schema_version"])
            self.assertEqual(1, len(manifest["targets"]))
            self.assertNotIn("publish_manifest.json", {entry["path"] for entry in manifest["files"]})

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
            self.assertTrue(output_dir.joinpath("web", "JE-1000F", "US", "md").is_dir())
            self.assertTrue(output_dir.joinpath("web", "JE-1000F", "JP", "md").is_dir())

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
