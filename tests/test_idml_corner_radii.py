"""A target may declare the corner radius of its own chrome -- and none does.

Every corner radius in the IDML renderer is read language-neutrally, and most
fall through to a helper's own default. `tools/idml/corner_radii.py` records
the audit that established this and provides a per-target channel: a
composition may declare `corner_radii` in the target-assembly contract, which
is the tightest scope there is.

The mechanism is kept and tested here. Its first use was withdrawn: BP@JP had
declared five radii (5.80 / 7.89 / 4.80 / 11.08 / 7.72) measured off a
hand-made JP PDF. Corner radius is a shared style token -- `comp_*_arc` -- and a
master is a structural key, not a source of geometry, so those declarations
encoded production error and forked one book off the house style. They are
gone, and this file now pins that **no** contract declares a radius. The channel
stays for the case it was built for: a book whose approved style genuinely
differs, declared on purpose.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from tools.idml.corner_radii import (
    declared_indexed_radius,
    declared_radii,
    declared_radius,
)
from tools.idml.target_assembly_plan import (
    INBOX_CORNER_RADII,
    WARRANTY_CORNER_RADII,
    _corner_radii_issues,
)

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "docs/renderers/contracts/target_assembly"

# Example values for exercising the reader and the gate. Not measurements.
EXAMPLE_INBOX = {"card": 6.2, "tip_strip": 7.0}
EXAMPLE_WARRANTY = {"section": 5.0, "section:7": 11.0, "lead": 7.5}


class Reader(unittest.TestCase):
    def test_a_declaration_wins(self) -> None:
        composition = {"corner_radii": {"card": 6.2}}
        self.assertEqual(6.2, declared_radius(composition, "card", 5.5))

    def test_an_undeclared_role_keeps_the_shared_default(self) -> None:
        composition = {"corner_radii": {"card": 6.2}}
        self.assertEqual(5.5, declared_radius(composition, "tip_strip", 5.5))

    def test_no_map_keeps_the_shared_default(self) -> None:
        self.assertEqual(5.5, declared_radius({"layout_variant": "x"}, "card", 5.5))

    def test_no_composition_keeps_the_shared_default(self) -> None:
        self.assertEqual(5.5, declared_radius(None, "card", 5.5))

    def test_zero_is_a_declaration_not_an_absence(self) -> None:
        """A style with square chrome must be expressible."""
        self.assertEqual(0.0, declared_radius({"corner_radii": {"card": 0}}, "card", 5.5))

    def test_integers_are_read_as_points(self) -> None:
        self.assertEqual(7.0, declared_radius({"corner_radii": {"card": 7}}, "card", 5.5))

    def test_a_non_mapping_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            declared_radii({"corner_radii": [6.2]})


class PlanGate(unittest.TestCase):
    def label(self, declared: object) -> list[str]:
        return _corner_radii_issues(declared, allowed=INBOX_CORNER_RADII, label="x")

    def test_absent_is_fine(self) -> None:
        self.assertEqual([], self.label(None))

    def test_allowed_names_pass(self) -> None:
        self.assertEqual([], self.label(EXAMPLE_INBOX))

    def test_an_empty_map_is_refused(self) -> None:
        self.assertTrue(self.label({}))

    def test_unknown_chrome_is_refused(self) -> None:
        """A typo must fail the build, not silently render the default."""
        self.assertTrue(self.label({"crad": 6.2}))

    def test_a_non_number_is_refused(self) -> None:
        self.assertTrue(self.label({"card": "6.2"}))
        self.assertTrue(self.label({"card": True}))

    def test_an_absurd_radius_is_refused(self) -> None:
        self.assertTrue(self.label({"card": 400.0}))
        self.assertTrue(self.label({"card": -1.0}))


class IndexedChrome(unittest.TestCase):
    """One member of a repeated component may carry its own radius."""

    SECTION = {"corner_radii": {"section": 5.0, "section:7": 11.0}}

    def test_the_addressed_member_takes_its_own_radius(self) -> None:
        self.assertEqual(11.0, declared_indexed_radius(self.SECTION, "section", 7, 6.8))

    def test_every_other_member_takes_the_composition_value(self) -> None:
        for index in (0, 2, 3, 4, 5, 6):
            self.assertEqual(
                5.0,
                declared_indexed_radius(self.SECTION, "section", index, 6.8),
                msg=f"index {index}",
            )

    def test_a_missing_index_still_takes_the_composition_value(self) -> None:
        self.assertEqual(5.0, declared_indexed_radius(self.SECTION, "section", None, 6.8))

    def test_declaring_only_an_index_leaves_the_others_on_the_default(self) -> None:
        only = {"corner_radii": {"section:7": 11.0}}
        self.assertEqual(6.8, declared_indexed_radius(only, "section", 3, 6.8))
        self.assertEqual(11.0, declared_indexed_radius(only, "section", 7, 6.8))

    def test_nothing_declared_keeps_the_shared_default(self) -> None:
        self.assertEqual(6.8, declared_indexed_radius(None, "section", 7, 6.8))

    def test_a_bare_index_name_is_refused_by_the_gate(self) -> None:
        self.assertTrue(
            _corner_radii_issues({"section:x": 11.0}, allowed=WARRANTY_CORNER_RADII, label="x")
        )

    def test_an_indexed_name_for_unknown_chrome_is_refused(self) -> None:
        self.assertTrue(
            _corner_radii_issues({"card:1": 5.8}, allowed=WARRANTY_CORNER_RADII, label="x")
        )

    def test_allowed_indexed_names_pass_the_gate(self) -> None:
        self.assertEqual(
            [],
            _corner_radii_issues(EXAMPLE_WARRANTY, allowed=WARRANTY_CORNER_RADII, label="x"),
        )


class NoContractDeclaresARadius(unittest.TestCase):
    def declarations(self) -> dict[str, dict[str, dict]]:
        found: dict[str, dict[str, dict]] = {}
        for path in sorted(CONTRACTS.glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            for page in data.get("pages", []):
                for name, composition in (page.get("composition_data") or {}).items():
                    if isinstance(composition, dict) and composition.get("corner_radii"):
                        found.setdefault(path.stem, {})[name] = composition["corner_radii"]
        return found

    def test_every_book_prints_the_shared_radii(self) -> None:
        """Corner radius is a shared style token. A declaration here is a book
        forking off the house style, and the withdrawn BP@JP set is the
        cautionary example."""
        self.assertEqual({}, self.declarations())

    def test_the_two_allow_lists_do_not_overlap(self) -> None:
        self.assertEqual(frozenset(), INBOX_CORNER_RADII & WARRANTY_CORNER_RADII)

    def test_inbox_chrome_is_refused_on_the_warranty(self) -> None:
        self.assertTrue(
            _corner_radii_issues({"card": 5.8}, allowed=WARRANTY_CORNER_RADII, label="x")
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
