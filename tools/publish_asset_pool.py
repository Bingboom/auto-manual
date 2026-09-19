#!/usr/bin/env python3
"""Keep one physical copy of every asset in the frozen Web publish tree.

Assembly used to write each manual asset into the RTD source twice — once
beside the Markdown it came from and once under ``_static/manual-assets`` so
raw ``<img>`` tags resolve — and then again for every sibling language that
shares the same artwork. Only the ``_static`` copy is ever referenced, and the
artwork is routinely byte-identical across languages and models, so the frozen
tree grew several times larger than the content it carries. That size is not
cosmetic: ``tools.rtd_deployment_receipt`` inventories the whole publish tree
and refuses to deploy past a fixed ceiling, so the duplication was consuming
the headroom that new languages need.

This module resolves every reference, stores one copy per unique content hash
under a pool, repoints the references, and drops what is left over. Rewriting
touches the ``src`` attribute only: ``data-web-finished-panel-path`` carries
the logical asset identity that the published stylesheet selects on, so it has
to survive unchanged.

The Markdown-adjacent ``assets`` directories disappear with everything else
here. ``docs/publish/web`` is a render tree; the self-contained replayable
bundle stays in ``docs/publish/sources``, which this module never touches.
"""

from __future__ import annotations

import hashlib
import posixpath
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlparse

POOL_SEGMENT = "_pool"

_HTML_IMG_SRC_RE = re.compile(r"(<img\b[^>]*?\bsrc=)([\"'])([^\"']+)(\2)", re.IGNORECASE)
_MARKDOWN_IMAGE_RE = re.compile(r"(!\[[^\]]*\]\()(\s*)([^)\s]+)")


@dataclass(frozen=True)
class PoolReport:
    unique_assets: int
    collapsed_files: int
    rewritten_references: int
    bytes_before: int
    bytes_after: int

    @property
    def bytes_freed(self) -> int:
        return self.bytes_before - self.bytes_after


def _is_local_reference(raw: str) -> bool:
    parsed = urlparse(raw)
    return not (parsed.scheme or parsed.netloc or parsed.path.startswith("/"))


def _referenced_path(raw: str, *, markdown_path: Path) -> Path | None:
    if not _is_local_reference(raw):
        return None
    parsed = urlparse(raw)
    if not parsed.path:
        return None
    return (markdown_path.parent / unquote(parsed.path)).resolve(strict=False)


def _rewrite_suffix(raw: str, replacement: str) -> str:
    parsed = urlparse(raw)
    if parsed.query:
        replacement = f"{replacement}?{parsed.query}"
    if parsed.fragment:
        replacement = f"{replacement}#{parsed.fragment}"
    return replacement


def _asset_files(output_dir: Path, *, pool_root: Path) -> list[Path]:
    """Every staged asset byte, whether or not a manual still points at it."""
    found: list[Path] = []
    for path in output_dir.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        relative = path.relative_to(output_dir)
        if "assets" not in relative.parts and not _under(path, output_dir / "_static" / "manual-assets"):
            continue
        if _under(path, pool_root):
            continue
        found.append(path)
    return sorted(found)


def _under(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _markdown_files(output_dir: Path) -> list[Path]:
    return sorted(output_dir.rglob("*.md"))


def _reference_values(text: str):
    for match in _HTML_IMG_SRC_RE.finditer(text):
        yield match.group(3)
    for match in _MARKDOWN_IMAGE_RE.finditer(text):
        yield match.group(3)


def _collect_references(output_dir: Path) -> set[Path]:
    found: set[Path] = set()
    for markdown_path in _markdown_files(output_dir):
        text = markdown_path.read_text(encoding="utf-8")
        for raw in _reference_values(text):
            resolved = _referenced_path(raw, markdown_path=markdown_path)
            if resolved is not None:
                found.add(resolved)
    return found


def _rewrite_references(output_dir: Path, *, pooled_for: dict[Path, Path]) -> int:
    rewritten = 0
    for markdown_path in _markdown_files(output_dir):
        text = markdown_path.read_text(encoding="utf-8")
        start = markdown_path.parent.as_posix()

        def pooled_target(raw: str) -> str | None:
            resolved = _referenced_path(raw, markdown_path=markdown_path)
            pooled = pooled_for.get(resolved) if resolved is not None else None
            if pooled is None:
                return None
            return _rewrite_suffix(raw, posixpath.relpath(pooled.as_posix(), start=start))

        def replace_html(match: re.Match[str]) -> str:
            nonlocal rewritten
            target = pooled_target(match.group(3))
            if target is None:
                return match.group(0)
            rewritten += 1
            return f"{match.group(1)}{match.group(2)}{target}{match.group(4)}"

        def replace_markdown(match: re.Match[str]) -> str:
            nonlocal rewritten
            target = pooled_target(match.group(3))
            if target is None:
                return match.group(0)
            rewritten += 1
            return f"{match.group(1)}{match.group(2)}{target}"

        updated = _MARKDOWN_IMAGE_RE.sub(replace_markdown, _HTML_IMG_SRC_RE.sub(replace_html, text))
        if updated != text:
            markdown_path.write_text(updated, encoding="utf-8")
    return rewritten


def _prune_empty_directories(output_dir: Path, *, keep: Path) -> None:
    for path in sorted(output_dir.rglob("*"), key=lambda item: len(item.parts), reverse=True):
        if path == keep or not path.is_dir() or path.is_symlink() or _under(path, keep):
            continue
        if not any(path.iterdir()):
            path.rmdir()


def _reference_fingerprint(output_dir: Path) -> dict[str, list[tuple[str, str | None]]]:
    """Per manual, the content every reference resolves to.

    This is the property pooling must not disturb: the same manual must keep
    pointing at the same bytes, in the same order. Comparing fingerprints taken
    before and after also leaves references that were already broken exactly as
    broken as they were, instead of turning a pre-existing defect into a new
    assembly failure.
    """
    fingerprint: dict[str, list[tuple[str, str | None]]] = {}
    digests: dict[Path, str] = {}
    for markdown_path in _markdown_files(output_dir):
        row: list[tuple[str, str | None]] = []
        for raw in _reference_values(markdown_path.read_text(encoding="utf-8")):
            resolved = _referenced_path(raw, markdown_path=markdown_path)
            if resolved is None:
                row.append(("external", raw))
            elif not resolved.is_file():
                row.append(("missing", None))
            else:
                digest = digests.get(resolved)
                if digest is None:
                    digest = hashlib.sha256(resolved.read_bytes()).hexdigest()
                    digests[resolved] = digest
                row.append(("asset", digest))
        fingerprint[markdown_path.relative_to(output_dir).as_posix()] = row
    return fingerprint


def _assert_same_rendering(before: dict, after: dict) -> None:
    changed = sorted(name for name in before.keys() | after.keys() if before.get(name) != after.get(name))
    if changed:
        raise RuntimeError(
            "pooling changed what these manuals point at:\n  " + "\n  ".join(changed[:20])
        )


def pool_publish_assets(*, output_dir: Path) -> PoolReport:
    """Collapse the assembled RTD source onto one copy per unique asset."""
    output_dir = output_dir.resolve(strict=False)
    pool_root = output_dir / "_static" / "manual-assets" / POOL_SEGMENT
    if pool_root.exists():
        raise RuntimeError(f"asset pool is already assembled: {pool_root}")

    staged = _asset_files(output_dir, pool_root=pool_root)
    if not staged:
        return PoolReport(0, 0, 0, 0, 0)
    bytes_before = sum(path.stat().st_size for path in staged)

    before = _reference_fingerprint(output_dir)
    referenced = _collect_references(output_dir)
    pooled_for: dict[Path, Path] = {}
    by_digest: dict[str, Path] = {}
    for path in staged:
        if path not in referenced:
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        target = by_digest.get(digest)
        if target is None:
            target = pool_root / digest[:2] / f"{digest}{path.suffix.lower()}"
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
            by_digest[digest] = target
        pooled_for[path] = target

    rewritten = _rewrite_references(output_dir, pooled_for=pooled_for)
    for path in staged:
        path.unlink()
    _prune_empty_directories(output_dir, keep=pool_root)
    _assert_same_rendering(before, _reference_fingerprint(output_dir))

    still_referenced = _collect_references(output_dir)
    orphans = sorted(str(path.relative_to(output_dir)) for path in by_digest.values() if path not in still_referenced)
    if orphans:
        raise RuntimeError("pooled assets nothing points at: " + ", ".join(orphans[:10]))

    return PoolReport(
        unique_assets=len(by_digest),
        collapsed_files=len(staged),
        rewritten_references=rewritten,
        bytes_before=bytes_before,
        bytes_after=sum(path.stat().st_size for path in by_digest.values()),
    )
