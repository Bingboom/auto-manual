from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.idml.flow_md import write_flow_artifacts


class IdmlFlowMarkdownTests(unittest.TestCase):
    def test_write_flow_artifacts_from_prepared_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            data_root = root / "data" / "phase2"
            data_root.mkdir(parents=True)
            (data_root / "snapshot_manifest.json").write_text('{"ok": true}\n', encoding="utf-8")
            (data_root / "Spec_Master.csv").write_text("document_key\n", encoding="utf-8")
            bundle = root / "docs" / "_build" / "JE-1000F" / "US" / "en" / "rst"
            page_dir = bundle / "page"
            page_dir.mkdir(parents=True)
            (bundle / "index.rst").write_text(
                "\n".join([
                    ".. include:: page/00_intro.rst",
                    ".. include:: page/01_notice.rst",
                ]),
                encoding="utf-8",
            )
            (page_dir / "00_intro.rst").write_text(
                "\n".join([
                    "INTRO",
                    "=====",
                    "",
                    "Body copy.",
                    "",
                    ".. image:: _assets/front.png",
                    "",
                    ".. list-table::",
                    "   :header-rows: 1",
                    "",
                    "   * - Item",
                    "     - Value",
                    "   * - Capacity",
                    "     - 1024 Wh",
                ]),
                encoding="utf-8",
            )
            (page_dir / "01_notice.rst").write_text(
                "\n".join([
                    ".. list-table::",
                    "",
                    "   * - NOTE",
                    "     - Keep the product dry.",
                    "     - Check it every three months.",
                ]),
                encoding="utf-8",
            )
            (bundle / "_assets").mkdir()
            (bundle / "_assets" / "front.png").write_bytes(b"png")

            artifacts = write_flow_artifacts(
                root=root,
                model="JE-1000F",
                region="US",
                lang="en",
                data_root=data_root,
                bundle_root=bundle,
                build_command=["build.py", "idml", "--idml-mode", "flow"],
            )

            markdown = artifacts.markdown.read_text(encoding="utf-8")
            self.assertIn("manual_id: JE1000F_US_EN", markdown)
            self.assertIn("<!-- source_ref: page=00_intro", markdown)
            self.assertIn("# INTRO", markdown)
            self.assertIn("| Item | Value |", markdown)
            self.assertIn("![front](_assets/front.png)", markdown)
            self.assertIn("::: note", markdown)
            self.assertIn("<!-- asset_id: front asset_ref: _assets/front.png -->", markdown)

            trace = json.loads(artifacts.source_trace.read_text(encoding="utf-8"))
            self.assertEqual("flow", trace["idml_mode"])
            self.assertEqual("JE1000F_US_EN", trace["manual_id"])
            self.assertEqual(["build.py", "idml", "--idml-mode", "flow"], trace["build_command"])
            self.assertIn("Spec_Master.csv", trace["source_tables"])

            manifest = artifacts.asset_manifest.read_text(encoding="utf-8")
            self.assertIn("front,_assets/front.png", manifest)


if __name__ == "__main__":
    unittest.main()
