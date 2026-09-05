"""Portable inline content in the prepared-RST projection.

Resolve definitions after tables are sliced, so replacing a short token with
a long value cannot move grid borders. Images use ordinary Markdown image
syntax, shared by the editable flow artifact and production renderer.
"""
from __future__ import annotations

import re

IMAGE = re.compile(r"!\[([^\]]*)\]\(([^\s)]+)\)")
_DEFINITION = re.compile(r"^\.\.\s+\|([^|]+)\|\s+(replace|image)::\s*(.*)$")
_REFERENCE = re.compile(r"\|([^|\n]+)\|")
_CELL_IMAGE = re.compile(r"^\.\.\s+image::\s*(\S+)(?:\s+:(?:alt|width|height|align):.*)?$", re.S)


def collect_substitutions(lines: list[str]) -> tuple[list[str], dict[str, str]]:
    remaining: list[str] = []
    definitions: dict[str, str] = {}
    i = 0
    while i < len(lines):
        match = _DEFINITION.match(lines[i])
        if match is None:
            remaining.append(lines[i])
            i += 1
            continue
        name, kind, value = match.groups()
        body: list[str] = []
        i += 1
        while i < len(lines) and (not lines[i].strip() or lines[i][:1].isspace()):
            body.append(lines[i].strip())
            i += 1
        if kind == "image":
            alt = next((line[5:].strip() for line in body if line.startswith(":alt:")), "")
            definitions[name] = f"![{alt}]({value})"
        else:
            definitions[name] = " ".join([value, *[line for line in body if line]]).strip()
        remaining.append("")
    return remaining, definitions


def expand_payload(value, definitions: dict[str, str]):
    if isinstance(value, list):
        return [expand_payload(item, definitions) for item in value]
    if isinstance(value, dict):
        return {key: expand_payload(item, definitions) for key, item in value.items()}
    if not isinstance(value, str):
        return value
    image = _CELL_IMAGE.fullmatch(value.strip())
    if image:
        return f"![]({image.group(1)})"

    def resolve(text: str, seen: frozenset[str]) -> str:
        def replace(match: re.Match) -> str:
            name = match.group(1)
            if name not in definitions:
                return match.group(0)
            if name in seen:
                raise ValueError(f"cyclic RST substitution: {name}")
            return resolve(definitions[name], seen | {name})
        return _REFERENCE.sub(replace, text)

    return resolve(value, frozenset())
