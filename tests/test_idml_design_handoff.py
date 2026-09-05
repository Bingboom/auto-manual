from __future__ import annotations

from dataclasses import replace
import json
import tempfile
import unittest
from pathlib import Path

from tools.idml.design_handoff import write_handoff_package
from tools.idml.flow_idml import FlowOutputs
from tools.manual_ir import build_manual_ir, write_manual_ir


class IdmlDesignHandoffTests(unittest.TestCase):
    def test_write_handoff_package(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            data_root = root / "data" / "phase2"
            data_root.mkdir(parents=True)
            (data_root / "Spec_Master.csv").write_text("x\n", encoding="utf-8")
            bundle = root / "docs" / "_build" / "JE-1000F" / "US" / "en" / "rst"
            bundle.mkdir(parents=True)
            idml_dir = root / "docs" / "_build" / "JE-1000F" / "US" / "en" / "idml"
            flow_dir = idml_dir / "flow"
            flow_dir.mkdir(parents=True)
            production = idml_dir / "manual_je1000f_us_en.idml"
            from tests.test_idml_delivery import _write_production_idml
            _write_production_idml(production, [])
            repo = Path(__file__).resolve().parents[1]
            ir = build_manual_ir(root=repo, bundle_root=repo / "tests/fixtures/idml_bundle",
                                 model="JE-1000F", region="US", lang="en", source="review")
            ir = replace(ir, pages=(replace(ir.pages[0], skipped_raw=2), *ir.pages[1:]),
                         metadata={**ir.metadata, "skipped_raw": 2})
            write_manual_ir(ir, idml_dir / "manual.ir.json")
            manifest = flow_dir / "manual.flow.asset_manifest.csv"
            manifest.write_text(
                "\n".join([
                    "asset_id,asset_ref,resolved_path,source_ref,kind",
                    "front,front.png,docs/_build/front.png,page=p1,image",
                    "missing,missing.png,,page=p2,image",
                ]) + "\n",
                encoding="utf-8",
            )
            flow = FlowOutputs(
                markdown=flow_dir / "manual.flow.md",
                source_trace=flow_dir / "manual.flow.source_trace.json",
                asset_manifest=manifest,
                conversion_notes=flow_dir / "flow_conversion_notes.md",
                idml=flow_dir / "manual.flow.idml",
                style_map=flow_dir / "flow_style_map.json",
            )
            for path in (flow.markdown, flow.source_trace, flow.conversion_notes,
                         flow.idml, flow.style_map):
                path.write_text("x", encoding="utf-8")

            outputs = write_handoff_package(
                root=root,
                model="JE-1000F",
                region="US",
                lang="en",
                data_root=data_root,
                bundle_root=bundle,
                production_idml=production,
                flow=flow,
                build_command=["build.py", "idml", "--idml-mode", "both"],
            )

            self.assertTrue(outputs.production_idml.is_file())
            self.assertTrue(outputs.production_idml.is_file())
            document_fonts = outputs.production_idml.parent / "Document fonts"
            self.assertTrue((document_fonts / "NotoSans-Regular.ttf").is_file())
            self.assertTrue(
                (document_fonts / "NotoSansSymbols-Regular.ttf").is_file()
            )
            self.assertTrue(
                (document_fonts / "NotoSansSymbols2-Regular.ttf").is_file()
            )
            trace = json.loads(outputs.production_trace.read_text(encoding="utf-8"))
            self.assertEqual("production", trace["idml_mode"])
            self.assertTrue(trace["production_idml"].endswith("manual.production.idml"))
            self.assertEqual(2, trace["skipped_raw_blocks"])
            self.assertTrue(trace["manual_ir"].endswith("idml/manual.ir.json"))
            report = outputs.missing_assets_report.read_text(encoding="utf-8")
            self.assertIn("Missing assets: 1", report)
            self.assertIn("missing.png", report)
            self.assertIn("production/manual.production.idml",
                          outputs.designer_checklist.read_text(encoding="utf-8"))
            self.assertIn("Flow IDML", outputs.layout_feedback.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
