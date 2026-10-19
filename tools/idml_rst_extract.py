"""Prose extraction for the IDML exporter (M4b).

Parses the prepared bundle under docs/_build/<model>/<region>/<lang>/rst/page
(variables already substituted) into blocks the IDML writer can emit:

    ("h1"|"h2"|"h3"|"body"|"list", text)
    ("image", bundle-relative-path)

Design decisions:
- ``.. only:: latex`` bodies are taken (they carry the component macro
  calls); ``.. only:: not latex / html`` bodies are skipped — same branch
  selection as the PDF build.
- Known raw-latex component macros are *textualized* via their known
  signatures (\\safetywarning{...}, \\HBNoticeBlock{...}{...}{...} etc.) so
  designers get editable text instead of holes. Unknown raw content is
  counted and dropped (reported by the caller).
- RST comments are dropped with their whole indented body, as docutils does;
  a multi-line maintainer note must never reach the IDML stories as copy.
- This is intentionally a small hand-rolled parser for the bundle's rst
  subset, not docutils: the bundle uses sphinx-only directives (only) and
  raw component calls that docutils would reject or bury.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

try:
    from tools.component_specs.adapters import idml_notice_payload_from_legacy
    from tools.idml.extract_contract import EMITTED_COMPONENT_KINDS as EMITTED_COMPONENT_KINDS, ExtractResult, JSON_BLOCK_KINDS as _JSON_BLOCK_KINDS
    from tools.idml.latex_conditionals import active_lines
    from tools.idml.notice_labels import notice_label_variant
    from tools.idml.only_expr import matches_only_expr
    from tools.idml.semantic_containers import append_semantic_container
    from tools.idml_rst_extract_latex import _detex as _detex, _extract_raw_latex
    from tools.idml_rst_line_blocks import class_section, consume_line_structure, indented_body
    from tools.idml_rst_tables import (
        parse_grid_table as _parse_grid_table_impl,
        parse_list_table as _parse_list_table_impl,
    )
except ModuleNotFoundError:  # direct tools/export_idml.py execution
    from component_specs.adapters import idml_notice_payload_from_legacy  # type: ignore
    from idml.extract_contract import EMITTED_COMPONENT_KINDS as EMITTED_COMPONENT_KINDS, ExtractResult, JSON_BLOCK_KINDS as _JSON_BLOCK_KINDS  # type: ignore
    from idml.latex_conditionals import active_lines  # type: ignore
    from idml.notice_labels import notice_label_variant  # type: ignore
    from idml.only_expr import matches_only_expr  # type: ignore
    from idml.semantic_containers import append_semantic_container  # type: ignore
    from idml_rst_extract_latex import _detex as _detex, _extract_raw_latex  # type: ignore
    from idml_rst_line_blocks import class_section, consume_line_structure, indented_body  # type: ignore
    from idml_rst_tables import (  # type: ignore
        parse_grid_table as _parse_grid_table_impl,
        parse_list_table as _parse_list_table_impl,
    )



def _unescape_stars(value: object) -> object:
    """Unescape ``\\*`` recursively through JSON containers and strings."""
    if isinstance(value, str):
        return value.replace("\\*", "*")
    if isinstance(value, list):
        return [_unescape_stars(item) for item in value]
    if isinstance(value, dict):
        return {key: _unescape_stars(item) for key, item in value.items()}
    return value


def _unescape_rst_stars(kind: str, text: str) -> str:
    """Apply the ``\\*`` -> ``*`` unescape.

    Prose blocks are plain text, so the replace runs on the whole string. JSON
    blocks (``table`` / ``component``) carry a serialized payload where ``\\*``
    is already JSON-escaped as ``\\\\*``; a blind replace would collapse it to
    an invalid ``\\*`` escape and crash the downstream ``json.loads``. So decode,
    unescape inside the string values, and re-encode.
    """
    if kind not in _JSON_BLOCK_KINDS:
        return text.replace("\\*", "*")
    return json.dumps(_unescape_stars(json.loads(text)), ensure_ascii=False)


def _clean_rst_text(s: str) -> str:
    s = re.sub(r"\*\*([^*]+)\*\*", r"\1", s)
    # Inline sub/sup roles render as plain text; drop the escaped joiner too
    # (otherwise prose ships literal "V\ :sub:`oc`").
    s = re.sub(r"\\?\s*:(?:sub|sup):`([^`]*)`", r"\1", s)
    s = s.replace("\\ ", "")
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def _notice_from_list_table(rows: list[list[str]]) -> dict | None:
    """Detect single-row list-table blocks used as HBNoticeBlock fallbacks."""
    if len(rows) != 1 or len(rows[0]) < 2:
        return None
    row = rows[0]
    label_variant = notice_label_variant(_clean_rst_text(row[0]))
    if label_variant is None:
        return None
    label, variant = label_variant
    texts = []
    list_like = len(row) > 2
    for cell in row[1:]:
        lines = [line.strip() for line in cell.splitlines() if line.strip()]
        has_bullets = any(line.startswith("- ") for line in lines)
        if not has_bullets:
            text = _clean_rst_text(cell).strip()
            if text:
                texts.append(text)
            continue
        list_like = list_like or has_bullets
        cell_texts: list[str] = []
        for line in lines:
            if line.startswith("- "):
                text = _clean_rst_text(line[2:]).strip()
                if text:
                    cell_texts.append(text)
            elif cell_texts and has_bullets:
                continuation = _clean_rst_text(line).strip()
                if continuation:
                    cell_texts[-1] = f"{cell_texts[-1]} {continuation}"
            else:
                text = _clean_rst_text(line).strip()
                if text:
                    cell_texts.append(text)
        texts.extend(cell_texts)
    if not texts:
        return None
    return idml_notice_payload_from_legacy(
        {"kind": "notice", "label": label, "variant": variant,
         "texts": texts, "list": list_like},
        source_ref="rst:list-table",
    )


def _is_signal_word_definition_table(rows: list[list[str]]) -> bool:
    """Keep complete, distinct signal-word definitions as an ordered table."""
    if len(rows) < 2 or any(
        len(row) != 2 or not _clean_rst_text(row[1]) for row in rows
    ):
        return False
    labels = [notice_label_variant(_clean_rst_text(row[0])) for row in rows]
    return all(label is not None for label in labels) and len(set(labels)) == len(labels)


# ---------------------------------------------------------------------------
# page parser
# ---------------------------------------------------------------------------

def _only_matches(expr: str, tags: set[str]) -> bool:
    """Evaluate Sphinx-style bare-tag boolean expressions without ``eval``."""
    return matches_only_expr(expr, tags)


_DIRECTIVE = re.compile(r"\.\.\s+(class|container|only|raw|image|list-table)::\s*(.*)")


def _append_manual_ir(body: list[str], result: ExtractResult) -> None:
    try:
        payload = json.loads("\n".join(line.strip() for line in body))
    except json.JSONDecodeError:
        result.skipped_raw += 1
    else:
        if isinstance(payload, dict) and payload.get("kind"):
            result.blocks.append(("data", json.dumps(payload, ensure_ascii=False)))
        else:
            result.skipped_raw += 1


def _append_only_body(arg: str, body: list[str], tags: set[str], result: ExtractResult) -> None:
    if not _only_matches(arg, tags):
        return  # non-matching branches are the PDF-skipped side: drop
    # re-parse the body as page content (dedented)
    dedent = min((len(b) - len(b.lstrip()) for b in body if b.strip()), default=0)
    sub = "\n".join(b[dedent:] for b in body)
    inner = _parse_text(sub, tags)
    result.blocks.extend(inner.blocks)
    result.skipped_raw += inner.skipped_raw
    result.twocol = result.twocol or inner.twocol


def _append_list_table(body: list[str], result: ExtractResult) -> None:
    rows = _parse_list_table(body)
    notice = _notice_from_list_table(rows)
    if notice is not None:
        result.blocks.append(("component", json.dumps(notice, ensure_ascii=False)))
    elif rows:
        first_cell = _clean_rst_text(rows[0][0]) if rows[0] else ""
        if (
            notice_label_variant(first_cell) is not None
            and not _is_signal_word_definition_table(rows)
        ):
            raise ValueError(
                "known notice label cannot fall back to a generic "
                f"table: {first_cell!r}"
            )
        result.blocks.append(("table", json.dumps(rows, ensure_ascii=False)))
    else:
        result.skipped_raw += 1


def _consume_directive(
    lines: list[str], i: int, directive: str, arg: str, tags: set[str], result: ExtractResult,
) -> int:
    """Handle a top-level directive at ``lines[i]``; return the index after its body."""
    body, i2 = indented_body(lines, i + 1, 0)
    if directive == "raw" and arg == "latex":
        _extract_raw_latex("\n".join(body), result)
    elif directive == "raw" and arg == "manual-ir":
        _append_manual_ir(body, result)
    elif directive == "only":
        _append_only_body(arg, body, tags, result)
    elif directive == "container":
        append_semantic_container(result, arg, body, tags, _parse_text)
    elif directive == "class":
        section, section_end = class_section(lines, i + 1)
        if section:
            append_semantic_container(result, arg, section, tags, _parse_text)
            i2 = section_end
    elif directive == "image":
        result.blocks.append(("image", arg))
    elif directive == "list-table":
        _append_list_table(body, result)
    return i2


def extract_page(path: Path, tags: set[str] | None = None) -> ExtractResult:
    tags = tags if tags is not None else {"latex"}
    result = ExtractResult()
    from tools.rst_inline import collect_substitutions, expand_payload

    lines, substitutions = collect_substitutions(
        active_lines(path.read_text(encoding="utf-8").splitlines(), tags)
    )
    i = 0
    while i < len(lines):
        line = lines[i]
        m = _DIRECTIVE.match(line.strip())
        if m and len(line) == len(line.lstrip()):
            i = _consume_directive(lines, i, m.group(1), m.group(2).strip(), tags, result)
        else:
            i = consume_line_structure(lines, i, result.blocks)

    result.blocks = [(k, _unescape_rst_stars(k, t)) for k, t in result.blocks if t.strip()]
    result.blocks = [(k, json.dumps(expand_payload(json.loads(t), substitutions), ensure_ascii=False)
                      if k in _JSON_BLOCK_KINDS else expand_payload(t, substitutions))
                     for k, t in result.blocks]
    return result


def _parse_text(text: str, tags: set[str] | None = None) -> ExtractResult:
    """Parse a dedented rst fragment (used for matching only:: bodies)."""
    import tempfile
    import os
    fd, tmp = tempfile.mkstemp(suffix=".rst")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        return extract_page(Path(tmp), tags)
    finally:
        os.unlink(tmp)


def bundle_page_order(bundle_root: Path) -> list[Path]:
    """Page files in reading order, from the bundle index toctree/includes."""
    index = bundle_root / "index.rst"
    order: list[Path] = []
    if index.exists():
        for m in re.finditer(r"\.\.\s+include::\s+(page/\S+)", index.read_text(encoding="utf-8")):
            p = bundle_root / m.group(1)
            if not p.is_file():
                raise ValueError(f"{index}: included page is missing or not a file: {m.group(1)}")
            order.append(p)
    return order
def _parse_grid_table(grid: list[str]) -> list[list[str]]:
    """Parse an rst grid table block into row cell-text lists."""
    return _parse_grid_table_impl(grid)

def _parse_list_table(body: list[str]) -> list[list[str]]:
    """Parse a list-table directive body into row cell-text lists."""
    return _parse_list_table_impl(body)
