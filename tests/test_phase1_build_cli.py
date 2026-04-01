from __future__ import annotations

import unittest
from unittest.mock import patch

from tools import phase1_build


class TestPhase1BuildCli(unittest.TestCase):
    def test_parse_args_should_use_phase1_csv_defaults(self) -> None:
        with patch("sys.argv", ["phase1_build.py"]):
            args = phase1_build.parse_args()

        self.assertEqual("data/phase1/page_registry.csv", args.page_registry)
        self.assertEqual("data/phase1", args.page_blocks_dir)
        self.assertEqual("data/phase1/Spec_Master.csv", args.spec_master_csv)
        self.assertEqual("data/phase1/Spec_Footnotes.csv", args.spec_footnotes_csv)
        self.assertEqual("data/phase1/Spec_Notes.csv", args.spec_notes_csv)
        self.assertEqual("data/phase1/spec_titles.csv", args.spec_titles_csv)

    def test_parse_args_should_derive_snapshot_paths_from_data_root(self) -> None:
        with patch("sys.argv", ["phase1_build.py", "--data-root", "data/phase2"]):
            args = phase1_build.parse_args()

        self.assertEqual("data/phase2", args.page_blocks_dir)
        self.assertEqual("data/phase2/Spec_Master.csv", args.spec_master_csv)
        self.assertEqual("data/phase2/Spec_Footnotes.csv", args.spec_footnotes_csv)
        self.assertEqual("data/phase2/Spec_Notes.csv", args.spec_notes_csv)
        self.assertEqual("data/phase2/spec_titles.csv", args.spec_titles_csv)


if __name__ == "__main__":
    unittest.main()
