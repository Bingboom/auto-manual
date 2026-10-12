"""RST comments must not reach the IDML extraction.

``tools/idml_rst_extract.py`` skipped only a comment's ``..`` marker line. The
comment's indented body does not start with ``..``, so the paragraph branch
emitted it as body copy: the #1297 note on the JE-1000H 140 W USB-C rating in
``docs/templates/page_eu-<lang>/05_operation_guide_placeholder.rst`` printed
in the JE-2000F/EU de IDML story, and every other multi-line template comment
(TOC, warranty, extra-battery and troubleshooting carriers) leaked the same way.

The extractor now ends a comment where docutils does: the body is every
following line that is blank or indented deeper than the marker. docutils is
the oracle throughout -- each sample is classified by docutils before the
extractor is asked about it, and the repo scan finds the comments by parsing
the templates with docutils, not with the extractor's own rule.
"""

from __future__ import annotations

import json
import re
import tempfile
import unittest
from pathlib import Path

from docutils import nodes
from docutils.core import publish_doctree
from docutils.parsers.rst import Directive, directives
from sphinx.util.docutils import docutils_namespace

from tools.idml_rst_extract import extract_page

ROOT = Path(__file__).resolve().parents[1]
# The ManualIR tag set of a JE-2000F/EU de page (tools/manual_ir/prepared_rst.py).
TAGS = {"latex", "idml", "region_eu", "model_je_2000f", "lang_de"}
PROBE = "QZX probe line that must not ship"
_JSON_KINDS = {"component", "data", "semantic", "table"}
_LIST_MARKER = re.compile(r"^(?:[-*•–]\s+)+")


def blocks_for(source: str, tags: set[str] = TAGS) -> list[tuple[str, str]]:
    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "page.rst"
        page.write_text(source, encoding="utf-8")
        return list(extract_page(page, tags).blocks)


def extracted_text(blocks: list[tuple[str, str]]) -> str:
    """Every string the extractor emitted, JSON payloads decoded."""

    def strings(value: object):
        if isinstance(value, str):
            yield value
        elif isinstance(value, list):
            for item in value:
                yield from strings(item)
        elif isinstance(value, dict):
            for item in value.values():
                yield from strings(item)

    return "\n".join(
        text
        for kind, payload in blocks
        for text in strings(json.loads(payload) if kind in _JSON_KINDS else payload)
    )


class _OnlyBody(Directive):
    """Sphinx's ``only`` without a Sphinx app: parse the body whatever the tags."""

    has_content = True
    required_arguments = 1
    final_argument_whitespace = True

    def run(self) -> list[nodes.Node]:
        node = nodes.container()
        self.state.nested_parse(self.content, self.content_offset, node)
        return [node]


def docutils_tree(source: str) -> nodes.document:
    with docutils_namespace():
        directives.register_directive("only", _OnlyBody)
        return publish_doctree(source, settings_overrides={
            "report_level": 5,
            "halt_level": 5,
            "warning_stream": False,
            "file_insertion_enabled": False,
            "doctitle_xform": False,
        })


def probe_source(first_line: str) -> str:
    return f"{first_line}\n   {PROBE}\n\nAfter.\n"


# Explicit markup docutils parses as a comment: none of footnote, citation,
# hyperlink target, substitution definition or directive matches.
COMMENT_FORMS = (
    ".. A maintainer note",
    "..  Two spaces after the marker",
    ".. hb-capability-begin: LED照明灯",
    ".. TODO(内容团队): 加电包扩容章节骨架",
    ".. [not a label] because of the space",
    ".. [a/b] is no citation label",
    ".. _ a spaced underscore is no target",
    ".. | a spaced bar is no substitution",
    ".. name: : one colon is no directive",
    ".. ::",
    "..",
)

# Explicit markup docutils parses as something else. The extractor has no
# branch for these, so the marker line is skipped and the indented line
# after it ships as body text -- admonition bodies are real copy. Exactly
# what main emitted; the comment rule must leave all of it alone.
NON_COMMENT_FORMS = (
    ".. note::",
    ".. warning::",
    ".. caution::",
    ".. tip::",
    ".. unknown-directive:: argument",
    ".. name ::",
    ".. [1] Numbered footnote",
    ".. [#] Auto-numbered footnote",
    ".. [#label] Labelled footnote",
    ".. [*] Symbol footnote",
    ".. [CIT2002] Citation",
    ".. _target: https://example.com/",
    ".. __: https://example.com/anonymous",
    ".. _`phrase target`: https://example.com/phrase",
    ".. |mark| unicode:: U+2122",
)


class CommentsAreDropped(unittest.TestCase):
    def test_every_comment_form_drops_its_indented_body(self) -> None:
        for first_line in COMMENT_FORMS:
            with self.subTest(first_line=first_line):
                tree = docutils_tree(probe_source(first_line))
                self.assertIsInstance(tree.children[0], nodes.comment)
                self.assertIn(PROBE, tree.children[0].astext())
                self.assertEqual([("body", "After.")], blocks_for(probe_source(first_line)))

    def test_multi_line_note_between_copy_is_dropped(self) -> None:
        """The #1297 shape: a wrapped maintainer note between two pieces of copy."""
        blocks = blocks_for(
            "| **Aus**\n"
            "| Einmal drücken\n"
            "\n"
            ".. The JE-1000H print (EU-UK V2.0-2026-08-03, PDF page 63) rates its high-power\n"
            "   USB-C port at 140 W and adds the 28 V/5 A cable rating; each model follows its\n"
            "   own print.\n"
            "\n"
            ".. only:: not model_je_1000h\n"
            "\n"
            "   Der USB-C-100-W-Anschluss ist ein Hochleistungs-Ausgangsanschluss.\n"
            "\n"
            "| Das Produkt kann Ihre Fahrzeugbatterie aufladen.\n"
        )
        self.assertEqual(
            [
                ("body", "**Aus**\nEinmal drücken"),
                ("body", "Der USB-C-100-W-Anschluss ist ein Hochleistungs-Ausgangsanschluss."),
                ("body", "Das Produkt kann Ihre Fahrzeugbatterie aufladen."),
            ],
            blocks,
        )

    def test_comment_body_continues_past_a_blank_line(self) -> None:
        """A non-empty comment keeps every deeper-indented paragraph (the French warranty note)."""
        source = (
            ".. First paragraph of the note\n"
            "   wraps here.\n"
            "\n"
            "   Second paragraph of the same note.\n"
            "\n"
            "WARRANTY\n"
            "========\n"
        )
        self.assertEqual(
            "First paragraph of the note\nwraps here.\n\nSecond paragraph of the same note.",
            docutils_tree(source).children[0].astext(),
        )
        self.assertEqual([("h1", "WARRANTY")], blocks_for(source))

    def test_comment_inside_a_selected_branch_is_dropped(self) -> None:
        for directive in (".. only:: latex", ".. container:: hb-note"):
            with self.subTest(directive=directive):
                blocks = blocks_for(
                    f"{directive}\n"
                    "\n"
                    "   .. A note inside the branch\n"
                    "      that wraps.\n"
                    "\n"
                    "   Branch paragraph.\n"
                )
                self.assertEqual([("body", "Branch paragraph.")], blocks)

    def test_german_operation_guide_carrier_keeps_its_copy_only(self) -> None:
        carrier = ROOT / "docs/templates/page_eu-de/05_operation_guide_placeholder.rst"
        for model, usb_c, car_12v in (
            ("je_2000f", "USB-C-100-W-Anschluss", "Der DC-12-V-Anschluss ist nur"),
            ("je_1000h", "USB-C-140-W-Anschluss", "Der Zigarettenanzünderanschluss ist nur"),
        ):
            with self.subTest(model=model):
                tags = {"latex", "idml", "region_eu", f"model_{model}", "lang_de"}
                text = extracted_text(list(extract_page(carrier, tags).blocks))
                self.assertIn(usb_c, text)
                self.assertIn(car_12v, text)
                self.assertNotIn("each model follows its own print", text)
                self.assertNotIn("USB-C port at 140 W", text)
                self.assertNotIn("this 12 V caution differently", text)


class CommentEndsWhereDocutilsEndsIt(unittest.TestCase):
    def test_dedented_paragraph_right_after_the_body_is_kept(self) -> None:
        source = ".. A note\n   that wraps.\nParagraph right after.\n"
        tree = docutils_tree(source)
        self.assertEqual("A note\nthat wraps.", tree.children[0].astext())
        self.assertEqual([("body", "Paragraph right after.")], blocks_for(source))

    def test_dedented_paragraph_after_a_blank_line_is_kept(self) -> None:
        source = ".. A note\n   that wraps.\n\nParagraph after a blank line.\n\n- bullet item\n"
        self.assertEqual(
            [("body", "Paragraph after a blank line."), ("list", "• bullet item")],
            blocks_for(source),
        )

    def test_following_explicit_markup_at_the_marker_column_is_kept(self) -> None:
        source = (
            ".. A note\n"
            "   that wraps.\n"
            ".. image:: asset:operation/demo\n"
            "\n"
            "Caption paragraph.\n"
        )
        self.assertEqual(
            [("image", "asset:operation/demo"), ("body", "Caption paragraph.")],
            blocks_for(source),
        )


class EmptyComment(unittest.TestCase):
    def test_bare_marker_then_blank_line_keeps_the_indented_block(self) -> None:
        """docutils' "tiny but practical wart": the empty comment ends at once."""
        source = "..\n\n   Block quote after an empty comment.\n"
        tree = docutils_tree(source)
        self.assertIsInstance(tree.children[0], nodes.comment)
        self.assertEqual("", tree.children[0].astext())
        self.assertIsInstance(tree.children[1], nodes.block_quote)
        self.assertEqual([("body", "Block quote after an empty comment.")], blocks_for(source))

    def test_bare_marker_with_its_body_on_the_next_line_is_dropped(self) -> None:
        source = "..\n   Comment body on the next line.\n\nParagraph.\n"
        self.assertEqual("Comment body on the next line.", docutils_tree(source).children[0].astext())
        self.assertEqual([("body", "Paragraph.")], blocks_for(source))

    def test_bare_marker_at_end_of_file(self) -> None:
        self.assertEqual([("body", "Paragraph.")], blocks_for("Paragraph.\n\n.."))


class OtherExplicitMarkupIsUnaffected(unittest.TestCase):
    def test_non_comment_constructs_keep_their_existing_output(self) -> None:
        for first_line in NON_COMMENT_FORMS:
            with self.subTest(first_line=first_line):
                tree = docutils_tree(probe_source(first_line))
                self.assertNotIsInstance(tree.children[0], nodes.comment)
                self.assertEqual(
                    [("body", PROBE), ("body", "After.")],
                    blocks_for(probe_source(first_line)),
                )

    def test_handled_directives_and_substitutions(self) -> None:
        source = (
            "Intro paragraph.\n"
            "\n"
            ".. image:: asset:operation/demo\n"
            "   :alt: Demo.\n"
            "   :width: 360px\n"
            "\n"
            ".. only:: latex\n"
            "\n"
            "   Print-only paragraph.\n"
            "\n"
            ".. only:: not latex\n"
            "\n"
            "   Web-only paragraph.\n"
            "\n"
            ".. list-table::\n"
            "   :header-rows: 1\n"
            "\n"
            "   * - Button\n"
            "     - Action\n"
            "   * - POWER\n"
            "     - Press once\n"
            "\n"
            ".. |unit| replace:: 140 W\n"
            "\n"
            "Rated |unit| output.\n"
            "\n"
            ".. container:: hb-note\n"
            "\n"
            "   Container paragraph.\n"
            "\n"
            "Closing paragraph.\n"
        )
        self.assertEqual(
            [
                ("body", "Intro paragraph."),
                ("image", "asset:operation/demo"),
                ("body", "Print-only paragraph."),
                ("table", json.dumps([["Button", "Action"], ["POWER", "Press once"]], ensure_ascii=False)),
                ("body", "Rated 140 W output."),
                ("body", "Container paragraph."),
                ("body", "Closing paragraph."),
            ],
            blocks_for(source),
        )


def comment_lines(comments: list[str]) -> list[str]:
    lines = []
    for comment in comments:
        for line in comment.splitlines():
            text = _LIST_MARKER.sub("", line.strip())
            if len(text) >= 10:
                lines.append(text)
    return lines


class RepoTemplates(unittest.TestCase):
    def test_no_template_comment_reaches_the_extraction(self) -> None:
        """No line of a docutils comment may appear in the extraction more often
        than the source prints it outside comments (a comment line can repeat
        real copy, e.g. a key-combination row fenced by a capability sentinel)."""
        self.maxDiff = None
        sources = sorted(
            path
            for tree in ("docs/templates", "docs/_review")
            for path in (ROOT / tree).rglob("*.rst")
        )
        self.assertGreater(len(sources), 100)
        commented, multi_line, leaks = 0, 0, set()
        for path in sources:
            source = path.read_text(encoding="utf-8")
            comments = [c.astext() for c in docutils_tree(source).findall(nodes.comment)]
            lines = comment_lines(comments)
            if not lines:
                continue
            commented += 1
            multi_line += any("\n" in comment for comment in comments)
            for tags in ({"latex"}, TAGS):
                text = extracted_text(list(extract_page(path, tags).blocks))
                for line in lines:
                    outside = source.count(line) - sum(comment.count(line) for comment in comments)
                    if text.count(line) > outside:
                        leaks.add(f"{path.relative_to(ROOT)}: {line}")
        # The scan must actually see comments, multi-line ones included.
        self.assertGreater(commented, 10)
        self.assertGreater(multi_line, 5)
        self.assertEqual([], sorted(leaks))


if __name__ == "__main__":
    unittest.main()
