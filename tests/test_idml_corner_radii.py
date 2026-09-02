"""A target may declare the corner radius of its own chrome.

Every corner radius in the IDML renderer is read language-neutrally, and most
are not read from a parameter at all -- they fall through to a helper's own
default. `tools/idml/corner_radii.py` records the audit that established this;
the practical consequence is that a `lang_jp_*_arc` row is a dead row, so a
book whose approved master rounds a panel differently could only be served by
moving a shared value that every other book reads.

A target's composition data is the tightest scope there is, because the
contract file belongs to one target. These tests pin the reader, the plan
gate, and -- most importantly -- that a composition which declares nothing
keeps the shared default, which is what every other contract does.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from tools.idml.corner_radii import declared_radii, declared_radius
from tools.idml.target_assembly_plan import (
    INBOX_CORNER_RADII,
    WARRANTY_CORNER_RADII,
    _corner_radii_issues,
)

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "docs/renderers/contracts/target_assembly"

# Path radii measured from the pinned JP master. Path, not ink: a pixel
# measurement of a stroked box reads half a stroke width larger, and the IDML
# stores a path radius -- the two differ by exactly half the stroke, which is
# what reconciled two disagreeing measurements of the same shapes.
MEASURED = {
    # reference page 4: cards 101.0 x 152.9 stroked 0.94; note strip
    # 311.8 x 42.6 stroked 1.05
    "inbox": {"card": 5.8, "tip_strip": 7.89},
    # reference pages 10-11: six section frames 312.1 wide stroked 1.10 at
    # 4.79-4.80; purchase-channel lead panel 311.8 x 37.2 unstroked at 7.72.
    # Both are rounder in the build than in the book, not flatter.
    "warranty": {"section": 4.8, "lead": 7.72},
}
ALLOWED = {"inbox": INBOX_CORNER_RADII, "warranty": WARRANTY_CORNER_RADII}
MEASURED_CARD = MEASURED["inbox"]["card"]
MEASURED_TIP_STRIP = MEASURED["inbox"]["tip_strip"]


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
        """A master with square chrome must be expressible."""
        self.assertEqual(0.0, declared_radius({"corner_radii": {"card": 0}}, "card", 5.5))

    def test_integers_are_read_as_points(self) -> None:
        self.assertEqual(7.0, declared_radius({"corner_radii": {"card": 7}}, "card", 5.5))

    def test_a_non_mapping_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            declared_radii({"corner_radii": [6.2]})


class PlanGate(unittest.TestCase):
    def label(self, declared: object) -> list[str]:
        return _corner_radii_issues(
            declared, allowed=INBOX_CORNER_RADII, label="x"
        )

    def test_absent_is_fine(self) -> None:
        self.assertEqual([], self.label(None))

    def test_measured_values_pass(self) -> None:
        self.assertEqual(
            [], self.label({"card": MEASURED_CARD, "tip_strip": MEASURED_TIP_STRIP})
        )

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


class ShippedContractsAreUnaffected(unittest.TestCase):
    def declarations(self) -> dict[str, dict[str, dict]]:
        """{contract stem: {composition name: declared radii}}."""
        found: dict[str, dict[str, dict]] = {}
        for path in sorted(CONTRACTS.glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            for page in data.get("pages", []):
                for name, composition in (
                    page.get("composition_data") or {}
                ).items():
                    if isinstance(composition, dict) and composition.get(
                        "corner_radii"
                    ):
                        found.setdefault(path.stem, {})[name] = composition[
                            "corner_radii"
                        ]
        return found

    def test_only_bp_jp_declares_corner_radii(self) -> None:
        """Pins the blast radius.

        BP@US and BP@EU render the same inbox and warranty compositions and
        keep the shared defaults. If another target starts declaring radii,
        this is where that shows up.
        """
        self.assertEqual(["jbp2000b_jp_v1_candidate"], sorted(self.declarations()))

    def test_bp_jp_declares_the_measured_master_values(self) -> None:
        self.assertEqual(MEASURED, self.declarations()["jbp2000b_jp_v1_candidate"])

    def test_every_declared_name_is_gate_allowed(self) -> None:
        for composition, radii in self.declarations()[
            "jbp2000b_jp_v1_candidate"
        ].items():
            for name in radii:
                self.assertIn(name, ALLOWED[composition], msg=composition)

    def test_the_two_allow_lists_do_not_overlap(self) -> None:
        """Chrome names are per composition, so a name means one thing."""
        self.assertEqual(frozenset(), INBOX_CORNER_RADII & WARRANTY_CORNER_RADII)


class WarrantyPlanGate(unittest.TestCase):
    def test_measured_warranty_values_pass(self) -> None:
        self.assertEqual(
            [],
            _corner_radii_issues(
                MEASURED["warranty"], allowed=WARRANTY_CORNER_RADII, label="x"
            ),
        )

    def test_inbox_chrome_is_refused_on_the_warranty(self) -> None:
        self.assertTrue(
            _corner_radii_issues(
                {"card": 5.8}, allowed=WARRANTY_CORNER_RADII, label="x"
            )
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
