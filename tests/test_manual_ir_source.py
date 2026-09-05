"""Source assembly works without IDML; real RST entrypoints cross that boundary."""
from __future__ import annotations

from contextlib import redirect_stdout
from dataclasses import replace
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import unittest
from unittest.mock import patch

from tools.manual_ir import (
    ManualSource, SourcePage, build_manual_ir, build_manual_ir_from_source,
    read_manual_ir, validate_manual_ir,
)
from tools.manual_ir.hashing import value_sha256
from tools.manual_ir.prepared_rst import load_prepared_rst_source

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "tests/fixtures/idml_bundle"
DATA = ROOT / "tests/fixtures/phase2"
# Captured through the real CLI/exporter on d41ecaf; a refactor must not refresh it.
FIXTURE_CONTENT_SHA = "0cb3f8a47e53d8dbdc1a36cd563c68da10505d57a1d06c4a9623abecfc6500bc"


def _source() -> ManualSource:
    return ManualSource(
        model="TEST", region="JP", language="ja", source="structured-source",
        bundle_root="unmounted/source", bundle_sha256="1" * 64,
        snapshot_sha256=None, layout_params_sha256="2" * 64,
        style_contract_sha256="3" * 64,
        pages=(SourcePage(
            page_id="source-intro", source_ref="manual/intro", source_path="intro.json",
            language="ja", source_sha256="4" * 64,
            blocks=(("body", '{"asset": "prose-is-not-json.png"}'),
                    ("component", {"kind": "extension", "items": [
                        {"img": "b.png"}, {"asset_ref": "a.svg"}, {"img": "b.png"}]}),
                    ("image", "c.png"), ("image", "a.svg")),
            skipped_raw=2,
        ),),
        metadata={"declared_languages": ["ja"], "page_count": 999},
    )


class ManualIRSourceTests(unittest.TestCase):
    def test_core_in_a_fresh_process_cannot_import_idml_or_rst_adapter(self) -> None:
        script = textwrap.dedent('''
            import importlib.abc
            import sys
            class ForbidLegacy(importlib.abc.MetaPathFinder):
                def find_spec(self, fullname, path=None, target=None):
                    if (fullname.startswith(("tools.idml", "idml"))
                            or fullname == "tools.manual_ir.prepared_rst"):
                        raise AssertionError("legacy import: " + fullname)
            sys.meta_path.insert(0, ForbidLegacy())
            from tools.manual_ir import (
                ManualSource, SourcePage, build_manual_ir_from_source,
                validate_manual_ir, write_manual_ir, read_manual_ir,
            )
            from pathlib import Path
            from tempfile import TemporaryDirectory
            page = SourcePage("intro", "source/intro", "intro.json", "ja", "1" * 64,
                              (("body", "Hello"), ("image", "figure.svg")))
            source = ManualSource("TEST", "JP", "ja", "memory", "unmounted",
                                  "2" * 64, None, "3" * 64, "4" * 64, (page,))
            ir = build_manual_ir_from_source(source)
            assert ir.pages[0].blocks[1].asset_refs == ("figure.svg",)
            assert ir.pages[0].language == "ja"
            assert validate_manual_ir(ir) == []
            with TemporaryDirectory() as tmp:
                assert read_manual_ir(write_manual_ir(ir, Path(tmp) / "ir.json")) == ir
            assert not any(name.startswith(("tools.idml", "idml")) for name in sys.modules)
        ''')
        result = subprocess.run([sys.executable, "-c", script], cwd=ROOT,
                                capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_source_payload_identity_hash_and_asset_order_without_file_reads(self) -> None:
        source = _source()
        before = json.dumps(source.metadata)
        with patch.object(Path, "open", side_effect=AssertionError("source file re-read")):
            ir = build_manual_ir_from_source(source)
        self.assertEqual([], validate_manual_ir(ir))
        self.assertEqual(before, json.dumps(source.metadata))
        self.assertEqual("ja", ir.pages[0].language)
        self.assertEqual("intro.json", ir.pages[0].source_path)
        self.assertEqual("4" * 64, ir.pages[0].source_sha256)
        self.assertEqual(("b.png", "a.svg", "c.png"), ir.asset_refs)
        self.assertEqual(1, ir.metadata["page_count"])
        self.assertEqual(4, ir.metadata["block_count"])
        self.assertEqual(2, ir.metadata["skipped_raw"])
        self.assertTrue(validate_manual_ir(ir, require_zero_skipped_raw=True))
        block = ir.pages[0].blocks[0]
        self.assertEqual("source-intro:block-0001", block.block_id)
        self.assertEqual("manual/intro#block-1", block.source_ref)
        self.assertEqual(source.pages[0].blocks[0][1], block.payload)
        self.assertEqual(value_sha256({"kind": "body", "payload": block.payload}),
                         block.content_sha256)
        changed_page = replace(source.pages[0], blocks=(("body", "changed"),))
        changed = build_manual_ir_from_source(replace(source, pages=(changed_page,)))
        self.assertNotEqual(ir.content_sha256, changed.content_sha256)
        self.assertEqual(ir.bundle_sha256, changed.bundle_sha256)
        with self.assertRaisesRegex(ValueError, "manual source has no pages"):
            build_manual_ir_from_source(replace(source, pages=()))

    def test_prepared_adapter_and_public_compatibility_have_exact_fixture_parity(self) -> None:
        args = dict(root=ROOT, bundle_root=BUNDLE, model="JE-1000F", region="US",
                    lang="en", source="review", data_root=DATA)
        prepared = load_prepared_rst_source(**args)
        ir = build_manual_ir_from_source(prepared)
        self.assertEqual(build_manual_ir(**args), ir)
        self.assertEqual(FIXTURE_CONTENT_SHA, ir.content_sha256)
        self.assertEqual("page-0001-00_preface", ir.pages[0].page_id)
        self.assertEqual("page/00_preface.rst", ir.pages[0].source_ref)
        self.assertEqual(10, len(ir.pages))
        self.assertEqual(51, ir.metadata["block_count"])

    def test_real_cli_production_export_and_sidecar_use_source_assembler(self) -> None:
        from tools import export_idml, manual_ir_cli
        from tools.idml import ir_sidecar
        from tools.manual_ir import builder
        from tools.manual_ir import prepared_rst

        args = ["--bundle-root", str(BUNDLE), "--model", "JE-1000F", "--region", "US",
                "--lang", "en", "--data-root", str(DATA)]
        # Production export deliberately retains its old public facade. Its
        # global assembler must be exercised, not just CLI's new direct import.
        for lane, module in (("cli", manual_ir_cli), ("production", builder),
                             ("sidecar", ir_sidecar)):
            with self.subTest(lane=lane), tempfile.TemporaryDirectory() as tmp:
                output = Path(tmp)
                built = []

                def assemble(source):
                    self.assertIsInstance(source, ManualSource)
                    built.append(build_manual_ir_from_source(source))
                    return built[-1]

                with patch.object(module, "build_manual_ir_from_source", side_effect=assemble), \
                     patch.object(prepared_rst, "bundle_page_order",
                                  wraps=prepared_rst.bundle_page_order) as discovery, \
                     redirect_stdout(io.StringIO()):
                    if lane == "cli":
                        path = output / "cli.ir.json"
                        with patch.object(sys, "argv", ["manual_ir_cli.py", *args,
                                                       "--out", str(path)]):
                            self.assertEqual(0, manual_ir_cli.main())
                    elif lane == "production":
                        path = output / "manual.ir.json"
                        with patch.object(sys, "argv", ["export_idml.py", *args,
                                                       "--out", str(output / "manual.idml")]):
                            self.assertEqual(0, export_idml.main())
                        self.assertTrue((output / "manual.idml").is_file())
                    else:
                        path = ir_sidecar.emit_manual_ir_sidecar(
                            root=ROOT, bundle_root=BUNDLE, out_dir=output, model="JE-1000F",
                            region="US", lang="en", data_root=DATA)
                    discovery.assert_called_once_with(BUNDLE)
                self.assertEqual(1, len(built))
                self.assertEqual(built[0], read_manual_ir(path))
                self.assertEqual(FIXTURE_CONTENT_SHA, built[0].content_sha256)

    def test_prepared_only_category_and_legacy_language_policy_remains_local(self) -> None:
        from tools.idml.flow_md import _FlowMarkdownWriter

        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp)
            (bundle / "page").mkdir()
            (bundle / "index.rst").write_text(".. include:: page/intro_en.rst\n")
            (bundle / "page/intro_en.rst").write_text(
                ".. raw:: latex\n\n   \\HBApplyLang{ja}\n\n"
                ".. only:: latex and idml and region_jp and model_test_model "
                "and category_power_bank and lang_jp\n\n   Selected production.\n\n"
                ".. only:: latex and not idml and lang_en\n\n   Selected flow.\n\n"
                ".. only:: lang_ja or html or category_other\n\n   Excluded.\n",
                encoding="utf-8",
            )
            source = load_prepared_rst_source(root=ROOT, bundle_root=bundle,
                model="TEST-MODEL", region="JP", lang="en", source="test",
                category="Power Bank", data_root=DATA)
            ir = build_manual_ir_from_source(source)
            self.assertEqual("jp", ir.pages[0].language)
            self.assertEqual(["Selected production."], [b.payload for b in ir.pages[0].blocks
                                                       if b.kind == "body"])
            flow = _FlowMarkdownWriter(root=ROOT, model="TEST-MODEL", region="JP", lang="en",
                data_root=DATA, bundle_root=bundle, out_dir=bundle, build_command=[])._markdown()
            self.assertIn("Selected flow.", flow)
            self.assertNotIn("Selected production.", flow)
            self.assertNotIn("Excluded.", flow)

    def test_empty_bundle_sidecar_remains_optional_but_public_build_rejects(self) -> None:
        from tools.idml.ir_sidecar import emit_manual_ir_sidecar

        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing"
            self.assertIsNone(emit_manual_ir_sidecar(root=missing, bundle_root=missing,
                out_dir=missing, model="TEST", region="US", lang="en", data_root=missing))
            self.assertFalse(missing.exists())
            with self.assertRaisesRegex(ValueError, "prepared bundle has no included page files"):
                build_manual_ir(root=missing, bundle_root=missing,
                                model="TEST", region="US", lang="en", source="test")


if __name__ == "__main__":
    unittest.main()
