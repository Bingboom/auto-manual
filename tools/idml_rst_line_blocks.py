"""Line-structure steps of the IDML prose extractor's hand-rolled RST scanner.

``tools.idml_rst_extract.extract_page`` walks a page line by line. Directives
(which may recurse into ``_parse_text``) stay there; the plain line structures
-- comments, section titles, grid tables, line blocks, bullet and enumerated
lists, paragraphs -- live here. Each ``_consume_*`` step looks at ``lines[i]``
and either returns the index after what it consumed (appending to ``blocks``)
or ``None`` when the line is not its construct, so the next step is tried.
"""
from __future__ import annotations

import re
from typing import Callable

try:
    from tools.idml_rst_tables import parse_grid_table
except ModuleNotFoundError:  # direct tools/export_idml.py execution
    from idml_rst_tables import parse_grid_table  # type: ignore

Blocks = list[tuple[str, str]]

UNDERLINES = {"=": "h1", "-": "h2", "~": "h3", "^": "h3"}
_LEVELS = {"=": 1, "-": 2, "~": 3, "^": 3}

ENUMERATED_ITEM = re.compile(r"^\d{1,2}[.)]\s+\S")

# An RST comment is explicit markup (``..`` then whitespace, or a bare ``..``)
# that is not a footnote, citation, hyperlink target, substitution definition
# or directive -- the same patterns docutils' ``Body.explicit_construct`` tries
# before falling back to ``Body.comment``.
_SIMPLENAME = r"(?:(?!_)\w)+(?:[-._+:](?:(?!_)\w)+)*"
_EXPLICIT_MARKUP = re.compile(r"\.\.(?:[ \t]+|$)")
_NOT_A_COMMENT = re.compile(
    r"\.\.[ \t]+(?:"
    rf"\[(?:[0-9]+|#(?:{_SIMPLENAME})?|\*|{_SIMPLENAME})\](?:[ \t]+|$)"  # footnote, citation
    r"|_(?![ \t]|$)"  # hyperlink target, anonymous ``.. __:`` included
    r"|\|(?![ \t]|$)"  # substitution definition
    rf"|{_SIMPLENAME}[ \t]?::(?:[ \t]+|$)"  # directive
    r")"
)


def is_rst_comment(stripped: str) -> bool:
    """True when a stripped line opens an RST comment."""
    return bool(_EXPLICIT_MARKUP.match(stripped)) and not _NOT_A_COMMENT.match(stripped)


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip())


def indented_body(lines: list[str], start: int, base_indent: int) -> tuple[list[str], int]:
    """Lines indented deeper than ``base_indent`` from ``start`` (trailing blanks dropped)."""
    out: list[str] = []
    k = start
    n = len(lines)
    while k < n:
        line = lines[k]
        if not line.strip():
            out.append("")
            k += 1
            continue
        if _indent(line) <= base_indent:
            break
        out.append(line)
        k += 1
    while out and not out[-1].strip():
        out.pop()
    return out, k


def _section_level(lines: list[str], k: int) -> int | None:
    """Heading level when ``lines[k]`` is a top-level title underlined on ``lines[k + 1]``."""
    underline = lines[k + 1].strip()
    if (
        _indent(lines[k]) != 0
        or not underline
        or len(set(underline)) != 1
        or underline[0] not in UNDERLINES
    ):
        return None
    return _LEVELS[underline[0]]


def _ends_section(lines: list[str], end: int, level: int) -> bool:
    candidate = lines[end]
    stripped_candidate = candidate.strip()
    if _indent(candidate) != 0:
        return False
    if stripped_candidate.startswith(".. class::"):
        return True
    if not stripped_candidate or end + 1 >= len(lines):
        return False
    next_underline = lines[end + 1].strip()
    return bool(
        next_underline
        and len(set(next_underline)) == 1
        and next_underline[0] in UNDERLINES
        and _LEVELS[next_underline[0]] <= level
    )


def class_section(lines: list[str], start: int) -> tuple[list[str], int]:
    """Return the top-level section targeted by an RST ``class`` directive.

    Docutils applies ``.. class::`` to the next element.  Warranty sources
    use that standard form so their headings remain real section nodes for
    every renderer, while the IDML extractor preserves the same semantic
    component payload previously carried by a container directive.
    """

    n = len(lines)
    k = start
    while k < n and not lines[k].strip():
        k += 1
    if k + 1 >= n:
        return [], k
    level = _section_level(lines, k)
    if level is None:
        return [], k
    end = k + 2
    while end < n and not _ends_section(lines, end, level):
        end += 1
    return lines[k:end], end


def _skip_comment(lines: list[str], i: int, blocks: Blocks) -> int | None:
    # A comment's body is every following line that is blank or indented
    # deeper than its ``..`` marker; it ends at the first non-blank line at or
    # left of the marker (docutils ``Body.comment``). Skipping only the marker
    # line let the indented body fall through to the paragraph branch and ship
    # as body copy. A bare ``..`` followed by a blank line is an empty comment
    # that ends there, so an indented block after it stays content (docutils'
    # "tiny but practical wart").
    stripped = lines[i].strip()
    if not is_rst_comment(stripped):
        return None
    indent = _indent(lines[i])
    n = len(lines)
    i += 1
    if stripped != ".." or (i < n and lines[i].strip()):
        while i < n and (not lines[i].strip() or _indent(lines[i]) > indent):
            i += 1
    return i


def _consume_heading(lines: list[str], i: int, blocks: Blocks) -> int | None:
    stripped = lines[i].strip()
    if not stripped or i + 1 >= len(lines):
        return None
    under = lines[i + 1].strip()
    if under and len(under) >= max(3, len(stripped) - 2) \
            and len(set(under)) == 1 and under[0] in UNDERLINES:
        blocks.append((UNDERLINES[under[0]], stripped))
        return i + 2
    return None


def _consume_grid_table(lines: list[str], i: int, blocks: Blocks) -> int | None:
    """rst grid tables (+---+ borders) -> ("table", json rows)."""
    import json as _json

    if not re.match(r"\+-[-+]*-\+$", lines[i].strip()):
        return None
    grid = [lines[i].rstrip()]
    k = i + 1
    n = len(lines)
    while k < n and (lines[k].strip().startswith("|") or
                     re.match(r"\+[=+| \-]+[+|]$", lines[k].strip())):
        grid.append(lines[k].rstrip())
        k += 1
    rows = parse_grid_table(grid)
    if not rows:
        return None
    blocks.append(("table", _json.dumps(rows, ensure_ascii=False)))
    return k


def _consume_line_block(lines: list[str], i: int, blocks: Blocks) -> int | None:
    if not lines[i].strip().startswith("| "):
        return None
    buf = []
    n = len(lines)
    while i < n and lines[i].strip().startswith("|"):
        buf.append(lines[i].strip()[1:].strip())
        i += 1
    text = "\n".join(b for b in buf if b)
    if text:
        blocks.append(("body", text))
    return i


def _consume_bullet(lines: list[str], i: int, blocks: Blocks) -> int | None:
    stripped = lines[i].strip()
    if not stripped.startswith("- "):
        return None
    indent = _indent(lines[i])
    item = [stripped[2:]]
    i += 1
    n = len(lines)
    while i < n and lines[i].strip() and not lines[i].strip().startswith("- ") \
            and _indent(lines[i]) >= 2:
        item.append(lines[i].strip())
        i += 1
    nested = indent >= 2
    blocks.append((
        "sublist" if nested else "list",
        ("– " if nested else "• ") + " ".join(item),
    ))
    return i


def _consume_enumerated(lines: list[str], i: int, blocks: Blocks) -> int | None:
    # Without this step `1. ` falls into the paragraph step, which greedily
    # absorbs any following line that does not start with a bullet, a line
    # block or a directive -- so `2. ` joins the first item and the whole list
    # ships as one paragraph. The printed books set these as separate numbered
    # lines, and the enumerator is part of the copy, so it is kept rather than
    # replaced with a marker.
    stripped = lines[i].strip()
    if not ENUMERATED_ITEM.match(stripped):
        return None
    indent = _indent(lines[i])
    item = [stripped]
    i += 1
    n = len(lines)
    while (
        i < n
        and lines[i].strip()
        and not ENUMERATED_ITEM.match(lines[i].strip())
        and not lines[i].strip().startswith(("- ", "|", ".."))
        and _indent(lines[i]) >= 2
    ):
        item.append(lines[i].strip())
        i += 1
    blocks.append((
        "sublist" if indent >= 2 else "list",
        " ".join(item),
    ))
    return i


def _consume_paragraph(lines: list[str], i: int, blocks: Blocks) -> int | None:
    stripped = lines[i].strip()
    if not stripped or stripped.startswith(".."):
        return None
    para = [stripped]
    i += 1
    n = len(lines)
    while i < n and lines[i].strip() and not lines[i].strip().startswith(("|", "- ", "..")):
        nxt_line = lines[i].strip()
        if i + 1 < n:
            under = lines[i + 1].strip()
            if under and len(set(under)) == 1 and under[0] in UNDERLINES:
                break
        para.append(nxt_line)
        i += 1
    blocks.append(("body", " ".join(para)))
    return i


_LINE_STEPS: tuple[Callable[[list[str], int, Blocks], int | None], ...] = (
    _skip_comment,
    _consume_heading,
    _consume_grid_table,
    _consume_line_block,
    _consume_bullet,
    _consume_enumerated,
    _consume_paragraph,
)


def consume_line_structure(lines: list[str], i: int, blocks: Blocks) -> int:
    """Consume the non-directive construct at ``lines[i]``; return the next index."""
    for step in _LINE_STEPS:
        nxt = step(lines, i, blocks)
        if nxt is not None:
            return nxt
    return i + 1
