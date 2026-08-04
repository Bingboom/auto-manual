"""Capability-conditional page selection (assembly-side filter)."""
from __future__ import annotations

import re
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.capability_pages import (  # noqa: E402
    SECTION_BEGIN_RE,
    filter_pages_by_capability,
    strip_capability_sections,
)
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
    def test_every_manifest_ups_page_is_capability_filtered(self) -> None:
        manifests = sorted((ROOT / "docs" / "manifests").glob("*.yaml"))
        annotated_pages: list[tuple[str, str]] = []
        capability_data = _data_dir("TEST_US,test,FALSE,TRUE")

        for manifest in manifests:
            payload = yaml.safe_load(manifest.read_text(encoding="utf-8"))
            ups_pages = [
                page
                for page in payload.get("pages", [])
                if "06_ups_mode.rst" in str(page.get("file", ""))
            ]
            for page in ups_pages:
                self.assertEqual(
                    page.get("capability"),
                    "UPS功能",
                    f"{manifest.name}: {page.get('file')}",
                )
                annotated_pages.append((manifest.name, page["file"]))

            declared_langs = sorted({
                lang
                for page in payload.get("pages", [])
                for lang in ([page["lang"]] if page.get("lang") else page.get("langs", []))
            })
            parsed_pages, issues = parse_config_pages(
                payload.get("pages", []),
                default_languages=declared_langs,
            )
            self.assertFalse(issues, manifest.name)
            kept, notes = filter_pages_by_capability(
                parsed_pages,
                model="TEST",
                region="US",
                data_dir=capability_data,
            )
            self.assertEqual(len(parsed_pages) - len(kept), len(ups_pages))
            self.assertEqual(len(notes), len(ups_pages))

        self.assertEqual(len(annotated_pages), 24)

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


_MARKED_PAGE = """LED LIGHT ON/OFF
----------------

| Press the LED Light button once.

.. hb-capability-begin: AC/DC输出记忆恢复

AC and DC Output Resume Function
--------------------------------

Enable it in the app to resume outputs automatically.

.. list-table::
   :header-rows: 1

   * - Resumes
     - Does not resume
   * - Power-on after shutdown
     - Output switched off by hand

.. hb-capability-end:

LCD SCREEN
----------

Body after the marked section.
"""


def _section_data_dir(resume: str) -> Path:
    td = Path(tempfile.mkdtemp())
    (td / "model_capabilities.csv").write_text(
        "Document_key,Project,AC/DC输出记忆恢复,UPS功能\n"
        f"JE-2000F_EU,HTE154,{resume},TRUE\n", encoding="utf-8")
    return td


class CapabilitySectionStripTests(unittest.TestCase):
    """Section granularity: one region's templates serve several models."""

    def test_false_capability_drops_the_marked_section(self) -> None:
        text, notes = strip_capability_sections(
            _MARKED_PAGE, model="JE-2000F", region="EU",
            data_dir=_section_data_dir("FALSE"))
        self.assertNotIn("Output Resume Function", text)
        self.assertNotIn("Does not resume", text)
        self.assertIn("LED LIGHT ON/OFF", text)
        self.assertIn("LCD SCREEN", text)
        self.assertIn("Body after the marked section.", text)
        self.assertEqual(1, len(notes))
        self.assertIn("AC/DC输出记忆恢复", notes[0])

    def test_true_capability_keeps_the_body_and_drops_both_markers(self) -> None:
        text, notes = strip_capability_sections(
            _MARKED_PAGE, model="JE-2000F", region="EU",
            data_dir=_section_data_dir("TRUE"))
        self.assertIn("AC and DC Output Resume Function", text)
        self.assertIn("Does not resume", text)
        self.assertNotIn("hb-capability", text)
        self.assertEqual([], notes)

    def test_true_capability_output_matches_an_unmarked_template(self) -> None:
        """Lines that have the feature keep their exact bytes, so their
        pinned reference-layout digests do not move."""
        unmarked = "\n".join(
            line for line in _MARKED_PAGE.splitlines()
            if "hb-capability" not in line) + "\n"
        text, _ = strip_capability_sections(
            _MARKED_PAGE, model="JE-2000F", region="EU",
            data_dir=_section_data_dir("TRUE"))
        self.assertEqual(unmarked, text)

    def test_missing_capability_row_keeps_the_section(self) -> None:
        text, notes = strip_capability_sections(
            _MARKED_PAGE, model="JE-9999X", region="EU",
            data_dir=_section_data_dir("FALSE"))
        self.assertIn("AC and DC Output Resume Function", text)
        self.assertNotIn("hb-capability", text)
        self.assertEqual([], notes)

    def test_no_target_context_keeps_the_section(self) -> None:
        text, _ = strip_capability_sections(
            _MARKED_PAGE, model=None, region=None,
            data_dir=_section_data_dir("FALSE"))
        self.assertIn("AC and DC Output Resume Function", text)
        self.assertNotIn("hb-capability", text)

    def test_capability_absent_from_the_row_keeps_the_section(self) -> None:
        td = Path(tempfile.mkdtemp())
        (td / "model_capabilities.csv").write_text(
            "Document_key,Project,UPS功能\nJE-2000F_EU,HTE154,TRUE\n",
            encoding="utf-8")
        text, notes = strip_capability_sections(
            _MARKED_PAGE, model="JE-2000F", region="EU", data_dir=td)
        self.assertIn("AC and DC Output Resume Function", text)
        self.assertEqual([], notes)

    def test_unmarked_text_is_returned_unchanged(self) -> None:
        plain = "LCD SCREEN\n----------\n\nBody.\n"
        text, notes = strip_capability_sections(
            plain, model="JE-2000F", region="EU",
            data_dir=_section_data_dir("FALSE"))
        self.assertEqual(plain, text)
        self.assertEqual([], notes)

    def test_begin_without_end_raises(self) -> None:
        with self.assertRaises(RuntimeError) as ctx:
            strip_capability_sections(
                "A\n\n.. hb-capability-begin: UPS功能\n\nB\n",
                model="JE-2000F", region="EU",
                data_dir=_section_data_dir("FALSE"), label="p.rst")
        self.assertIn("never closed", str(ctx.exception))

    def test_end_without_begin_raises(self) -> None:
        with self.assertRaises(RuntimeError) as ctx:
            strip_capability_sections(
                "A\n\n.. hb-capability-end:\n\nB\n",
                model="JE-2000F", region="EU",
                data_dir=_section_data_dir("FALSE"), label="p.rst")
        self.assertIn("without a matching begin", str(ctx.exception))

    def test_nested_markers_raise(self) -> None:
        with self.assertRaises(RuntimeError) as ctx:
            strip_capability_sections(
                ".. hb-capability-begin: UPS功能\n\n"
                ".. hb-capability-begin: 加电包扩容\n\n.. hb-capability-end:\n",
                model="JE-2000F", region="EU",
                data_dir=_section_data_dir("FALSE"), label="p.rst")
        self.assertIn("nested", str(ctx.exception))

    def test_markers_are_rst_comments_that_render_nothing(self) -> None:
        """The syntax must be safe unprocessed: a leftover marker is visible
        as a comment, never a section swallowed silently."""
        try:
            from docutils.core import publish_parts
        except ImportError:  # pragma: no cover - docutils always present here
            self.skipTest("docutils unavailable")
        parts = publish_parts(
            source=_MARKED_PAGE, writer_name="html5",
            settings_overrides={"report_level": 5, "halt_level": 5,
                                "file_insertion_enabled": False})
        body = parts["body"]
        self.assertIn("Output Resume Function", body)
        self.assertIn("<!-- hb-capability-begin: AC/DC输出记忆恢复 -->", body)
        self.assertIn("<!-- hb-capability-end: -->", body)
        # Every marker occurrence is inside an HTML comment: a template that
        # somehow reaches a renderer unprocessed still ships a correct-looking
        # page, and the leftover is greppable rather than a missing section.
        outside_comments = re.sub(r"<!--.*?-->", "", body, flags=re.DOTALL)
        self.assertNotIn("hb-capability", outside_comments)


class MarkedTemplateInventoryTests(unittest.TestCase):
    def test_every_marked_section_names_a_known_capability(self) -> None:
        rules = (ROOT / "data" / "capability_page_rules.csv").read_text(encoding="utf-8")
        known = {line.split(",", 1)[0] for line in rules.splitlines()[1:] if line.strip()}
        marked = 0
        for path in sorted((ROOT / "docs" / "templates").rglob("*.rst")):
            for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                match = SECTION_BEGIN_RE.match(line)
                if not match:
                    continue
                marked += 1
                self.assertIn(
                    match.group("name"), known,
                    f"{path.relative_to(ROOT)}:{index} marks an unknown capability")
        self.assertGreater(marked, 0, "expected at least one marked template section")

    def test_every_marked_template_section_is_balanced(self) -> None:
        for path in sorted((ROOT / "docs" / "templates").rglob("*.rst")):
            text = path.read_text(encoding="utf-8")
            if "hb-capability" not in text:
                continue
            strip_capability_sections(
                text, model=None, region=None, data_dir=ROOT / "data",
                label=str(path.relative_to(ROOT)))


if __name__ == "__main__":
    unittest.main()
