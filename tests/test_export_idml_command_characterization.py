"""Freeze exporter command dispatch before extracting command handlers.

The renderer's existing IDML zip-part goldens remain the rendering oracle.
These cases freeze CLI text, exits and boundary ordering without real outputs.
Run --update only on the original implementation, before production edits.
"""
from __future__ import annotations

import io
import json
import subprocess
import sys
import unittest
from contextlib import ExitStack, redirect_stderr, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from tools import export_idml as exporter
from tools.idml import font_assets

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "tests/fixtures/export_idml_cli_golden.json"
BASE = ["--model", "TEST-MODEL", "--region", "TEST-REGION", "--lang", "en",
        "--bundle-root", str(ROOT / "fixture-bundle"),
        "--out", str(ROOT / "fixture-output/production.idml")]


def normalize(value):
    if isinstance(value, Path):
        return str(value).replace(str(ROOT), "<ROOT>")
    if isinstance(value, str):
        return value.replace(str(ROOT), "<ROOT>")
    if isinstance(value, (list, tuple)):
        return [normalize(item) for item in value]
    if isinstance(value, dict):
        return {key: normalize(item) for key, item in value.items()}
    return value


def capture(argv, *, check_exit=0, preparation_error=False, issues=(),
            coverage_warning=False, page_count_error=False, boundary_error=None,
            symbol_overflow=False):
    events = []
    out = ROOT / "fixture-output/production.idml"
    flow = SimpleNamespace(markdown=out.parent / "flow/manual.flow.md",
                           idml=out.parent / "flow/manual.flow.idml")
    manual_ir = object()
    writer = Mock(registered_components=False, stories=[], spreads=[])
    renderer = Mock(toc_planned=False, back_cover_added=False)
    renderer.render.return_value = None
    renderer.prepare_page_blocks.side_effect = lambda page, blocks: blocks
    story_emitter = Mock()
    overflow = Mock()
    overflow.has_rows.return_value = True
    writer.add_safety_symbols_page.return_value = ("symbol-story", overflow)
    symbol_data = SimpleNamespace(signals=[], icons=[], title="Symbols",
                                  signal_headers=(), icon_headers=())
    pages = [SimpleNamespace(path=ROOT / "fixture-bundle" / name,
                             blocks=[("p", "Frozen prose")], twocol=True, skipped_raw=0)
             for name in ("safety_en.rst", "symbols_en.rst")] if symbol_overflow else []

    def record(name, result=None, *, arguments=False):
        def call(*args, **kwargs):
            event = {"boundary": name}
            if arguments:
                event["args"] = normalize(args)
                event["kwargs"] = normalize(kwargs)
            events.append(event)
            if name == boundary_error:
                raise ValueError("frozen boundary failure")
            return result
        return call

    def prepare(*args, **kwargs):
        events.append({"boundary": "prepare-ir", "kwargs": normalize(kwargs)})
        if preparation_error:
            raise ValueError("frozen preparation failure")
        return manual_ir

    def run_check(value):
        events.append({"boundary": "check-only", "path": normalize(value)})
        print("[idml-check] OK" if not check_exit else "[idml-check] FAIL: frozen issue")
        return check_exit

    writer.write.side_effect = record("write-production", arguments=True)
    story_emitter.report_spans.side_effect = record("report-spans")
    projection = exporter._ir_projection
    patches = [
        (exporter._check, "run_check_cli", run_check),
        (exporter, "load_layout_params", record("load-layout", {}, arguments=True)),
        (projection, "build_same_source_ir", prepare),
        (projection, "resolve_component_target", record("component-target")),
        (projection, "build_reference_page_plan", record("reference-plan")),
        (projection, "project_pages", record("project-pages", pages)),
        (projection, "spec_page_data", lambda *a, **k: None),
        (projection, "governed_lcd_page_data", lambda *a, **k: None),
        (projection, "trouble_page_data", lambda *a, **k: None),
        (projection, "symbol_page_data", lambda *a, **k: symbol_data if symbol_overflow else None),
        (projection, "toc_with_front_matter", record("toc-source", (None, None))),
        (projection, "report_reference_page_count_issues", record("page-count", page_count_error)),
        (projection, "emit_reference_page_plan", record("emit-plan")),
        (exporter, "_new_production_writer", lambda *a, **k: writer),
        (exporter._reference_story_flow, "ReferenceStoryEmitter", lambda *a, **k: story_emitter),
        (exporter._target_assembly_render, "TargetAssemblyRenderer", lambda *a, **k: renderer),
        (exporter._target_assembly_render, "needs_legacy_back_cover_fallback", lambda *a: False),
        (exporter._prose_flow, "ProseFlowBuffer", lambda **k: Mock()),
        (exporter._prose_flow, "idml_page_estimator", lambda *a: Mock()),
        (exporter, "split_safety_first_page", lambda blocks: ([], [("p", "Pending symbols")])),
        (exporter._folio, "apply", record("folio")),
        (exporter._page_roles, "assembly_coverage_warning",
         lambda *a: "[export-idml] WARNING: frozen coverage" if coverage_warning else None),
        (exporter._ir_sidecar, "emit_manual_ir_sidecar", record("flow-ir", arguments=True)),
        (exporter._ir_sidecar, "write_manual_ir_sidecar", record("production-ir")),
        (exporter._flow_idml, "write_flow_outputs", record("flow", flow, arguments=True)),
        (exporter._design_handoff, "write_handoff_package", record("handoff", SimpleNamespace(root=out.parent))),
        (exporter._template_merge, "bake_beside", record("template")),
        (exporter._export_cli, "dump_prepared_bundle_debug", record("debug", arguments=True)),
        (font_assets, "provision_document_fonts", record("fonts", arguments=True)),
        (exporter, "check_idml", record("self-check", list(issues), arguments=True)),
    ]
    stdout, stderr = io.StringIO(), io.StringIO()
    with ExitStack() as stack:
        for owner, name, replacement in patches:
            stack.enter_context(patch.object(owner, name, replacement))
        stack.enter_context(patch.object(sys, "argv", ["export_idml.py", *argv]))
        stack.enter_context(redirect_stdout(stdout))
        stack.enter_context(redirect_stderr(stderr))
        try:
            exit_code = exporter.main()
            exception = None
        except SystemExit as exc:
            exit_code, exception = exc.code, None
        except ValueError as exc:
            exit_code, exception = None, f"ValueError: {exc}"
    return {"exit": exit_code, "exception": exception,
            "stdout": normalize(stdout.getvalue()), "stderr": normalize(stderr.getvalue()),
            "events": events}


def snapshots():
    cases = {
        "help": (["--help"], {}),
        "missing-model": ([], {}),
        "invalid-mode": (["--mode", "pages"], {}),
        "check-success-without-model": (["--check", "sample.idml"], {}),
        "check-failure-before-export": ([*BASE, "--mode", "both", "--check", "bad.idml"], {"check_exit": 1}),
        "production-default": (BASE, {}),
        "production-explicit": ([*BASE, "--mode", "production"], {}),
        "flow": ([*BASE, "--mode", "flow"], {}),
        "flow-alias": ([*BASE, "--idml-mode", "flow"], {}),
        "both": ([*BASE, "--mode", "both"], {}),
        "both-template-self-check-issues": ([*BASE, "--mode", "both", "--template", "template.idml"], {"issues": ["first issue", "second issue"]}),
        "production-template": ([*BASE, "--template", "template.idml"], {}),
        "preparation-error": (BASE, {"preparation_error": True}),
        "coverage-warning": (BASE, {"coverage_warning": True}),
        "page-count-error": ([*BASE, "--mode", "both"], {"page_count_error": True}),
        "unconsumed-symbol-overflow": (BASE, {"symbol_overflow": True}),
        "flow-error-propagates": ([*BASE, "--mode", "flow"], {"boundary_error": "flow"}),
        "both-flow-error-after-production": ([*BASE, "--mode", "both"], {"boundary_error": "flow"}),
        "template-error-propagates": ([*BASE, "--template", "template.idml"], {"boundary_error": "template"}),
    }
    return {name: capture(argv, **options) for name, (argv, options) in cases.items()}


class ExportCommandCharacterizationTests(unittest.TestCase):
    def test_frozen_command_contracts(self):
        expected = json.loads(GOLDEN.read_text(encoding="utf-8"))
        actual = snapshots()
        self.assertEqual(expected.keys(), actual.keys())
        for name in expected:
            with self.subTest(case=name):
                self.assertEqual(expected[name], actual[name])

    def test_script_and_module_help_match_frozen_text(self):
        expected = json.loads(GOLDEN.read_text(encoding="utf-8"))["help"]
        for invocation in ([str(ROOT / "tools/export_idml.py")], ["-m", "tools.export_idml"]):
            with self.subTest(invocation=invocation):
                result = subprocess.run([sys.executable, *invocation, "--help"],
                                        cwd=ROOT, capture_output=True, text=True, check=False)
                self.assertEqual(expected["exit"], result.returncode)
                self.assertEqual(expected["stdout"], normalize(result.stdout))
                self.assertEqual(expected["stderr"], normalize(result.stderr))


if __name__ == "__main__":
    if sys.argv[1:] == ["--update"]:
        GOLDEN.write_text(json.dumps(snapshots(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    else:
        unittest.main()
