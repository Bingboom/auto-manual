#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import ast
import re


def _normalize_only_tag(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def _build_word_only_tags(*, model: str | None, region: str | None, lang: str | None) -> set[str]:
    tags = {"html"}
    if isinstance(model, str) and model.strip():
        tags.add(f"model_{_normalize_only_tag(model)}")
    if isinstance(region, str) and region.strip():
        tags.add(f"region_{_normalize_only_tag(region)}")
    if isinstance(lang, str) and lang.strip():
        tags.add(f"lang_{_normalize_only_tag(lang)}")
    return tags


def _evaluate_only_expression(expression: str, active_tags: set[str]) -> bool:
    normalized = expression.strip()
    if not normalized:
        return False

    try:
        tree = ast.parse(normalized, mode="eval")
    except SyntaxError as exc:
        raise RuntimeError(f"Invalid only expression: {expression}") from exc

    tags = {tag.strip().lower() for tag in active_tags if tag.strip()}

    def _eval(node: ast.AST) -> bool:
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Name):
            ident = node.id.lower()
            if ident == "true":
                return True
            if ident == "false":
                return False
            return ident in tags
        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool):
                return node.value
            raise RuntimeError(f"Invalid only expression value: {expression}")
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            return not _eval(node.operand)
        if isinstance(node, ast.BoolOp):
            values = [_eval(value) for value in node.values]
            if isinstance(node.op, ast.And):
                return all(values)
            if isinstance(node.op, ast.Or):
                return any(values)
        raise RuntimeError(f"Unsupported only expression: {expression}")

    return _eval(tree)


def _dedent_only_block_lines(block: list[str], indent: int) -> list[str]:
    base = indent + 3
    dedented: list[str] = []
    for line in block:
        if not line.strip():
            dedented.append("")
        elif len(line) > base:
            dedented.append(line[base:])
        else:
            dedented.append(line.lstrip())
    return dedented
