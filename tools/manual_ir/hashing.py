"""Canonical hashing helpers shared by manual IR builders and validators."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def value_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ordered_files_sha256(files: Iterable[tuple[str, Path]]) -> str:
    digest = hashlib.sha256()
    for display_path, path in files:
        digest.update(display_path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(bytes.fromhex(file_sha256(path)))
        digest.update(b"\0")
    return digest.hexdigest()


# Matches `<semantic_name>_<feishu-file-token>.<ext>` wherever the basename
# appears — full `_attachments/...` paths in CSV cells and RST directives, and
# bare basenames inside rendered LaTeX macro arguments alike. The token is a
# single 16+ char alphanumeric run; the all-lowercase lookahead keeps long
# English name words (e.g. `internationalization`) out of the match.
_ATTACHMENT_TOKEN_RE = re.compile(
    r"([A-Za-z0-9_][A-Za-z0-9_.\-]*?)"
    r"_(?![a-z]{16,}\.)[A-Za-z0-9]{16,}"
    r"(\.(?:png|jpe?g|pdf|svg))"
)


def _token_normalized_sha256(text: str) -> str:
    return hashlib.sha256(
        _ATTACHMENT_TOKEN_RE.sub(r"\1\2", text).encode("utf-8")
    ).hexdigest()


def _normalized_table_sha256(path: Path) -> str:
    """Digest of one synced table with volatile attachment tokens stripped.

    Synced CSVs embed attachment file paths whose basenames end in a Feishu
    file token, and tokens rotate on EVERY export — so the raw bytes of e.g.
    ``symbols_blocks.csv`` differ between two syncs of identical data. Strip
    the token (keep the semantic name and extension) before hashing so the
    identity tracks content, not export runs.
    """
    return _token_normalized_sha256(path.read_text(encoding="utf-8", errors="replace"))


def _normalized_page_sha256(path: Path) -> str:
    """Digest of one bundle page with volatile attachment tokens stripped.

    Finalized bundle pages embed staged attachment paths whose basenames end
    in a Feishu file token, and tokens rotate on EVERY export — the same
    volatility the snapshot identity already normalizes away. The per-page
    ``source_sha256`` feeds the reference-layout contract pins, so hash the
    token-normalized text: identical page content pins identically across
    export runs, while any real content change still changes the digest.
    """
    return _token_normalized_sha256(path.read_text(encoding="utf-8", errors="replace"))


def _snapshot_sha256(data_root: Path | None) -> str | None:
    """Content identity of the phase2 snapshot, stable across re-syncs.

    Two volatility sources used to make this pin structurally un-matchable on
    CI (part of why the 1.6 publish had to bypass the same-source gate):
    hashing the manifest FILE picked up ``generated_at``/tool metadata, and
    the per-table digests picked up rotated attachment tokens embedded in the
    CSVs. Hash the canonical set of token-normalized per-table digests
    instead: identical data ⇒ identical identity, whenever and wherever the
    sync ran; a real value change still changes the identity. Falls back to
    the manifest file hash for legacy manifests without a tables list.
    """
    if data_root is None:
        return None
    manifest = data_root / "snapshot_manifest.json"
    if not manifest.is_file():
        return None
    try:
        payload = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return file_sha256(manifest)
    tables = payload.get("tables")
    if not isinstance(tables, list) or not tables:
        return file_sha256(manifest)
    canonical: list[tuple[str, str, str]] = []
    for entry in tables:
        if not isinstance(entry, dict):
            continue
        logical_name = str(entry.get("logical_name"))
        file_name = str(entry.get("file_name"))
        table_path = data_root / file_name
        if table_path.is_file():
            digest = _normalized_table_sha256(table_path)
        else:
            digest = str(entry.get("sha256"))
        canonical.append((logical_name, file_name, digest))
    return value_sha256(sorted(canonical))
