from __future__ import annotations

import unittest
from unittest.mock import patch

from tools import phase1_build


class TestPhase1BuildCli(unittest.TestCase):
    def test_parse_args_should_use_phase1_csv_defaults(self) -> None:
        with patch("sys.argv", ["phase1_build.py"]):
            args = phase1_build.parse_args()

        self.assertEqual("data/phase1/Spec_Master.csv", args.spec_master_csv)
        self.assertEqual("data/phase1/Spec_Footnotes.csv", args.spec_footnotes_csv)


if __name__ == "__main__":
    unittest.main()
