from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace

from tools import build_dispatch


class TestBuildDispatch(unittest.TestCase):
    def test_registered_actions_should_cover_explicit_non_build_actions(self) -> None:
        expected = {
            "validate",
            "doctor",
            "asset-check",
            "asset-intake",
            "review",
            "check",
            "sync-review",
            "sync-data",
            "spec-master-rebuild",
            "translation-memory",
            "message-control-dry-run",
            "manual-index-query",
            "queue-query",
            "queue-resolve-action",
            "queue-execute",
            "process-review-start-queue",
            "process-build-queue",
            "listen-build-queue",
            "listen-message-control",
            "publish",
            "diff-report",
            "release-manifest",
            "clean",
            "idml",
        }

        self.assertEqual(expected, set(build_dispatch.registered_actions()))
        self.assertEqual(len(expected), len(build_dispatch.registered_actions()))

    def test_dispatch_action_should_route_validate_with_target_context(self) -> None:
        calls = self._dispatch("validate")

        self.assertEqual(("ensure", "validate"), calls[0])
        self.assertEqual("validate", calls[1][0])
        self.assertEqual((Path("config.us.yaml"),), calls[1][1])
        self.assertEqual(
            {
                "data_root": "data/phase2",
                "model": "JE-1000F",
                "region": "US",
            },
            calls[1][2],
        )

    def test_dispatch_action_should_run_review_prepare_then_bundle(self) -> None:
        calls = self._dispatch("review")

        self.assertEqual(
            [
                ("ensure", "review"),
                (
                    "build-docs",
                    "review",
                    {
                        "action_override": "rst",
                        "source_override": "runtime",
                    },
                ),
                ("run-checked", ("build-docs",)),
                ("review-bundle", "review"),
                ("run-checked", ("review-bundle",)),
            ],
            calls,
        )

    def test_dispatch_asset_actions_should_share_the_asset_facade(self) -> None:
        for action in ("asset-check", "asset-intake"):
            with self.subTest(action=action):
                self.assertEqual(
                    [("ensure", action), ("asset-command", action)],
                    self._dispatch(action),
                )

    def test_dispatch_action_should_fallback_to_build_action(self) -> None:
        calls = self._dispatch("word")

        self.assertEqual(
            [
                ("ensure", "word"),
                ("maybe-sync-review", "word", {}),
                ("build-docs", "word", {}),
                ("run-checked", ("build-docs",)),
            ],
            calls,
        )

    def test_dispatch_action_fast_forces_runtime_source_for_review_presync(self) -> None:
        # `fast` builds runtime + no-clean, so the review pre-sync must be told the
        # effective source is runtime (else it runs a --clean RST rebuild + a
        # docs/_review params rewrite as a surprise side effect of a quick build).
        calls = self._dispatch("fast")

        self.assertEqual(("maybe-sync-review", "fast", {"source_override": "runtime"}), calls[1])

    def test_dispatch_idml_should_prepare_latex_reference_before_export(self) -> None:
        calls = self._dispatch("idml")

        self.assertEqual(("ensure", "idml"), calls[0])
        self.assertEqual(
            (
                "build-docs",
                "idml",
                {
                    "action_override": "pdf",
                    "source_override": "runtime",
                },
            ),
            calls[1],
        )
        self.assertEqual(("run-checked", ("build-docs",)), calls[2])
        self.assertEqual(calls[3][0], "run-checked")
        export_script = Path(calls[3][1][1])
        self.assertEqual("tools", export_script.parent.name)
        self.assertEqual("export_idml.py", export_script.name)
        self.assertIn("--data-root", calls[3][1])
        self.assertIn("--mode", calls[3][1])
        self.assertIn("production", calls[3][1])

    def test_dispatch_idml_should_pass_requested_mode_to_exporter(self) -> None:
        calls = self._dispatch("idml", idml_mode="flow")

        self.assertEqual("rst", calls[1][2]["action_override"])
        self.assertIn("--mode", calls[3][1])
        mode_index = calls[3][1].index("--mode")
        self.assertEqual("flow", calls[3][1][mode_index + 1])

    def test_dispatch_idml_preserves_review_asis_source(self) -> None:
        calls = self._dispatch("idml", source="review-asis")

        self.assertEqual("review-asis", calls[1][2]["source_override"])

    def _dispatch(self, action: str, **overrides) -> list[tuple]:
        values = {
            "action": action,
            "data_root": "data/phase2",
            "model": "JE-1000F",
            "region": "US",
            "idml_mode": "production",
        }
        values.update(overrides)
        args = SimpleNamespace(**values)
        calls: list[tuple] = []

        def record_call(name: str):
            return lambda *argv, **kwargs: calls.append((name, argv, kwargs))

        def record_arg(name: str):
            return lambda parsed_args: calls.append((name, parsed_args.action))

        def record_command(name: str):
            def command(parsed_args, **kwargs):
                calls.append((name, parsed_args.action, kwargs))
                return [name]

            return command

        def record_maybe_sync(parsed_args, **kwargs):
            calls.append(("maybe-sync-review", parsed_args.action, kwargs))

        def review_bundle_command(parsed_args):
            calls.append(("review-bundle", parsed_args.action))
            return ["review-bundle"]

        build_dispatch.dispatch_action(
            args,
            config_path=Path("config.us.yaml"),
            ensure_supported_staging_action=record_arg("ensure"),
            run_validate=record_call("validate"),
            run_doctor=record_arg("doctor"),
            run_checked=lambda cmd: calls.append(("run-checked", tuple(cmd))),
            build_docs_command=record_command("build-docs"),
            review_bundle_command=review_bundle_command,
            run_check=record_arg("check"),
            sync_review_command=lambda parsed_args: ["sync-review", parsed_args.action],
            sync_data_command=lambda parsed_args: ["sync-data", parsed_args.action],
            spec_master_rebuild_command=lambda parsed_args: ["spec-master-rebuild", parsed_args.action],
            run_translation_memory=record_arg("translation-memory"),
            run_message_control_dry_run=record_arg("message-control-dry-run"),
            run_manual_index_query=record_arg("manual-index-query"),
            run_queue_query=record_arg("queue-query"),
            run_queue_resolve_action=record_arg("queue-resolve-action"),
            run_queue_execute=record_arg("queue-execute"),
            process_review_start_queue_command=lambda parsed_args: ["process-review-start-queue", parsed_args.action],
            process_build_queue_command=lambda parsed_args: ["process-build-queue", parsed_args.action],
            listen_build_queue_command=lambda parsed_args: ["listen-build-queue", parsed_args.action],
            listen_message_control_command=lambda parsed_args: ["listen-message-control", parsed_args.action],
            run_publish=record_arg("publish"),
            run_diff_report=record_arg("diff-report"),
            release_manifest_command=lambda parsed_args: ["release-manifest", parsed_args.action],
            clean_build_artifacts=lambda config_path: calls.append(("clean", config_path)),
            maybe_sync_review_before_build=record_maybe_sync,
            run_asset_command=record_arg("asset-command"),
        )
        return calls


if __name__ == "__main__":
    unittest.main()
