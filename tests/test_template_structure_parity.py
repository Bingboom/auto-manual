"""Per-language template carriers must not drift apart in structure.

Adding a language today means cloning a directory of RST carriers and
translating them. Measured across the two trees that have language
subdirectories, that clone duplicates the *structure* and not the prose:

    page_bp      48 (reference x other) pairs   structure median 1.000   prose median 0.308
    page_shared  68 pairs                       structure median 1.000   prose median 0.317

Structure at the median is byte-for-byte the same shape; the text is genuine
translation. That is the debt worth removing -- one structure, prose as data --
and it is the same inheritance-and-override shape the layout plane just gained
(`code-as-doc/dev/layout_params_guide.md` §3).

This is the safety net that has to exist first. **No gate detects drift between
these carriers today**: of the twenty `tools/check_*.py` gates, only
`check_review_branch_sync.py` reads the template trees at all and it only
computes review-branch blast radius, while `check_docs_duplicate_text.py`
compares an RST list against its `.. only:: html` twin *within one page*.

So this test pins, per carrier, which languages currently share an identical
structural skeleton. Two things then become impossible to do quietly:

* one language's carrier drifting in structure -- its group splits, red;
* a structural merge landing -- groups collapse, red until the baseline is
  updated deliberately, which is exactly the moment a reviewer should look.

Update `tests/fixtures/template_structure_parity.json` as a deliberate act,
with the reason in the PR body. Never to make a build pass.

Scope: only trees carrying language subdirectories, because only those have
language variants to compare. `page_jp`, `page_zh` and the small per-region
trees are flat and out of scope; drift between whole trees is a different
question and `page_bp` vs `page_shared` is measurably not a fork (all 21
same-path pairs score below 0.80, most below 0.15).
"""

from __future__ import annotations

import hashlib
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "docs" / "templates"
BASELINE = ROOT / "tests" / "fixtures" / "template_structure_parity.json"

# A directive ends in `::`; a hyperlink target is `.. _name:`. Everything else
# beginning `..` is a comment, and a comment is not structure -- without this
# distinction `.. The EU booklet's ...` reads as a directive named "the", so
# rewording a comment moves the digest and two carriers with the same shape but
# different comments look like two structures. That noise would erode the gate.
DIRECTIVE = re.compile(r"^\s*\.\.\s+([a-z0-9_|-]+(?:\s*[a-z0-9_-]+)*)::")
TARGET = re.compile(r"^\s*\.\.\s+_[^:]+:\s*$")
COMMENT_START = re.compile(r"^\s*\.\.(\s|$)")
HEADING_UNDERLINE = re.compile(r"^[=\-~^\"'#*+`]{3,}\s*$")
ITEM = ("- ", "* ", "#. ")


def skeleton(path: Path) -> list[str]:
    """The carrier's shape with the prose removed.

    Directive names, heading depth markers and list-item positions survive;
    every run of body text collapses to a single ``TEXT`` atom, so a
    translation of the same page yields the same skeleton.

    Comment blocks are dropped whole, marker and indented continuation both.
    They carry the reasons, not the shape, and counting them would mean a
    reworded comment reads as a structural change -- and two carriers of the
    same shape with comments of different lengths would read as two structures.
    """
    atoms: list[str] = []
    previous_was_text = False
    comment_indent: int | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        indent = len(line) - len(line.lstrip())

        if comment_indent is not None:
            # Inside a comment: blank lines and anything more indented than the
            # `..` marker still belong to it.
            if not line.strip() or indent > comment_indent:
                continue
            comment_indent = None

        directive = DIRECTIVE.match(line)
        if directive:
            atoms.append("DIR:" + directive.group(1).strip())
            previous_was_text = False
            continue
        if TARGET.match(line):
            atoms.append("TARGET")
            previous_was_text = False
            continue
        if COMMENT_START.match(line):
            comment_indent = indent
            previous_was_text = False
            continue
        if HEADING_UNDERLINE.match(line) and previous_was_text:
            atoms.append("HEADING:" + line.strip()[0])
            previous_was_text = False
            continue
        if line.strip().startswith(ITEM):
            atoms.append("ITEM")
            previous_was_text = False
            continue
        previous_was_text = bool(line.strip())
        if previous_was_text:
            atoms.append("TEXT")
    return atoms


def skeleton_digest(path: Path) -> str:
    return hashlib.sha256("\n".join(skeleton(path)).encode("utf-8")).hexdigest()[:16]


def language_trees() -> list[Path]:
    return sorted(
        tree
        for tree in TEMPLATES.glob("page_*")
        if tree.is_dir() and any(child.is_dir() for child in tree.iterdir())
    )


def observed() -> dict[str, dict[str, list[list[str]]]]:
    """tree -> carrier -> groups of languages sharing one skeleton."""
    result: dict[str, dict[str, list[list[str]]]] = {}
    for tree in language_trees():
        carriers: dict[str, dict[str, list[str]]] = {}
        for rst in sorted(tree.rglob("*.rst")):
            relative = rst.relative_to(tree)
            if len(relative.parts) != 2:
                continue  # not <lang>/<carrier>.rst
            lang, carrier = relative.parts
            carriers.setdefault(carrier, {}).setdefault(
                skeleton_digest(rst), []
            ).append(lang)
        result[tree.name] = {
            carrier: sorted(
                (sorted(langs) for langs in by_digest.values()),
                key=lambda group: (-len(group), group[0]),
            )
            for carrier, by_digest in sorted(carriers.items())
        }
    return result


class TheStructureGroupingIsPinned(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(
            BASELINE.is_file(),
            f"missing baseline {BASELINE.relative_to(ROOT)}; generate it with "
            "python tests/test_template_structure_parity.py --regenerate",
        )
        self.baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
        self.observed = observed()

    def test_the_same_trees_are_covered(self) -> None:
        self.assertEqual(sorted(self.baseline), sorted(self.observed))

    def test_every_carrier_groups_exactly_as_pinned(self) -> None:
        for tree in sorted(self.observed):
            with self.subTest(tree=tree):
                self.assertEqual(
                    self.baseline[tree],
                    self.observed[tree],
                    "a carrier's per-language structure grouping moved. A split "
                    "means one language drifted; a collapse means structures "
                    "were merged. Either way, update the baseline deliberately "
                    "and say why in the PR body.",
                )

    def test_the_pin_is_not_vacuous(self) -> None:
        """A gate over an empty set would pass forever."""
        carriers = sum(len(carriers) for carriers in self.observed.values())
        self.assertGreaterEqual(len(self.observed), 2, self.observed.keys())
        self.assertGreaterEqual(carriers, 20, carriers)


class TheDetectorFires(unittest.TestCase):
    """A gate that cannot fail is not a gate."""

    def test_a_planted_structural_change_alters_the_digest(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            base = Path(td) / "a.rst"
            base.write_text(
                "Title\n=====\n\nBody line.\n\n.. note::\n\n   Careful.\n",
                encoding="utf-8",
            )
            translated = Path(td) / "b.rst"
            translated.write_text(
                "Titel\n=====\n\nTextzeile.\n\n.. note::\n\n   Vorsicht.\n",
                encoding="utf-8",
            )
            drifted = Path(td) / "c.rst"
            drifted.write_text(
                "Titel\n=====\n\nTextzeile.\n\n.. warning::\n\n   Vorsicht.\n",
                encoding="utf-8",
            )

            self.assertEqual(
                skeleton_digest(base),
                skeleton_digest(translated),
                "translating the prose must not change the skeleton",
            )
            self.assertNotEqual(
                skeleton_digest(base),
                skeleton_digest(drifted),
                "swapping a directive must change the skeleton",
            )

    def test_a_comment_block_is_not_structure(self) -> None:
        """Otherwise a reworded comment reads as drift, and the gate is noise."""
        import tempfile

        page = "Title\n=====\n\nBody line.\n"
        commented = (
            ".. Why this carrier exists, at some length,\n"
            "   continuing onto a second indented line\n"
            "   and a third.\n"
            "\n" + page
        )
        differently_commented = ".. One short note.\n\n" + page

        with tempfile.TemporaryDirectory() as td:
            plain = Path(td) / "plain.rst"
            plain.write_text(page, encoding="utf-8")
            long_comment = Path(td) / "long.rst"
            long_comment.write_text(commented, encoding="utf-8")
            short_comment = Path(td) / "short.rst"
            short_comment.write_text(differently_commented, encoding="utf-8")

            self.assertEqual(skeleton_digest(plain), skeleton_digest(long_comment))
            self.assertEqual(skeleton_digest(plain), skeleton_digest(short_comment))


def _regenerate() -> None:
    BASELINE.parent.mkdir(parents=True, exist_ok=True)
    BASELINE.write_text(
        json.dumps(observed(), ensure_ascii=False, indent=1, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"[template-parity] wrote {BASELINE.relative_to(ROOT)}")


if __name__ == "__main__":  # pragma: no cover
    import sys

    if "--regenerate" in sys.argv:
        _regenerate()
    else:
        unittest.main()
