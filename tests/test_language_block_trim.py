"""In-page language-block trimming for multi-language pages (prefaces)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.gen_index_bundle_assets import (  # noqa: E402
    normalize_rst_empty_line_blocks,
)
from tools.language_block_trim import (  # noqa: E402
    marker_languages,
    trim_language_blocks,
)

EU_PREFACE = ROOT / "docs/templates/page_eu/00_preface.rst"
SHARED_PREFACE = ROOT / "docs/templates/page_shared/en/00_preface.rst"
AU_SINGLE_PREFACE = ROOT / "docs/templates/page_shared/en/00_preface_single_language.rst"

CYRILLIC = "\u0400-\u04ff"


def _cyrillic_count(text: str) -> int:
    import re
    return len(re.findall(f"[{CYRILLIC}]", text))


class MarkerDetectionTests(unittest.TestCase):
    def test_bold_tag_markers(self):
        text = "**IMPORTANT**\n\nbody\n\n**FR IMPORTANT**\n\ncorps\n"
        self.assertEqual(("fr",), marker_languages(text))

    def test_latex_tag_markers(self):
        text = (
            ".. raw:: latex\n\n   \\HBLangTagLine{EN}{IMPORTANT}\n\n"
            "body\n\n.. raw:: latex\n\n   \\HBLangTagLine{ES}{IMPORTANTE}\n"
        )
        self.assertEqual(("en", "es"), marker_languages(text))

    def test_bold_run_that_is_not_a_language_tag(self):
        # `**FRAGILE**` and `**ITEM 3 —**` must not read as FR / IT blocks.
        text = "**FRAGILE**\n\n**ITEMISED LIST**\n\n**NOTE - read this**\n"
        self.assertEqual((), marker_languages(text))

    def test_unregistered_tag_is_not_a_marker(self):
        self.assertEqual((), marker_languages("**XX WARNING**\n"))


class TrimTests(unittest.TestCase):
    def test_no_op_when_every_marker_is_in_scope(self):
        text = SHARED_PREFACE.read_text(encoding="utf-8")
        trimmed, dropped = trim_language_blocks(
            text, languages=["en", "fr", "es"], page_lang="en")
        self.assertEqual((), dropped)
        self.assertEqual(text, trimmed, "in-scope pages must stay byte-identical")

    def test_empty_scope_is_a_no_op(self):
        text = SHARED_PREFACE.read_text(encoding="utf-8")
        trimmed, dropped = trim_language_blocks(text, languages=[], page_lang="en")
        self.assertEqual((), dropped)
        self.assertEqual(text, trimmed)

    def test_eu_preface_drops_only_ukrainian(self):
        text = EU_PREFACE.read_text(encoding="utf-8")
        self.assertGreater(_cyrillic_count(text), 100)
        trimmed, dropped = trim_language_blocks(
            text, languages=["en", "fr", "es", "de", "it"], page_lang="en")
        self.assertEqual(("uk",), dropped)
        self.assertEqual(0, _cyrillic_count(trimmed))
        # Every kept language keeps its header and its body.
        for tag in ("**IMPORTANT**", "**FR IMPORTANT**", "**ES IMPORTANTE**",
                    "**DE WICHTIG**", "**IT IMPORTANTE**"):
            self.assertIn(tag, trimmed)
        self.assertNotIn("**UK", trimmed)
        self.assertIn("|MANUAL_LANGUAGE_SCOPE|", trimmed)

    def test_shared_preface_trimmed_to_english_matches_the_hand_forked_template(self):
        """The mechanism must reproduce the AU precedent, not approximate it.

        `00_preface_single_language.rst` is the hand-forked EN-only preface a
        human produced for the AU line. Trimming the shared trilingual preface
        to `en` has to land on the same page after the bundle's own
        empty-line-block normalisation, or the mechanism is not a
        drop-in replacement for forking.
        """
        trimmed, dropped = trim_language_blocks(
            SHARED_PREFACE.read_text(encoding="utf-8"),
            languages=["en"], page_lang="en")
        self.assertEqual(("fr", "es"), dropped)
        self.assertEqual(
            normalize_rst_empty_line_blocks(
                AU_SINGLE_PREFACE.read_text(encoding="utf-8")),
            normalize_rst_empty_line_blocks(trimmed),
        )

    def test_page_structure_macros_survive_a_dropped_block(self):
        """A dropped block must not take the page's LaTeX scaffolding with it."""
        text = (
            ".. raw:: latex\n\n   \\HBPrefacePageBegin\n"
            "   \\HBLangTagLine{FR}{IMPORTANT}\n\n"
            "corps\n\n"
            ".. raw:: latex\n\n   \\HBPrefacePageEnd\n"
        )
        trimmed, dropped = trim_language_blocks(
            text, languages=["en"], page_lang="en")
        self.assertEqual(("fr",), dropped)
        self.assertIn("\\HBPrefacePageBegin", trimmed)
        self.assertIn("\\HBPrefacePageEnd", trimmed)
        self.assertNotIn("HBLangTagLine", trimmed)
        self.assertNotIn("corps", trimmed)

    def test_only_directive_of_a_dropped_block_is_dropped_whole(self):
        """No empty `.. only::` may be left behind."""
        text = (
            "**IMPORTANT**\n\nbody\n\n"
            ".. only:: not latex\n\n   **FR IMPORTANT**\n\n"
            "corps\n"
        )
        trimmed, dropped = trim_language_blocks(
            text, languages=["en"], page_lang="en")
        self.assertEqual(("fr",), dropped)
        self.assertNotIn(".. only:: not latex", trimmed)
        self.assertNotIn("corps", trimmed)
        self.assertIn("body", trimmed)

    def test_leading_untagged_block_belongs_to_the_page_language(self):
        text = "intro for the page language\n\n**UK ВАЖЛИВО**\n\nтекст\n"
        trimmed, dropped = trim_language_blocks(
            text, languages=["en"], page_lang="en")
        self.assertEqual(("uk",), dropped)
        self.assertIn("intro for the page language", trimmed)
        self.assertEqual(0, _cyrillic_count(trimmed))

    def test_trimming_is_idempotent(self):
        text = EU_PREFACE.read_text(encoding="utf-8")
        once, _ = trim_language_blocks(
            text, languages=["en", "fr", "es", "de", "it"], page_lang="en")
        twice, dropped = trim_language_blocks(
            once, languages=["en", "fr", "es", "de", "it"], page_lang="en")
        self.assertEqual((), dropped)
        self.assertEqual(once, twice)

    def test_historical_alias_scope_keeps_the_block(self):
        text = "**IMPORTANT**\n\nbody\n\n**UKR ВАЖЛИВО**\n\nтекст\n"
        trimmed, dropped = trim_language_blocks(
            text, languages=["en", "uk"], page_lang="en")
        self.assertEqual((), dropped)
        self.assertEqual(text, trimmed)


if __name__ == "__main__":
    unittest.main()
