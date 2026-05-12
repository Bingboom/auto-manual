from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


@dataclass(frozen=True)
class FeishuDocCreateResult:
    document_id: str
    document_url: str


def _nested_text(payload: dict[str, Any], path: tuple[str, ...]) -> str:
    current: Any = payload
    for key in path:
        if not isinstance(current, dict):
            return ""
        current = current.get(key)
    return str(current or "").strip()


def parse_feishu_doc_create_payload(payload: dict[str, Any]) -> FeishuDocCreateResult:
    doc_id = ""
    for path in (
        ("doc_id",),
        ("document_id",),
        ("token",),
        ("data", "doc_id"),
        ("data", "document_id"),
        ("data", "token"),
        ("data", "document", "doc_id"),
        ("data", "document", "document_id"),
        ("data", "document", "token"),
    ):
        doc_id = _nested_text(payload, path)
        if doc_id:
            break

    doc_url = ""
    for path in (
        ("doc_url",),
        ("url",),
        ("document_url",),
        ("data", "doc_url"),
        ("data", "url"),
        ("data", "document_url"),
        ("data", "document", "doc_url"),
        ("data", "document", "url"),
        ("data", "document", "document_url"),
    ):
        doc_url = _nested_text(payload, path)
        if doc_url:
            break

    if not doc_url:
        raise RuntimeError("docs +create response is missing doc_url")
    return FeishuDocCreateResult(document_id=doc_id, document_url=doc_url)


def create_feishu_doc_from_markdown(
    *,
    cli_bin: str,
    identity: str,
    markdown_path: Path,
    destination: Any,
    title: str,
    run_lark_cli_json: Callable[..., dict[str, Any]],
    cli_relative_file_arg: Callable[[Path], str],
) -> FeishuDocCreateResult:
    if not markdown_path.exists():
        raise RuntimeError(f"MyST markdown output was not created: {markdown_path}")

    args = [
        "docs",
        "+create",
        "--api-version",
        "v2",
        "--as",
        identity,
        "--markdown",
        "@" + cli_relative_file_arg(markdown_path),
    ]
    clean_title = title.strip()
    if clean_title:
        args += ["--title", clean_title]
    parent_wiki_token = str(getattr(destination, "parent_wiki_token", "") or "").strip()
    space_id = str(getattr(destination, "space_id", "") or "").strip()
    if parent_wiki_token:
        args += ["--wiki-node", parent_wiki_token]
    elif space_id:
        args += ["--wiki-space", space_id]

    payload = run_lark_cli_json(cli_bin=cli_bin, args=args)
    return parse_feishu_doc_create_payload(payload)


__all__ = [
    "FeishuDocCreateResult",
    "create_feishu_doc_from_markdown",
    "parse_feishu_doc_create_payload",
]
