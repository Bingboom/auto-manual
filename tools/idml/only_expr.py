"""Small fail-closed evaluator for Sphinx ``only`` tag expressions."""
from __future__ import annotations

import re


def matches_only_expr(expr: str, tags: set[str]) -> bool:
    """Evaluate bare-tag boolean expressions without executing source text."""

    tokens = re.findall(r"\(|\)|\b(?:and|or|not)\b|[A-Za-z0-9_-]+", expr)
    compact_source = re.sub(r"\s+", "", expr)
    if "".join(tokens) != compact_source:
        return False
    cursor = 0

    def parse_atom() -> bool:
        nonlocal cursor
        if cursor >= len(tokens):
            raise ValueError("missing only-expression operand")
        token = tokens[cursor]
        if token == "(":
            cursor += 1
            value = parse_or()
            if cursor >= len(tokens) or tokens[cursor] != ")":
                raise ValueError("unclosed only-expression group")
            cursor += 1
            return value
        if token in {"and", "or", "not", ")"}:
            raise ValueError("invalid only-expression operand")
        cursor += 1
        return token in tags

    def parse_not() -> bool:
        nonlocal cursor
        if cursor < len(tokens) and tokens[cursor] == "not":
            cursor += 1
            return not parse_not()
        return parse_atom()

    def parse_and() -> bool:
        nonlocal cursor
        value = parse_not()
        while cursor < len(tokens) and tokens[cursor] == "and":
            cursor += 1
            rhs = parse_not()
            value = value and rhs
        return value

    def parse_or() -> bool:
        nonlocal cursor
        value = parse_and()
        while cursor < len(tokens) and tokens[cursor] == "or":
            cursor += 1
            rhs = parse_and()
            value = value or rhs
        return value

    if not tokens:
        return False
    try:
        result = parse_or()
    except ValueError:
        return False
    return result if cursor == len(tokens) else False


__all__ = ["matches_only_expr"]
