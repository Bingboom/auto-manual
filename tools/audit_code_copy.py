#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import ast
import csv
import re
from collections import Counter
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Iterable

FIELDNAMES = (
    "file",
    "line",
    "symbol_or_context",
    "text",
    "copy_kind",
    "recommended_owner",
    "priority",
    "reason",
    "page_or_surface",
    "content_role",
    "source_lang",
    "source_key",
    "suggested_destination",
    "suggested_identifier",
    "rst_template_option",
    "duplicate_count",
    "operator_decision",
    "operator_notes",
)

DEFAULT_SCAN_ROOTS = ("tools", "build.py", "scripts", "integrations")
EXCLUDED_PARTS = {"__pycache__", ".git", ".mypy_cache", ".pytest_cache", ".ruff_cache", ".venv", "venv"}
EXCLUDED_REL_PREFIXES = ("docs/_build", "reports")

ALERT_LABELS = {
    "WARNING",
    "CAUTION",
    "DANGER",
    "NOTE",
    "TIP",
    "TIPS",
    "AVERTISSEMENT",
    "ATTENTION",
    "REMARQUE",
    "CONSEIL",
    "CONSEILS",
    "ADVERTENCIA",
    "PELIGRO",
    "PRECAUCIÓN",
    "PRECAUCION",
    "NOTA",
    "CONSEJO",
    "CONSEJOS",
    "WARNUNG",
    "VORSICHT",
    "HINWEIS",
    "TIPP",
    "AVVERTENZA",
    "ATTENZIONE",
    "SUGGERIMENTO",
    "ПОПЕРЕДЖЕННЯ",
    "УВАГА",
    "ПРИМІТКА",
    "ПОРАДИ",
    "警告",
    "注意",
    "ご注意",
    "提示",
    "说明",
    "備考",
    "備註",
    "备注",
}

DIAGNOSTIC_WORDS = (
    "error",
    "failed",
    "missing",
    "not found",
    "requires",
    "must be",
    "unsupported",
    "invalid",
    "expected",
    "cannot",
    "unable",
    "timed out",
)

LANG_CODES = {"en", "zh", "ja", "jp", "fr", "es", "pt", "pt-BR", "pt-br", "de", "it", "uk"}


@dataclass(frozen=True)
class AuditFinding:
    file: str
    line: int
    symbol_or_context: str
    text: str
    copy_kind: str
    recommended_owner: str
    priority: str
    reason: str
    page_or_surface: str = ""
    content_role: str = ""
    source_lang: str = ""
    source_key: str = ""
    suggested_destination: str = ""
    suggested_identifier: str = ""
    rst_template_option: str = ""
    duplicate_count: int = 1
    operator_decision: str = ""
    operator_notes: str = ""

    def as_row(self) -> dict[str, str]:
        return {
            "file": self.file,
            "line": str(self.line),
            "symbol_or_context": self.symbol_or_context,
            "text": self.text,
            "copy_kind": self.copy_kind,
            "recommended_owner": self.recommended_owner,
            "priority": self.priority,
            "reason": self.reason,
            "page_or_surface": self.page_or_surface,
            "content_role": self.content_role,
            "source_lang": self.source_lang,
            "source_key": self.source_key,
            "suggested_destination": self.suggested_destination,
            "suggested_identifier": self.suggested_identifier,
            "rst_template_option": self.rst_template_option,
            "duplicate_count": str(self.duplicate_count),
            "operator_decision": self.operator_decision,
            "operator_notes": self.operator_notes,
        }


@dataclass(frozen=True)
class Classification:
    copy_kind: str
    recommended_owner: str
    priority: str
    reason: str
    page_or_surface: str = ""
    content_role: str = ""
    suggested_destination: str = ""
    suggested_identifier: str = ""
    rst_template_option: str = ""


def _repo_relative(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _iter_python_files(repo_root: Path, scan_roots: Iterable[str]) -> list[Path]:
    files: list[Path] = []
    for raw_root in scan_roots:
        root = Path(raw_root)
        if not root.is_absolute():
            root = repo_root / root
        if root.is_file() and root.suffix == ".py":
            candidates = [root]
        elif root.is_dir():
            candidates = sorted(root.rglob("*.py"))
        else:
            continue
        for path in candidates:
            rel = _repo_relative(path, repo_root)
            if any(part in EXCLUDED_PARTS for part in path.parts):
                continue
            if any(rel == prefix or rel.startswith(f"{prefix}/") for prefix in EXCLUDED_REL_PREFIXES):
                continue
            files.append(path)
    return sorted(set(files))


def _docstring_node_ids(tree: ast.AST) -> set[int]:
    nodes: set[int] = set()
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if not isinstance(body, list) or not body:
            continue
        first = body[0]
        if (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
        ):
            nodes.add(id(first.value))
    return nodes


def _build_parent_map(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    parents: dict[ast.AST, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent
    return parents


def _node_chain(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> list[ast.AST]:
    chain = [node]
    while node in parents:
        node = parents[node]
        chain.append(node)
    return chain


def _target_name(target: ast.AST) -> str | None:
    if isinstance(target, ast.Name):
        return target.id
    if isinstance(target, ast.Attribute):
        return target.attr
    if isinstance(target, ast.Subscript):
        return _target_name(target.value)
    if isinstance(target, (ast.Tuple, ast.List)):
        names = [_target_name(item) for item in target.elts]
        return ",".join(name for name in names if name)
    return None


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _call_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""


def _context_for_node(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> str:
    symbols: list[str] = []
    for item in _node_chain(node, parents):
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            symbols.append(item.name)
        if isinstance(item, ast.Assign):
            names = [_target_name(target) for target in item.targets]
            names = [name for name in names if name]
            if names:
                symbols.append(",".join(names))
                break
        if isinstance(item, ast.AnnAssign):
            name = _target_name(item.target)
            if name:
                symbols.append(name)
                break
    if not symbols:
        return "<module>"
    return ".".join(reversed(symbols))


def _is_dict_key(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> bool:
    parent = parents.get(node)
    return isinstance(parent, ast.Dict) and node in parent.keys


def _dict_value_key(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> str | None:
    parent = parents.get(node)
    if not isinstance(parent, ast.Dict):
        return None
    for key, value in zip(parent.keys, parent.values):
        if value is not node:
            continue
        if isinstance(key, ast.Constant) and isinstance(key.value, str):
            return key.value
    return None


def _dict_value_key_path(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> list[str]:
    keys: list[str] = []
    child = node
    while child in parents:
        parent = parents[child]
        if isinstance(parent, ast.Dict):
            for key, value in zip(parent.keys, parent.values):
                if value is not child:
                    continue
                if isinstance(key, ast.Constant) and isinstance(key.value, str):
                    keys.append(key.value)
                break
        child = parent
    return list(reversed(keys))


def _keyword_name(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> str | None:
    parent = parents.get(node)
    if isinstance(parent, ast.keyword):
        return parent.arg
    return None


def _has_cli_ancestor(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> bool:
    for item in _node_chain(node, parents):
        if not isinstance(item, ast.Call):
            continue
        name = _call_name(item.func)
        if name.endswith("add_argument") or name.endswith("ArgumentParser") or name.endswith("add_parser"):
            return True
    return False


def _has_call_ancestor(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> bool:
    return any(isinstance(item, ast.Call) for item in _node_chain(node, parents))


def _normalize_text(value: str) -> str:
    return " ".join(value.replace("\u00a0", " ").split()).strip()


def _joined_string_text(node: ast.JoinedStr) -> str:
    parts: list[str] = []
    for value in node.values:
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            parts.append(value.value)
        elif isinstance(value, ast.FormattedValue):
            try:
                expr = ast.unparse(value.value)
            except Exception:  # pragma: no cover - ast.unparse is best-effort context only.
                expr = "expr"
            parts.append(f"{{{expr}}}")
    return "".join(parts)


def _joined_string_constant_ids(node: ast.JoinedStr) -> set[int]:
    return {id(value) for value in node.values if isinstance(value, ast.Constant) and isinstance(value.value, str)}


def _looks_like_path_or_token(text: str) -> bool:
    if not text:
        return True
    if text.startswith(("http://", "https://")):
        return True
    if "/" in text or "\\" in text:
        return " " not in text and not text.endswith(".")
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", text):
        return True
    if re.fullmatch(r"[A-Z0-9_./{}:-]+", text) and " " not in text:
        return True
    if text.startswith(("{{", "{%", "<!--", ".. ")):
        return True
    if "(?P<" in text or "\\s" in text or "\\d" in text:
        return True
    return False


def _looks_like_diagnostic(text: str) -> bool:
    lowered = text.casefold()
    if any(word in lowered for word in DIAGNOSTIC_WORDS):
        return True
    if lowered.startswith(("[build]", "[check]", "[doc-links]", "[maintainability]")):
        return True
    return False


def _looks_like_structural_value(text: str) -> bool:
    if text in {"banner", "icon_label", "140px"}:
        return True
    if re.fullmatch(r"\d+(?:px|pt|em|rem|%)", text):
        return True
    if "/" in text or "\\" in text:
        return True
    return False


def _looks_like_markup_or_code(text: str) -> bool:
    stripped = text.strip()
    if re.fullmatch(r"[\w.-]+\.(?:html|md|rst|py|css|js|png|jpg|jpeg|svg|json|yaml|yml)", stripped):
        return True
    if stripped.startswith(("<", "</", "<!", "{", "}", ".", "#", ":", ".. ")):
        return True
    if re.match(r"^(if|for|while|const|let|var|return|function|def|import|from)\b", stripped):
        return True
    if any(ch in stripped for ch in "{};=[]()"):
        return True
    code_markers = (
        "</",
        " class=",
        " id=",
        " data-",
        "function ",
        "const ",
        "document.",
        "window.",
        "=>",
        "${",
        "html.escape",
        "querySelector",
        "border:",
        "display:",
        "padding:",
        "margin:",
        "font-",
    )
    return any(marker in stripped for marker in code_markers)


def _has_human_words(text: str) -> bool:
    alpha = sum(ch.isalpha() for ch in text)
    if alpha < 3:
        return False
    if text.upper() in ALERT_LABELS:
        return True
    return " " in text or "." in text or any(ord(ch) > 127 for ch in text)


def _is_sentence_like(text: str) -> bool:
    return len(text) >= 45 or "." in text or "," in text or "。" in text or "、" in text


def _in_path(rel_path: str, *parts: str) -> bool:
    return any(part in rel_path for part in parts)


def _source_lang_from_key_path(key_path: list[str]) -> str:
    for key in key_path:
        if key in LANG_CODES or key.casefold() in {code.casefold() for code in LANG_CODES}:
            return key
    return ""


def _source_key_from_context(
    *,
    key_path: list[str],
    dict_value_key: str | None,
    keyword_name: str | None,
    classification: Classification,
) -> str:
    role = classification.content_role
    lang = _source_lang_from_key_path(key_path)
    usable_path = [key for key in key_path if key != lang]
    if keyword_name and not (role == "alt_text" and usable_path):
        usable_path.append(keyword_name)
    elif dict_value_key and (not usable_path or usable_path[-1] != dict_value_key):
        usable_path.append(dict_value_key)

    if role in {"alert_label", "generated_alt_text", "manual_title", "page_title_fallback"}:
        return role
    if usable_path:
        return ".".join(usable_path)
    return role


def _slug_text(text: str) -> str:
    slug = re.sub(r"[^0-9A-Za-z]+", "_", text.casefold()).strip("_")
    return slug or "copy"


def _materialize_identifier(template: str, *, source_key: str, text: str) -> str:
    if not template:
        return ""
    return (
        template.replace("<source_key>", source_key or _slug_text(text))
        .replace("<normalized_text>", _slug_text(text))
        .replace("<review_required>", source_key or "review_required")
    )


def _dedupe_key(text: str) -> str:
    return " ".join(text.casefold().split())


def classify_string(
    *,
    rel_path: str,
    line: int,
    context: str,
    text: str,
    is_dict_key: bool = False,
    dict_value_key: str | None = None,
    keyword_name: str | None = None,
    has_cli_ancestor: bool = False,
    has_call_ancestor: bool = False,
    include_ignored: bool = False,
) -> Classification | None:
    if not text or len(text) < 2:
        return None
    if "/tests/" in f"/{rel_path}" or rel_path.startswith("tests/"):
        return Classification("test_fixture", "ignore", "P2", "test fixture") if include_ignored else None
    if has_cli_ancestor:
        return Classification("tooling_message", "ignore", "P2", "CLI/help copy outside manual scope") if include_ignored else None
    if is_dict_key and not _has_human_words(text):
        return None

    if rel_path == "tools/signal_words.py" and context.startswith("_SIGNAL_WORDS") and not is_dict_key:
        return Classification(
            "manual_output",
            "phase2_blocks",
            "P0",
            "manual notice/signal word in Python",
            page_or_surface="shared_signal_words",
            content_role="signal_word",
            suggested_destination="symbols_blocks.csv signal_row",
            suggested_identifier="symbols_blocks.signal_row.<source_key>",
            rst_template_option="no: shared rendered term",
        )

    if rel_path == "tools/csv_pages/renderers_symbols.py":
        if (context.startswith("LANG_COPY") or ".LANG_COPY" in context) and not is_dict_key:
            if has_call_ancestor:
                return None
            if _looks_like_structural_value(text):
                return None
            if dict_value_key == "meaning":
                owner = "phase2_blocks"
                role = "signal_meaning"
                destination = "symbols_blocks.csv signal_row"
                identifier = "symbols_blocks.signal_row.meaning"
                rst_option = "maybe: only if meaning is fixed across all products/languages"
            elif dict_value_key in {"page_title", "header_symbol", "header_meaning", "alt", "label"}:
                owner = "manual_copy_source"
                role = {
                    "page_title": "page_title",
                    "header_symbol": "table_header",
                    "header_meaning": "table_header",
                    "alt": "alt_text",
                    "label": "signal_label",
                }[dict_value_key]
                destination = "Manual_Copy_Source.csv plus Translation Memory manual_copy tag"
                identifier = f"symbols.{dict_value_key}"
                rst_option = "yes: template copy is possible if not operator-maintained"
            else:
                return None
            return Classification(
                "renderer_fallback",
                owner,
                "P0",
                "legacy Symbols fallback copy still stored in renderer",
                page_or_surface="symbols",
                content_role=role,
                suggested_destination=destination,
                suggested_identifier=identifier,
                rst_template_option=rst_option,
            )
        if context.startswith(("SYMBOL_ASSETS", "SIGNAL_DEFAULT_ASSETS")) or any(
            token in context for token in ("SYMBOL_ASSETS", "SIGNAL_DEFAULT_ASSETS")
        ):
            if keyword_name != "alt":
                return None
            if _looks_like_structural_value(text):
                return None
            identifier_prefix = "symbols.signal" if "SIGNAL_DEFAULT_ASSETS" in context else "symbols.symbol"
            return Classification(
                "manual_output",
                "phase2_blocks",
                "P0",
                "Symbols alt text default in renderer",
                page_or_surface="symbols",
                content_role="alt_text",
                suggested_destination="derive from symbols_blocks.csv symbol_key or signal_row labels",
                suggested_identifier=f"{identifier_prefix}.<source_key>.alt",
                rst_template_option="no: derive from owned source rows",
            )

    if rel_path == "tools/word_bundle_html_rewrite.py":
        if context.startswith(("_ALERT_LABELS", "_WARNING_BOX_LABEL_TEXTS")):
            return Classification(
                "manual_output",
                "phase2_blocks",
                "P0",
                "manual alert label used by HTML/Word rewrite",
                page_or_surface="word_html_rewrite",
                content_role="alert_label",
                suggested_destination="symbols_blocks.csv signal_row label fields",
                suggested_identifier="symbols_blocks.signal_row.<symbol_key>.label_<lang>",
                rst_template_option="no: shared rewrite detection term",
            )
        if context.startswith("_SAFETY_SUBLIST_RULES") or "_SAFETY_SUBLIST_RULES" in context:
            return Classification(
                "manual_output",
                "phase2_blocks",
                "P0",
                "manual safety text rule stored in rewrite code",
                page_or_surface="word_html_rewrite",
                content_role="safety_snippet",
                suggested_destination="safety/business blocks table",
                suggested_identifier="safety_blocks.<review_required>",
                rst_template_option="maybe: RST if this is pure template prose",
            )
        if "banner placeholder" in text:
            return Classification(
                "manual_output",
                "manual_copy_source",
                "P0",
                "generated alt text used by HTML/Word rewrite",
                page_or_surface="word_html_rewrite",
                content_role="generated_alt_text",
                suggested_destination="Manual_Copy_Source.csv plus Translation Memory manual_copy tag if not derivable",
                suggested_identifier="alert_banner.alt",
                rst_template_option="yes: template alt is possible if static",
            )

    if rel_path == "tools/csv_pages/renderers_spec_parser.py" and text == "SPECIFICATIONS":
        return Classification(
            "manual_output",
            "manual_copy_source",
            "P0",
            "spec page title fallback stored in renderer",
            page_or_surface="specifications",
            content_role="page_title_fallback",
            suggested_destination="Manual_Copy_Source.csv plus Translation Memory manual_copy tag or spec title block",
            suggested_identifier="spec.page_title",
            rst_template_option="yes: template title is possible if fixed",
        )

    if rel_path == "tools/word_bundle_common.py" and text == "User Manual":
        return Classification(
            "manual_output",
            "config",
            "P0",
            "default Word title stored in code",
            page_or_surface="word_bundle",
            content_role="manual_title",
            suggested_destination="config or Manual_Copy_Source.csv plus Translation Memory manual_copy tag",
            suggested_identifier="manual.title.default",
            rst_template_option="no: document metadata/title",
        )

    if _looks_like_path_or_token(text):
        return None
    if _looks_like_diagnostic(text):
        return Classification("tooling_message", "ignore", "P2", "diagnostic/tooling message") if include_ignored else None
    if not _has_human_words(text):
        return None

    if _in_path(
        rel_path,
        "diff_report_render.py",
        "build_review_preview_pages.py",
        "build_docs_index.py",
    ):
        if _looks_like_markup_or_code(text):
            return None
        return Classification(
            "report_ui",
            "keep_in_code",
            "P1",
            "report/catalog UI copy, not manual body copy",
            page_or_surface="review_report",
            content_role="report_ui",
            suggested_destination="keep in code",
            suggested_identifier="",
            rst_template_option="no: not manual template content",
        )

    return None


def audit_paths(
    repo_root: Path,
    *,
    scan_roots: Iterable[str] = DEFAULT_SCAN_ROOTS,
    include_ignored: bool = False,
) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    for path in _iter_python_files(repo_root, scan_roots):
        rel_path = _repo_relative(path, repo_root)
        try:
            text = path.read_text(encoding="utf-8")
            tree = ast.parse(text, filename=rel_path)
        except (OSError, SyntaxError, UnicodeDecodeError):
            continue
        docstrings = _docstring_node_ids(tree)
        parents = _build_parent_map(tree)
        joined_string_chunks: set[int] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.JoinedStr):
                joined_string_chunks.update(_joined_string_constant_ids(node))
                normalized = _normalize_text(_joined_string_text(node))
                classification = classify_string(
                    rel_path=rel_path,
                    line=getattr(node, "lineno", 0),
                    context=_context_for_node(node, parents),
                    text=normalized,
                    is_dict_key=False,
                    dict_value_key=_dict_value_key(node, parents),
                    keyword_name=_keyword_name(node, parents),
                    has_cli_ancestor=_has_cli_ancestor(node, parents),
                    has_call_ancestor=_has_call_ancestor(node, parents),
                    include_ignored=include_ignored,
                )
                if classification is not None:
                    key_path = _dict_value_key_path(node, parents)
                    source_key = _source_key_from_context(
                        key_path=key_path,
                        dict_value_key=_dict_value_key(node, parents),
                        keyword_name=_keyword_name(node, parents),
                        classification=classification,
                    )
                    findings.append(
                        AuditFinding(
                            file=rel_path,
                            line=getattr(node, "lineno", 0),
                            symbol_or_context=_context_for_node(node, parents),
                            text=normalized,
                            copy_kind=classification.copy_kind,
                            recommended_owner=classification.recommended_owner,
                            priority=classification.priority,
                            reason=classification.reason,
                            page_or_surface=classification.page_or_surface,
                            content_role=classification.content_role,
                            source_lang=_source_lang_from_key_path(key_path),
                            source_key=source_key,
                            suggested_destination=classification.suggested_destination,
                            suggested_identifier=_materialize_identifier(
                                classification.suggested_identifier,
                                source_key=source_key,
                                text=normalized,
                            ),
                            rst_template_option=classification.rst_template_option,
                        )
                    )
                continue
            if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
                continue
            if id(node) in docstrings:
                continue
            if id(node) in joined_string_chunks:
                continue
            normalized = _normalize_text(node.value)
            classification = classify_string(
                rel_path=rel_path,
                line=getattr(node, "lineno", 0),
                context=_context_for_node(node, parents),
                text=normalized,
                is_dict_key=_is_dict_key(node, parents),
                dict_value_key=_dict_value_key(node, parents),
                keyword_name=_keyword_name(node, parents),
                has_cli_ancestor=_has_cli_ancestor(node, parents),
                has_call_ancestor=_has_call_ancestor(node, parents),
                include_ignored=include_ignored,
            )
            if classification is None:
                continue
            key_path = _dict_value_key_path(node, parents)
            source_key = _source_key_from_context(
                key_path=key_path,
                dict_value_key=_dict_value_key(node, parents),
                keyword_name=_keyword_name(node, parents),
                classification=classification,
            )
            findings.append(
                AuditFinding(
                    file=rel_path,
                    line=getattr(node, "lineno", 0),
                    symbol_or_context=_context_for_node(node, parents),
                    text=normalized,
                    copy_kind=classification.copy_kind,
                    recommended_owner=classification.recommended_owner,
                    priority=classification.priority,
                    reason=classification.reason,
                    page_or_surface=classification.page_or_surface,
                    content_role=classification.content_role,
                    source_lang=_source_lang_from_key_path(key_path),
                    source_key=source_key,
                    suggested_destination=classification.suggested_destination,
                    suggested_identifier=_materialize_identifier(
                        classification.suggested_identifier,
                        source_key=source_key,
                        text=normalized,
                    ),
                    rst_template_option=classification.rst_template_option,
                )
            )
    duplicate_counts = Counter(_dedupe_key(item.text) for item in findings)
    findings = [
        replace(item, duplicate_count=duplicate_counts[_dedupe_key(item.text)])
        for item in findings
    ]
    return sorted(findings, key=lambda item: (item.priority, item.file, item.line, item.text))


def write_csv(findings: list[AuditFinding], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        for finding in findings:
            writer.writerow(finding.as_row())


def _table_row(values: Iterable[str]) -> str:
    escaped = [str(value).replace("|", "\\|").replace("\n", " ") for value in values]
    return "| " + " | ".join(escaped) + " |"


def write_summary(findings: list[AuditFinding], path: Path, *, max_items: int = 120) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    by_priority = Counter(item.priority for item in findings)
    by_owner = Counter(item.recommended_owner for item in findings)
    by_kind = Counter(item.copy_kind for item in findings)
    by_role = Counter(item.content_role for item in findings if item.content_role)
    by_file = Counter(item.file for item in findings)
    p0_items = [item for item in findings if item.priority == "P0"]
    p1_items = [item for item in findings if item.priority == "P1"]
    p0_files = {item.file for item in p0_items}

    lines = [
        "# Code Copy Inventory",
        "",
        "Generated by `python3 tools/audit_code_copy.py`.",
        "",
        "## Scope",
        "",
        "- Scans Python source under `tools/`, `build.py`, `scripts/`, and `integrations/`.",
        "- Excludes tests, generated reports/build output, CLI help, diagnostics, logs, paths, and code-only HTML/CSS/JS fragments.",
        "- Focuses on copy that can enter manuals, review pages, PDF/HTML output, or operator-facing report pages.",
        "- The CSV includes blank `operator_decision` and `operator_notes` columns for manual triage.",
        "",
        "## Summary",
        "",
        f"- Total findings: {len(findings)}",
        f"- P0 manual-output migration candidates: {by_priority.get('P0', 0)}",
        f"- P1 report/catalog UI candidates: {by_priority.get('P1', 0)}",
        f"- P2 ignored/tooling findings included: {by_priority.get('P2', 0)}",
        "",
        "## Counts",
        "",
        _table_row(["Bucket", "Count"]),
        _table_row(["---", "---:"]),
    ]
    for name, count in sorted(by_owner.items()):
        lines.append(_table_row([f"owner:{name}", str(count)]))
    for name, count in sorted(by_kind.items()):
        lines.append(_table_row([f"kind:{name}", str(count)]))
    for name, count in sorted(by_role.items()):
        lines.append(_table_row([f"role:{name}", str(count)]))

    lines.extend(
        [
            "",
            "## Files",
            "",
            _table_row(["File", "Count"]),
            _table_row(["---", "---:"]),
        ]
    )
    for name, count in by_file.most_common():
        lines.append(_table_row([name, str(count)]))

    lines.extend(
        [
            "",
            "## P0 Migration Candidates",
            "",
            _table_row(["File", "Line", "Role", "Owner", "Suggested Destination", "RST Option", "Text"]),
            _table_row(["---", "---:", "---", "---", "---", "---", "---"]),
        ]
    )
    for item in p0_items[:max_items]:
        lines.append(
            _table_row(
                [
                    item.file,
                    str(item.line),
                    item.content_role,
                    item.recommended_owner,
                    item.suggested_destination,
                    item.rst_template_option,
                    item.text,
                ]
            )
        )
    if len(p0_items) > max_items:
        lines.append("")
        lines.append(f"Additional P0 findings omitted from this summary: {len(p0_items) - max_items}. See CSV.")

    lines.extend(
        [
            "",
            "## P1 Keep-In-Code Candidates",
            "",
            _table_row(["File", "Line", "Role", "Suggested Destination", "Text", "Reason"]),
            _table_row(["---", "---:", "---", "---", "---", "---"]),
        ]
    )
    for item in p1_items[:max_items]:
        lines.append(
            _table_row(
                [
                    item.file,
                    str(item.line),
                    item.content_role,
                    item.suggested_destination,
                    item.text,
                    item.reason,
                ]
            )
        )
    if len(p1_items) > max_items:
        lines.append("")
        lines.append(f"Additional P1 findings omitted from this summary: {len(p1_items) - max_items}. See CSV.")

    lines.extend(
        [
            "",
            "## Recommended Next Batches",
            "",
        ]
    )
    if "tools/csv_pages/renderers_symbols.py" in p0_files:
        lines.append(
            "- `tools/csv_pages/renderers_symbols.py`: migrate legacy `LANG_COPY` page chrome to `Manual_Copy_Source.csv` plus tagged Translation Memory; derive alt text from existing source rows and move signal meanings to `symbols_blocks.csv`."
        )
    if "tools/signal_words.py" in p0_files:
        lines.append(
            "- `tools/signal_words.py`: replace hardcoded signal words with `symbols_blocks.csv` "
            "signal-row metadata."
        )
    if "tools/word_bundle_html_rewrite.py" in p0_files:
        lines.append(
            "- `tools/word_bundle_html_rewrite.py`: move safety sublist snippets to a business blocks table if they remain manual content; alert labels should stay in `symbols_blocks.csv` `signal_row` `label_*` fields."
        )
    if "tools/csv_pages/renderers_spec_parser.py" in p0_files:
        lines.append("- `tools/csv_pages/renderers_spec_parser.py`: replace the `SPECIFICATIONS` title fallback with required manual copy source or data validation.")
    if "tools/word_bundle_common.py" in p0_files:
        lines.append("- `tools/word_bundle_common.py`: make the default Word manual title config/data driven.")
    if not p0_files:
        lines.append("- No P0 code-copy migration batches remain in the current scan.")

    lines.extend(
        [
            "",
            "## Migration Guidance",
            "",
            "- Move short manual labels, titles, and table headers to `Manual_Copy_Source.csv`; generate multilingual runtime copy from Translation Memory rows tagged `manual_copy`.",
            "- Move grouped business rows such as signal descriptions or symbol meanings to the relevant phase2 blocks table.",
            "- Move regional legal/support/channel values to config only when they are reused outside one template.",
            "- Keep report UI and technical diagnostics in code unless they become operator-maintained content.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit manual-facing copy embedded in Python code.")
    parser.add_argument("--repo-root", default=".", help="Repository root to inspect.")
    parser.add_argument(
        "--scan-root",
        action="append",
        dest="scan_roots",
        help="Root file/directory to scan. Defaults to tools, build.py, scripts, integrations.",
    )
    parser.add_argument("--write", default=None, help="Optional CSV output path.")
    parser.add_argument("--summary", default=None, help="Optional Markdown summary output path.")
    parser.add_argument("--include-ignored", action="store_true", help="Include ignored tooling/test findings.")
    parser.add_argument("--max-summary-items", type=int, default=120, help="Maximum P0/P1 rows to inline in summary.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    scan_roots = tuple(args.scan_roots or DEFAULT_SCAN_ROOTS)
    findings = audit_paths(repo_root, scan_roots=scan_roots, include_ignored=args.include_ignored)
    if args.write:
        write_csv(findings, repo_root / args.write)
    if args.summary:
        write_summary(findings, repo_root / args.summary, max_items=args.max_summary_items)
    print(
        "[audit-code-copy] findings="
        f"{len(findings)} p0={sum(1 for item in findings if item.priority == 'P0')} "
        f"p1={sum(1 for item in findings if item.priority == 'P1')} "
        f"p2={sum(1 for item in findings if item.priority == 'P2')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
