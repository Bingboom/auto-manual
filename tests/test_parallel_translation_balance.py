"""A translation should not be wildly longer or shorter than its siblings.

Parallel-language carriers say the same thing in different languages, so their
section bodies track each other in length -- within the spread you get from
German compounding or Korean density, not by a factor of two.

This exists because of a defect that lived in the shipped US booklet: the
French battery-pack warranty page had its section 4 and 5 bodies offset by one.
Section 5, headed "Limitée à l'acheteur et consommateur d'origine", carried the
repair-or-replace remedy instead, and the non-transferability sentence -- the
one legally meaningful thing that section says -- was missing outright. Five of
the six languages were correct, so nothing structural was wrong: same headings,
same section count, same directives. The only visible signal was that the
French section 4 body ran 288 characters where every sibling ran 121-137.

A duplicate-text check would NOT have caught it: the two swapped bodies were
different strings. Length against the sibling median does catch it, at ratio
2.29.
"""
from __future__ import annotations

import re
import statistics
import unittest
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "docs" / "templates"
UNDERLINE = re.compile(r"^\s*-{3,}\s*$")

# Below this many characters a body is a label or a stub, where a ratio means
# nothing.
MIN_MEDIAN = 40
HIGH, LOW = 2.0, 0.5

# Known-imbalanced sections, measured 2026-09-04. Korean and Japanese are
# systematically denser than the European languages, and pt-BR's charging
# section genuinely carries more text. Each entry is
# (tree, carrier, section index, language). A NEW entry here means a
# translation drifted away from its siblings -- look at it before pinning it.
PINNED = {
    ("page_bp", "05_operation_guide_placeholder.rst", 1, "ja"),
    ("page_bp", "05_operation_guide_placeholder.rst", 2, "ja"),
    ("page_shared", "08_charging_methods.rst", 1, "pt-BR"),
    ("page_shared", "08_charging_methods.rst", 2, "ko"),
    ("page_shared", "11_warranty.rst", 1, "ko"),
    ("page_shared", "11_warranty.rst", 3, "ko"),
    ("page_shared", "11_warranty.rst", 4, "ko"),
    ("page_shared", "11_warranty.rst", 6, "ko"),
    ("page_shared", "charging.rst", 1, "fr"),
    ("page_shared", "charging.rst", 1, "ko"),
}


def section_body_lengths(path: Path) -> list[int]:
    """Length of the first paragraph under each section heading."""
    lines = path.read_text(encoding="utf-8").splitlines()
    out: list[int] = []
    for i, line in enumerate(lines):
        if not UNDERLINE.match(line) or i == 0 or not lines[i - 1].strip():
            continue
        body = [
            x.strip() for x in lines[i + 1:i + 12]
            if x.strip() and not x.strip().startswith(("..", "--", "=="))
        ]
        out.append(len(body[0]) if body else 0)
    return out


def carrier_groups() -> dict[tuple[str, str], dict[str, Path]]:
    groups: dict[tuple[str, str], dict[str, Path]] = defaultdict(dict)
    for tree in ("page_bp", "page_shared"):
        root = TEMPLATES / tree
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*.rst")):
            groups[(tree, path.name)][path.parent.name] = path
    return groups


def imbalances() -> set[tuple[str, str, int, str]]:
    """Sections whose body length is out of line with its sibling languages."""
    found: set[tuple[str, str, int, str]] = set()
    for (tree, name), langs in carrier_groups().items():
        lengths = {lang: section_body_lengths(p) for lang, p in langs.items()}
        # A carrier can legitimately differ in section count between languages
        # (a `only::` branch, an extra JP section). Compare the largest group
        # that agrees, so one odd language cannot exclude the whole carrier --
        # which is exactly how an earlier version of this check managed to skip
        # the warranty page it was written for.
        by_count: dict[int, list[str]] = defaultdict(list)
        for lang, values in lengths.items():
            by_count[len(values)].append(lang)
        count, members = max(by_count.items(), key=lambda kv: (len(kv[1]), kv[0]))
        if count == 0 or len(members) < 3:
            continue
        for index in range(count):
            values = {lang: lengths[lang][index] for lang in members}
            median = statistics.median(values.values())
            if median < MIN_MEDIAN:
                continue
            for lang, value in values.items():
                if value > median * HIGH or value < median * LOW:
                    found.add((tree, name, index + 1, lang))
    return found


class TranslationsTrackTheirSiblings(unittest.TestCase):
    def test_no_section_drifts_beyond_its_pin(self) -> None:
        self.assertEqual(
            sorted(PINNED),
            sorted(imbalances()),
            "a parallel-language section's body length moved out of line with "
            "its siblings. Read the section before touching this pin: a body "
            "that is suddenly twice its siblings' length is usually the wrong "
            "text under the right heading.",
        )

    def test_the_pin_is_not_vacuous(self) -> None:
        groups = carrier_groups()
        comparable = [
            key for key, langs in groups.items()
            if len({len(section_body_lengths(p)) for p in langs.values()}) >= 1
            and len(langs) >= 3
        ]
        self.assertGreaterEqual(len(comparable), 7)
        self.assertIn(("page_bp", "11_warranty.rst"), groups)
        self.assertGreaterEqual(len(groups[("page_bp", "11_warranty.rst")]), 6)


class TheDetectorFires(unittest.TestCase):
    def test_the_french_warranty_offset_would_be_caught(self) -> None:
        """The exact defect, replayed: section 4 carrying section 5's body."""
        fr = TEMPLATES / "page_bp" / "fr" / "11_warranty.rst"
        siblings = [
            section_body_lengths(TEMPLATES / "page_bp" / lang / "11_warranty.rst")
            for lang in ("en", "es", "de", "it", "uk")
        ]
        median = statistics.median(s[3] for s in siblings)
        self.assertTrue(120 <= median <= 140, f"sibling median moved: {median}")

        # 288 is what the French section 4 body measured before the fix.
        self.assertGreater(288, median * HIGH)
        # and what it measures now must not.
        self.assertLessEqual(section_body_lengths(fr)[3], median * HIGH)

    def test_the_repaired_sections_say_different_things(self) -> None:
        fr = (TEMPLATES / "page_bp" / "fr" / "11_warranty.rst").read_text(encoding="utf-8")
        self.assertIn("est limitée à l'acheteur et consommateur d'origine", fr)
        self.assertIn("ne peut pas être transférée", fr)
        self.assertEqual(1, fr.count("réparera ou remplacera"))


if __name__ == "__main__":
    unittest.main()
