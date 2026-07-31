from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from tools.new_line_scaffold import _auto_check, build_plan, materialize_scaffold


ROOT = Path(__file__).resolve().parents[1]


class TestNewLineScaffold(unittest.TestCase):
    def test_kr_replay_has_no_unexpected_scaffold_diff(self) -> None:
        plan = build_plan(ROOT / "configs/config.kr.yaml", root=ROOT)

        self.assertEqual("KR", plan.target["region"])
        self.assertEqual(["ko"], plan.target["languages"])
        self.assertEqual([], list(plan.whitelist_diff))
        self.assertEqual("passed", plan.validation["status"])
        self.assertEqual("blocked", plan.write_policy["source_table_write"])

    def test_au_replay_has_no_unexpected_scaffold_diff(self) -> None:
        plan = build_plan(ROOT / "configs/config.au-en.yaml", root=ROOT)

        self.assertEqual("AU", plan.target["region"])
        self.assertEqual(["en"], plan.target["languages"])
        self.assertEqual([], list(plan.whitelist_diff))
        self.assertEqual("passed", plan.validation["status"])

    def test_replay_plan_includes_source_table_boundaries(self) -> None:
        plan = build_plan(ROOT / "configs/config.kr.yaml", root=ROOT)

        self.assertIn("source-table", {reference.role for reference in plan.references})
        self.assertIn(
            {"role": "source-table", "path": "data/phase2", "operation": "F6-gated"},
            plan.write_surface,
        )

    def test_write_materializes_only_explicit_config_and_manifest(self) -> None:
        plan = build_plan(ROOT / "configs/config.kr.yaml", root=ROOT)

        with TemporaryDirectory(dir=ROOT) as tmp:
            output_root = Path(tmp)
            result = materialize_scaffold(
                plan,
                source_config=ROOT / "configs/config.kr.yaml",
                root=ROOT,
                output_config=output_root / "config.yaml",
                output_manifest=output_root / "manifest.yaml",
            )

            self.assertTrue(result.manifest.endswith("/manifest.yaml"))
            self.assertTrue((ROOT / result.config).is_file())
            self.assertTrue((ROOT / result.manifest).is_file())
            import yaml

            generated = yaml.safe_load((ROOT / result.config).read_text(encoding="utf-8"))
            self.assertEqual("JE-1000F", generated["build"]["default_model"])
            self.assertEqual("KR", generated["build"]["default_region"])
            self.assertEqual([{"model": "JE-1000F", "region": "KR"}], generated["build"]["targets"])
            self.assertEqual(result.manifest, generated["paths"]["page_manifest"])

    def test_write_rejects_phase2_output_surface(self) -> None:
        plan = build_plan(ROOT / "configs/config.kr.yaml", root=ROOT)

        with self.assertRaisesRegex(RuntimeError, "controlled scaffold surface"):
            materialize_scaffold(
                plan,
                source_config=ROOT / "configs/config.kr.yaml",
                root=ROOT,
                output_config=ROOT / "data/phase2/generated.yaml",
                output_manifest=ROOT / "docs/manifests/generated.yaml",
            )

    def test_auto_check_uses_runtime_source_without_review_side_effects(self) -> None:
        completed = SimpleNamespace(returncode=0, stdout="", stderr="")
        with patch("tools.new_line_scaffold.subprocess.run", return_value=completed) as runner:
            result = _auto_check(
                root=ROOT,
                config=ROOT / "configs/config.kr.yaml",
                model="JE-1000F",
                region="KR",
                data_root=ROOT / "tests/fixtures/phase2",
                staging_root=ROOT / ".tmp-stage3-6-test-staging",
            )

        command = runner.call_args.args[0]
        source_index = command.index("--source")
        self.assertEqual("runtime", command[source_index + 1])
        self.assertEqual("passed", result["status"])


if __name__ == "__main__":
    unittest.main()
