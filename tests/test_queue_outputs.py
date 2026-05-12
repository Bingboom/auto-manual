from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools import queue_outputs


class QueueOutputsTests(unittest.TestCase):
    def test_stage_draft_md_output_should_copy_myst_sidecars(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            built_md = root / "worktree" / "docs" / "_build" / "MODEL" / "US" / "en" / "md" / "manual.md"
            built_md.parent.mkdir(parents=True)
            built_md.write_text("# Manual\n<img src=\"assets/demo.png\" />\n", encoding="utf-8")
            (built_md.parent / "assets").mkdir()
            (built_md.parent / "assets" / "demo.png").write_bytes(b"png")
            (built_md.parent / "conf.py").write_text('extensions = ["myst_parser"]\n', encoding="utf-8")
            (built_md.parent / "index.md").write_text("# Demo\n\nmanual\n", encoding="utf-8")
            host_md = root / "host" / "docs" / "_build" / "MODEL" / "US" / "en" / "md" / "manual.md"

            staged = queue_outputs.stage_draft_md_output_to_host_repo(
                built_md_output_path=built_md,
                host_config_path=root / "host" / "config.us-en.yaml",
                model="MODEL",
                region="US",
                version="0.2",
                doc_phase="draft",
                resolve_md_output_path_for_target=lambda **_: host_md,
                versioned_md_output_path=lambda path, *, version, doc_phase: path.with_name("manual_0.2.md"),
            )

            self.assertEqual(host_md.with_name("manual_0.2.md"), staged)
            self.assertEqual(built_md.read_text(encoding="utf-8"), staged.read_text(encoding="utf-8"))
            self.assertTrue((staged.parent / "assets" / "demo.png").exists())
            self.assertTrue((staged.parent / "conf.py").exists())
            self.assertIn("manual_0.2", (staged.parent / "index.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
