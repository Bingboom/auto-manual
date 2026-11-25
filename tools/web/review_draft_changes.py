"""What changed in a review draft's Web copy from one version to the next.

A Web candidate's copy is the draft's manual copy without its review layer
(``review_draft_overlay``), so comparing two stripped drafts compares their
candidates without converting either. ``compare`` lists, per chapter, the
blocks added, removed or changed, a changed block with a character diff;
figures take part as ``［図］<file>`` entries, so a swapped image shows too.

``write_changes`` records the working draft against its previous version as
``web-changes.json`` beside ``draft.json``; the private review site renders it
on the line page. The previous version is the newest commit in the line's Git
history whose ``draft.json`` names another version, or a directory copy of it
(the writing procedure keeps one in scratch).
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from difflib import SequenceMatcher
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
from typing import Any
from urllib.parse import unquote, urlparse

from bs4 import BeautifulSoup, Comment, NavigableString, Tag

from tools.web.review_draft_overlay import strip_review_layer

SCHEMA = "review-draft-web-changes/v1"
CHANGES_JSON = "web-changes.json"
DRAFT_MANIFEST = "draft.json"
INLINE_TAGS = frozenset({
    "a", "abbr", "b", "br", "code", "del", "em", "i", "ins", "mark", "s", "small",
    "span", "strong", "sub", "sup", "u",
})
_SPACE = re.compile(r"\s+")

GitRunner = Callable[[Sequence[str], Path], str]


@dataclass(frozen=True)
class Page:
    page_id: str
    title: str
    blocks: tuple[str, ...]


def _owner(node: NavigableString) -> Tag | None:
    owner = node.parent
    while owner is not None and owner.name in INLINE_TAGS:
        owner = owner.parent
    return owner


def blocks_of(section: Tag) -> tuple[str, ...]:
    """Visible copy of one chapter as ordered blocks: text by its block owner, figures by file."""

    order: list[object] = []
    texts: dict[int, list[str]] = {}
    for node in section.descendants:
        if isinstance(node, Tag) and node.name == "img":
            name = PurePosixPath(unquote(urlparse(str(node.get("src") or "")).path)).name
            order.append(f"［図］{name}")
        elif isinstance(node, NavigableString) and not isinstance(node, Comment) and node.strip():
            owner = _owner(node)
            key = id(owner)
            if key not in texts:
                texts[key] = []
                order.append(key)
            texts[key].append(str(node))
    blocks = [
        _SPACE.sub(" ", "".join(texts[item])).strip() if isinstance(item, int) else str(item)
        for item in order
    ]
    return tuple(block for block in blocks if block)


def pages_of(html: str) -> list[Page]:
    soup = BeautifulSoup(html, "html.parser")
    article = soup.select_one("article#furo-main-content")
    if article is None:
        raise ValueError("review draft has no manual article (article#furo-main-content)")
    strip_review_layer(article)
    body = article.find("div", recursive=False) or article
    pages = []
    for section in body.find_all("section", recursive=False):
        if section.get("id"):
            heading = section.find(["h1", "h2"])
            title = _SPACE.sub(" ", heading.get_text(" ", strip=True)) if heading else ""
            pages.append(Page(str(section["id"]), title, blocks_of(section)))
    return pages


def _segments(before: str, after: str) -> list[list[str]]:
    segments: list[list[str]] = []
    matcher = SequenceMatcher(None, before, after, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            segments.append(["=", before[i1:i2]])
            continue
        if i2 > i1:
            segments.append(["-", before[i1:i2]])
        if j2 > j1:
            segments.append(["+", after[j1:j2]])
    return segments


def _block_changes(before: Sequence[str], after: Sequence[str]) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []
    matcher = SequenceMatcher(None, list(before), list(after), autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        old, new = list(before[i1:i2]), list(after[j1:j2])
        for previous, current in zip(old, new, strict=False):  # extra blocks follow below
            changes.append({"kind": "changed", "before": previous, "after": current,
                            "segments": _segments(previous, current)})
        changes += [{"kind": "removed", "before": text} for text in old[len(new):]]
        changes += [{"kind": "added", "after": text} for text in new[len(old):]]
    return changes


def compare(base: Sequence[Page], head: Sequence[Page]) -> list[dict[str, Any]]:
    """Per-chapter block changes from ``base`` to ``head``, in ``head`` order."""

    remaining = {page.page_id: page for page in base}
    result = []
    for page in head:
        old = remaining.pop(page.page_id, None)
        changes = _block_changes(old.blocks if old else (), page.blocks)
        if changes:
            result.append({"page_id": page.page_id, "title": page.title, "changes": changes})
    for page in remaining.values():
        result.append({"page_id": page.page_id, "title": page.title,
                       "changes": [{"kind": "removed", "before": text} for text in page.blocks]})
    return result


def _git(args: Sequence[str], cwd: Path) -> str:
    completed = subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)
    return completed.stdout


def previous_version(line: Path, *, git: GitRunner = _git) -> tuple[str, dict[str, Any]] | None:
    """The newest commit whose ``draft.json`` names a version other than the working one."""

    current = json.loads((line / DRAFT_MANIFEST).read_text(encoding="utf-8"))["version"]
    top = Path(git(["rev-parse", "--show-toplevel"], line).strip())
    relative = (line.resolve() / DRAFT_MANIFEST).relative_to(top.resolve()).as_posix()
    for revision in git(["log", "--format=%H", "--", relative], top).split():
        manifest = json.loads(git(["show", f"{revision}:{relative}"], top))
        if manifest.get("version") != current:
            return revision, manifest
    return None


def changes_record(
    line: Path, *, base_dir: Path | None = None, git: GitRunner = _git,
) -> dict[str, Any]:
    """Compare the working draft in ``line`` with its previous version."""

    manifest = json.loads((line / DRAFT_MANIFEST).read_text(encoding="utf-8"))
    head_html = (line / manifest["html"]).read_text(encoding="utf-8")
    if base_dir is not None:
        base_manifest = json.loads((base_dir / DRAFT_MANIFEST).read_text(encoding="utf-8"))
        base_html = (base_dir / base_manifest["html"]).read_text(encoding="utf-8")
        source = "directory"
    else:
        found = previous_version(line, git=git)
        if found is None:
            raise ValueError(f"{line}: no earlier version of this draft in its Git history")
        revision, base_manifest = found
        top = Path(git(["rev-parse", "--show-toplevel"], line).strip())
        html_path = (line.resolve() / str(base_manifest["html"])).relative_to(top.resolve()).as_posix()
        base_html = git(["show", f"{revision}:{html_path}"], top)
        source = f"git {revision[:12]}"
    pages = compare(pages_of(base_html), pages_of(head_html))
    counts = {kind: sum(1 for page in pages for change in page["changes"] if change["kind"] == kind)
              for kind in ("changed", "added", "removed")}
    return {
        "schema": SCHEMA,
        "base": {"version": str(base_manifest.get("version") or ""), "from": source},
        "head": {"version": str(manifest["version"]),
                 "html_sha256": hashlib.sha256(head_html.encode("utf-8")).hexdigest()},
        "counts": counts,
        "pages": pages,
    }


def write_changes(line: Path, *, base_dir: Path | None = None, git: GitRunner = _git) -> dict[str, Any]:
    record = changes_record(line, base_dir=base_dir, git=git)
    (line / CHANGES_JSON).write_text(json.dumps(record, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return record


__all__ = [
    "CHANGES_JSON",
    "Page",
    "SCHEMA",
    "blocks_of",
    "changes_record",
    "compare",
    "pages_of",
    "previous_version",
    "write_changes",
]
