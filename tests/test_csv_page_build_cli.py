from __future__ import annotations

import unittest
from unittest.mock import patch

from tools import csv_page_build


class TestCsvPageBuildCli(unittest.TestCase):
    def test_parse_args_should_use_phase2_csv_defaults(self) -> None:
        with patch("sys.argv", ["csv_page_build.py"]):
            args = csv_page_build.parse_args()

        self.assertEqual("data/phase2/page_registry.csv", args.page_registry)
        self.assertEqual("data/phase2", args.page_blocks_dir)
        self.assertEqual("data/phase2/Spec_Master.csv", args.spec_master_csv)
        self.assertEqual("data/phase2/Spec_Footnotes.csv", args.spec_footnotes_csv)
        self.assertEqual("data/phase2/Spec_Notes.csv", args.spec_notes_csv)
        self.assertEqual("data/phase2/spec_titles.csv", args.spec_titles_csv)

    def test_parse_args_should_derive_snapshot_paths_from_data_root(self) -> None:
        with patch("sys.argv", ["csv_page_build.py", "--data-root", "data/phase2"]):
            args = csv_page_build.parse_args()

        self.assertEqual("data/phase2", args.page_blocks_dir)
        self.assertEqual("data/phase2/Spec_Master.csv", args.spec_master_csv)
        self.assertEqual("data/phase2/Spec_Footnotes.csv", args.spec_footnotes_csv)
        self.assertEqual("data/phase2/Spec_Notes.csv", args.spec_notes_csv)
        self.assertEqual("data/phase2/spec_titles.csv", args.spec_titles_csv)


if __name__ == "__main__":
    unittest.main()
