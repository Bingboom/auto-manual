"""The troubleshooting table gets the label-column tint every other table has.

Every data table in the book tints its label column `HB Bg K05` -- the
specification table, the LCD table, the symbol table, the signal-word table --
and the troubleshooting table tinted nothing, so it printed as a bare grid. The
master tints its error-code column too.

`add_trouble_story` also serves the `troubleshooting` and
`storage_troubleshooting` compositions, which BP@US and BP@EU use, so the fill
defaults to empty and only the combined `troubleshooting_specifications`
composition asks for it. That composition is declared by exactly one contract,
which is what keeps the change off the other books.
"""

from __future__ import annotations

import inspect
import json
import unittest
from pathlib import Path

from tools.idml.data_stories import add_trouble_story

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "docs/renderers/contracts/target_assembly"
SHARED_PAGE = ROOT / "tools/idml/shared_page.py"


class DefaultProtectsTheOtherCompositions(unittest.TestCase):
    def test_the_fill_defaults_to_absent(self) -> None:
        """If this default became truthy, BP@US and BP@EU would gain a tint."""
        self.assertEqual(
            "",
            inspect.signature(add_trouble_story).parameters["label_column_fill"].default,
        )

    def test_only_the_combined_composition_asks_for_it(self) -> None:
        source = SHARED_PAGE.read_text(encoding="utf-8")
        self.assertEqual(1, source.count('label_column_fill="Color/HB Bg K05"'))
        # It sits inside the combined composition, not the other two.
        combined = source.index("def add_troubleshooting_specifications_page")
        following = source.index("__all__", combined)
        self.assertIn(
            'label_column_fill="Color/HB Bg K05"', source[combined:following]
        )


class BlastRadius(unittest.TestCase):
    def test_one_contract_declares_the_combined_composition(self) -> None:
        """Pins that the tint reaches exactly one book."""
        declaring = []
        for path in sorted(CONTRACTS.glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            for page in data.get("pages", []):
                if page.get("composition_type") == "troubleshooting_specifications":
                    declaring.append(path.stem)
        self.assertEqual(["jbp2000b_jp_v1_candidate"], sorted(set(declaring)))

    def test_the_other_troubleshooting_compositions_still_exist(self) -> None:
        """If these disappeared, the default above would stop protecting anyone."""
        source = SHARED_PAGE.read_text(encoding="utf-8")
        for name in (
            "add_connection_tail_troubleshooting_page",
            "add_storage_troubleshooting_page",
        ):
            self.assertIn(f"def {name}", source)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
