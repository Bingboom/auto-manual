"""Enumerated list items must stay separate items.

The extractor recognised `- ` bullets but had no branch for `1. `, so an
enumerated item fell into the paragraph branch, which greedily absorbs any
following line that is not a bullet, line block or directive. The next item
joined the first and the whole list shipped as one paragraph -- visible in the
BP@JP warranty page, where eight runs across two sections rendered as running
prose against the shipped book's numbered lines.

The golden IDML fixtures do not reach this code path (regenerating all four
leaves them byte-identical), so these tests are the only coverage.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.idml_rst_extract import extract_page

TAGS = {"latex", "lang_ja", "region_jp"}


def blocks_for(source: str) -> list[tuple[str, str]]:
    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "page.rst"
        page.write_text(source, encoding="utf-8")
        return list(extract_page(page, TAGS).blocks)


class EnumeratedLists(unittest.TestCase):
    def test_consecutive_items_do_not_merge(self) -> None:
        blocks = blocks_for(
            "1. 保証期間はご購入日から3年間です。\n"
            "2. また、延長保証にご登録いただくと、さらに2年間の保証が追加されます。\n"
        )
        kinds = [kind for kind, _ in blocks]
        self.assertEqual(["list", "list"], kinds)
        self.assertEqual("1. 保証期間はご購入日から3年間です。", blocks[0][1])
        self.assertTrue(blocks[1][1].startswith("2. また、"))

    def test_enumerator_is_kept_because_it_is_part_of_the_copy(self) -> None:
        """Unlike a bullet, the number is authored text, not a marker."""
        blocks = blocks_for("1. first\n2. second\n3. third\n")
        self.assertEqual(
            ["1. first", "2. second", "3. third"], [text for _, text in blocks]
        )

    def test_six_item_run_stays_six_items(self) -> None:
        source = "".join(f"{n}. item {n}\n" for n in range(1, 7))
        self.assertEqual(6, len(blocks_for(source)))

    def test_wrapped_continuation_joins_its_own_item(self) -> None:
        blocks = blocks_for(
            "1. first item that wraps\n"
            "   onto a second line\n"
            "2. second item\n"
        )
        self.assertEqual(2, len(blocks))
        self.assertEqual("1. first item that wraps onto a second line", blocks[0][1])

    def test_paren_enumerator_is_recognised(self) -> None:
        blocks = blocks_for("1) first\n2) second\n")
        self.assertEqual(["list", "list"], [kind for kind, _ in blocks])

    def test_indented_items_become_sublist(self) -> None:
        blocks = blocks_for("  1. nested one\n  2. nested two\n")
        self.assertEqual(["sublist", "sublist"], [kind for kind, _ in blocks])

    def test_bullets_are_unchanged(self) -> None:
        """The bullet branch keeps its marker; only enumerators are new."""
        blocks = blocks_for("- alpha\n- beta\n")
        self.assertEqual(["list", "list"], [kind for kind, _ in blocks])
        self.assertEqual(["• alpha", "• beta"], [text for _, text in blocks])

    def test_a_number_inside_prose_is_still_prose(self) -> None:
        """`1.` only starts a list at the head of a line.

        Otherwise a sentence mentioning a figure would be torn into a list.
        """
        blocks = blocks_for("定格容量は 2048 Wh です。1.5 倍まで拡張できます。\n")
        self.assertEqual(["body"], [kind for kind, _ in blocks])

    def test_decimal_at_line_start_is_not_an_item(self) -> None:
        """`1.5 倍` opens a line in some copy; it must not become a list."""
        blocks = blocks_for("1.5 倍まで拡張できます。\n")
        self.assertEqual(["body"], [kind for kind, _ in blocks])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
