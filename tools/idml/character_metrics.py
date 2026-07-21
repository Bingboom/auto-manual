"""Native-import-safe character metric overrides for IDML text runs."""
from __future__ import annotations

import re


def with_character_metrics(
    xml: str,
    *,
    point_size: float,
    leading: float,
) -> str:
    """Apply native-import-safe point size and leading to text runs.

    InDesign accepts ``PointSize`` on ``CharacterStyleRange`` but silently
    ignores a numeric ``Leading`` attribute there (and on the enclosing
    paragraph range).  Native round-tripping serializes leading as a unit
    property instead.  Rewrite every content-bearing run so symbol fallback
    runs receive the same compact metrics while paragraph-break-only runs stay
    untouched.
    """
    pattern = re.compile(
        r'<CharacterStyleRange (?P<attrs>[^>]*)>'
        r'(?P<body>.*?)</CharacterStyleRange>',
        re.S,
    )

    def rewrite(match: re.Match[str]) -> str:
        body = match.group("body")
        if "<Content>" not in body:
            return match.group(0)
        attrs = re.sub(r'\s+PointSize="[^"]*"', "", match.group("attrs"))
        attrs = re.sub(r'\s+Leading="[^"]*"', "", attrs)
        leading_xml = f'<Leading type="unit">{leading:g}</Leading>'
        if "<Properties>" in body:
            body = body.replace("<Properties>", "<Properties>" + leading_xml, 1)
        else:
            body = f"<Properties>{leading_xml}</Properties>" + body
        return (
            f'<CharacterStyleRange {attrs} PointSize="{point_size:g}">'
            f"{body}</CharacterStyleRange>"
        )

    return pattern.sub(rewrite, xml)
