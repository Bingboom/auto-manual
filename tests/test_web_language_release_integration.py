from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest

from tools import publish_branch_assembly, queue_outputs, release_contract
from tools.web_language_release_evidence import RECEIPT_FILENAME, capture_projection
from tests.web_language_evidence_fixture import write_projection_fixture


class WebLanguageReleaseIntegrationTests(unittest.TestCase):
    def _release_paths(self, root: Path, releases_root: Path):
        def version_dir(**kwargs: object) -> Path:
            return release_contract.release_version_dir_for_target(
                repo_root=root,
                releases_root=releases_root,
                **kwargs,
            )

        def latest_dir(**kwargs: object) -> Path:
            return release_contract.release_latest_dir_for_target(
                repo_root=root,
                releases_root=releases_root,
                **kwargs,
            )

        return version_dir, latest_dir

    def test_explicit_second_language_should_flow_from_stage_to_stored_source(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            releases_root = root / "reports" / "releases"
            config = root / "configs" / "config.shared.yaml"
            config.parent.mkdir(parents=True)
            config.write_text("build:\n  languages: [en, fr]\n", encoding="utf-8")
            built_md = root / "build" / "fr" / "md" / "manual_fr.md"
            built_md.parent.mkdir(parents=True)
            built_md.write_text("# Manuel\n", encoding="utf-8")
            (built_md.parent / "conf.py").write_text("extensions = []\n", encoding="utf-8")
            (built_md.parent / "index.md").write_text(
                "# Manuel\n\n```{toctree}\n\nmanual_fr\n```\n", encoding="utf-8"
            )
            built_html = root / "build" / "fr" / "html"
            built_html.mkdir(parents=True)
            (built_html / "index.html").write_text("<html>fr</html>\n", encoding="utf-8")
            manifest = write_projection_fixture(
                root / "projection", model="MODEL", region="EU", language="fr"
            )
            captures = tuple(
                capture_projection(
                    manifest,
                    action=action,
                    model="MODEL",
                    region="EU",
                    language="fr",
                )
                for action in ("check", "md", "html")
            )
            version_dir_for_target, latest_dir_for_target = self._release_paths(
                root, releases_root
            )

            staged_md, staged_html = queue_outputs.stage_web_publish_assets_to_host_repo(
                built_md_output_path=built_md,
                built_html_dir=built_html,
                host_config_path=config,
                model="MODEL",
                region="EU",
                version="2.0",
                publish_release_version_dir_for_target=version_dir_for_target,
                projection_captures=captures,
                git_ref=" review/MODEL-EU ",
                target_lang="fr",
            )
            evidence = staged_md.parent.parent / "evidence" / RECEIPT_FILENAME
            latest_metadata = queue_outputs.write_web_publish_metadata(
                config_path=config,
                model="MODEL",
                region="EU",
                version="2.0",
                git_ref=" review/MODEL-EU ",
                built_at=datetime(2026, 9, 13, tzinfo=timezone.utc),
                md_output_path=staged_md,
                html_dir=staged_html,
                target_lang="fr",
                language_projection_evidence_path=evidence,
                publish_release_version_dir_for_target=version_dir_for_target,
                publish_release_latest_dir_for_target=latest_dir_for_target,
                release_lang_for_config=release_contract.release_lang_for_config,
                repo_relative=lambda path: path.relative_to(root).as_posix(),
            )
            output_dir = root / "publish-worktree" / "docs" / "publish"
            publish_manifest = publish_branch_assembly.assemble_web_publish_branch(
                repo_root=root,
                releases_root=releases_root,
                output_dir=output_dir,
                title="Manual Library",
            )

            self.assertIn("/fr/", staged_md.as_posix())
            release_metadata = json.loads(latest_metadata.read_text(encoding="utf-8"))
            self.assertEqual("fr", release_metadata["lang"])
            self.assertEqual("single", release_metadata["language_scope"])
            stored_md = output_dir / "sources" / "web" / "MODEL" / "EU" / "fr" / "md"
            stored_metadata = json.loads(
                (stored_md / "publish_meta.json").read_text(encoding="utf-8")
            )
            self.assertEqual("single", stored_metadata["language_scope"])
            self.assertTrue((stored_md / "evidence" / RECEIPT_FILENAME).is_file())
            inventory = json.loads(publish_manifest.read_text(encoding="utf-8"))["files"]
            self.assertIn(
                "sources/web/MODEL/EU/fr/md/evidence/" + RECEIPT_FILENAME,
                {item["path"] for item in inventory},
            )

    def test_release_path_default_and_explicit_language_validation(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            config = root / "config.yaml"
            config.write_text("build:\n  languages: [en, fr]\n", encoding="utf-8")
            releases_root = root / "releases"

            default = release_contract.release_version_dir_for_target(
                repo_root=root,
                releases_root=releases_root,
                config_path=config,
                model="MODEL",
                region="EU",
                version="2.0",
            )
            self.assertEqual(releases_root / "MODEL" / "EU" / "en" / "versions" / "2.0", default)
            with self.assertRaisesRegex(RuntimeError, "not configured"):
                release_contract.release_version_dir_for_target(
                    repo_root=root,
                    releases_root=releases_root,
                    config_path=config,
                    model="MODEL",
                    region="EU",
                    version="2.0",
                    lang="de",
                )

    def test_stage_should_reject_capture_identity_before_promotion(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            config = root / "config.yaml"
            config.write_text("build:\n  languages: [en, fr]\n", encoding="utf-8")
            built_md = root / "build" / "md" / "manual.md"
            built_md.parent.mkdir(parents=True)
            built_md.write_text("# Manual\n", encoding="utf-8")
            built_html = root / "build" / "html"
            built_html.mkdir(parents=True)
            (built_html / "index.html").write_text("<html></html>\n", encoding="utf-8")
            manifest = write_projection_fixture(
                root / "projection", model="OTHER", region="EU", language="fr"
            )
            captures = tuple(
                capture_projection(
                    manifest,
                    action=action,
                    model="OTHER",
                    region="EU",
                    language="fr",
                )
                for action in ("check", "md", "html")
            )
            version_dir = root / "releases" / "MODEL" / "EU" / "fr" / "versions" / "2.0"

            with self.assertRaisesRegex(RuntimeError, "capture identity mismatch"):
                queue_outputs.stage_web_publish_assets_to_host_repo(
                    built_md_output_path=built_md,
                    built_html_dir=built_html,
                    host_config_path=config,
                    model="MODEL",
                    region="EU",
                    version="2.0",
                    publish_release_version_dir_for_target=lambda **_: version_dir,
                    projection_captures=captures,
                    git_ref="review/MODEL-EU",
                    target_lang="fr",
                )
            self.assertFalse(version_dir.exists())

    def test_explicit_language_and_evidence_must_be_supplied_together(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            common = dict(
                config_path=root / "config.yaml",
                model="MODEL",
                region="EU",
                version="2.0",
                git_ref="review/MODEL-EU",
                built_at=datetime(2026, 9, 13, tzinfo=timezone.utc),
                md_output_path=root / "versions" / "2.0" / "web" / "md" / "manual.md",
                html_dir=root / "versions" / "2.0" / "web" / "html",
                publish_release_version_dir_for_target=lambda **_: root / "versions" / "2.0",
                publish_release_latest_dir_for_target=lambda **_: root / "latest",
                release_lang_for_config=lambda _: "en",
                repo_relative=lambda path: path.relative_to(root).as_posix(),
            )
            with self.assertRaisesRegex(RuntimeError, "provided together"):
                queue_outputs.write_web_publish_metadata(**common, target_lang="fr")
            with self.assertRaisesRegex(RuntimeError, "provided together"):
                queue_outputs.write_web_publish_metadata(
                    **common,
                    language_projection_evidence_path=root / RECEIPT_FILENAME,
                )


if __name__ == "__main__":
    unittest.main()
