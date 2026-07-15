from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from tools.idml.check import check_idml
from tools.idml.flow_idml import write_flow_outputs


class IdmlFlowIdmlTests(unittest.TestCase):
    def test_write_flow_idml_from_flow_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            data_root = root / "data" / "phase2"
            data_root.mkdir(parents=True)
            (root / "data").mkdir(exist_ok=True)
            (root / "data" / "layout_params.csv").write_text(
                "\n".join([
                    "key,value,unit",
                    "page_paperwidth,368.79,pt",
                    "page_paperheight,524.69,pt",
                    "page_margin_left,28.35,pt",
                    "page_margin_right,28.35,pt",
                    "page_margin_top,14.17,pt",
                    "page_margin_bottom,36.85,pt",
                ]),
                encoding="utf-8",
            )
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

            outputs = write_flow_outputs(
                root=root,
                model="JE-1000F",
                region="US",
                lang="en",
                data_root=data_root,
                bundle_root=bundle,
                build_command=["build.py", "idml", "--idml-mode", "flow"],
            )

            self.assertEqual(check_idml(outputs.idml), [])
            self.assertTrue(outputs.style_map.is_file())
            with zipfile.ZipFile(outputs.idml) as zf:
                names = zf.namelist()
                story = zf.read("Stories/Story_st_flow_main.xml").decode("utf-8")
                all_stories = "\n".join(
                    zf.read(name).decode("utf-8")
                    for name in names if name.startswith("Stories/")
                )
                styles = zf.read("Resources/Styles.xml").decode("utf-8")
            self.assertIn("Stories/Story_st_flow_main.xml", names)
            self.assertIn("INTRO", story)
            self.assertIn("Body copy.", story)
            self.assertIn('<Rectangle Self="flow_img_2"', story)
            self.assertIn("LinkResourceURI=", story)
            self.assertIn("front.png", story)
            self.assertIn('<Table Self="tbl_flow_3"', story)
            self.assertNotIn("[FIGURE: front]", story)
            self.assertNotIn("Item\tValue", story)
            self.assertIn("NOTE", all_stories)
            self.assertIn('Name="Manual H1"', styles)
            self.assertIn('Name="Heading1"', styles)

            trace = json.loads(outputs.source_trace.read_text(encoding="utf-8"))
            self.assertEqual("flow", trace["idml_mode"])
            self.assertTrue(trace["flow_idml"].endswith("manual.flow.idml"))
            self.assertTrue(trace["style_map"].endswith("flow_style_map.json"))
            self.assertEqual("page", trace["trace_granularity"])


if __name__ == "__main__":
    unittest.main()
