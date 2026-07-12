"""Capability-conditional page selection (assembly-side filter)."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.capability_pages import filter_pages_by_capability  # noqa: E402
from tools.config_pages import parse_config_pages  # noqa: E402


def _data_dir(rows: str) -> Path:
    td = Path(tempfile.mkdtemp())
    (td / "model_capabilities.csv").write_text(
        "Document_key,Project,UPS功能,加电包扩容\n" + rows + "\n", encoding="utf-8")
    return td


def _pages():
    pages, issues = parse_config_pages([
        {"type": "rst_include", "lang": "en",
         "file": "templates/page_shared/en/06_ups_mode.rst",
         "capability": "UPS功能"},
        {"type": "rst_include", "lang": "en",
         "file": "templates/page_shared/en/07_extra_battery.rst",
         "capability": "加电包扩容"},
        {"type": "rst_include", "lang": "en",
         "file": "templates/page_shared/en/charging.rst"},
    ], default_languages=["en"])
    assert not issues
    return pages


class CapabilityPageFilterTests(unittest.TestCase):
    def test_false_capability_drops_the_page(self) -> None:
        kept, notes = filter_pages_by_capability(
            _pages(), model="JE-1000F", region="US",
            data_dir=_data_dir("JE-1000F_US,HTE153,TRUE,FALSE"))
        files = [p.file for p in kept]
        self.assertIn("templates/page_shared/en/06_ups_mode.rst", files)
        self.assertNotIn("templates/page_shared/en/07_extra_battery.rst", files)
        self.assertIn("templates/page_shared/en/charging.rst", files)
        self.assertEqual(len(notes), 1)
        self.assertIn("加电包扩容", notes[0])

    def test_true_capability_keeps_the_page(self) -> None:
        kept, _ = filter_pages_by_capability(
            _pages(), model="JE-2000E", region="US",
            data_dir=_data_dir("JE-2000E_US,HTE152,TRUE,TRUE"))
        files = [p.file for p in kept]
        self.assertIn("templates/page_shared/en/07_extra_battery.rst", files)

    def test_target_without_capability_row_keeps_everything(self) -> None:
        kept, notes = filter_pages_by_capability(
            _pages(), model="JE-900B", region="JP",
            data_dir=_data_dir("JE-1000F_US,HTE153,TRUE,FALSE"))
        self.assertEqual(len(kept), 3)
        self.assertEqual(notes, [])

    def test_no_target_context_is_a_noop(self) -> None:
        kept, notes = filter_pages_by_capability(
            _pages(), model=None, region=None,
            data_dir=_data_dir("JE-1000F_US,HTE153,TRUE,FALSE"))
        self.assertEqual(len(kept), 3)
        self.assertEqual(notes, [])

    def test_parser_rejects_blank_capability(self) -> None:
        _, issues = parse_config_pages(
            [{"type": "rst_include", "lang": "en", "file": "x.rst",
              "capability": "  "}], default_languages=["en"])
        self.assertTrue(any("capability" in i.msg for i in issues))


if __name__ == "__main__":
    unittest.main()
