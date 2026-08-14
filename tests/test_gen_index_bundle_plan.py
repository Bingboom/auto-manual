from __future__ import annotations

import unittest

from tools.gen_index_bundle import plan_materialized_pages


def _rst(file: str, **extra: object) -> dict:
    return {"type": "rst_include", "lang": "en", "file": file, **extra}


class TestPlanMaterializedPagesOrdinals(unittest.TestCase):
    def test_duplicate_names_take_positional_ordinal_prefix(self) -> None:
        cfg = {
            "pages": [
                _rst("templates/a/one.rst"),
                _rst("templates/a/two.rst"),
                _rst("templates/b/one.rst"),
            ]
        }
        planned = plan_materialized_pages(cfg)
        self.assertEqual(
            ["one.rst", "two.rst", "p03_one.rst"],
            [page.file_name for page in planned],
        )

    def test_ordinal_neutral_insertion_keeps_tail_numbering(self) -> None:
        # A print-only page inserted mid-manifest must not renumber the pNN_
        # names after it: review branches and the approved reference-layout
        # contract pin those names (2026-08-13/14 same-source gate incidents).
        cfg = {
            "pages": [
                _rst("templates/a/one.rst"),
                _rst("templates/a/00_toc.rst", ordinal_neutral=True),
                _rst("templates/a/two.rst"),
                _rst("templates/b/one.rst"),
            ]
        }
        planned = plan_materialized_pages(cfg)
        self.assertEqual(
            ["one.rst", "00_toc.rst", "two.rst", "p03_one.rst"],
            [page.file_name for page in planned],
        )

    def test_ordinal_consuming_insertion_shifts_tail_numbering(self) -> None:
        # Contrast case: without ordinal_neutral the same insertion shifts the
        # duplicate's prefix, which is exactly the drift the flag prevents.
        cfg = {
            "pages": [
                _rst("templates/a/one.rst"),
                _rst("templates/a/00_toc.rst"),
                _rst("templates/a/two.rst"),
                _rst("templates/b/one.rst"),
            ]
        }
        planned = plan_materialized_pages(cfg)
        self.assertEqual(
            ["one.rst", "00_toc.rst", "two.rst", "p04_one.rst"],
            [page.file_name for page in planned],
        )


if __name__ == "__main__":
    unittest.main()
