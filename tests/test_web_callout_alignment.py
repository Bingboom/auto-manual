from __future__ import annotations

import unittest

from bs4 import BeautifulSoup

from tools.web.callout_alignment import LABEL_SIZER_CLASS, align_callout_label_columns


def _callout(label: str, body: str = "Body copy.") -> str:
    return (
        '<table class="manual-callout-table" style="width:100%;"><tbody><tr>'
        f'<td class="manual-callout-label" style="width:16%;"><p><strong>{label}</strong></p></td>'
        f'<td class="manual-callout-body"><p>{body}</p></td>'
        "</tr></tbody></table>"
    )


def _sizers(page: str) -> list[list[str]]:
    soup = BeautifulSoup(page, "html.parser")
    return [
        [span.get_text() for span in cell.select(f"span.{LABEL_SIZER_CLASS}")]
        for cell in soup.select("table.manual-callout-table td.manual-callout-label")
    ]


class CalloutLabelAlignmentTests(unittest.TestCase):
    def test_every_label_cell_carries_the_page_labels(self) -> None:
        page = "<h1>Safety</h1>\n" + _callout("AVERTISSEMENT") + "\n<p>Text</p>\n" + _callout("REMARQUE") + _callout("AVERTISSEMENT")
        aligned = align_callout_label_columns(page)
        self.assertEqual([["AVERTISSEMENT", "REMARQUE"]] * 3, _sizers(aligned))
        # Only the width references are added; every other byte stays.
        self.assertEqual(page, aligned.replace(
            f'<span class="{LABEL_SIZER_CLASS}" aria-hidden="true">AVERTISSEMENT</span>'
            f'<span class="{LABEL_SIZER_CLASS}" aria-hidden="true">REMARQUE</span>', ""))
        soup = BeautifulSoup(aligned, "html.parser")
        self.assertEqual(
            ["AVERTISSEMENT", "REMARQUE", "AVERTISSEMENT"],
            [cell.select_one("strong").get_text() for cell in soup.select("td.manual-callout-label")],
        )
        self.assertTrue(all(span["aria-hidden"] == "true" for span in soup.select(f"span.{LABEL_SIZER_CLASS}")))

    def test_is_idempotent(self) -> None:
        page = _callout("ADVERTENCIA") + _callout("NOTA")
        once = align_callout_label_columns(page)
        self.assertEqual(once, align_callout_label_columns(once))

    def test_single_label_pages_are_unchanged(self) -> None:
        page = _callout("NOTE") + _callout("NOTE", "Other body.")
        self.assertEqual(page, align_callout_label_columns(page))
        self.assertEqual("<p>No callouts.</p>", align_callout_label_columns("<p>No callouts.</p>"))

    def test_labels_are_escaped_and_other_tables_untouched(self) -> None:
        other = '<table class="hb-spec-table"><tr><td class="manual-callout-label">NOT A CALLOUT</td></tr></table>'
        page = _callout("A &amp; B") + other + _callout("ПОПЕРЕДЖЕННЯ")
        aligned = align_callout_label_columns(page)
        self.assertIn(other, aligned)
        self.assertEqual([["A & B", "ПОПЕРЕДЖЕННЯ"]] * 2, _sizers(aligned))
        self.assertIn('aria-hidden="true">A &amp; B</span>', aligned)


if __name__ == "__main__":
    unittest.main()
