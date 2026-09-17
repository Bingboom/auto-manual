from __future__ import annotations

import unittest
from contextlib import nullcontext
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from tools import build_dispatch


class TestBuildDispatch(unittest.TestCase):
    def test_registered_actions_should_cover_explicit_non_build_actions(self) -> None:
        expected = {
            "validate",
            "doctor",
            "asset-check",
            "asset-intake",
            "new-line",
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
            "release-rebuild-verify",
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

    def test_dispatch_action_should_route_release_rebuild_verifier(self) -> None:
        calls = self._dispatch("release-rebuild-verify")

        self.assertEqual(
            [
                ("ensure", "release-rebuild-verify"),
                ("run-checked", ("release-rebuild", "release-rebuild-verify")),
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

    def test_dispatch_idml_configured_assembly_prepares_rst_and_forwards_plan(
        self,
    ) -> None:
        plan = Path("docs/renderers/contracts/target_assembly/candidate.json")
        with patch.object(
            build_dispatch,
            "resolve_idml_assembly_plan",
            return_value=plan,
        ):
            calls = self._dispatch("idml", _preserve_assembly_patch=True)

        self.assertEqual("rst", calls[1][2]["action_override"])
        command = calls[3][1]
        plan_index = command.index("--assembly-plan")
        self.assertEqual(str(plan), command[plan_index + 1])

    def test_dispatch_idml_forwards_configured_layout_token_layers(self) -> None:
        base = Path("data/layout_params.csv")
        overlay = Path("data/layout_params.idml-compact.csv")
        with patch.object(
            build_dispatch,
            "resolve_layout_params_csv",
            return_value=base,
        ), patch.object(
            build_dispatch,
            "resolve_idml_layout_param_overlays",
            return_value=(overlay,),
        ):
            calls = self._dispatch("idml", _preserve_layout_patch=True)

        command = calls[3][1]
        base_index = command.index("--layout-params-csv")
        overlay_index = command.index("--layout-params-overlay")
        self.assertEqual(str(base), command[base_index + 1])
        self.assertEqual(str(overlay), command[overlay_index + 1])

    def test_idml_assembly_plan_resolves_one_target_from_shared_config(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = root / "config.yaml"
            config.write_text(
                "build:\n"
                "  default_model: JE-1000F\n"
                "  default_region: KR\n"
                "paths:\n"
                "  idml_assembly_plans:\n"
                "    JE-3000C_KR: plans/je3000c.json\n",
                encoding="utf-8",
            )

            self.assertEqual(
                root / "plans" / "je3000c.json",
                build_dispatch.resolve_idml_assembly_plan(
                    config,
                    repo_root=root,
                    model="JE-3000C",
                    region="KR",
                ),
            )
            self.assertIsNone(
                build_dispatch.resolve_idml_assembly_plan(
                    config,
                    repo_root=root,
                    model="JE-2000E",
                    region="KR",
                )
            )

    def test_idml_assembly_plan_uses_shared_config_defaults(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = root / "config.yaml"
            config.write_text(
                "build:\n"
                "  default_model: JE-3000C\n"
                "  default_region: KR\n"
                "paths:\n"
                "  idml_assembly_plans:\n"
                "    je-3000c_kr: plans/je3000c.json\n",
                encoding="utf-8",
            )

            self.assertEqual(
                root / "plans" / "je3000c.json",
                build_dispatch.resolve_idml_assembly_plan(
                    config,
                    repo_root=root,
                ),
            )

    def test_idml_assembly_plan_rejects_ambiguous_config_shapes(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = root / "config.yaml"
            config.write_text(
                "paths:\n"
                "  idml_assembly_plan: plans/default.json\n"
                "  idml_assembly_plans:\n"
                "    JE-3000C_KR: plans/je3000c.json\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "mutually exclusive"):
                build_dispatch.resolve_idml_assembly_plan(
                    config,
                    repo_root=root,
                    model="JE-3000C",
                    region="KR",
                )

    def test_idml_layout_param_overlays_resolve_relative_to_repo(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = root / "config.yaml"
            config.write_text(
                "paths:\n"
                "  idml_layout_params_overlays:\n"
                "    - data/compact.csv\n",
                encoding="utf-8",
            )

            resolved = build_dispatch.resolve_idml_layout_param_overlays(
                config,
                repo_root=root,
            )

        self.assertEqual((root / "data" / "compact.csv",), resolved)

    def test_idml_layout_param_overlays_select_only_the_requested_target(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = root / "config.yaml"
            config.write_text(
                "build:\n"
                "  default_model: JE-1000F\n"
                "  default_region: KR\n"
                "paths:\n"
                "  idml_layout_params_overlays_by_target:\n"
                "    JE-3000C_KR:\n"
                "      - data/je3000c-kr.csv\n",
                encoding="utf-8",
            )

            selected = build_dispatch.resolve_idml_layout_param_overlays(
                config,
                repo_root=root,
                model="JE-3000C",
                region="KR",
            )
            unselected = build_dispatch.resolve_idml_layout_param_overlays(
                config,
                repo_root=root,
                model="JE-1000F",
                region="KR",
            )

        self.assertEqual((root / "data" / "je3000c-kr.csv",), selected)
        self.assertEqual((), unselected)

    def test_dispatch_idml_uses_single_configured_language(self) -> None:
        with patch.object(
            build_dispatch,
            "_effective_idml_language",
            return_value="ja",
        ):
            calls = self._dispatch("idml")

        export_command = calls[3][1]
        language_index = export_command.index("--lang")
        self.assertEqual("ja", export_command[language_index + 1])

    def test_effective_idml_language_preserves_multilingual_default(self) -> None:
        with TemporaryDirectory() as tmp:
            config = Path(tmp) / "config.yaml"
            config.write_text(
                "build:\n  languages: [en, fr, es]\n",
                encoding="utf-8",
            )

            language = build_dispatch._effective_idml_language(
                SimpleNamespace(lang=None),
                config_path=config,
            )

        self.assertIsNone(language)

    def test_effective_idml_language_prefers_explicit_selection(self) -> None:
        language = build_dispatch._effective_idml_language(
            SimpleNamespace(lang="fr"),
            config_path=Path("missing-config.yaml"),
        )

        self.assertEqual("fr", language)

    def test_effective_idml_language_reads_single_language_family(self) -> None:
        with TemporaryDirectory() as tmp:
            config = Path(tmp) / "config.yaml"
            config.write_text(
                "build:\n  languages: [ja]\n",
                encoding="utf-8",
            )

            language = build_dispatch._effective_idml_language(
                SimpleNamespace(lang=None),
                config_path=config,
            )

        self.assertEqual("ja", language)

    def test_dispatch_idml_approved_target_skips_unrelated_latex_pdf(self) -> None:
        with patch.object(
            build_dispatch,
            "_target_has_approved_reference_plan",
            return_value=True,
        ):
            calls = self._dispatch("idml")

        self.assertEqual("rst", calls[1][2]["action_override"])
        self.assertEqual("review-asis", calls[1][2]["source_override"])

    def test_dispatch_idml_approved_target_preserves_explicit_runtime(self) -> None:
        with patch.object(
            build_dispatch,
            "_target_has_approved_reference_plan",
            return_value=True,
        ):
            calls = self._dispatch("idml", source="runtime")

        self.assertEqual("runtime", calls[1][2]["source_override"])

    def test_approved_reference_target_requires_exact_model_region_languages(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = root / "configs" / "config.us.yaml"
            config.parent.mkdir(parents=True)
            config.write_text(
                "build:\n"
                "  default_model: JE-1000F\n"
                "  default_region: US\n"
                "  languages: [en, fr, es]\n",
                encoding="utf-8",
            )
            registry = (
                root
                / "docs"
                / "renderers"
                / "contracts"
                / "reference_layout_registry.json"
            )
            registry.parent.mkdir(parents=True)
            registry.write_text(
                '{"plans":[{"target":{"model":"JE-1000F","region":"US",'
                '"languages":["en","fr","es"]}}]}\n',
                encoding="utf-8",
            )
            args = SimpleNamespace(model="JE-1000F", region="US")

            self.assertTrue(
                build_dispatch._target_has_approved_reference_plan(
                    args,
                    config_path=config,
                    repo_root=root,
                )
            )
            args.region = "EU"
            self.assertFalse(
                build_dispatch._target_has_approved_reference_plan(
                    args,
                    config_path=config,
                    repo_root=root,
                )
            )

    def test_approved_reference_target_uses_model_language_scope(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = root / "configs" / "config.eu.yaml"
            config.parent.mkdir(parents=True)
            config.write_text(
                "build:\n"
                "  default_model: JE-1000F\n"
                "  default_region: EU\n"
                "  languages: [en, fr, es, de, it, uk]\n",
                encoding="utf-8",
            )
            data_dir = root / "data"
            data_dir.mkdir()
            (data_dir / "model_languages.csv").write_text(
                "Document_key,languages\n"
                "JE-1000F_EU,en;fr;es;de;it\n",
                encoding="utf-8",
            )
            registry = (
                root
                / "docs"
                / "renderers"
                / "contracts"
                / "reference_layout_registry.json"
            )
            registry.parent.mkdir(parents=True)
            registry.write_text(
                '{"plans":[{"target":{"model":"JE-1000F","region":"EU",'
                '"languages":["en","fr","es","de","it"]}}]}\n',
                encoding="utf-8",
            )

            self.assertTrue(
                build_dispatch._target_has_approved_reference_plan(
                    SimpleNamespace(model="JE-1000F", region="EU"),
                    config_path=config,
                    repo_root=root,
                )
            )

    def test_dispatch_idml_preserves_review_asis_source(self) -> None:
        calls = self._dispatch("idml", source="review-asis")

        self.assertEqual("review-asis", calls[1][2]["source_override"])

    def _dispatch(self, action: str, **overrides) -> list[tuple]:
        preserve_assembly_patch = overrides.pop("_preserve_assembly_patch", False)
        preserve_layout_patch = overrides.pop("_preserve_layout_patch", False)
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

        assembly_patch = (
            patch.object(build_dispatch, "resolve_idml_assembly_plan", return_value=None)
            if not preserve_assembly_patch
            else nullcontext()
        )
        layout_base_patch = (
            patch.object(
                build_dispatch,
                "resolve_layout_params_csv",
                return_value=Path("data/layout_params.csv"),
            )
            if not preserve_layout_patch
            else nullcontext()
        )
        layout_overlay_patch = (
            patch.object(
                build_dispatch,
                "resolve_idml_layout_param_overlays",
                return_value=(),
            )
            if not preserve_layout_patch
            else nullcontext()
        )
        with assembly_patch, layout_base_patch, layout_overlay_patch:
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
                release_rebuild_command=lambda parsed_args: ["release-rebuild", parsed_args.action],
                clean_build_artifacts=lambda config_path: calls.append(("clean", config_path)),
                maybe_sync_review_before_build=record_maybe_sync,
                run_asset_command=record_arg("asset-command"),
                run_new_line=record_arg("new-line"),
            )
        return calls


if __name__ == "__main__":
    unittest.main()
