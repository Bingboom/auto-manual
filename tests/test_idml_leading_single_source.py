"""Leading lives in the paragraph style, never in a hand-built attribute.

InDesign silently ignores a numeric ``Leading`` attribute on a
``CharacterStyleRange`` or its enclosing ``ParagraphStyleRange``; only
``<Leading type="unit">`` inside ``<Properties>`` is honored.
``character_metrics.with_character_metrics`` exists to strip the attribute form
and re-emit the element form, and it was written in #692 while aligning panels
that would not match their reference -- that is, by someone who hit this.

Ten call sites under ``tools/idml`` built the attribute form by hand anyway, so
each declared a leading no page ever used: warranty body asking 7.0 and
composing at 6.0, a year badge asking 22.0 and composing at 12.0, table carrier
markers asking 0.1 and getting 7.2, five back-cover lines asking 10.0 to 18.5
and getting 7.2 to 9.6. Removing them changed nothing that prints, which is the
proof they never printed.

The reason to pin it rather than trust review: a value that cannot reach the
page cannot be falsified. No build fails, no golden moves, no CI lane goes red,
and later work tunes on top of it -- three languages had already fitted their
own rows against the dead warranty 7.0. The only defence is not writing it.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IDML = ROOT / "tools" / "idml"

# `Leading="` cannot match the honored element form, which reads
# `<Leading type="unit">` -- the attribute name is followed by a space there.
ATTRIBUTE_FORM = re.compile(r'Leading="')


def offending_lines(root: Path = IDML) -> list[str]:
    hits: list[str] = []
    for path in sorted(root.rglob("*.py")):
        for number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if not ATTRIBUTE_FORM.search(line):
                continue
            # The stripper is allowed to name the form it removes.
            if "re.sub" in line:
                continue
            hits.append(f"{path}:{number}: {line.strip()}")
    return hits


class NoModuleBuildsALeadingAttribute(unittest.TestCase):
    def test_the_writer_never_emits_the_ignored_form(self) -> None:
        hits = offending_lines()
        self.assertEqual(
            [],
            hits,
            "these build a Leading attribute InDesign will drop; put the value "
            "in the paragraph style, or route the run through "
            "character_metrics.with_character_metrics:\n  " + "\n  ".join(hits),
        )

    def test_the_detector_fires_on_a_planted_violation(self) -> None:
        """A gate that cannot fail is not a gate."""
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            sample = Path(td) / "planted.py"
            sample.write_text(
                'attrs = f\'PointSize="{size:g}" Leading="{leading:g}"\'\n',
                encoding="utf-8",
            )
            self.assertEqual(1, len(offending_lines(Path(td))))

    def test_the_detector_allows_the_honored_element_form(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            sample = Path(td) / "honored.py"
            sample.write_text(
                'xml = f\'<Leading type="unit">{leading:g}</Leading>\'\n',
                encoding="utf-8",
            )
            self.assertEqual([], offending_lines(Path(td)))


class TheHonoredFormStillExists(unittest.TestCase):
    """The gate above must not be satisfiable by removing leading entirely."""

    def setUp(self) -> None:
        self.source = (IDML / "character_metrics.py").read_text(encoding="utf-8")

    def test_the_helper_emits_the_element_form(self) -> None:
        self.assertIn('<Leading type="unit">', self.source)

    def test_the_helper_strips_the_attribute_form(self) -> None:
        self.assertIn('re.sub(r\'\\s+Leading="[^"]*"\'', self.source)

    def test_the_helper_is_reachable(self) -> None:
        users = [
            path.name
            for path in sorted(IDML.rglob("*.py"))
            if "with_character_metrics" in path.read_text(encoding="utf-8")
            and path.name != "character_metrics.py"
        ]
        self.assertGreater(len(users), 5, users)

    def test_it_actually_rewrites_a_run(self) -> None:
        from tools.idml.character_metrics import with_character_metrics

        out = with_character_metrics(
            '<CharacterStyleRange PointSize="9" Leading="9">'
            "<Content>x</Content></CharacterStyleRange>",
            point_size=6.0,
            leading=7.2,
        )
        self.assertIn('<Leading type="unit">7.2</Leading>', out)
        self.assertNotIn('Leading="9"', out)


class TheStyleTableCarriesWarrantyLeading(unittest.TestCase):
    """The value the removed warranty attribute claimed lives here instead."""

    def test_the_body_style_declares_its_own_leading(self) -> None:
        from tools.idml.params import load_layout_params
        from tools.idml.styles import para_styles

        params = load_layout_params(
            ROOT / "data/layout_params.csv",
            [ROOT / "data/layout_params.idml-compact.csv"],
        )
        leadings = {
            name: leading
            for name, _size, leading, _weight, _kind in para_styles(params, "ja")
        }
        self.assertAlmostEqual(6.0, leadings["HB Warranty Body"], delta=0.01)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
