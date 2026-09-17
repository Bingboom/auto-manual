from __future__ import annotations

import argparse
import json
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from tools import build_cli, web_assemble
from tools.web_assemble import resolve_hello_docs_remote, run_web_assemble


def _proc(returncode: int = 0, stdout: str = "", stderr: str = "") -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(args=["git"], returncode=returncode, stdout=stdout, stderr=stderr)


class ResolveHelloDocsRemoteTests(unittest.TestCase):
    def test_defaults_to_the_github_slug(self) -> None:
        self.assertEqual(
            "https://github.com/Bingboom/Hello-Docs.git", resolve_hello_docs_remote(None)
        )
        self.assertEqual(
            "https://github.com/Bingboom/Hello-Docs.git", resolve_hello_docs_remote("  ")
        )

    def test_passes_through_a_full_url(self) -> None:
        self.assertEqual(
            "git@github.com:Bingboom/Hello-Docs.git",
            resolve_hello_docs_remote("git@github.com:Bingboom/Hello-Docs.git"),
        )
        self.assertEqual(
            "https://example.com/hello-docs.git",
            resolve_hello_docs_remote("https://example.com/hello-docs.git"),
        )

    def test_resolves_an_owner_repo_slug_to_a_github_url(self) -> None:
        self.assertEqual(
            "https://github.com/Acme/Docs.git", resolve_hello_docs_remote("Acme/Docs")
        )

    def test_passes_through_an_existing_local_path_for_tests(self) -> None:
        with TemporaryDirectory() as tmp:
            local_repo = Path(tmp) / "fake-hello-docs"
            local_repo.mkdir()
            self.assertEqual(str(local_repo), resolve_hello_docs_remote(str(local_repo)))


class PublishBranchExistsTests(unittest.TestCase):
    def test_true_on_exit_zero(self) -> None:
        run = mock.Mock(return_value=_proc(returncode=0))
        self.assertTrue(web_assemble._publish_branch_exists(run, Path("/clone")))

    def test_false_on_exit_two_no_matching_refs(self) -> None:
        run = mock.Mock(return_value=_proc(returncode=2))
        self.assertFalse(web_assemble._publish_branch_exists(run, Path("/clone")))

    def test_raises_on_an_unexpected_exit_code(self) -> None:
        run = mock.Mock(return_value=_proc(returncode=128, stderr="network unreachable"))
        with self.assertRaisesRegex(RuntimeError, "network unreachable"):
            web_assemble._publish_branch_exists(run, Path("/clone"))


class ValidateScopeTests(unittest.TestCase):
    def test_accepts_a_diff_entirely_under_docs_publish(self) -> None:
        def fake_run(cmd, cwd):
            if "merge-base" in cmd:
                return _proc(returncode=0)
            if "diff" in cmd:
                return _proc(returncode=0, stdout="docs/publish/web/index.html\0docs/publish/publish_manifest.json\0")
            raise AssertionError(f"unexpected command: {cmd}")

        count, paths = web_assemble._validate_scope(fake_run, Path("/clone"))

        self.assertEqual(2, count)
        self.assertEqual(
            ("docs/publish/web/index.html", "docs/publish/publish_manifest.json"), paths
        )

    def test_rejects_a_path_outside_docs_publish(self) -> None:
        def fake_run(cmd, cwd):
            if "merge-base" in cmd:
                return _proc(returncode=0)
            if "diff" in cmd:
                return _proc(returncode=0, stdout="docs/publish/web/index.html\0build.py\0")
            raise AssertionError(f"unexpected command: {cmd}")

        with self.assertRaisesRegex(RuntimeError, "only docs/publish"):
            web_assemble._validate_scope(fake_run, Path("/clone"))

    def test_raises_when_main_is_not_yet_an_ancestor(self) -> None:
        def fake_run(cmd, cwd):
            if "merge-base" in cmd:
                return _proc(returncode=1)
            raise AssertionError(f"unexpected command: {cmd}")

        with self.assertRaisesRegex(RuntimeError, "ancestor"):
            web_assemble._validate_scope(fake_run, Path("/clone"))


class AggregateStrictVerificationTests(unittest.TestCase):
    """``.readthedocs.yaml``'s ``docs/publish/web`` build runs

        python -m sphinx -b html -D extensions=myst_parser,tools.rtd_portal docs/publish/web ...

    Before this fix, this local gate ran plain ``sphinx -W -b html`` with no
    ``-D`` override, so ``tools.rtd_portal`` -- and the language-table lookup
    inside its ``page_context`` handler -- never executed here even though
    Read the Docs always bolts that extension on at build time (the
    assembled ``conf.py`` only ever declares ``extensions = ["myst_parser"]``;
    see ``tools/readthedocs_source.py::_write_conf_py``). Production build
    34602012 crashed with ``Unknown portal publication language: ja`` while
    this same-looking local check stayed green.
    """

    def test_sphinx_invocation_matches_the_rtd_build_command(self) -> None:
        with TemporaryDirectory() as clone_tmp:
            clone_dir = Path(clone_tmp)
            (clone_dir / "docs" / "publish" / "web").mkdir(parents=True)
            calls: list[list[str]] = []

            def fake_run(cmd, cwd):
                self.assertEqual(clone_dir, cwd)
                calls.append(list(cmd))
                return _proc(returncode=0)

            web_assemble._run_aggregate_strict_verification(fake_run, clone_dir)

        self.assertEqual(1, len(calls))
        cmd = calls[0]
        self.assertIn("-W", cmd)
        self.assertIn("-b", cmd)
        self.assertIn("html", cmd)
        self.assertIn("-D", cmd)
        d_index = cmd.index("-D")
        self.assertEqual("extensions=myst_parser,tools.rtd_portal", cmd[d_index + 1])

    def test_missing_web_source_raises_before_running_sphinx(self) -> None:
        with TemporaryDirectory() as clone_tmp:
            clone_dir = Path(clone_tmp)  # no docs/publish/web assembled

            def fake_run(cmd, cwd):
                raise AssertionError("sphinx must not run without an assembled Web source")

            with self.assertRaisesRegex(RuntimeError, "no Web source to verify"):
                web_assemble._run_aggregate_strict_verification(fake_run, clone_dir)

    def test_sphinx_failure_surfaces_as_a_runtime_error(self) -> None:
        with TemporaryDirectory() as clone_tmp:
            clone_dir = Path(clone_tmp)
            (clone_dir / "docs" / "publish" / "web").mkdir(parents=True)

            def fake_run(cmd, cwd):
                return _proc(returncode=1, stderr="Unknown portal publication language: ja")

            with self.assertRaisesRegex(RuntimeError, "Unknown portal publication language: ja"):
                web_assemble._run_aggregate_strict_verification(fake_run, clone_dir)


class CommitCandidateTests(unittest.TestCase):
    def test_returns_none_when_nothing_is_staged(self) -> None:
        calls: list[list[str]] = []

        def fake_run(cmd, cwd):
            calls.append(list(cmd))
            if cmd[:2] == ["git", "diff"]:
                return _proc(returncode=0)  # --quiet: 0 means no diff
            return _proc(returncode=0)

        result = web_assemble._commit_candidate(fake_run, Path("/clone"))

        self.assertIsNone(result)
        self.assertNotIn(["git", "commit", "-m", web_assemble._COMMIT_MESSAGE], calls)

    def test_commits_and_returns_the_new_sha_when_something_changed(self) -> None:
        def fake_run(cmd, cwd):
            if cmd[:2] == ["git", "diff"]:
                return _proc(returncode=1)  # --quiet: 1 means there is a diff
            if cmd[:2] == ["git", "rev-parse"]:
                return _proc(returncode=0, stdout="a" * 40 + "\n")
            return _proc(returncode=0)

        result = web_assemble._commit_candidate(fake_run, Path("/clone"))

        self.assertEqual("a" * 40, result)

    def test_raises_on_an_unexpected_diff_exit_code(self) -> None:
        def fake_run(cmd, cwd):
            if cmd[:2] == ["git", "diff"]:
                return _proc(returncode=128, stderr="fatal: bad revision")
            return _proc(returncode=0)

        with self.assertRaisesRegex(RuntimeError, "bad revision"):
            web_assemble._commit_candidate(fake_run, Path("/clone"))


class PushCandidateTests(unittest.TestCase):
    def test_skips_the_push_when_already_current(self) -> None:
        def fake_run(cmd, cwd):
            if cmd[:2] == ["git", "rev-parse"] and "--verify" in cmd:
                return _proc(returncode=0, stdout="a" * 40 + "\n")
            if cmd[:2] == ["git", "rev-parse"]:
                return _proc(returncode=0, stdout="a" * 40 + "\n")
            if cmd[:2] == ["git", "push"] or (len(cmd) > 2 and cmd[2] == "push"):
                raise AssertionError("push must not run when already current")
            return _proc(returncode=0)

        pushed = web_assemble._push_candidate(fake_run, Path("/clone"))

        self.assertFalse(pushed)

    def test_pushes_when_the_remote_tip_differs(self) -> None:
        push_calls: list[list[str]] = []

        def fake_run(cmd, cwd):
            if "--verify" in cmd:
                return _proc(returncode=0, stdout="b" * 40 + "\n")
            if cmd[:2] == ["git", "rev-parse"]:
                return _proc(returncode=0, stdout="a" * 40 + "\n")
            if "push" in cmd:
                push_calls.append(list(cmd))
                return _proc(returncode=0)
            return _proc(returncode=0)

        pushed = web_assemble._push_candidate(fake_run, Path("/clone"))

        self.assertTrue(pushed)
        self.assertEqual(1, len(push_calls))
        self.assertIn("HEAD:refs/heads/publish", push_calls[0])

    def test_a_non_fast_forward_push_raises_instead_of_forcing(self) -> None:
        def fake_run(cmd, cwd):
            if "--verify" in cmd:
                return _proc(returncode=0, stdout="b" * 40 + "\n")
            if cmd[:2] == ["git", "rev-parse"]:
                return _proc(returncode=0, stdout="a" * 40 + "\n")
            if "push" in cmd:
                return _proc(returncode=1, stderr="! [rejected] non-fast-forward")
            return _proc(returncode=0)

        with self.assertRaisesRegex(RuntimeError, "non-fast-forward"):
            web_assemble._push_candidate(fake_run, Path("/clone"))


class OpenOrUpdatePrTests(unittest.TestCase):
    def test_returns_the_existing_open_pr_without_creating_one(self) -> None:
        create_calls: list[list[str]] = []

        def fake_run(cmd, cwd):
            if cmd[:2] == ["gh", "pr"] and cmd[2] == "list":
                return _proc(returncode=0, stdout="https://github.com/Bingboom/Hello-Docs/pull/7\n")
            if cmd[:2] == ["gh", "pr"] and cmd[2] == "create":
                create_calls.append(list(cmd))
                return _proc(returncode=0)
            raise AssertionError(f"unexpected command: {cmd}")

        url = web_assemble._open_or_update_pr(fake_run, Path("/clone"))

        self.assertEqual("https://github.com/Bingboom/Hello-Docs/pull/7", url)
        self.assertEqual([], create_calls)

    def test_creates_a_pr_when_none_is_open(self) -> None:
        def fake_run(cmd, cwd):
            if cmd[:2] == ["gh", "pr"] and cmd[2] == "list":
                return _proc(returncode=0, stdout="")
            if cmd[:2] == ["gh", "pr"] and cmd[2] == "create":
                return _proc(returncode=0, stdout="https://github.com/Bingboom/Hello-Docs/pull/9\n")
            raise AssertionError(f"unexpected command: {cmd}")

        url = web_assemble._open_or_update_pr(fake_run, Path("/clone"))

        self.assertEqual("https://github.com/Bingboom/Hello-Docs/pull/9", url)

    def test_raises_when_gh_pr_create_fails(self) -> None:
        def fake_run(cmd, cwd):
            if cmd[:2] == ["gh", "pr"] and cmd[2] == "list":
                return _proc(returncode=0, stdout="")
            if cmd[:2] == ["gh", "pr"] and cmd[2] == "create":
                return _proc(returncode=1, stderr="HTTP 403: not authorized")
            raise AssertionError(f"unexpected command: {cmd}")

        with self.assertRaisesRegex(RuntimeError, "not authorized"):
            web_assemble._open_or_update_pr(fake_run, Path("/clone"))


class ReconcileCandidateTests(unittest.TestCase):
    def test_first_run_with_no_publish_branch_does_nothing_else(self) -> None:
        calls: list[list[str]] = []

        def fake_run(cmd, cwd):
            calls.append(list(cmd))
            if "ls-remote" in cmd:
                return _proc(returncode=2)  # no matching refs: publish does not exist yet
            raise AssertionError(f"unexpected command beyond ls-remote: {cmd}")

        with TemporaryDirectory() as tmp:
            clone_dir = Path(tmp) / "clone"
            clone_dir.mkdir()
            preserved_dir = Path(tmp) / "preserved"
            web_assemble._reconcile_candidate(fake_run, clone_dir, preserved_dir)

        self.assertEqual(1, len(calls))

    def test_preserves_and_restores_docs_publish_across_the_reset(self) -> None:
        """The read-tree reset can drop docs/publish (main may not carry the
        same content yet); the Python-level backup/restore around it must
        bring back what the existing publish branch already staged."""

        with TemporaryDirectory() as tmp:
            clone_dir = Path(tmp) / "clone"
            docs_publish_dir = clone_dir / "docs" / "publish"
            docs_publish_dir.mkdir(parents=True)
            (docs_publish_dir / "publish_manifest.json").write_text("{\"targets\": []}\n", encoding="utf-8")
            preserved_dir = Path(tmp) / "preserved"

            def fake_run(cmd, cwd):
                if "ls-remote" in cmd:
                    return _proc(returncode=0)  # publish already exists
                if "read-tree" in cmd:
                    # Simulate git replacing the working tree with main's,
                    # which does not (yet) carry this docs/publish content.
                    import shutil

                    shutil.rmtree(docs_publish_dir, ignore_errors=True)
                    return _proc(returncode=0)
                if "merge-base" in cmd:
                    return _proc(returncode=0)  # main already an ancestor: no -s ours merge
                if "merge" in cmd:
                    raise AssertionError("must not merge when main is already an ancestor")
                return _proc(returncode=0)

            web_assemble._reconcile_candidate(fake_run, clone_dir, preserved_dir)

            self.assertTrue((preserved_dir / "publish_manifest.json").is_file())
            self.assertTrue(docs_publish_dir.is_dir())
            self.assertTrue((docs_publish_dir / "publish_manifest.json").is_file())

    def test_runs_a_tree_preserving_merge_when_main_is_not_yet_an_ancestor(self) -> None:
        merge_calls: list[list[str]] = []

        def fake_run(cmd, cwd):
            if "ls-remote" in cmd:
                return _proc(returncode=0)
            if "merge-base" in cmd:
                return _proc(returncode=1)  # not yet an ancestor
            if cmd[:2] == ["git", "merge"]:
                merge_calls.append(list(cmd))
                return _proc(returncode=0)
            return _proc(returncode=0)

        with TemporaryDirectory() as tmp:
            clone_dir = Path(tmp) / "clone"
            clone_dir.mkdir()
            preserved_dir = Path(tmp) / "preserved"
            web_assemble._reconcile_candidate(fake_run, clone_dir, preserved_dir)

        self.assertEqual(1, len(merge_calls))
        self.assertIn("-s", merge_calls[0])
        self.assertIn("ours", merge_calls[0])


class ManifestHelperTests(unittest.TestCase):
    def test_reads_target_rows_from_the_manifest(self) -> None:
        with TemporaryDirectory() as tmp:
            manifest_path = Path(tmp) / "publish_manifest.json"
            manifest_path.write_text(
                json.dumps({"targets": [{"model": "JE-1000F", "region": "US", "lang": "en"}]}),
                encoding="utf-8",
            )

            targets = web_assemble._read_manifest_targets(manifest_path)

        self.assertEqual([{"model": "JE-1000F", "region": "US", "lang": "en"}], targets)

    def test_hashes_the_manifest_bytes(self) -> None:
        with TemporaryDirectory() as tmp:
            manifest_path = Path(tmp) / "publish_manifest.json"
            manifest_path.write_bytes(b"hello")

            import hashlib

            self.assertEqual(hashlib.sha256(b"hello").hexdigest(), web_assemble._sha256_file(manifest_path))


class CliRegistrationTests(unittest.TestCase):
    def test_web_assemble_action_and_flags_parse(self) -> None:
        args = build_cli.parse_args(
            [
                "web-assemble",
                "--releases-root",
                "reports/releases",
                "--title",
                "Auto Manual Library",
                "--hello-docs-repo",
                "Acme/Docs",
                "--push",
                "--dry-run",
            ],
            default_config="configs/config.us.yaml",
            build_actions=("rst", "word", "html", "pdf", "md", "all"),
            staging_root_env="AUTO_MANUAL_STAGING_ROOT",
        )

        self.assertEqual("web-assemble", args.action)
        self.assertEqual("reports/releases", args.releases_root)
        self.assertEqual("Auto Manual Library", args.title)
        self.assertEqual("Acme/Docs", args.hello_docs_repo)
        self.assertTrue(args.push)
        self.assertTrue(args.dry_run)

    def test_web_assemble_flags_default_to_none_or_false(self) -> None:
        args = build_cli.parse_args(
            ["web-assemble"],
            default_config="configs/config.us.yaml",
            build_actions=("rst", "word", "html", "pdf", "md", "all"),
            staging_root_env="AUTO_MANUAL_STAGING_ROOT",
        )

        self.assertIsNone(args.releases_root)
        self.assertIsNone(args.title)
        self.assertIsNone(args.hello_docs_repo)
        self.assertFalse(args.push)
        self.assertFalse(args.dry_run)


class RunWebAssembleOrchestrationTests(unittest.TestCase):
    def _args(self, **overrides) -> argparse.Namespace:
        values = {
            "releases_root": None,
            "title": None,
            "hello_docs_repo": None,
            "push": False,
            "dry_run": False,
        }
        values.update(overrides)
        return argparse.Namespace(**values)

    def test_dry_run_touches_no_subprocess_at_all(self) -> None:
        args = self._args(dry_run=True)

        def forbidden_run(cmd, cwd):
            raise AssertionError(f"--dry-run must not run any command, got {cmd}")

        report = run_web_assemble(
            args, repo_root=Path("/repo"), resolve_path_from_root=lambda raw: Path("/repo") / raw,
            run=forbidden_run,
        )

        self.assertTrue(report.dry_run)
        self.assertEqual("https://github.com/Bingboom/Hello-Docs.git", report.hello_docs_remote)

    def test_clone_uses_a_blobless_filter_not_a_shallow_depth(self) -> None:
        # _reconcile_candidate's merge-base --is-ancestor check and
        # _validate_scope's three-dot diff are the whole safety net for this
        # command; both need the real commit graph, so the clone must stay
        # full-history (--filter=blob:none lazily fetches file contents
        # instead) and must never truncate history with --depth.
        args = self._args()
        clone_calls: list[list[str]] = []

        def fake_run(cmd, cwd):
            if "clone" in cmd:
                clone_calls.append(list(cmd))
                return _proc(returncode=0)
            raise AssertionError(f"unexpected raw command: {cmd}")

        with mock.patch.object(web_assemble, "_reconcile_candidate", side_effect=RuntimeError("stop")):
            with self.assertRaises(RuntimeError):
                run_web_assemble(
                    args, repo_root=Path("/repo"), resolve_path_from_root=lambda raw: Path("/repo") / raw,
                    run=fake_run,
                )

        self.assertEqual(1, len(clone_calls))
        self.assertIn("--filter=blob:none", clone_calls[0])
        self.assertNotIn("--depth", clone_calls[0])

    def _patched(self, **overrides):
        defaults = dict(
            manifest_path=Path("/tmp/clone/docs/publish/publish_manifest.json"),
            manifest_sha256="deadbeef",
            included_targets=[{"model": "JE-1000F", "region": "US", "lang": "en"}],
        )
        defaults.update(overrides)
        patches = [
            mock.patch.object(web_assemble, "_reconcile_candidate"),
            mock.patch.object(
                web_assemble, "_assemble_candidate", return_value=defaults["manifest_path"]
            ),
            mock.patch.object(web_assemble, "_run_aggregate_strict_verification"),
            mock.patch.object(
                web_assemble, "_sha256_file", return_value=defaults["manifest_sha256"]
            ),
            mock.patch.object(
                web_assemble, "_read_manifest_targets", return_value=defaults["included_targets"]
            ),
        ]
        return patches

    def test_default_run_assembles_and_verifies_but_never_pushes(self) -> None:
        args = self._args()

        def fake_run(cmd, cwd):
            if "clone" in cmd:
                return _proc(returncode=0)
            raise AssertionError(f"unexpected raw command: {cmd}")

        patches = self._patched()
        with patches[0], patches[1], patches[2], patches[3], patches[4], mock.patch.object(
            web_assemble, "_commit_candidate", return_value="a" * 40
        ), mock.patch.object(
            web_assemble, "_validate_scope", return_value=(2, ("docs/publish/web/index.html",))
        ), mock.patch.object(
            web_assemble, "_push_candidate"
        ) as push, mock.patch.object(
            web_assemble, "_open_or_update_pr"
        ) as open_pr:
            report = run_web_assemble(
                args, repo_root=Path("/repo"), resolve_path_from_root=lambda raw: Path("/repo") / raw,
                run=fake_run,
            )

        push.assert_not_called()
        open_pr.assert_not_called()
        self.assertFalse(report.pushed)
        self.assertIsNone(report.pr_url)
        self.assertTrue(report.committed)
        self.assertEqual(2, report.changed_path_count)
        self.assertEqual("deadbeef", report.manifest_sha256)
        self.assertEqual([{"model": "JE-1000F", "region": "US", "lang": "en"}], list(report.included_targets))

    def test_push_flag_pushes_and_opens_the_pr_when_there_are_changes(self) -> None:
        args = self._args(push=True)

        def fake_run(cmd, cwd):
            if "clone" in cmd:
                return _proc(returncode=0)
            raise AssertionError(f"unexpected raw command: {cmd}")

        patches = self._patched()
        with patches[0], patches[1], patches[2], patches[3], patches[4], mock.patch.object(
            web_assemble, "_commit_candidate", return_value="a" * 40
        ), mock.patch.object(
            web_assemble, "_validate_scope", return_value=(1, ("docs/publish/web/index.html",))
        ), mock.patch.object(
            web_assemble, "_push_candidate", return_value=True
        ) as push, mock.patch.object(
            web_assemble,
            "_open_or_update_pr",
            return_value="https://github.com/Bingboom/Hello-Docs/pull/3",
        ) as open_pr:
            report = run_web_assemble(
                args, repo_root=Path("/repo"), resolve_path_from_root=lambda raw: Path("/repo") / raw,
                run=fake_run,
            )

        push.assert_called_once()
        open_pr.assert_called_once()
        self.assertTrue(report.pushed)
        self.assertEqual("https://github.com/Bingboom/Hello-Docs/pull/3", report.pr_url)

    def test_push_flag_pushes_but_skips_the_pr_when_nothing_changed(self) -> None:
        args = self._args(push=True)

        def fake_run(cmd, cwd):
            if "clone" in cmd:
                return _proc(returncode=0)
            raise AssertionError(f"unexpected raw command: {cmd}")

        patches = self._patched()
        with patches[0], patches[1], patches[2], patches[3], patches[4], mock.patch.object(
            web_assemble, "_commit_candidate", return_value=None
        ), mock.patch.object(
            web_assemble, "_validate_scope", return_value=(0, ())
        ), mock.patch.object(
            web_assemble, "_push_candidate", return_value=False
        ) as push, mock.patch.object(
            web_assemble, "_open_or_update_pr"
        ) as open_pr:
            report = run_web_assemble(
                args, repo_root=Path("/repo"), resolve_path_from_root=lambda raw: Path("/repo") / raw,
                run=fake_run,
            )

        push.assert_called_once()
        open_pr.assert_not_called()
        self.assertFalse(report.pushed)
        self.assertIsNone(report.pr_url)

    def test_a_scope_violation_aborts_before_any_push(self) -> None:
        args = self._args(push=True)

        def fake_run(cmd, cwd):
            if "clone" in cmd:
                return _proc(returncode=0)
            raise AssertionError(f"unexpected raw command: {cmd}")

        patches = self._patched()
        with patches[0], patches[1], patches[2], patches[3], patches[4], mock.patch.object(
            web_assemble, "_commit_candidate", return_value="a" * 40
        ), mock.patch.object(
            web_assemble,
            "_validate_scope",
            side_effect=RuntimeError("web-assemble PR may change only docs/publish/**; found: build.py"),
        ), mock.patch.object(
            web_assemble, "_push_candidate"
        ) as push, mock.patch.object(
            web_assemble, "_open_or_update_pr"
        ) as open_pr:
            with self.assertRaisesRegex(RuntimeError, "only docs/publish"):
                run_web_assemble(
                    args, repo_root=Path("/repo"), resolve_path_from_root=lambda raw: Path("/repo") / raw,
                    run=fake_run,
                )

        push.assert_not_called()
        open_pr.assert_not_called()

    def test_releases_root_and_title_and_remote_are_resolved_from_args(self) -> None:
        args = self._args(
            releases_root="custom/releases", title="My Library", hello_docs_repo="Acme/Docs"
        )

        def fake_run(cmd, cwd):
            if "clone" in cmd:
                self.assertIn("https://github.com/Acme/Docs.git", cmd)
                return _proc(returncode=0)
            raise AssertionError(f"unexpected raw command: {cmd}")

        patches = self._patched()
        with patches[0], patches[1] as assemble, patches[2], patches[3], patches[4], mock.patch.object(
            web_assemble, "_commit_candidate", return_value=None
        ), mock.patch.object(
            web_assemble, "_validate_scope", return_value=(0, ())
        ):
            report = run_web_assemble(
                args, repo_root=Path("/repo"), resolve_path_from_root=lambda raw: Path("/repo") / raw,
                run=fake_run,
            )

        self.assertEqual(Path("/repo/custom/releases"), report.releases_root)
        self.assertEqual("My Library", report.title)
        self.assertEqual("https://github.com/Acme/Docs.git", report.hello_docs_remote)
        assemble.assert_called_once()
        self.assertEqual("My Library", assemble.call_args.args[2] if len(assemble.call_args.args) > 2 else assemble.call_args.kwargs.get("title"))


def _write_minimal_web_publish_target(
    repo_root: Path,
    *,
    model: str,
    region: str,
    lang: str,
    version: str,
    git_ref: str,
) -> None:
    """Stage the smallest legal ``latest/web`` + ``versions/<v>/web`` pair.

    Mirrors ``PublishBranchAssemblyTests._write_target`` in
    ``tests/test_publish_branch_assembly.py`` at its simplest (legacy,
    no-evidence) shape -- the one already proven to round-trip through
    ``assemble_web_publish_branch`` when ``repo_root`` and the releases tree
    share one root. Deliberately trimmed to just that path: this fixture
    exists to prove the *repo_root wiring*, not to re-cover
    ``load_web_publish_target``'s validation, which already has its own
    dedicated tests.
    """

    lang_root = repo_root / "reports" / "releases" / model / region / lang
    web_root = lang_root / "versions" / version / "web"
    md_root = web_root / "md"
    html_root = web_root / "html"
    metadata_root = lang_root / "latest" / "web"
    for directory in (md_root, html_root, metadata_root):
        directory.mkdir(parents=True, exist_ok=True)

    manual_stem = f"manual_{model.lower().replace('-', '')}_{region.lower()}_{lang}_web_publish_{version}"
    markdown_path = md_root / f"{manual_stem}.md"
    markdown_path.write_text("# Manual\n\nHello world.\n", encoding="utf-8")
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

    relative = lambda path: path.relative_to(repo_root).as_posix()
    payload = {
        "schema_version": "auto-manual-web-publish/v1",
        "model": model,
        "region": region,
        "lang": lang,
        "version": version,
        "git_ref": git_ref,
        "workflow_action": "Web Publish",
        "built_at": "2026-09-16T12:00:00+00:00",
        "md_output_path": relative(markdown_path),
        "html_dir": relative(html_root),
        "html_index": relative(html_root / "index.html"),
        "queue_record_ids": ["rec_web"],
    }
    (metadata_root / "publish_meta.json").write_text(
        json.dumps(payload) + "\n", encoding="utf-8"
    )


class RunWebAssembleRealAssemblyTests(unittest.TestCase):
    """Exercise the real ``assemble_web_publish_branch`` call inside ``run_web_assemble``.

    Every ``RunWebAssembleOrchestrationTests`` case above mocks
    ``_assemble_candidate`` itself, so none of them can catch a bug inside
    it (the same blind spot #1178 found for the RTD verify step). This test
    only fakes the injected ``run`` (git/gh/sphinx) callable and lets the
    real assembler run against a minimal staged fixture -- which is exactly
    the layer that regressed: ``_assemble_candidate`` passed the throwaway
    Hello-Docs clone directory as ``repo_root``, but every staged target's
    ``publish_meta.json`` stores ``md_output_path``/``html_dir`` relative to
    the *real* auto-manual repo root, so resolving them against the clone
    directory always failed ``_path_from_metadata``'s releases-root
    containment check on every real invocation -- reproducing the reported
    ``build.py web-assemble`` failure: "Web Publish metadata path escapes
    releases root".
    """

    def _fake_run(self, cmd: list[str], cwd: Path) -> subprocess.CompletedProcess:
        if "clone" in cmd:
            return _proc(returncode=0)
        if "ls-remote" in cmd:
            return _proc(returncode=2)  # no publish branch yet
        if cmd[:2] == ["git", "add"]:
            return _proc(returncode=0)
        if cmd[:2] == ["git", "diff"] and "--cached" in cmd:
            return _proc(returncode=1)  # something to commit
        if cmd[:2] == ["git", "diff"]:
            return _proc(returncode=0, stdout="docs/publish/publish_manifest.json\0")
        if cmd[:2] == ["git", "commit"]:
            return _proc(returncode=0)
        if cmd[:2] == ["git", "rev-parse"]:
            return _proc(returncode=0, stdout="a" * 40 + "\n")
        if cmd[:2] == ["git", "merge-base"]:
            return _proc(returncode=0)
        if "sphinx" in cmd:
            return _proc(returncode=0)
        raise AssertionError(f"unexpected command: {cmd}")

    def test_real_assembly_resolves_staged_metadata_against_the_real_repo_root(self) -> None:
        with TemporaryDirectory() as repo_tmp:
            repo_root = Path(repo_tmp)
            _write_minimal_web_publish_target(
                repo_root,
                model="JE-1000F",
                region="US",
                lang="en",
                version="2.0",
                git_ref="review/JE-1000F-US",
            )
            args = argparse.Namespace(
                releases_root=None, title=None, hello_docs_repo=None, push=False, dry_run=False
            )

            # Must not raise. Before the fix this always raised RuntimeError
            # ("Web Publish metadata path escapes releases root: ...")
            # because _assemble_candidate resolved the staged target's
            # repo-relative md_output_path/html_dir against the ephemeral
            # Hello-Docs clone directory instead of repo_root.
            report = run_web_assemble(
                args,
                repo_root=repo_root,
                resolve_path_from_root=lambda raw: repo_root / raw,
                run=self._fake_run,
            )

        self.assertTrue(report.committed)
        self.assertEqual(1, len(report.included_targets))
        included = report.included_targets[0]
        self.assertEqual("JE-1000F", included["model"])
        self.assertEqual("US", included["region"])
        self.assertEqual("en", included["lang"])


if __name__ == "__main__":
    unittest.main()
