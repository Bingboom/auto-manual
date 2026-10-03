from __future__ import annotations

import html
import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


BULLET_RE = re.compile(r"^(\s*)-\s+(.*)$")
HTML_ONLY_RE = re.compile(r"^\s*\.\. only:: html\s*$")


class _HtmlListItemParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._stack: list[list[str]] = []
        self.items: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "li":
            self._stack.append([])
        elif tag.lower() == "br" and self._stack:
            self._stack[-1].append(" ")

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "li" or not self._stack:
            return
        item = _normalize_text("".join(self._stack.pop()))
        if item:
            self.items.append(item)

    def handle_data(self, data: str) -> None:
        if self._stack:
            self._stack[-1].append(data)


def _normalize_text(value: str) -> str:
    text = html.unescape(value).replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip()


def _line_indent(line: str) -> int:
    return len(line) - len(line.lstrip())


def extract_rst_list_items(text: str) -> list[str]:
    lines = text.splitlines()
    html_start = next((idx for idx, line in enumerate(lines) if HTML_ONLY_RE.match(line)), len(lines))

    items: list[str] = []
    current: list[str] = []
    current_indent = 0

    def flush() -> None:
        if not current:
            return
        item = _normalize_text(" ".join(current))
        if item:
            items.append(item)
        current.clear()

    for line in lines[:html_start]:
        bullet = BULLET_RE.match(line)
        if bullet:
            flush()
            current_indent = len(bullet.group(1))
            current.append(bullet.group(2).strip())
            continue

        stripped = line.strip()
        if current and stripped and _line_indent(line) > current_indent:
            current.append(stripped)
        else:
            flush()
    flush()
    return items


def extract_html_list_items(text: str) -> list[str]:
    parser = _HtmlListItemParser()
    parser.feed(text)
    parser.close()
    return parser.items


def _sample(items: set[str]) -> str:
    value = next(iter(sorted(items)), "")
    sample = value if len(value) <= 160 else f"{value[:157]}..."
    return sample.encode("ascii", errors="backslashreplace").decode("ascii")


def _collect_file_issues(
    *,
    path: Path,
    issue_cls: type[Any],
    model: str | None,
    region: str | None,
) -> list[Any]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    if ".. raw:: html" not in text or "<li" not in text:
        return []

    rst_items = set(extract_rst_list_items(text))
    html_items = set(extract_html_list_items(text))
    if not rst_items or not html_items:
        return []

    rst_only = rst_items - html_items
    html_only = html_items - rst_items
    if not rst_only and not html_only:
        return []

    details: list[str] = []
    if rst_only:
        details.append(f"RST-only sample: '{_sample(rst_only)}'")
    if html_only:
        details.append(f"HTML-only sample: '{_sample(html_only)}'")

    return [
        issue_cls(
            code="DUPLICATE_RENDER_TEXT_MISMATCH",
            message=(
                "RST list text and raw HTML list text diverge. "
                f"Keep the RST list as the source wording and update the raw HTML list. "
                f"RST-only={len(rst_only)} HTML-only={len(html_only)}. {'; '.join(details)}"
            ),
            model=model,
            region=region,
            path=path,
        )
    ]


def _iter_rst_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(path for path in root.rglob("*.rst") if path.is_file())


def collect_duplicate_render_text_issues(
    *,
    repo_root: Path,
    docs_dir: Path,
    bundle_dir: Path,
    model: str | None,
    region: str | None,
    issue_cls: type[Any],
) -> list[Any]:
    del repo_root

    issues: list[Any] = []
    for root in (docs_dir / "templates", bundle_dir):
        for path in _iter_rst_files(root):
            issues.extend(
                _collect_file_issues(
                    path=path,
                    issue_cls=issue_cls,
                    model=model,
                    region=region,
                )
            )
    return issues
