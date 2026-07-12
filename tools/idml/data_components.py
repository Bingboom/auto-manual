"""Parse generated data-page LaTeX calls into renderer-neutral payloads.

The prepared RST bundle is the handoff source shared by LaTeX and InDesign.
Generated data pages currently expose their semantics as stable HB macros, so
this module decodes those calls once into ``manual-ir/v1`` data blocks.  It
does not read phase2 CSV files.
"""
from __future__ import annotations

import re
from typing import Any


def _read_braced_args(text: str, start: int, count: int) -> tuple[list[str], int]:
    args: list[str] = []
    cursor = start
    for _ in range(count):
        while cursor < len(text) and text[cursor] in " \t\n%":
            cursor += 1
        if cursor >= len(text) or text[cursor] != "{":
            break
        depth = 0
        end = cursor
        while end < len(text):
            if text[end] == "{":
                depth += 1
            elif text[end] == "}":
                depth -= 1
                if depth == 0:
                    break
            end += 1
        if depth != 0:
            break
        args.append(text[cursor + 1:end])
        cursor = end + 1
    return args, cursor


def _text(value: str) -> str:
    """Decode the narrow LaTeX vocabulary emitted by CSV page renderers."""
    value = re.sub(r"(?<!\\)%[^\n]*\n?", "", value)
    value = value.replace(r"\textasciitilde{}", "~")
    value = value.replace(r"\HBSpecMarkerOne{}", "①")
    value = value.replace(r"\HBSpecMultilineRowStrut{}", "")
    value = value.replace(r"\newline", "\n").replace(r"\par", "\n")
    value = value.replace(r"\textbullet", "•")
    value = re.sub(r"\\textbf\{([^{}]*)\}", r"\1", value)
    value = re.sub(r"\\text(?:sub|super)script\{([^{}]*)\}", r"\1", value)
    value = value.replace("~", " ").replace(r"\&", "&").replace(r"\%", "%")
    value = re.sub(r"\\[a-zA-Z@]+", " ", value)
    value = re.sub(r"[{}]", "", value)
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in value.splitlines()]
    return "\n".join(line for line in lines if line)


def _calls(text: str, macro: str, argc: int) -> list[list[str]]:
    found: list[list[str]] = []
    cursor = 0
    needle = "\\" + macro
    while True:
        start = text.find(needle, cursor)
        if start < 0:
            return found
        args, end = _read_braced_args(text, start + len(needle), argc)
        if len(args) == argc:
            found.append(args)
            cursor = end
        else:
            cursor = start + len(needle)


def _spec_payload(body: str) -> dict[str, Any] | None:
    start = body.find(r"\HBSpecPageStart")
    if start >= 0:
        sections = _calls(body[start:], "section", 1)
        return {"kind": "spec_start", "title": _text(sections[0][0]) if sections else ""}

    titles = _calls(body, "specsectiontitle", 1)
    if titles:
        labels = _calls(body, "HBTypeSpecLabel", 1)
        values = _calls(body, "HBTypeSpecValue", 1)
        return {
            "kind": "spec_section",
            "title": _text(titles[0][0]),
            "rows": [[_text(label[0]), _text(value[0])]
                     for label, value in zip(labels, values)],
        }

    notes = _calls(body, "HBTypeSpecNote", 1)
    if notes:
        return {"kind": "spec_annotations", "texts": [_text(note[0]) for note in notes]}
    return None


def _lcd_payload(body: str) -> dict[str, Any] | None:
    if r"\begin{HBLcdIconTable}" not in body:
        return None
    rows = []
    for number, figure, name, description in _calls(body, "HBLcdIconRow", 4):
        rows.append({
            "no": _text(number),
            "figure": figure.strip(),
            "name": _text(name),
            "desc": _text(description),
        })
    return {"kind": "lcd_icons", "rows": rows}


def _symbol_payload(body: str) -> dict[str, Any] | None:
    for macro in ("HBSymbolTable", "HBSymbolTwoColumnTablesSplit",
                  "HBSymbolTwoColumnTables"):
        pos = body.find("\\" + macro)
        if pos < 0:
            continue
        argc = 6 if macro.endswith("Split") else (4 if "TwoColumn" in macro else 3)
        args, _ = _read_braced_args(body, pos + len(macro) + 1, argc)
        if len(args) != argc:
            return None
        headers = [_text(args[0]), _text(args[1])]
        if macro == "HBSymbolTable":
            rows = [
                {"figure": figure.strip(), "label": _text(label), "text": _text(meaning)}
                for figure, label, meaning in _calls(args[2], "HBSymbolSignalRow", 3)
            ]
            return {"kind": "symbol_signals", "headers": headers, "rows": rows}
        groups = args[2:]
        rows = [
            {"figure": figure.strip(), "text": _text(meaning)}
            for group in groups
            for figure, meaning in _calls(group, "HBSymbolIconRow", 2)
        ]
        return {"kind": "symbol_icons", "headers": headers, "rows": rows}
    return None


def parse_data_component(body: str) -> dict[str, Any] | None:
    """Return a typed data-page payload for one raw LaTeX block."""
    return _lcd_payload(body) or _symbol_payload(body) or _spec_payload(body)


def is_data_plumbing(body: str) -> bool:
    """True for non-content wrappers that should not count as lost content."""
    stripped = re.sub(r"(?m)^\s*%.*$", "", body).strip()
    if not stripped:
        return True
    stripped = re.sub(r"\\HBApplyLang\{[^}]*\}", "", stripped).strip()
    return stripped in {
        r"\fi",
        r"\HBPageBreak",
        r"\HBPrefacePageEnd",
        r"\HBSpecPageEnd",
    }
