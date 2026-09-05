"""Untrusted v1 files must cross the same boundary in every real consumer."""
from __future__ import annotations

from argparse import Namespace
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools.idml_pdf_parity import build_report
from tools.manual_ir import (
    ManualIRValidationError, build_manual_ir, read_manual_ir,
    validate_manual_ir, write_manual_ir,
)
from tools.manual_ir.hashing import value_sha256

ROOT = Path(__file__).resolve().parents[1]


def _set(raw, path, value):
    for key in path[:-1]:
        raw = raw[key]
    raw[path[-1]] = value


class ManualIRReadContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.ir = build_manual_ir(
            root=ROOT, bundle_root=ROOT / "tests/fixtures/idml_bundle",
            model="JE-1000F", region="US", lang="en", source="review",
            data_root=ROOT / "tests/fixtures/phase2",
        )
        cls.raw = json.loads(json.dumps(cls.ir.to_dict()))

    def _read(self, raw):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "input.ir.json"
            path.write_text(json.dumps(raw), encoding="utf-8")
            return read_manual_ir(path)

    def test_round_trip_is_byte_identical_and_does_not_mutate_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = write_manual_ir(self.ir, Path(tmp) / "input.ir.json")
            before = path.read_bytes()
            loaded = read_manual_ir(path)
            output = write_manual_ir(loaded, Path(tmp) / "output.ir.json")
            self.assertEqual(before, path.read_bytes())
            self.assertEqual(before, output.read_bytes())
            self.assertEqual(self.ir, loaded)
            self.assertEqual([], validate_manual_ir(loaded))

    def test_malformed_envelopes_never_coerce_or_silently_default(self) -> None:
        cases = [
            (("model",), None, "model"),
            (("region",), 12, "region"),
            (("language",), False, "language"),
            (("bundle_root",), [], "bundle_root"),
            (("source",), " ", "source"),
            (("pages",), None, "pages"),
            (("pages",), {}, "pages"),
            (("pages",), "pages", "pages"),
            (("pages", 0), False, "pages[0]"),
            (("pages", 0, "page_id"), "", "pages[0].page_id"),
            (("pages", 0, "source_ref"), 1, "pages[0].source_ref"),
            (("pages", 0, "source_path"), None, "pages[0].source_path"),
            (("pages", 0, "language"), {}, "pages[0].language"),
            (("pages", 0, "skipped_raw"), "0", "pages[0].skipped_raw"),
            (("pages", 0, "skipped_raw"), -1, "pages[0].skipped_raw"),
            (("pages", 0, "skipped_raw"), True, "pages[0].skipped_raw"),
            (("pages", 0, "blocks"), None, "pages[0].blocks"),
            (("pages", 0, "blocks"), {}, "pages[0].blocks"),
            (("pages", 0, "blocks", 0), [], "pages[0].blocks[0]"),
            (("pages", 0, "blocks", 0, "block_id"), 0, "block_id"),
            (("pages", 0, "blocks", 0, "kind"), {}, "kind"),
            (("pages", 0, "blocks", 0, "payload"), float("nan"), "payload"),
            (("pages", 0, "blocks", 0, "payload"), {"x": float("inf")}, "payload"),
            (("pages", 0, "blocks", 0, "payload"), "\ud800", "payload"),
            (("pages", 0, "blocks", 0, "asset_refs"), "a.png", "asset_refs"),
            (("asset_refs",), [None], "asset_refs[0]"),
            (("asset_refs",), None, "asset_refs"),
            (("metadata",), [], "metadata"),
            (("metadata",), None, "metadata"),
            (("metadata", "declared_languages"), "en", "metadata.declared_languages"),
            (("metadata", "page_count"), True, "metadata.page_count"),
        ]
        for path, value, location in cases:
            with self.subTest(path=path, value=value):
                raw = deepcopy(self.raw)
                _set(raw, path, value)
                with self.assertRaises(ManualIRValidationError) as caught:
                    self._read(raw)
                self.assertIn(location, str(caught.exception))
                self.assertIn("input.ir.json", str(caught.exception))
        for value in (None, [], "text", 12):
            with self.subTest(root=value), self.assertRaisesRegex(ManualIRValidationError, "JSON object"):
                self._read(value)

    def test_required_fields_cannot_disappear(self) -> None:
        for parent, field in (((), "schema_version"), ((), "pages"),
                              (("pages", 0), "blocks"),
                              (("pages", 0, "blocks", 0), "payload")):
            raw = deepcopy(self.raw)
            target = raw
            for key in parent:
                target = target[key]
            del target[field]
            with self.subTest(field=field), self.assertRaisesRegex(ManualIRValidationError, field):
                self._read(raw)

    def test_every_external_digest_is_validated_without_rereading_external_files(self) -> None:
        for path in (("bundle_sha256",), ("snapshot_sha256",),
                     ("layout_params_sha256",), ("style_contract_sha256",),
                     ("content_sha256",), ("pages", 0, "source_sha256"),
                     ("pages", 0, "blocks", 0, "content_sha256")):
            for value in (123, "g" * 64, "A" * 64, "f" * 63):
                with self.subTest(path=path, value=value):
                    raw = deepcopy(self.raw)
                    _set(raw, path, value)
                    with self.assertRaisesRegex(ManualIRValidationError, path[-1]):
                        self._read(raw)
        raw = deepcopy(self.raw)
        raw["bundle_root"] = "/not-mounted/source-bundle"
        self.assertEqual(raw["bundle_root"], self._read(raw).bundle_root)

    def test_semantic_rejection_matches_in_memory_validation(self) -> None:
        page = self.ir.pages[0]
        block = page.blocks[0]
        cases = [
            (replace(self.ir, schema_version="manual-ir/v2"), "schema_version"),
            (replace(self.ir, pages=()), "has no pages"),
            (replace(self.ir, pages=(page, *self.ir.pages)), "duplicate page_id"),
            (replace(self.ir, pages=(replace(page, page_id="unique"), *self.ir.pages)),
             "duplicate page source_ref"),
            (replace(self.ir, pages=(replace(page, blocks=(block, *page.blocks)), *self.ir.pages[1:])),
             "duplicate block_id"),
            (replace(self.ir, pages=(replace(page, blocks=(replace(block, block_id="unique"), *page.blocks)), *self.ir.pages[1:])),
             "duplicate block source_ref"),
            (replace(self.ir, pages=(replace(page, blocks=(replace(block, payload="changed"), *page.blocks[1:])), *self.ir.pages[1:])),
             "content hash mismatch"),
            (replace(self.ir, content_sha256="0" * 64), "manual content hash mismatch"),
            (replace(self.ir, pages=tuple(reversed(self.ir.pages))), "manual content hash mismatch"),
            (replace(self.ir, asset_refs=tuple(reversed(self.ir.asset_refs))), "asset_refs"),
        ]
        for ir, diagnostic in cases:
            with self.subTest(diagnostic=diagnostic):
                issues = validate_manual_ir(ir)
                self.assertTrue(any(diagnostic in issue for issue in issues), issues)
                with self.assertRaises(ManualIRValidationError) as caught:
                    self._read(ir.to_dict())
                self.assertEqual(tuple(issues), caught.exception.issues)

    def test_valid_v1_defaults_and_extension_payloads_remain_compatible(self) -> None:
        raw = deepcopy(self.raw)
        for field in ("metadata", "snapshot_sha256"):
            raw.pop(field)
        for page in raw["pages"]:
            page.pop("skipped_raw")
            for block in page["blocks"]:
                if not block["asset_refs"]:
                    block.pop("asset_refs")
        loaded = self._read(raw)
        self.assertEqual({}, loaded.metadata)
        self.assertIsNone(loaded.snapshot_sha256)
        self.assertEqual(self.ir.content_sha256, loaded.content_sha256)
        # The envelope does not invent a second component/kind registry.
        raw["language"] = "x-build"
        raw["pages"][0]["language"] = ""
        raw["pages"][0]["skipped_raw"] = 2
        page = raw["pages"][0]
        page["source_ref"] = "page/custom#source.rst"
        for index, child in enumerate(page["blocks"]):
            child["source_ref"] = f"{page['source_ref']}#custom-{index}"
        block = raw["pages"][0]["blocks"][0]
        block.update(kind="extension-kind", payload={"nested": [True, None, 3.5, "한글"]})
        block["content_sha256"] = value_sha256({"kind": block["kind"], "payload": block["payload"]})
        raw["content_sha256"] = value_sha256({
            "page_ids": [page["page_id"] for page in raw["pages"]],
            "block_hashes": [b["content_sha256"] for page in raw["pages"] for b in page["blocks"]],
        })
        loaded = self._read(raw)
        self.assertEqual([], validate_manual_ir(loaded))
        self.assertTrue(validate_manual_ir(loaded, require_zero_skipped_raw=True))
        self.assertTrue(validate_manual_ir(loaded, require_known_languages=True))

    def test_cross_page_block_move_is_rejected_even_with_unchanged_content_hash(self) -> None:
        first, second = self.ir.pages[:2]
        moved = replace(self.ir, pages=(
            replace(first, blocks=first.blocks[:-1]),
            replace(second, blocks=(first.blocks[-1], *second.blocks)),
            *self.ir.pages[2:],
        ))
        # v1 hashes flatten blocks, so ownership must be checked separately.
        self.assertEqual(self.ir.content_sha256, moved.content_sha256)
        self.assertEqual(
            [b.content_sha256 for p in self.ir.pages for b in p.blocks],
            [b.content_sha256 for p in moved.pages for b in p.blocks],
        )
        issues = validate_manual_ir(moved)
        self.assertFalse(any("hash mismatch" in issue for issue in issues))
        with self.assertRaisesRegex(ManualIRValidationError, "non-empty block fragment"):
            self._read(moved.to_dict())

    def test_json_syntax_encoding_and_duplicate_keys_have_file_context(self) -> None:
        for data in (b'{"pages":', b'\xff', b'{"model":"a","model":"b"}'):
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "broken.ir.json"
                path.write_bytes(data)
                with self.assertRaisesRegex(ManualIRValidationError, "broken.ir.json"):
                    read_manual_ir(path)

    def test_all_file_consumers_reject_before_output_or_plan_mutation(self) -> None:
        cases = [
            (("schema_version",), "manual-ir/v2", "schema_version"),
            (("pages",), None, "pages"),
            (("pages", 0, "blocks", 0, "payload"), "changed", "content hash mismatch"),
            (("pages", 1, "page_id"), self.raw["pages"][0]["page_id"], "duplicate page_id"),
            (("snapshot_sha256",), "bad", "snapshot_sha256"),
            (("pages", 0, "blocks", 0, "source_ref"), "page/other.rst#block-1", "non-empty block fragment"),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ir_path, plan, output = (root / name for name in ("bad.ir.json", "plan.json", "output.json"))
            sentinel = b'{"existing": "must survive rejected input"}\n'
            plan.write_bytes(sentinel)
            output.write_bytes(sentinel)
            commands = [
                ["tools.idml.target_assembly_scaffold", "--ir", str(ir_path), "--physical-pages", "10", "--out", str(output), "--force"],
                ["tools.reference_layout_scaffold", "--manual-ir", str(ir_path), "--seed-plan", str(plan), "--output", str(output), "--force"],
                ["tools.reference_layout_rebind", "--manual-ir", str(ir_path), "--plan", str(plan), "--write"],
                ["tools.reference_layout_rebind", "--manual-ir", str(ir_path), "--all-registered", "--registry", str(plan)],
                ["tools.idml_pdf_parity", "--manual-ir", str(ir_path), "--latex-pdf", "missing.pdf", "--indesign-pdf", "missing.pdf", "--preflight", "missing.json", "--out", str(output)],
            ]
            for path, value, diagnostic in cases:
                raw = deepcopy(self.raw)
                _set(raw, path, value)
                ir_path.write_text(json.dumps(raw), encoding="utf-8")
                before = ir_path.read_bytes()
                for command in commands:
                    with self.subTest(consumer=command[0], diagnostic=diagnostic):
                        result = subprocess.run([sys.executable, "-m", *command], cwd=ROOT, capture_output=True, text=True, check=False)
                        self.assertNotEqual(0, result.returncode)
                        self.assertIn(diagnostic, result.stderr)
                        self.assertIn(str(ir_path), result.stderr)
                        self.assertNotIn("Traceback", result.stderr)
                        self.assertEqual(sentinel, plan.read_bytes())
                        self.assertEqual(sentinel, output.read_bytes())
                        self.assertEqual(before, ir_path.read_bytes())
                        self.assertFalse(output.with_suffix(".todos.md").exists())
                        self.assertFalse(output.with_suffix(".md").exists())

    def test_parity_passes_validated_ir_unchanged_to_plan_consumer(self) -> None:
        # Stop at the next real consumer, before invoking external PDF tools.
        with tempfile.TemporaryDirectory() as tmp:
            path = write_manual_ir(self.ir, Path(tmp) / "manual.ir.json")
            args = Namespace(manual_ir=str(path), latex_pdf="unused.pdf", indesign_pdf="unused.pdf", reference_layout_plan=None)
            with patch("tools.idml_pdf_parity._read_reference_plan", side_effect=RuntimeError("boundary reached")) as consume:
                with self.assertRaisesRegex(RuntimeError, "boundary reached"):
                    build_report(args)
            self.assertEqual(self.ir, consume.call_args.args[1])
