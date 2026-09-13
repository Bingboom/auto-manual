"""Different source labels must survive shared-key specification grouping."""

import csv
from pathlib import Path
import unittest

from tools.csv_pages.renderers_spec import render_spec_page
from tools.csv_pages.renderers_spec_parser import collect_spec_content


class SpecRowLabelTests(unittest.TestCase):
    def rows(self):
        return [
            {"Section": "OUTPUT PORTS", "Row_key": "usb_c", "Row_order": "3",
             "Line_order": str(order), "Row_label_source": label,
             "Value_source": value}
            for order, label, value in (
                (1, "USB-C 30W", "30W Max"),
                (2, "USB-C 140W", "140W Max"),
            )
        ]

    def test_distinct_labels_survive_shared_key(self):
        content = collect_spec_content(self.rows(), "", "en", {})
        self.assertEqual(content["sections"][0]["rows"],
                         [("USB-C 30W", "30W Max"), ("USB-C 140W", "140W Max")])

    def test_same_label_still_groups_multiline_values(self):
        rows = self.rows()
        for row in rows:
            row["Row_label_source"] = "2 × USB-C"
        content = collect_spec_content(rows, "", "en", {})
        self.assertEqual(content["sections"][0]["rows"],
                         [("2 × USB-C", "30W Max\n140W Max")])

    def test_distinct_labels_follow_line_order_not_csv_storage_order(self):
        content = collect_spec_content(list(reversed(self.rows())), "", "en", {})
        self.assertEqual(content["sections"][0]["rows"],
                         [("USB-C 30W", "30W Max"), ("USB-C 140W", "140W Max")])

    def test_localized_labels_survive(self):
        rows = self.rows()
        rows[0]["Row_label_fr"] = "Sortie USB-C 30 W"
        rows[1]["Row_label_fr"] = "Sortie USB-C 140 W"
        content = collect_spec_content(rows, "", "fr", {})
        self.assertEqual([r[0] for r in content["sections"][0]["rows"]],
                         ["Sortie USB-C 30 W", "Sortie USB-C 140 W"])

    def test_label_footnotes_are_not_merged(self):
        rows = self.rows()
        for index, row in enumerate(rows, 1):
            row["Row_label_source"] = "USB-C"
            row["Row_label_footnote_refs"] = f"port{index}"
        rows.extend({"Section": "", "Row_key": "", "Line_order": "",
                     "Footnote_id": f"port{index}", "footnote_order": str(index),
                     "footnote_text": f"Port {index} note"}
                    for index in (1, 2))
        content = collect_spec_content(rows, "", "en", {})
        self.assertEqual(content["sections"][0]["rows"],
                         [("USB-C①", "30W Max"), ("USB-C②", "140W Max")])

    def test_frozen_target_port_labels_and_order(self):
        root = Path(__file__).resolve().parents[1]
        for model, high_power in (("JE-1000H", "140W"), ("JE-2000F", "100W")):
            with self.subTest(model=model):
                path = root / "manual_sources" / model / "EU/en/2.0/phase2/Spec_Master.csv"
                with path.open(encoding="utf-8-sig", newline="") as stream:
                    rows = list(csv.DictReader(stream))
                content = collect_spec_content(rows, "", "en", {"model": model, "region": "EU"})
                ports = [row for section in content["sections"] for row in section["rows"]
                         if row[0].startswith("USB-C")]
                self.assertEqual([row[0] for row in ports], ["USB-C 30W", f"USB-C {high_power}"])
                self.assertNotIn("\n", ports[0][1])
                self.assertNotIn("\n", ports[1][1])

    def test_native_html_preserves_both_labels(self):
        html = render_spec_page("{{ spec_sections_html }}", self.rows(), "", "en", {})
        self.assertIn('class="hb-spec-label">USB-C 30W</th>', html)
        self.assertIn('class="hb-spec-label">USB-C 140W</th>', html)


if __name__ == "__main__":
    unittest.main()
