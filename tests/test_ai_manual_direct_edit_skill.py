from __future__ import annotations

import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from types import ModuleType

import fitz
import yaml

from tools.rtd import system_tooling as tooling

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = REPO_ROOT / ".agents" / "skills" / "ai-manual-direct-edit"
SCRIPTS_DIR = SKILL_DIR / "scripts"


def _load_script(name: str) -> ModuleType:
    path = SCRIPTS_DIR / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"test_ai_direct_edit_{name}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _make_sample_pdf(path: Path, pages: list[str], *, embed_illustrator_marker: bool = False) -> None:
    doc = fitz.open()
    for text in pages:
        page = doc.new_page(width=368.5, height=524.4)
        page.insert_text((36, 72), text, fontsize=10)
    if embed_illustrator_marker and len(doc) > 0:
        xref = doc[0].xref
        doc.xref_set_key(xref, "PieceInfo", "<</Illustrator <</Private <<>>>>>>")
    doc.save(path)
    doc.close()


class AiManualDirectEditSkillTests(unittest.TestCase):
    def test_bundled_jsx_library_is_strictly_pure_ascii(self) -> None:
        runner = _load_script("run_illustrator_jsx")
        lib_path = SCRIPTS_DIR / "ai_edit_lib.jsx"
        self.assertTrue(lib_path.is_file())
        lib_text = lib_path.read_text(encoding="utf-8")
        errors = runner.check_pure_ascii(lib_text, label="ai_edit_lib.jsx")
        self.assertEqual(errors, [])
        for symbol in (
            "function aiMakePureYellow(",
            "function aiMakePureBlack(",
            "function aiCloseOpenDocByName(",
            "function aiSafeSetCharFill(",
            "function aiSafeSetCharFont(",
            "function aiAddHighlightPill(",
            "function aiSetHighlightedText(",
        ):
            self.assertIn(symbol, lib_text)
        # Ensure executable character edits route via textRange.characters to avoid MRAP
        code_lines = [
            line for line in lib_text.splitlines() if not line.lstrip().startswith("//")
        ]
        self.assertNotIn("tf.characters[", "\n".join(code_lines))

    def test_runner_rejects_non_ascii_with_unicode_escape_hint(self) -> None:
        runner = _load_script("run_illustrator_jsx")
        with tempfile.TemporaryDirectory() as tmp:
            bad_jsx = Path(tmp) / "bad.jsx"
            bad_jsx.write_text('var s = "Temp 14°F and LiFePO₄";\n', encoding="utf-8")
            err_buf = io.StringIO()
            with redirect_stderr(err_buf):
                rc = runner.main(["--script", str(bad_jsx), "--check-only"])
            self.assertEqual(rc, 1)
            msg = err_buf.getvalue()
            self.assertIn("\\u00B0", msg)
            self.assertIn("\\u2084", msg)

    def test_runner_refuses_to_overwrite_source_master(self) -> None:
        runner = _load_script("run_illustrator_jsx")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ok_jsx = root / "ok.jsx"
            ok_jsx.write_text('"OK";\n', encoding="ascii")
            master = root / "master.pdf"
            master.write_bytes(b"%PDF-1.4\n")
            err_buf = io.StringIO()
            with redirect_stderr(err_buf):
                rc = runner.main(
                    [
                        "--script",
                        str(ok_jsx),
                        "--source",
                        str(master),
                        "--out",
                        str(master),
                        "--check-only",
                    ]
                )
            self.assertEqual(rc, 2)
            self.assertIn("Refusing to overwrite source master", err_buf.getvalue())

    def test_runner_bundles_library_and_preserves_target_directive(self) -> None:
        runner = _load_script("run_illustrator_jsx")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task_jsx = root / "task.jsx"
            task_jsx.write_text('#target illustrator\n\nvar x = "14\\u00B0F";\n', encoding="ascii")
            bundled = root / "bundled.jsx"
            out_buf = io.StringIO()
            with redirect_stdout(out_buf):
                rc = runner.main(
                    [
                        "--script",
                        str(task_jsx),
                        "--with-lib",
                        "--emit-bundled",
                        str(bundled),
                        "--check-only",
                    ]
                )
            self.assertEqual(rc, 0)
            text = bundled.read_text(encoding="ascii")
            self.assertTrue(text.startswith("#target illustrator\n"))
            self.assertIn("function aiReplaceSub(", text)
            self.assertIn('var x = "14\\u00B0F";', text)
            self.assertEqual(runner.check_pure_ascii(text), [])

    def test_scan_log_issues_detects_warnings_and_errors(self) -> None:
        runner = _load_script("run_illustrator_jsx")
        log = "Opened: doc.pdf\nWARNING: frame not found\nERROR: failed save\nSaved OK\n"
        self.assertEqual(
            runner.scan_log_issues(log),
            ["WARNING: frame not found", "ERROR: failed save"],
        )

    def test_inspect_emits_pure_ascii_jsx_for_artboards_and_imposition_boxes(self) -> None:
        inspect_mod = _load_script("inspect_ai_doc")
        runner = _load_script("run_illustrator_jsx")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = root / "测试原稿.pdf"
            report = root / "inspect.txt"
            frames = root / "frames.txt"
            boxes_json = root / "boxes.json"
            boxes_json.write_text(
                json.dumps(
                    [
                        {"name": "P01_Cover", "rect": [-100, 500, 268.5, -24.4]},
                        {"name": "P02_Preface", "rect": [300, 500, 668.5, -24.4]},
                    ]
                ),
                encoding="utf-8",
            )
            emitted = root / "inspect_out.jsx"
            with redirect_stdout(io.StringIO()):
                rc = inspect_mod.main(
                    [
                        "--source",
                        str(src),
                        "--out-report",
                        str(report),
                        "--dump-frames",
                        str(frames),
                        "--page-boxes",
                        str(boxes_json),
                        "--emit-jsx",
                        str(emitted),
                    ]
                )
            self.assertEqual(rc, 0)
            jsx_text = emitted.read_text(encoding="ascii")
            self.assertEqual(runner.check_pure_ascii(jsx_text), [])
            self.assertIn("P01_Cover", jsx_text)
            self.assertIn("CUSTOM_BOXES", jsx_text)
            self.assertIn("\\u6d4b\\u8bd5", jsx_text.lower())

    def test_verify_normalize_text_handles_ligatures_quotes_and_whitespace(self) -> None:
        verifier = _load_script("verify_ai_output")
        self.assertEqual(
            verifier.normalize_text(
                "First\u00a0\ufb01le  \ufb02ow  chi\ufb00re  o\ufb03ce  wa\ufb04e  user\u2019s\ncheck"
            ),
            "First file flow chiffre office waffle user's check",
        )

    def test_verify_pdf_renders_spec_crops_without_full_page_raster(self) -> None:
        verifier = _load_script("verify_ai_output")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pdf_box = root / "box.pdf"
            _make_sample_pdf(
                pdf_box,
                ["Model: JE-3000E-GY\nchiffre d'affaires"],
                embed_illustrator_marker=True,
            )
            spec = {
                "expected_pages": 1,
                "require_illustrator": True,
                "must_exist": [{"page": 1, "phrase": "JE-3000E-GY"}],
                "crops": [
                    {"name": "spec_panel", "page": 1, "rect": [0, 0, 200, 150], "dpi": 72},
                ],
            }
            render_dir = root / "crops"
            result = verifier.verify_pdf(pdf_box, qa_spec=spec, render_dir=render_dir)
            self.assertTrue(result["ok"])
            self.assertEqual(len(result["rendered_files"]), 1)
            self.assertTrue((render_dir / "spec_panel.png").is_file())
            self.assertFalse((render_dir / "p01.png").exists())

    def test_verify_pdf_checks_illustrator_marker_stale_values_and_renders_pngs(self) -> None:
        verifier = _load_script("verify_ai_output")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pdf_ok = root / "edited.pdf"
            _make_sample_pdf(
                pdf_ok,
                [
                    "Model: NEW-1500\nUser Manual\nFirst file verified",
                    "Page 2 authority to operate the device.\nLCD Screen kept in TOC only",
                ],
                embed_illustrator_marker=True,
            )
            spec = {
                "expected_pages": 2,
                "require_illustrator": True,
                "stale_patterns": [
                    {"pattern": "OLD-1000", "desc": "gen-1 model"},
                    {"pattern": "LCD Screen", "desc": "removed section", "ignore_pages": [2]},
                ],
                "must_exist": [
                    {"page": 1, "phrase": "Model: NEW-1500"},
                    {"page": 1, "phrase": "First file verified"},
                    {"page": 2, "phrase": "authority to operate the device."},
                ],
            }
            spec_path = root / "qa.json"
            spec_path.write_text(json.dumps(spec), encoding="utf-8")
            render_dir = root / "pngs"

            out_buf = io.StringIO()
            with redirect_stdout(out_buf):
                rc = verifier.main(
                    [
                        "--pdf",
                        str(pdf_ok),
                        "--spec",
                        str(spec_path),
                        "--render-dir",
                        str(render_dir),
                        "--dpi",
                        "72",
                        "--json",
                    ]
                )
            self.assertEqual(rc, 0)
            payload = json.loads(out_buf.getvalue())
            self.assertTrue(payload["ok"])
            self.assertTrue(payload["has_illustrator_piece_info"])
            self.assertEqual(len(payload["rendered_files"]), 2)
            self.assertTrue((render_dir / "p01.png").is_file())
            self.assertTrue((render_dir / "p02.png").is_file())

    def test_verify_pdf_fails_on_missing_illustrator_pieceinfo_and_stale_value(self) -> None:
        verifier = _load_script("verify_ai_output")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pdf_bad = root / "broken.pdf"
            _make_sample_pdf(
                pdf_bad,
                ["Model: OLD-1000\nIncomplete text"],
                embed_illustrator_marker=False,
            )
            spec = {
                "expected_pages": 2,
                "require_illustrator": True,
                "stale_patterns": [{"pattern": "OLD-1000", "desc": "gen-1 model"}],
                "must_exist": [{"page": 1, "phrase": "Model: NEW-1500"}],
            }
            result = verifier.verify_pdf(pdf_bad, qa_spec=spec)
            self.assertFalse(result["ok"])
            self.assertFalse(result["has_illustrator_piece_info"])
            self.assertEqual(len(result["errors"]), 2)
            self.assertEqual(len(result["stale_hits"]), 1)
            self.assertEqual(len(result["missing_phrases"]), 1)

    def test_skill_registration_metadata_and_openai_binding(self) -> None:
        facts = {entry["id"]: entry for entry in tooling.skill_facts(REPO_ROOT)}
        self.assertIn("ai-manual-direct-edit", facts)
        entry = facts["ai-manual-direct-edit"]
        self.assertEqual(entry["unregistered"], [])
        self.assertEqual(entry["problems"], [])
        self.assertEqual(entry["lifecycle"]["status"], "active")

        binding = yaml.safe_load((SKILL_DIR / "agents" / "openai.yaml").read_text(encoding="utf-8"))
        self.assertIn("$ai-manual-direct-edit", binding["interface"]["default_prompt"])


if __name__ == "__main__":
    unittest.main()
