from __future__ import annotations

from contextlib import redirect_stdout
import csv
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
from types import ModuleType
import unittest
from typing import Any

from tools.rtd.system_tooling import skill_facts
from tools.utils.path_utils import repo_root


def _load_preflight_module(root: Path) -> ModuleType:
    script = root / ".agents" / "skills" / "web-manual-agent-authoring" / "scripts" / "authoring_preflight.py"
    spec = importlib.util.spec_from_file_location("authoring_preflight", script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load authoring_preflight from {script}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_ir(
    root: Path,
    rel_path: str,
    *,
    model: str,
    region: str,
    language: str,
    publication_eligible: bool | None,
) -> None:
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    metadata: dict[str, Any] = {"projection": "whole-document-components/v1"}
    if publication_eligible is not None:
        metadata["publication_eligible"] = publication_eligible
    payload = {
        "schema_version": "manual-ir/v2",
        "model": model,
        "region": region,
        "language": language,
        "source": "prepared-document",
        "metadata": metadata,
        "pages": [{"page_id": "overview", "blocks": []}],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _write_asset_registry(root: Path, rows: list[dict[str, str]]) -> None:
    path = root / "data" / "asset_registry.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "asset_key",
        "override_for",
        "类别",
        "语言维度",
        "状态",
        "待无字化",
        "适用机型",
        "适用区域",
        "导出物路径",
        "语言变体",
        "内容哈希",
        "备注",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


class WebManualAgentAuthoringSkillTests(unittest.TestCase):
    def test_skill_registered_for_codex_and_claude(self) -> None:
        root = repo_root()
        facts = {entry["id"]: entry for entry in skill_facts(root)}
        self.assertIn("web-manual-agent-authoring", facts)
        entry = facts["web-manual-agent-authoring"]
        self.assertEqual(entry["agents"], ["Codex", "Claude"])
        self.assertEqual(entry["unregistered"], [])
        self.assertEqual(entry["problems"], [])
        self.assertTrue(entry["description"])

    def test_preflight_synthetic_fixture_json_and_text(self) -> None:
        preflight = _load_preflight_module(repo_root())
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_root = Path(tmp_dir)
            _write_ir(
                tmp_root,
                "manual_sources/JE-9000X/US/v1/web/en/manual.ir.json",
                model="JE-9000X",
                region="US",
                language="en",
                publication_eligible=True,
            )
            _write_ir(
                tmp_root,
                "manual_sources/JE-9000X/EU/v1/web/fr/manual.ir.json",
                model="JE-9000X",
                region="EU",
                language="fr",
                publication_eligible=False,
            )
            _write_ir(
                tmp_root,
                "manual_sources/OTHER-100/US/v1/web/en/manual.ir.json",
                model="OTHER-100",
                region="US",
                language="en",
                publication_eligible=True,
            )
            _write_asset_registry(
                tmp_root,
                [
                    {
                        "asset_key": "model/je9000x/overview",
                        "类别": "插图",
                        "语言维度": "中立",
                        "状态": "✅成品",
                        "待无字化": "FALSE",
                        "适用机型": "JE-9000X",
                        "适用区域": "US",
                    },
                    {
                        "asset_key": "model/je9000x/panel",
                        "类别": "图文混排",
                        "语言维度": "按语言",
                        "状态": "🔧临时替代",
                        "待无字化": "TRUE",
                        "适用机型": "JE-9000X",
                        "适用区域": "EU",
                    },
                    {
                        "asset_key": "shared/button/power",
                        "类别": "图标",
                        "语言维度": "中立",
                        "状态": "✅成品",
                        "待无字化": "FALSE",
                        "适用机型": "通用",
                        "适用区域": "ALL",
                    },
                    {
                        "asset_key": "shared/symbol/warn",
                        "类别": "标记",
                        "语言维度": "中立",
                        "状态": "✅成品",
                        "待无字化": "FALSE",
                        "适用机型": "SHARED",
                        "适用区域": "ALL",
                    },
                    {
                        "asset_key": "shared/all/logo",
                        "类别": "图标",
                        "语言维度": "中立",
                        "状态": "✅成品",
                        "待无字化": "FALSE",
                        "适用机型": "ALL",
                        "适用区域": "ALL",
                    },
                    {
                        "asset_key": "other/only",
                        "类别": "图标",
                        "语言维度": "中立",
                        "状态": "✅成品",
                        "待无字化": "FALSE",
                        "适用机型": "OTHER-100",
                        "适用区域": "US",
                    },
                ],
            )
            contracts = tmp_root / "docs" / "renderers" / "contracts"
            contracts.mkdir(parents=True, exist_ok=True)
            (contracts / "web_manual.css").write_text("/* shared */\n", encoding="utf-8")
            (contracts / "web_safety_components.css").write_text("/* safety */\n", encoding="utf-8")

            report = preflight.build_authoring_preflight(
                repo_root=tmp_root,
                model="JE-9000X",
                region="US",
                lang="en",
            )
            self.assertEqual(report["schema_version"], "auto-manual-web-authoring-preflight/v1")
            siblings = report["ir_siblings"]
            self.assertEqual(siblings["same_region_count"], 1)
            self.assertEqual(siblings["cross_region_count"], 1)
            self.assertEqual(siblings["same_region_languages"], ["en"])
            self.assertEqual(siblings["cross_region_languages"], ["EU:fr"])
            self.assertTrue(siblings["target_lang_present"])

            assets = report["assets"]
            self.assertEqual(assets["total_matched"], 5)
            self.assertEqual(assets["model_matched"], 2)
            self.assertEqual(assets["shared_matched"], 3)
            self.assertEqual(assets["ready_count"], 4)
            self.assertEqual(assets["pending_textless_count"], 1)
            self.assertEqual(
                assets["reusable_asset_keys"],
                [
                    "model/je9000x/overview",
                    "shared/all/logo",
                    "shared/button/power",
                    "shared/symbol/warn",
                ],
            )

            shared = report["shared_contracts"]
            self.assertEqual(
                shared["web_stylesheets"],
                [
                    "docs/renderers/contracts/web_manual.css",
                    "docs/renderers/contracts/web_safety_components.css",
                ],
            )
            self.assertIn("HB-CALLOUT-STRIP", shared["component_specs"])

            json_buf = io.StringIO()
            with redirect_stdout(json_buf):
                rc_json = preflight.main(
                    [
                        "--repo-root",
                        str(tmp_root),
                        "--model",
                        "JE-9000X",
                        "--region",
                        "US",
                        "--lang",
                        "es",
                        "--json",
                    ]
                )
            self.assertEqual(rc_json, 0)
            cli_payload = json.loads(json_buf.getvalue())
            self.assertFalse(cli_payload["ir_siblings"]["target_lang_present"])

            text_buf = io.StringIO()
            with redirect_stdout(text_buf):
                rc_text = preflight.main(
                    ["--repo-root", str(tmp_root), "--model", "JE-9000X", "--region", "US"]
                )
            self.assertEqual(rc_text, 0)
            self.assertIn("Web Authoring Preflight: JE-9000X (US)", text_buf.getvalue())

    def test_preflight_real_repo_root(self) -> None:
        root = repo_root()
        preflight = _load_preflight_module(root)
        report = preflight.build_authoring_preflight(
            repo_root=root,
            model="JE-1000F",
            region="US",
            lang="en",
        )
        self.assertEqual(report["schema_version"], "auto-manual-web-authoring-preflight/v1")
        self.assertTrue(report["assets"]["registry_present"])
        self.assertGreater(report["assets"]["ready_count"], 0)
        self.assertGreater(report["ir_siblings"]["cross_region_count"], 0)
        self.assertGreater(len(report["shared_contracts"]["web_stylesheets"]), 0)
        self.assertIn("HB-SPECIAL-OVERVIEW", report["shared_contracts"]["component_specs"])
        self.assertIn("HB-TABLE-SPEC", report["shared_contracts"]["component_specs"])


if __name__ == "__main__":
    unittest.main()
