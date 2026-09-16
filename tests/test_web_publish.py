from __future__ import annotations

import argparse
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import mock

from tools import build_cli, web_publish
from tools.web_publish import (
    DebtEntry,
    WebReleaseTarget,
    check_batch_for_collisions,
    parse_debt_flag,
    parse_targets_file,
    record_debt_entries,
    run_web_release,
)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class TargetsFileParsingTests(unittest.TestCase):
    def test_parses_rows_with_and_without_explicit_version(self) -> None:
        with TemporaryDirectory() as tmp:
            targets_path = Path(tmp) / "targets.txt"
            _write(
                targets_path,
                "\n".join(
                    [
                        "# a comment line",
                        "",
                        "JE-1000F,US,en,2.0",
                        "  JE-1000F , US , fr  ",
                    ]
                ),
            )

            targets = parse_targets_file(targets_path)

        self.assertEqual(
            [
                WebReleaseTarget(model="JE-1000F", region="US", lang="en", version="2.0"),
                WebReleaseTarget(model="JE-1000F", region="US", lang="fr", version=""),
            ],
            targets,
        )

    def test_rejects_a_row_with_the_wrong_column_count(self) -> None:
        with TemporaryDirectory() as tmp:
            targets_path = Path(tmp) / "targets.txt"
            _write(targets_path, "JE-1000F,US\n")

            with self.assertRaisesRegex(RuntimeError, "MODEL,REGION,LANG"):
                parse_targets_file(targets_path)

    def test_rejects_an_empty_file(self) -> None:
        with TemporaryDirectory() as tmp:
            targets_path = Path(tmp) / "targets.txt"
            _write(targets_path, "# only comments\n\n")

            with self.assertRaisesRegex(RuntimeError, "no target rows"):
                parse_targets_file(targets_path)

    def test_rejects_a_missing_file(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "must be a real file"):
            parse_targets_file(Path("/does/not/exist.txt"))


class DebtFlagParsingTests(unittest.TestCase):
    def test_parses_category_location_and_payoff_action(self) -> None:
        self.assertEqual(
            ("译文缺失", "05_operation_guide", "wait on translation intake"),
            parse_debt_flag("译文缺失:05_operation_guide:wait on translation intake"),
        )

    def test_payoff_action_may_itself_contain_colons(self) -> None:
        self.assertEqual(
            ("其他", "loc", "see https://example.com:8080/note"),
            parse_debt_flag("其他:loc:see https://example.com:8080/note"),
        )

    def test_rejects_missing_fields(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "category:location:payoff action"):
            parse_debt_flag("only-one-field")

    def test_rejects_blank_category(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "category:location:payoff action"):
            parse_debt_flag(":loc:action")


class CollisionPrecheckTests(unittest.TestCase):
    def test_allows_the_same_book_across_several_languages(self) -> None:
        targets = [
            WebReleaseTarget(model="JE-1000F", region="US", lang="en", version="2.0"),
            WebReleaseTarget(model="JE-1000F", region="US", lang="fr", version="2.0"),
            WebReleaseTarget(model="JE-1000F", region="US", lang="es", version="2.0"),
        ]

        def fake_build_path(*, config_path, model, region, lang):
            return Path(f"/repo/docs/_build/{model}/{region}/{lang}/md/manual_{model}_{region}.md")

        with mock.patch.object(
            web_publish, "resolve_md_output_path_for_target", side_effect=fake_build_path
        ):
            check_batch_for_collisions(config_path=Path("configs/config.us.yaml"), targets=targets)

    def test_rejects_two_targets_that_resolve_to_the_same_build_path(self) -> None:
        targets = [
            WebReleaseTarget(model="JE-1000F", region="US", lang="en", version="2.0"),
            WebReleaseTarget(model="JE-1000F", region="US", lang="en", version="2.0"),
        ]

        with mock.patch.object(
            web_publish,
            "resolve_md_output_path_for_target",
            return_value=Path("/repo/docs/_build/JE-1000F/US/en/md/manual.md"),
        ):
            with self.assertRaisesRegex(RuntimeError, "same build\noutput path|same build output path"):
                check_batch_for_collisions(
                    config_path=Path("configs/config.us.yaml"), targets=targets
                )

    def test_rejects_two_different_books_that_alias_to_the_same_route(self) -> None:
        targets = [
            WebReleaseTarget(model="je-1000f", region="US", lang="en", version="2.0"),
            WebReleaseTarget(model="JE-1000F", region="us", lang="EN", version="2.0"),
        ]

        def fake_build_path(*, config_path, model, region, lang):
            # Different-cased identities still land on the same real path.
            return Path("/repo/docs/_build/JE-1000F/US/en/md/manual.md")

        with mock.patch.object(
            web_publish, "resolve_md_output_path_for_target", side_effect=fake_build_path
        ):
            with self.assertRaises(RuntimeError):
                check_batch_for_collisions(
                    config_path=Path("configs/config.us.yaml"), targets=targets
                )


class DebtLedgerTests(unittest.TestCase):
    def test_records_to_the_per_book_ledger_and_the_total_ledger(self) -> None:
        with TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            version_dir = repo_root / "reports" / "releases" / "JE-1000F" / "US" / "en" / "versions" / "2.0"
            target = WebReleaseTarget(model="JE-1000F", region="US", lang="en", version="2.0")
            entry = DebtEntry(
                model="JE-1000F",
                region="US",
                lang="en",
                date="2026-09-16",
                category="内容糙",
                location="05_operation_guide",
                payoff_action="tighten the wording",
                source="manual",
            )

            with mock.patch.object(
                web_publish,
                "publish_release_version_dir_for_target",
                return_value=version_dir,
            ):
                record_debt_entries(
                    repo_root=repo_root,
                    config_path=Path("configs/config.us.yaml"),
                    target=target,
                    entries=[entry],
                )
                # A second call must append, not overwrite.
                record_debt_entries(
                    repo_root=repo_root,
                    config_path=Path("configs/config.us.yaml"),
                    target=target,
                    entries=[entry],
                )

            per_book_path = version_dir / "web" / "debt_ledger.json"
            per_book_payload = json.loads(per_book_path.read_text(encoding="utf-8"))
            self.assertEqual(2, len(per_book_payload["entries"]))
            self.assertEqual("内容糙", per_book_payload["entries"][0]["category"])
            self.assertEqual(
                {"model": "JE-1000F", "region": "US", "lang": "en"},
                per_book_payload["entries"][0]["target"],
            )

            total_path = repo_root / "reports" / "web_debt_ledger.jsonl"
            lines = total_path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(2, len(lines))
            for line in lines:
                row = json.loads(line)
                self.assertEqual("manual", row["source"])

            # The evidence directory sibling invariant: nothing was written
            # inside a would-be evidence/ folder (verify_release_evidence
            # asserts that directory holds exactly two fixed files).
            self.assertFalse((version_dir / "web" / "evidence").exists())

    def test_records_nothing_when_there_are_no_entries(self) -> None:
        with TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            record_debt_entries(
                repo_root=repo_root,
                config_path=Path("configs/config.us.yaml"),
                target=WebReleaseTarget(model="JE-1000F", region="US", lang="en", version="2.0"),
                entries=[],
            )
            self.assertFalse((repo_root / "reports" / "web_debt_ledger.jsonl").exists())


class CliRegistrationTests(unittest.TestCase):
    def test_web_release_action_and_flags_parse(self) -> None:
        args = build_cli.parse_args(
            [
                "web-release",
                "--config",
                "configs/config.us.yaml",
                "--model",
                "JE-1000F",
                "--region",
                "US",
                "--lang",
                "en",
                "--version",
                "2.0",
                "--targets-file",
                "targets.txt",
                "--debt",
                "内容糙:page:tighten wording",
                "--debt",
                "其他:page2:follow up",
                "--skip-verify",
                "--dry-run",
            ],
            default_config="configs/config.us.yaml",
            build_actions=("rst", "word", "html", "pdf", "md", "all"),
            staging_root_env="AUTO_MANUAL_STAGING_ROOT",
        )

        self.assertEqual("web-release", args.action)
        self.assertEqual("targets.txt", args.targets_file)
        self.assertEqual(
            ["内容糙:page:tighten wording", "其他:page2:follow up"], args.debt
        )
        self.assertTrue(args.skip_verify)
        self.assertTrue(args.dry_run)


class RunWebReleaseOrchestrationTests(unittest.TestCase):
    def _args(self, **overrides) -> argparse.Namespace:
        values = {
            "config": "configs/config.us.yaml",
            "model": "JE-1000F",
            "region": "US",
            "lang": "en",
            "version": "2.0",
            "data_root": "data/phase2",
            "targets_file": None,
            "debt": [],
            "skip_verify": True,
            "dry_run": False,
        }
        values.update(overrides)
        return argparse.Namespace(**values)

    def test_dry_run_checks_collisions_but_builds_nothing(self) -> None:
        args = self._args(dry_run=True)

        with mock.patch.object(
            web_publish, "check_batch_for_collisions"
        ) as collision_check, mock.patch.object(
            web_publish, "_current_git_head_sha"
        ) as head_sha, mock.patch.object(
            web_publish, "run_web_language_build_steps"
        ) as build_steps:
            run_web_release(args, repo_root=Path("/repo"), resolve_path_from_root=lambda raw: Path("/repo") / raw)

        collision_check.assert_called_once()
        head_sha.assert_not_called()
        build_steps.assert_not_called()

    def test_missing_version_is_rejected_before_any_build(self) -> None:
        args = self._args(version="")

        with mock.patch.object(web_publish, "run_web_language_build_steps") as build_steps:
            with self.assertRaisesRegex(RuntimeError, "requires a version"):
                run_web_release(
                    args, repo_root=Path("/repo"), resolve_path_from_root=lambda raw: Path("/repo") / raw
                )

        build_steps.assert_not_called()

    def test_single_target_happy_path_runs_every_step_in_order(self) -> None:
        args = self._args(skip_verify=False)
        calls: list[str] = []
        md_path = Path("/repo/docs/_build/JE-1000F/US/en/md/manual.md")
        html_dir = Path("/repo/docs/_build/JE-1000F/US/en/html")
        staged_md = Path("/repo/reports/releases/JE-1000F/US/en/versions/2.0/web/md/manual.md")
        staged_html = Path("/repo/reports/releases/JE-1000F/US/en/versions/2.0/web/html")
        version_dir = Path("/repo/reports/releases/JE-1000F/US/en/versions/2.0")
        captures = [SimpleNamespace(action=action) for action in ("check", "md", "html")]

        with mock.patch.object(
            web_publish, "check_batch_for_collisions"
        ), mock.patch.object(
            web_publish, "_current_git_head_sha", return_value="a" * 40
        ), mock.patch.object(
            web_publish, "run_command", side_effect=lambda *a, **k: calls.append("warmup-check")
        ), mock.patch.object(
            web_publish,
            "run_web_language_build_steps",
            side_effect=lambda **_: (calls.append("build-capture"), captures)[1],
        ), mock.patch.object(
            web_publish, "require_consistent_captures", side_effect=lambda c: calls.append("require-consistent") or tuple(c)
        ), mock.patch.object(
            web_publish, "resolve_md_output_path_for_target", return_value=md_path
        ), mock.patch.object(
            web_publish, "resolve_html_output_dir_for_target", return_value=html_dir
        ), mock.patch.object(
            web_publish, "_run_strict_web_verification"
        ) as strict_verify, mock.patch.object(
            web_publish,
            "stage_web_publish_assets_to_host_repo",
            side_effect=lambda **_: (calls.append("stage"), (staged_md, staged_html))[1],
        ) as stage, mock.patch.object(
            web_publish, "publish_release_version_dir_for_target", return_value=version_dir
        ), mock.patch.object(
            web_publish, "write_web_publish_metadata", side_effect=lambda **_: calls.append("write-metadata")
        ) as write_meta, mock.patch.object(
            web_publish, "record_debt_entries"
        ) as record_debt:
            run_web_release(
                args, repo_root=Path("/repo"), resolve_path_from_root=lambda raw: Path("/repo") / raw
            )

        self.assertEqual(
            ["warmup-check", "build-capture", "require-consistent", "stage", "write-metadata"],
            calls,
        )
        strict_verify.assert_called_once()
        stage.assert_called_once()
        self.assertEqual("a" * 40, stage.call_args.kwargs["git_ref"])
        self.assertEqual("en", stage.call_args.kwargs["target_lang"])
        write_meta.assert_called_once()
        # No --debt flags were supplied, so no manual ledger write for a
        # successful target.
        record_debt.assert_not_called()

    def test_skip_verify_flag_bypasses_the_strict_verification_pass(self) -> None:
        args = self._args(skip_verify=True)
        version_dir = Path("/repo/reports/releases/JE-1000F/US/en/versions/2.0")

        with mock.patch.object(
            web_publish, "check_batch_for_collisions"
        ), mock.patch.object(
            web_publish, "_current_git_head_sha", return_value="a" * 40
        ), mock.patch.object(
            web_publish, "run_command"
        ), mock.patch.object(
            web_publish, "run_web_language_build_steps", return_value=[]
        ), mock.patch.object(
            web_publish, "require_consistent_captures", return_value=()
        ), mock.patch.object(
            web_publish, "resolve_md_output_path_for_target", return_value=Path("/repo/md/manual.md")
        ), mock.patch.object(
            web_publish, "resolve_html_output_dir_for_target", return_value=Path("/repo/html")
        ), mock.patch.object(
            web_publish, "_run_strict_web_verification"
        ) as strict_verify, mock.patch.object(
            web_publish,
            "stage_web_publish_assets_to_host_repo",
            return_value=(Path("/repo/staged.md"), Path("/repo/staged-html")),
        ), mock.patch.object(
            web_publish, "publish_release_version_dir_for_target", return_value=version_dir
        ), mock.patch.object(
            web_publish, "write_web_publish_metadata"
        ):
            run_web_release(
                args, repo_root=Path("/repo"), resolve_path_from_root=lambda raw: Path("/repo") / raw
            )

        strict_verify.assert_not_called()

    def test_manual_debt_flags_are_recorded_only_for_successful_targets(self) -> None:
        args = self._args(debt=["内容糙:p1:tighten wording"])
        version_dir = Path("/repo/reports/releases/JE-1000F/US/en/versions/2.0")

        with mock.patch.object(
            web_publish, "check_batch_for_collisions"
        ), mock.patch.object(
            web_publish, "_current_git_head_sha", return_value="a" * 40
        ), mock.patch.object(
            web_publish, "run_command"
        ), mock.patch.object(
            web_publish, "run_web_language_build_steps", return_value=[]
        ), mock.patch.object(
            web_publish, "require_consistent_captures", return_value=()
        ), mock.patch.object(
            web_publish, "resolve_md_output_path_for_target", return_value=Path("/repo/md/manual.md")
        ), mock.patch.object(
            web_publish, "resolve_html_output_dir_for_target", return_value=Path("/repo/html")
        ), mock.patch.object(
            web_publish, "_run_strict_web_verification"
        ), mock.patch.object(
            web_publish,
            "stage_web_publish_assets_to_host_repo",
            return_value=(Path("/repo/staged.md"), Path("/repo/staged-html")),
        ), mock.patch.object(
            web_publish, "publish_release_version_dir_for_target", return_value=version_dir
        ), mock.patch.object(
            web_publish, "write_web_publish_metadata"
        ), mock.patch.object(
            web_publish, "record_debt_entries"
        ) as record_debt:
            run_web_release(
                args, repo_root=Path("/repo"), resolve_path_from_root=lambda raw: Path("/repo") / raw
            )

        record_debt.assert_called_once()
        recorded_entries = record_debt.call_args.kwargs["entries"]
        self.assertEqual(1, len(recorded_entries))
        self.assertEqual("内容糙", recorded_entries[0].category)
        self.assertEqual("manual", recorded_entries[0].source)

    def test_batch_isolates_a_single_failure_and_still_raises_overall(self) -> None:
        targets_calls: list[str] = []

        def fake_build_steps(*, model, region, lang, **_):
            targets_calls.append(lang)
            if lang == "fr":
                raise RuntimeError("pandoc exploded")
            return []

        args = self._args(model=None, region=None, lang=None, targets_file="targets.txt")

        def fake_parse_targets_file(path):
            return [
                WebReleaseTarget(model="JE-1000F", region="US", lang="en", version="2.0"),
                WebReleaseTarget(model="JE-1000F", region="US", lang="fr", version="2.0"),
                WebReleaseTarget(model="JE-1000F", region="US", lang="es", version="2.0"),
            ]

        version_dir = Path("/repo/reports/releases/JE-1000F/US/x/versions/2.0")

        with mock.patch.object(
            web_publish, "parse_targets_file", side_effect=fake_parse_targets_file
        ), mock.patch.object(
            web_publish, "check_batch_for_collisions"
        ), mock.patch.object(
            web_publish, "_current_git_head_sha", return_value="a" * 40
        ), mock.patch.object(
            web_publish, "run_command"
        ), mock.patch.object(
            web_publish, "run_web_language_build_steps", side_effect=fake_build_steps
        ), mock.patch.object(
            web_publish, "require_consistent_captures", return_value=()
        ), mock.patch.object(
            web_publish, "resolve_md_output_path_for_target", return_value=Path("/repo/md/manual.md")
        ), mock.patch.object(
            web_publish, "resolve_html_output_dir_for_target", return_value=Path("/repo/html")
        ), mock.patch.object(
            web_publish, "_run_strict_web_verification"
        ), mock.patch.object(
            web_publish,
            "stage_web_publish_assets_to_host_repo",
            return_value=(Path("/repo/staged.md"), Path("/repo/staged-html")),
        ), mock.patch.object(
            web_publish, "publish_release_version_dir_for_target", return_value=version_dir
        ), mock.patch.object(
            web_publish, "write_web_publish_metadata"
        ), mock.patch.object(
            web_publish, "record_debt_entries"
        ) as record_debt:
            with self.assertRaisesRegex(RuntimeError, r"1/3 target\(s\) failed"):
                run_web_release(
                    args, repo_root=Path("/repo"), resolve_path_from_root=lambda raw: Path("/repo") / raw
                )

        # All three targets were attempted despite the middle one failing.
        self.assertEqual(["en", "fr", "es"], targets_calls)
        record_debt.assert_called_once()
        auto_entries = record_debt.call_args.kwargs["entries"]
        self.assertEqual(1, len(auto_entries))
        self.assertEqual("构建失败", auto_entries[0].category)
        self.assertEqual("auto", auto_entries[0].source)
        self.assertEqual("fr", record_debt.call_args.kwargs["target"].lang)


if __name__ == "__main__":
    unittest.main()
