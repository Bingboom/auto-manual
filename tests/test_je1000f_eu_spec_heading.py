from __future__ import annotations

import csv
from pathlib import Path
import unittest

from tools.csv_pages import renderers


ROOT = Path(__file__).resolve().parents[1]
FORMAL_DATA_ROOT = ROOT / "manual_sources" / "JE-1000F" / "EU" / "en-fr" / "2.0" / "phase2"
HEADING_KEY = "ENVIRONMENTAL OPERATING TEMPERATURE"

# The released print's heading for this section in each Web route that the
# `--source review` build regenerates from the frozen cells
# (V2.0 EU-UK-2026-06-18, PDF physical pages 53, 71 and 88).
PRINTED_HEADINGS = {
    "es": "TEMPERATURA DE FUNCIONAMIENTO",
    "de": "UMGEBUNGSBETRIEBSTEMPERATUR",
    "it": "TEMPERATURA OPERATIVA AMBIENTALE",
}


def _rows(name: str) -> list[dict[str, str]]:
    with (FORMAL_DATA_ROOT / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class Je1000fEuSpecHeadingTests(unittest.TestCase):
    def test_operating_temperature_cells_hold_each_print_blocks_heading(self) -> None:
        """es/de/it held the English fallback and the Web pages printed it until 2026-09-27."""
        (title,) = [row for row in _rows("spec_titles.csv") if row["title_en"] == HEADING_KEY]
        (copy,) = [
            row
            for row in _rows("Localized_Copy.csv")
            if row["copy_key"] == "spec.section.environmental_operating_temperature"
        ]
        for lang, heading in PRINTED_HEADINGS.items():
            self.assertEqual(heading, title[f"title_{lang}"], lang)
            self.assertEqual(heading, copy[f"text_{lang}"], lang)

    def test_review_built_routes_render_no_english_spec_heading(self) -> None:
        """The spec page these routes publish is rebuilt from Spec_Master + spec_titles."""
        english = renderers.collect_spec_content(
            blocks=_rows("Spec_Master.csv"),
            sku_id="JE-1000F_EU",
            lang="en",
            vars_map={
                "model": "JE-1000F",
                "region": "EU",
                "spec_titles_csv": str(FORMAL_DATA_ROOT / "spec_titles.csv"),
            },
        )
        english_titles = [section["title"] for section in english["sections"]]
        self.assertIn(HEADING_KEY, english_titles)
        for lang, heading in PRINTED_HEADINGS.items():
            with self.subTest(lang=lang):
                data = renderers.collect_spec_content(
                    blocks=_rows("Spec_Master.csv"),
                    sku_id="JE-1000F_EU",
                    lang=lang,
                    vars_map={
                        "model": "JE-1000F",
                        "region": "EU",
                        "spec_titles_csv": str(FORMAL_DATA_ROOT / "spec_titles.csv"),
                    },
                )
                titles = [section["title"] for section in data["sections"]]
                self.assertEqual(heading, titles[english_titles.index(HEADING_KEY)])
                # No section or page heading may fall back to its English key.
                self.assertEqual([], sorted(set(titles) & set(english_titles)))
                self.assertNotEqual(english["title_main"], data["title_main"])


if __name__ == "__main__":
    unittest.main()
