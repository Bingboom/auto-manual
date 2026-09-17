from __future__ import annotations

import argparse
import shutil
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from tools import build_cli, web_sideload
from tools.web_language_release_evidence import SOURCE_KIND_PDF_SIDELOAD
from tools.web_sideload import (
    DEBT_CATEGORY_UNSTRUCTURED_BOOK,
    DEBT_PAYOFF_ACTION_UNSTRUCTURED_BOOK,
    run_web_sideload,
)


class MdDirShapeTests(unittest.TestCase):
    def test_accepts_a_directory_with_the_expected_manual_file(self) -> None:
        with TemporaryDirectory() as tmp:
            md_dir = Path(tmp)
            manual = md_dir / "manual_je1000f_us_en.md"
            manual.write_text("# Manual\n", encoding="utf-8")

            result = web_sideload._validate_md_dir_shape(
                md_dir=md_dir, expected_manual_name="manual_je1000f_us_en.md"
            )

            self.assertEqual(manual, result)

    def test_rejects_a_stem_mismatch_and_names_both_files(self) -> None:
        with TemporaryDirectory() as tmp:
            md_dir = Path(tmp)
            (md_dir / "manual_wrong_stem.md").write_text("# Manual\n", encoding="utf-8")

            with self.assertRaises(RuntimeError) as ctx:
                web_sideload._validate_md_dir_shape(
                    md_dir=md_dir, expected_manual_name="manual_je1000f_us_en.md"
                )

            message = str(ctx.exception)
            self.assertIn("manual_je1000f_us_en.md", message)
            self.assertIn("manual_wrong_stem.md", message)

    def test_rejects_a_missing_directory(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "must be a real directory"):
            web_sideload._validate_md_dir_shape(
                md_dir=Path("/does/not/exist/at/all"), expected_manual_name="manual.md"
            )

    def test_rejects_a_symlinked_directory(self) -> None:
        with TemporaryDirectory() as tmp:
            real_dir = Path(tmp) / "real"
            real_dir.mkdir()
            (real_dir / "manual.md").write_text("# Manual\n", encoding="utf-8")
            linked = Path(tmp) / "linked"
            linked.symlink_to(real_dir, target_is_directory=True)

            with self.assertRaisesRegex(RuntimeError, "must be a real directory"):
                web_sideload._validate_md_dir_shape(
                    md_dir=linked, expected_manual_name="manual.md"
                )


class CliRegistrationTests(unittest.TestCase):
    def test_web_sideload_action_and_flags_parse(self) -> None:
        args = build_cli.parse_args(
            [
                "web-sideload",
                "--config",
                "configs/config.us.yaml",
                "--model",
                "JE-1000F",
                "--region",
                "US",
                "--lang",
                "en",
                "--version",
                "git-2026-09-16-abc123",
                "--md-dir",
                "/tmp/external-md",
                "--debt",
                "整本未结构化补充说明:page:see intake ticket",
                "--dry-run",
            ],
            default_config="configs/config.us.yaml",
            build_actions=("rst", "word", "html", "pdf", "md", "all"),
            staging_root_env="AUTO_MANUAL_STAGING_ROOT",
        )

        self.assertEqual("web-sideload", args.action)
        self.assertEqual("/tmp/external-md", args.md_dir)
        self.assertEqual(
            ["整本未结构化补充说明:page:see intake ticket"], args.debt
        )
        self.assertTrue(args.dry_run)


class RunWebSideloadOrchestrationTests(unittest.TestCase):
    def _args(self, *, md_dir: str, **overrides) -> argparse.Namespace:
        values = {
            "config": "configs/config.us.yaml",
            "model": "JE-1000F",
            "region": "US",
            "lang": "en",
            "version": "git-2026-09-16-abc123",
            "md_dir": md_dir,
            "debt": [],
            "dry_run": False,
        }
        values.update(overrides)
        return argparse.Namespace(**values)

    @staticmethod
    def _resolve_path_from_root(raw: str) -> Path:
        # Matches build.py's real resolver: an absolute --md-dir (or config)
        # value passes through untouched; a relative one is joined to a
        # (fictitious, never-touched-on-disk) repo root.
        return Path("/repo") / raw

    def test_dry_run_validates_shape_but_stages_nothing(self) -> None:
        with TemporaryDirectory() as tmp:
            md_dir = Path(tmp) / "external-md"
            md_dir.mkdir()
            manual = md_dir / "manual_je1000f_us_en.md"
            manual.write_text("# Manual\n", encoding="utf-8")
            args = self._args(md_dir=str(md_dir), dry_run=True)

            with mock.patch.object(
                web_sideload, "check_batch_for_collisions"
            ) as collision_check, mock.patch.object(
                web_sideload, "resolve_md_output_path_for_target", return_value=manual
            ), mock.patch.object(
                web_sideload, "_current_git_head_sha"
            ) as head_sha, mock.patch.object(
                web_sideload, "_run_sideload_strict_verification"
            ) as strict_verify, mock.patch.object(
                web_sideload, "stage_web_publish_assets_to_host_repo"
            ) as stage, mock.patch.object(
                web_sideload, "write_web_publish_metadata"
            ) as write_meta, mock.patch.object(
                web_sideload, "record_debt_entries"
            ) as record_debt:
                run_web_sideload(
                    args,
                    repo_root=Path("/repo"),
                    resolve_path_from_root=self._resolve_path_from_root,
                )

        collision_check.assert_called_once()
        head_sha.assert_not_called()
        strict_verify.assert_not_called()
        stage.assert_not_called()
        write_meta.assert_not_called()
        record_debt.assert_not_called()

    def test_missing_flags_are_rejected_before_any_build(self) -> None:
        args = self._args(md_dir="", model="")

        with mock.patch.object(web_sideload, "_run_sideload_strict_verification") as strict_verify:
            with self.assertRaisesRegex(RuntimeError, "--model"):
                run_web_sideload(
                    args,
                    repo_root=Path("/repo"),
                    resolve_path_from_root=self._resolve_path_from_root,
                )

        strict_verify.assert_not_called()

    def test_stem_mismatch_stops_before_verification_staging_or_debt(self) -> None:
        with TemporaryDirectory() as tmp:
            md_dir = Path(tmp) / "external-md"
            md_dir.mkdir()
            (md_dir / "manual_wrong_stem.md").write_text("# Manual\n", encoding="utf-8")
            args = self._args(md_dir=str(md_dir))
            expected = Path("/repo/docs/_build/JE-1000F/US/en/md/manual_je1000f_us_en.md")

            with mock.patch.object(
                web_sideload, "check_batch_for_collisions"
            ), mock.patch.object(
                web_sideload, "resolve_md_output_path_for_target", return_value=expected
            ), mock.patch.object(
                web_sideload, "_run_sideload_strict_verification"
            ) as strict_verify, mock.patch.object(
                web_sideload, "stage_web_publish_assets_to_host_repo"
            ) as stage, mock.patch.object(
                web_sideload, "record_debt_entries"
            ) as record_debt:
                with self.assertRaisesRegex(RuntimeError, "manual_je1000f_us_en.md"):
                    run_web_sideload(
                        args,
                        repo_root=Path("/repo"),
                        resolve_path_from_root=self._resolve_path_from_root,
                    )

            strict_verify.assert_not_called()
            stage.assert_not_called()
            record_debt.assert_not_called()

    def test_happy_path_stages_with_source_kind_and_always_records_debt(self) -> None:
        with TemporaryDirectory() as tmp:
            md_dir = Path(tmp) / "external-md"
            md_dir.mkdir()
            manual = md_dir / "manual_je1000f_us_en.md"
            manual.write_text("# Manual\n", encoding="utf-8")
            # Nested one level below tmp, so cleaning it up in the staging
            # `finally` never removes the TemporaryDirectory's own root.
            verify_root = Path(tmp) / "verify-root"
            html_dir = verify_root / "html"
            html_dir.mkdir(parents=True)
            args = self._args(
                md_dir=str(md_dir), debt=["内容糙:page:tighten wording"]
            )

            calls: list[str] = []
            staged_md = Path(
                "/repo/reports/releases/JE-1000F/US/en/versions/git-2026-09-16-abc123/web/md/manual_je1000f_us_en.md"
            )
            staged_html = Path(
                "/repo/reports/releases/JE-1000F/US/en/versions/git-2026-09-16-abc123/web/html"
            )
            metadata_path = Path(
                "/repo/reports/releases/JE-1000F/US/en/latest/web/publish_meta.json"
            )

            with mock.patch.object(
                web_sideload,
                "check_batch_for_collisions",
                side_effect=lambda **_: calls.append("collision"),
            ) as collision_check, mock.patch.object(
                web_sideload, "resolve_md_output_path_for_target", return_value=manual
            ), mock.patch.object(
                web_sideload, "_current_git_head_sha", return_value="a" * 40
            ) as head_sha, mock.patch.object(
                web_sideload,
                "_run_sideload_strict_verification",
                side_effect=lambda **_: (calls.append("verify"), html_dir)[1],
            ) as strict_verify, mock.patch.object(
                web_sideload,
                "stage_web_publish_assets_to_host_repo",
                side_effect=lambda **_: (calls.append("stage"), (staged_md, staged_html))[1],
            ) as stage, mock.patch.object(
                web_sideload,
                "write_web_publish_metadata",
                side_effect=lambda **_: (calls.append("write-metadata"), metadata_path)[1],
            ) as write_meta, mock.patch.object(
                web_sideload,
                "record_debt_entries",
                side_effect=lambda **_: calls.append("debt"),
            ) as record_debt:
                run_web_sideload(
                    args,
                    repo_root=Path("/repo"),
                    resolve_path_from_root=self._resolve_path_from_root,
                )

            self.assertFalse(verify_root.exists())  # whole verify scratch root cleaned up
            self.assertTrue(Path(tmp).exists())  # the enclosing tmp root is untouched

        collision_check.assert_called_once()
        head_sha.assert_called_once_with(Path("/repo"))
        self.assertEqual(
            ["collision", "verify", "stage", "write-metadata", "debt"], calls
        )

        strict_verify.assert_called_once_with(md_dir=md_dir, title="JE-1000F US en")
        stage.assert_called_once()
        self.assertEqual(manual, stage.call_args.kwargs["built_md_output_path"])
        self.assertEqual(html_dir, stage.call_args.kwargs["built_html_dir"])
        self.assertEqual("en", stage.call_args.kwargs["target_lang"])
        self.assertEqual(SOURCE_KIND_PDF_SIDELOAD, stage.call_args.kwargs["source_kind"])

        write_meta.assert_called_once()
        self.assertEqual("en", write_meta.call_args.kwargs["target_lang"])
        self.assertEqual(SOURCE_KIND_PDF_SIDELOAD, write_meta.call_args.kwargs["source_kind"])
        self.assertEqual(staged_md, write_meta.call_args.kwargs["md_output_path"])
        self.assertEqual(staged_html, write_meta.call_args.kwargs["html_dir"])
        self.assertNotIn("language_projection_evidence_path", write_meta.call_args.kwargs)

        record_debt.assert_called_once()
        entries = list(record_debt.call_args.kwargs["entries"])
        self.assertEqual(2, len(entries))
        auto_entries = [entry for entry in entries if entry.source == "auto"]
        manual_entries = [entry for entry in entries if entry.source == "manual"]
        self.assertEqual(1, len(auto_entries))
        self.assertEqual(DEBT_CATEGORY_UNSTRUCTURED_BOOK, auto_entries[0].category)
        self.assertEqual(
            DEBT_PAYOFF_ACTION_UNSTRUCTURED_BOOK, auto_entries[0].payoff_action
        )
        self.assertEqual(1, len(manual_entries))
        self.assertEqual("内容糙", manual_entries[0].category)

    def test_debt_is_recorded_even_without_any_manual_debt_flag(self) -> None:
        with TemporaryDirectory() as tmp:
            md_dir = Path(tmp) / "external-md"
            md_dir.mkdir()
            manual = md_dir / "manual_je1000f_us_en.md"
            manual.write_text("# Manual\n", encoding="utf-8")
            verify_root = Path(tmp) / "verify-root"
            html_dir = verify_root / "html"
            html_dir.mkdir(parents=True)
            args = self._args(md_dir=str(md_dir), debt=[])

            with mock.patch.object(
                web_sideload, "check_batch_for_collisions"
            ), mock.patch.object(
                web_sideload, "resolve_md_output_path_for_target", return_value=manual
            ), mock.patch.object(
                web_sideload, "_current_git_head_sha", return_value="a" * 40
            ), mock.patch.object(
                web_sideload,
                "_run_sideload_strict_verification",
                return_value=html_dir,
            ), mock.patch.object(
                web_sideload,
                "stage_web_publish_assets_to_host_repo",
                return_value=(Path("/repo/staged.md"), Path("/repo/staged-html")),
            ), mock.patch.object(
                web_sideload, "write_web_publish_metadata", return_value=Path("/repo/meta.json")
            ), mock.patch.object(
                web_sideload, "record_debt_entries"
            ) as record_debt:
                run_web_sideload(
                    args,
                    repo_root=Path("/repo"),
                    resolve_path_from_root=self._resolve_path_from_root,
                )

        record_debt.assert_called_once()
        entries = list(record_debt.call_args.kwargs["entries"])
        self.assertEqual(1, len(entries))
        self.assertEqual("auto", entries[0].source)
        self.assertEqual(DEBT_CATEGORY_UNSTRUCTURED_BOOK, entries[0].category)


class SideloadStrictVerificationRealAssemblyTests(unittest.TestCase):
    """Exercise the real ``assemble_rtd_source`` call inside the verify step.

    Every ``run_web_sideload`` orchestration test above mocks
    ``_run_sideload_strict_verification`` itself, so none of them can catch a
    bug inside it. This test only mocks the ``sphinx`` subprocess (no Sphinx
    install required) and lets the real ``build_root``/``assembled_dir``
    plumbing run, which is exactly the layer that regressed: the assembled
    RTD output dir was built as a *sibling* of ``build_root`` instead of
    nested inside it, tripping ``assemble_rtd_source``'s own "RTD source
    output must stay under build root" containment check on every real
    invocation.
    """

    def test_real_assembly_stays_inside_its_own_build_root(self) -> None:
        with TemporaryDirectory() as tmp:
            md_dir = Path(tmp) / "external-md"
            md_dir.mkdir()
            (md_dir / "conf.py").write_text("project = 'source'\n", encoding="utf-8")
            (md_dir / "index.md").write_text(
                "# Manual\n\n```{toctree}\n:hidden:\n\nmanual\n```\n", encoding="utf-8"
            )
            (md_dir / "manual.md").write_text("# Manual\n\nHello world.\n", encoding="utf-8")

            fake_proc = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
            html_dir = None
            with mock.patch.object(
                web_sideload.subprocess, "run", return_value=fake_proc
            ) as run_sphinx:
                # Must not raise. Before the fix this always raised
                # RuntimeError("RTD source output must stay under build
                # root: ...") because assembled_dir was temp_dir/"rtd", a
                # sibling of build_root = temp_dir/"source".
                html_dir = web_sideload._run_sideload_strict_verification(
                    md_dir=md_dir, title="Real Run"
                )

            try:
                run_sphinx.assert_called_once()
                sphinx_argv = run_sphinx.call_args.args[0]
                assembled_dir = Path(sphinx_argv[-2])
                build_root = assembled_dir.parent

                self.assertTrue(assembled_dir.is_relative_to(build_root))
                self.assertEqual("source", build_root.name)
                self.assertEqual("rtd", assembled_dir.name)
                # assemble_rtd_source really ran: real generated output on disk.
                self.assertTrue((assembled_dir / "index.md").is_file())
                self.assertTrue((assembled_dir / "conf.py").is_file())
                # The returned html dir is the staging input, not cleaned up
                # by this function itself -- the caller owns that.
                self.assertEqual(str(html_dir), sphinx_argv[-1])
                self.assertTrue(html_dir.parent.is_dir())
            finally:
                if html_dir is not None:
                    shutil.rmtree(html_dir.parent, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
