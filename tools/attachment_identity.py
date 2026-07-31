"""Stable attachment identity across Feishu file-token refreshes.

Synced attachment filenames end in an opaque file token. Review RST is a
frozen content surface and may legitimately retain an older token after the
active snapshot refreshes the same semantic icon. Resolve the stable prefix
only when it identifies exactly one current file; ambiguity remains a hard
error instead of silently selecting the wrong artwork.
"""
from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path


_TOKEN_RE = re.compile(r"^(?P<identity>.+)_(?P<token>[A-Za-z0-9]{16,})$")
_DISPLAY_ORDINAL_RE = re.compile(r"^\d+_")
_ATTACHMENT_REF_RE = re.compile(
    r"(?P<path>[^\s{}\"']*?_attachments/(?P<category>lcd_icons|symbols)/"
    r"(?P<name>[^\s{}\"']+\.(?:png|jpe?g|pdf|svg)))",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class AttachmentAliasReport:
    aliases: int
    rewritten_files: int
    missing: tuple[str, ...]


def semantic_attachment_key(value: str | Path) -> tuple[str, str]:
    """Return the stable filename identity and lower-case extension."""
    path = Path(value)
    match = _TOKEN_RE.match(path.stem)
    identity = match.group("identity") if match else path.stem
    # Row ordinals are presentation metadata and can change when the source
    # table is reordered.  Keep the descriptive slug as the stable identity;
    # duplicate slugs still fail closed as ambiguous in the resolver below.
    identity = _DISPLAY_ORDINAL_RE.sub("", identity, count=1)
    return identity.casefold(), path.suffix.casefold()


def resolve_semantic_attachment(directory: Path, reference: str | Path) -> Path | None:
    """Resolve an exact or uniquely same-semantic attachment in ``directory``."""
    exact = directory / Path(reference).name
    if exact.is_file():
        return exact
    if not directory.is_dir():
        return None
    key = semantic_attachment_key(reference)
    matches = sorted(
        path for path in directory.iterdir()
        if path.is_file() and semantic_attachment_key(path) == key
    )
    if len(matches) > 1:
        names = ", ".join(path.name for path in matches)
        raise ValueError(f"ambiguous semantic attachment {Path(reference).name}: {names}")
    return matches[0] if matches else None


def stage_bundle_attachment_aliases(bundle_dir: Path, data_root: Path) -> AttachmentAliasReport:
    """Stage current files under frozen review basenames and rewrite stale paths.

    Raw LaTeX component macros use the basename, so aliases intentionally keep
    the frozen name. RST image directives are normalized to the staged
    ``_repo_assets`` location so Sphinx can resolve them from any page folder.
    """
    aliases: set[tuple[str, str]] = set()
    missing: set[str] = set()
    rewritten_files = 0
    for rst in sorted(bundle_dir.rglob("*.rst")):
        text = rst.read_text(encoding="utf-8")

        def replace(match: re.Match[str]) -> str:
            category = match.group("category")
            name = match.group("name")
            source = resolve_semantic_attachment(
                data_root / "_attachments" / category,
                name,
            )
            if source is None:
                missing.add(f"{category}/{name}")
                return match.group("path")
            target = (
                bundle_dir / "_repo_assets" / "data" / "phase2" /
                "_attachments" / category / name
            )
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                shutil.copy2(source, target)
            aliases.add((category, name))
            return target.relative_to(bundle_dir).as_posix()

        rewritten = _ATTACHMENT_REF_RE.sub(replace, text)
        if rewritten != text:
            rst.write_text(rewritten, encoding="utf-8")
            rewritten_files += 1
    return AttachmentAliasReport(
        aliases=len(aliases),
        rewritten_files=rewritten_files,
        missing=tuple(sorted(missing)),
    )


def frozen_attachment_names(text: str) -> dict[tuple[str, str, str], str]:
    """Map (category, identity, extension) -> frozen basename found in ``text``.

    Identities carried by more than one distinct basename are dropped —
    preservation must never guess between two frozen candidates.
    """
    names: dict[tuple[str, str, str], str] = {}
    ambiguous: set[tuple[str, str, str]] = set()
    for match in _ATTACHMENT_REF_RE.finditer(text):
        name = match.group("name")
        identity, ext = semantic_attachment_key(name)
        key = (match.group("category").casefold(), identity, ext)
        if key in names and names[key] != name:
            ambiguous.add(key)
        names.setdefault(key, name)
    for key in ambiguous:
        names.pop(key, None)
    return names


def preserve_frozen_attachment_names(*, frozen_text: str, refreshed_text: str) -> tuple[str, int]:
    """Rewrite refreshed attachment basenames back to their frozen names.

    A re-synced page re-emits attachment references with the CURRENT Feishu
    file token in the basename. Tokens rotate on every export, so copying the
    refreshed text verbatim makes review pages byte-unstable across syncs —
    which is exactly what breaks the same-source reference-layout gate on CI
    (a pin made from any one sync can never match the next). When a refreshed
    reference's semantic identity matches one already present in the frozen
    page, keep the frozen basename; ``stage_bundle_attachment_aliases``
    resolves it to the current file at build time. New identities keep their
    refreshed name; ambiguous identities stay untouched (fail-open — the gate
    still reports them rather than silently guessing).
    """
    frozen = frozen_attachment_names(frozen_text)
    if not frozen:
        return refreshed_text, 0
    preserved = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal preserved
        name = match.group("name")
        identity, ext = semantic_attachment_key(name)
        key = (match.group("category").casefold(), identity, ext)
        old = frozen.get(key)
        if old is None or old == name:
            return match.group("path")
        preserved += 1
        return match.group("path")[: -len(name)] + old

    return _ATTACHMENT_REF_RE.sub(replace, refreshed_text), preserved
